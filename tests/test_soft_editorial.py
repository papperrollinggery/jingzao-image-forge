"""Behavioral regression coverage for the optional family and honest evidence."""
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


def read(path):
    return json.loads((ROOT / path).read_text())


class SoftEditorialTests(unittest.TestCase):
    def test_recorded_execution_inputs_remain_reproducible(self):
        record = read('tests/forward-evidence/soft-editorial-style-review.json')
        for case in record['cases']:
            spec = read(case['spec_ref'])
            capsule = read(case['capsule_ref'])
            self.assertEqual(validate_spec(spec), [])
            self.assertEqual(validate_style_capsule(capsule), [])
            result = compile_spec(spec, 'openai', capsule)
            self.assertEqual(result['prompt_review']['status'], 'ready')
            self.assertEqual(lint_compiled_result(result), [])
            self.assertEqual(hashlib.sha256(result['prompt'].encode()).hexdigest(), case['prompt_sha256'])

    def test_body_coverage_and_new_palette_survive_all_platforms(self):
        cap = read('references/style-capsules/soft-editorial-character.json')
        spec = read('tests/forward-specs/soft-crimson-performer.json')
        # New target owns color; the common capsule must not force the source palette.
        spec['intent'] = '原创成年人物的藏青色时装肖像。'
        spec['scene']['summary'] = '藏青背景和藏青织物，暖白柔光，三分之四身。'
        spec['subjects'][0]['description'] = spec['intent']
        spec['subjects'][0]['appearance'][1] = '藏青连衣裙，方领，不透明衣片覆盖胸腹，胸省和腰缝承接身体体量。'
        before = copy.deepcopy(spec)
        for platform in ('openai', 'flux', 'midjourney', 'generic'):
            result = compile_spec(spec, platform, cap)
            prompt = result['prompt']
            self.assertIn('藏青', prompt)
            self.assertNotIn('暗绯红', prompt)
            for clause in spec['subjects'][0]['appearance']:
                self.assertIn(clause.rstrip('.'), json.dumps(result, ensure_ascii=False))
            self.assertNotEqual(result['prompt_review']['status'], 'blocked')
            self.assertEqual(before, spec)

    def test_blocked_outputs_cannot_be_reported_as_validated_style(self):
        cap = read('references/style-capsules/soft-editorial-character.json')
        self.assertEqual(cap['status'], 'draft')
        record = read('tests/forward-evidence/soft-editorial-style-review.json')
        for item in cap['validation']['evidence']:
            case_id = item['evidence_ref'].split('#')[1]
            case = next(c for c in record['cases'] if c['case_id'] == case_id)
            self.assertEqual(case['scenario'], item['scenario'])
            self.assertEqual(cap['validation']['prompts'][item['prompt_index']], read(case['spec_ref'])['intent'])
            if case['status'] == 'TOOL_BLOCKED':
                self.assertFalse(case['image_returned'])
                self.assertNotIn('output_sha256', case)
                self.assertNotIn('local_artifact_locator', case)
            else:
                self.assertEqual(case['status'], 'partial')
                self.assertEqual(case['artifact_availability'], 'local_only_not_distributed')
                self.assertRegex(case['output_sha256'], '^[0-9a-f]{64}$')
                self.assertFalse(Path(case['local_artifact_locator']).is_absolute())
        serialized = json.dumps(cap, ensure_ascii=False)
        self.assertNotIn('/Users/', serialized)
        self.assertFalse(cap['source_summary']['raw_images_stored'])


if __name__ == '__main__':
    unittest.main()
