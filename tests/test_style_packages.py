"""Validate opt-in style-package contracts and local-only evidence linkage."""
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from compile_prompt import compile_spec
from prompt_lint import lint_compiled_result
from validate_spec import validate_spec
from validate_style_capsule import validate_style_capsule


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))


class StylePackageTests(unittest.TestCase):
    def test_adopted_capsules_bind_real_review_cases(self):
        for name in ('changsheng-inhabited-fantasy', 'azure-summer-character-photography'):
            capsule = read_json(f'references/style-capsules/{name}.json')
            self.assertEqual(validate_style_capsule(capsule), [])
            scenarios = set()
            for evidence in capsule['validation']['evidence']:
                file, case_id = evidence['evidence_ref'].split('#', 1)
                self.assertTrue((ROOT / file).resolve().is_relative_to(ROOT))
                review = read_json(file)
                cases = [c for c in review['cases'] if c['case_id'] == case_id]
                self.assertEqual(len(cases), 1)
                case = cases[0]
                self.assertNotEqual(case['status'], 'partial')
                self.assertEqual(case['scenario'], evidence['scenario'])
                self.assertEqual(capsule['validation']['prompts'][evidence['prompt_index']],
                                 read_json(case['spec_ref'])['intent'])
                scenarios.add(case['scenario'])
            self.assertGreaterEqual(len(scenarios), 2)

    def test_local_evidence_never_promises_packaged_pixels(self):
        for name in ('changsheng-style-review', 'changsheng-extensions-review', 'azure-summer-style-review', 'changsheng-wardrobe-v2-review'):
            review = read_json(f'tests/forward-evidence/{name}.json')
            self.assertTrue(review['distribution'])
            for case in review['cases']:
                with self.subTest(case=case['case_id']):
                    self.assertEqual(case['artifact_availability'], 'local_only_not_distributed')
                    self.assertNotIn('output_ref', case)
                    self.assertFalse(Path(case['local_artifact_locator']).is_absolute())
                    self.assertRegex(case['output_sha256'], r'^[0-9a-f]{64}$')
                    self.assertEqual(len(case['dimensions']), 2)
                    if case.get('spec_ref'):
                        self.assertTrue((ROOT / case['spec_ref']).resolve().is_relative_to(ROOT))
                        self.assertEqual(validate_spec(read_json(case['spec_ref'])), [])

    def test_new_text_only_prompts_reproduce_recorded_inputs(self):
        for name in ('changsheng-style-review', 'changsheng-extensions-review', 'azure-summer-style-review', 'changsheng-wardrobe-v2-review'):
            review = read_json(f'tests/forward-evidence/{name}.json')
            for case in review['cases']:
                if case['reference_images_sent']:
                    continue  # Local edit base is intentionally not distributed.
                with self.subTest(case=case['case_id']):
                    spec = read_json(case['spec_ref'])
                    capsule = read_json(case['capsule_ref'])
                    result = compile_spec(spec, 'openai', capsule)
                    if result['prompt_review']['status'] == 'review_required':
                        self.assertEqual(result['prompt_review']['reasons'], ['length_over_target'])
                        result = compile_spec(spec, 'openai', capsule, review_approved=True)
                    self.assertEqual(lint_compiled_result(result), [])
                    prompt = result['prompt'] + case['prompt_suffix']
                    self.assertEqual(hashlib.sha256(prompt.encode()).hexdigest(), case['prompt_sha256'])

    def test_wardrobe_revision_preserves_historical_capsule(self):
        frozen = ROOT / 'tests/fixtures/changsheng-capsule-v1.7.0.json'
        self.assertEqual(hashlib.sha256(frozen.read_bytes()).hexdigest(),
                         '0242b97ae21f3c381c195d72845192794ad1469718843dab3a669773b79cc798')
        for review_name in ('changsheng-style-review', 'changsheng-extensions-review'):
            for case in read_json(f'tests/forward-evidence/{review_name}.json')['cases']:
                self.assertEqual(case['capsule_ref'], 'tests/fixtures/changsheng-capsule-v1.7.0.json')

    def test_wardrobe_revision_targets_survive_all_platforms(self):
        capsule = read_json('references/style-capsules/changsheng-inhabited-fantasy.json')
        for path in sorted((ROOT / 'tests/forward-specs').glob('changsheng-v2-*.json')):
            spec = json.loads(path.read_text())
            before = copy.deepcopy(spec)
            for platform in ('openai', 'flux', 'midjourney', 'generic'):
                with self.subTest(case=path.stem, platform=platform):
                    result = compile_spec(spec, platform, capsule)
                    self.assertNotEqual(result['prompt_review']['status'], 'blocked')
                    self.assertIn(spec['intent'].rstrip('.'), json.dumps(result, ensure_ascii=False))
                    self.assertEqual(spec, before)

    def test_azure_target_survives_all_platforms_without_mutation(self):
        capsule = read_json('references/style-capsules/azure-summer-character-photography.json')
        for path in sorted((ROOT / 'tests/forward-specs').glob('azure-*.json')):
            spec = json.loads(path.read_text())
            before = copy.deepcopy(spec)
            for platform in ('openai', 'flux', 'midjourney', 'generic'):
                result = compile_spec(spec, platform, capsule)
                self.assertIn(spec['intent'].rstrip('.'), json.dumps(result, ensure_ascii=False))
                self.assertNotEqual(result['prompt_review']['status'], 'blocked')
                self.assertEqual(spec, before)


if __name__ == '__main__':
    unittest.main()
