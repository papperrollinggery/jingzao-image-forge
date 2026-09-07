"""Cross-platform contracts for the opt-in learned fantasy capsule."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from compile_prompt import compile_spec
from validate_spec import validate_spec
from validate_style_capsule import validate_style_capsule


class ChangshengStyleTests(unittest.TestCase):
    def test_transfer_specs_compile_without_changing_target(self):
        capsule = json.loads((ROOT / 'references/style-capsules/changsheng-inhabited-fantasy.json').read_text())
        self.assertEqual(validate_style_capsule(capsule), [])
        for name in ('changsheng-tidal-archive', 'changsheng-weaver-portrait'):
            spec = json.loads((ROOT / f'tests/forward-specs/{name}.json').read_text())
            original = copy.deepcopy(spec)
            self.assertEqual(validate_spec(spec), [])
            for platform in ('openai', 'flux', 'midjourney', 'generic'):
                with self.subTest(name=name, platform=platform):
                    result = compile_spec(spec, platform, capsule)
                    self.assertNotEqual(result['prompt_review']['status'], 'blocked')
                    self.assertIn(spec['intent'].rstrip('.'), json.dumps(result, ensure_ascii=False))
                    self.assertEqual(spec, original)
            self.assertEqual(compile_spec(spec, 'openai', capsule)['prompt_review']['status'], 'ready')

    def test_unrelated_request_does_not_apply_capsule(self):
        spec = {'visual_generation_spec': '1.0', 'mode': 'create',
                'intent': 'Photograph a plain white ceramic cup on a gray table.',
                'canvas': {'aspect_ratio': '1:1'}, 'constraints': {}}
        result = compile_spec(spec, 'openai')
        self.assertNotIn('changsheng-inhabited-fantasy', json.dumps(result))
        self.assertNotIn('Chinese period-fantasy', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
