"""Protect reference trait projection and its existing compiler/handoff boundary."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.compile_prompt import compile_spec
from scripts.reference_profile import validate_reference_profile
from scripts.validate_spec import validate_spec

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))


class ReferenceProfileIntegrationTests(unittest.TestCase):
    def test_profiles_preserve_selected_traits_across_platforms(self):
        paths = list((ROOT / 'examples').glob('reference-profile-*.json'))
        self.assertTrue(paths)
        for path in paths:
            profile = json.loads(path.read_text(encoding='utf-8'))
            spec = read('tests/forward-specs/' + path.name)
            self.assertEqual(validate_reference_profile(profile), [])
            self.assertEqual(validate_spec(spec), [])
            before, profile_before = copy.deepcopy(spec), copy.deepcopy(profile)
            for platform in ('openai', 'flux', 'midjourney', 'generic'):
                with self.subTest(profile=path.name, platform=platform):
                    result = compile_spec(spec, platform, reference_profile=profile)
                    self.assertNotEqual(result['prompt_review']['status'], 'blocked')
                    for facet in profile['facets']:
                        if facet['decision'] in ('preserve', 'adapt'):
                            self.assertIn(facet['prompt'], result['prompt'])
                    self.assertNotIn('review_check', result['prompt'])
                    self.assertNotIn('reference_profile_audit', result['prompt'])
                    self.assertEqual(len(result['reference_profile_audit']['facets']), 14)
                    self.assertEqual(spec, before)
                    self.assertEqual(profile, profile_before)

    def test_attached_runtime_placeholder_is_not_executable(self):
        profile = read('examples/reference-profile-cream-rose.json')
        spec = read('tests/forward-specs/reference-profile-cream-rose.json')
        result = compile_spec(spec, 'openai', reference_profile=profile)
        self.assertEqual(result['prompt_review']['status'], 'ready')
        self.assertEqual(result['imagegen_call_plan']['status'], 'blocked')
        self.assertEqual(result['reference_profile_audit']['metadata']['attachment_status'], 'declared_must_attach')

    def test_profile_cannot_be_silently_combined_with_capsule(self):
        profile = read('examples/reference-profile-cream-rose.json')
        spec = read('tests/forward-specs/reference-profile-cream-rose.json')
        capsule = read('references/style-capsules/soft-editorial-character.json')
        with self.assertRaisesRegex(ValueError, 'one resolved reference profile'):
            compile_spec(spec, 'openai', capsule, reference_profile=profile)
        completed = subprocess.run([
            sys.executable, str(ROOT / 'scripts/compile_prompt.py'),
            str(ROOT / 'tests/forward-specs/reference-profile-cream-rose.json'),
            '--reference-profile', str(ROOT / 'examples/reference-profile-cream-rose.json'),
            '--style-capsule', str(ROOT / 'references/style-capsules/soft-editorial-character.json'),
        ], capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 2)

    def test_evidence_notes_stay_outside_generation_and_unknown_never_projects(self):
        profile = read('examples/reference-profile-cream-rose-text.json')
        spec = read('tests/forward-specs/reference-profile-cream-rose-text.json')
        profile['facets'][0]['observation'] = 'BACKSTAGE_OBSERVATION_ONLY'
        profile['facets'][0]['review_check'] = 'BACKSTAGE_REVIEW_ONLY'
        body = next(f for f in profile['facets'] if f['id'] == 'body')
        body.update(evidence='unknown', decision='unknown', source_ids=[], observation='', prompt='',
                    reason='原图只见头肩，没有可用的全身体型证据。', review_check='')
        result = compile_spec(spec, 'openai', reference_profile=profile)
        self.assertNotIn(body['reason'], result['prompt'])
        self.assertNotIn('BACKSTAGE_', result['prompt'])
        audit_body = next(f for f in result['reference_profile_audit']['facets'] if f['facet'] == 'body')
        self.assertEqual(audit_body['reason'], body['reason'])
        self.assertEqual(audit_body['projection_status'], 'not_adopted')
        body.update(decision='adapt', prompt='凭空新增一个全身体型。', review_check='不应被接受。')
        with self.assertRaisesRegex(ValueError, 'unknown evidence cannot'):
            compile_spec(spec, 'openai', reference_profile=profile)

    def test_context_residue_remains_blocked_after_projection(self):
        profile = read('examples/reference-profile-cream-rose-text.json')
        spec = read('tests/forward-specs/reference-profile-cream-rose-text.json')
        profile['facets'][0]['prompt'] = '继续保持上一版的角色。'
        result = compile_spec(spec, 'openai', reference_profile=profile, review_approved=True)
        self.assertEqual(result['prompt_review']['status'], 'blocked')
        self.assertEqual(result['imagegen_call_plan']['status'], 'blocked')


if __name__ == '__main__':
    unittest.main()
