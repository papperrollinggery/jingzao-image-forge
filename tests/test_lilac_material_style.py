"""Validate product-style transfer contracts and their recorded image evidence."""
import copy
import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from compile_prompt import compile_spec
from prompt_lint import lint_compiled_result
from validate_spec import validate_spec
from validate_style_capsule import validate_style_capsule


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


class LilacMaterialTests(unittest.TestCase):
    def setUp(self):
        self.cap = read('references/style-capsules/lilac-material-reveal.json')
        self.record = read('tests/forward-evidence/lilac-material-reveal-review.json')

    def test_adopted_capsule_binds_distinct_product_review_cases(self):
        self.assertEqual(validate_style_capsule(self.cap), [])
        self.assertEqual(self.cap['status'], 'adopted')
        self.assertTrue(self.cap['adoption_approved'])
        scenarios = set()
        for evidence in self.cap['validation']['evidence']:
            path, case_id = evidence['evidence_ref'].split('#')
            case = next(c for c in read(path)['cases'] if c['case_id'] == case_id)
            self.assertIn(case['status'], ('passed', 'passed_with_concerns'))
            self.assertEqual(case['scenario'], evidence['scenario'])
            self.assertEqual(self.cap['validation']['prompts'][evidence['prompt_index']], read(case['spec_ref'])['intent'])
            scenarios.add(case['scenario'])
        self.assertGreaterEqual(len(scenarios), 2)

    def test_actual_sent_prompts_reproduce_and_historical_suffixes_are_explicit(self):
        for case in self.record['cases']:
            with self.subTest(case=case['case_id']):
                spec = read(case['spec_ref'])
                self.assertEqual(validate_spec(spec), [])
                result = compile_spec(spec, 'openai', self.cap if case['capsule_ref'] else None)
                self.assertEqual(lint_compiled_result(result), [])
                sent = result['prompt'] + case['prompt_suffix']
                self.assertEqual(hashlib.sha256(sent.encode()).hexdigest(), case['prompt_sha256'])
                self.assertEqual(case['reference_images_sent'], len(case['reference_input_sha256']))
                if case['reference_images_sent']:
                    self.assertEqual(case['parent_case_id'], 'lilac-pastel-release')
                self.assertEqual('Canvas: 16:9.' in sent, case['canvas_in_sent_prompt'])

    def test_published_outputs_are_the_reviewed_pixels(self):
        for case in self.record['cases']:
            if case['artifact_availability'] == 'local_only_not_distributed':
                self.assertNotIn('output_ref', case)
                self.assertFalse(Path(case['local_artifact_locator']).is_absolute())
                continue
            path = (ROOT / case['output_ref']).resolve()
            self.assertTrue(path.is_relative_to(ROOT))
            data = path.read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), case['output_sha256'])
            self.assertEqual(list(struct.unpack('>II', data[16:24])), case['dimensions'])
            self.assertEqual(case['artifact_availability'], 'distributed')
        self.assertFalse(self.cap['source_summary']['raw_images_stored'])
        for material in (self.cap, self.record):
            self.assertNotIn('/Users/', json.dumps(material))
            self.assertNotIn('xwechat', json.dumps(material))

    def test_target_product_and_materials_survive_all_platforms(self):
        for path in sorted((ROOT / 'tests/forward-specs').glob('lilac-*.json')):
            spec = json.loads(path.read_text(encoding='utf-8'))
            before = copy.deepcopy(spec)
            for platform in ('openai', 'flux', 'midjourney', 'generic'):
                with self.subTest(spec=path.name, platform=platform):
                    result = compile_spec(spec, platform, None if spec['mode'] == 'edit' else self.cap)
                    self.assertNotEqual(result['prompt_review']['status'], 'blocked')
                    output = json.dumps(result, ensure_ascii=False)
                    self.assertIn(spec['intent'], output)
                    for material in spec.get('materials', []):
                        self.assertIn(material['description'], output)
                    self.assertEqual(before, spec)


if __name__ == '__main__':
    unittest.main()
