"""Verify current prompt/source links and published pixel evidence, not aesthetics."""
import hashlib
import json
import struct
import unittest
from pathlib import Path

from scripts.compile_prompt import compile_spec
from scripts.reference_profile import FACET_IDS

ROOT = Path(__file__).resolve().parents[1]


class ReferenceProfileEvidenceTests(unittest.TestCase):
    def test_recorded_prompts_reproduce_the_profile_input_and_reference_count(self):
        record = json.loads((ROOT / 'tests/forward-evidence/reference-profile-style-review.json').read_text())
        seen = set()
        for case in record['cases']:
            with self.subTest(case=case['case_id']):
                self.assertNotIn(case['case_id'], seen)
                seen.add(case['case_id'])
                spec = json.loads((ROOT / case['spec_ref']).read_text())
                profile = json.loads((ROOT / case['profile_ref']).read_text())
                result = compile_spec(spec, 'openai', reference_profile=profile)
                self.assertEqual(hashlib.sha256(result['prompt'].encode()).hexdigest(), case['prompt_sha256'])
                self.assertEqual(case['reference_images_sent'], len(case['reference_input_sha256']))
                self.assertEqual(case['reference_images_sent'], 1 if profile['reference_mode'] == 'attached' else 0)
                self.assertEqual(set(case['checks']), FACET_IDS)
                for facet in profile['facets']:
                    self.assertEqual(case['checks'][facet['id']]['criterion'], facet['review_check'])
                self.assertEqual(case['checks']['body']['status'], 'untestable')
                self.assertNotIn('/Users/', json.dumps(case))

    def test_distributed_sample_matches_recorded_pixels_and_size(self):
        record = json.loads((ROOT / 'tests/forward-evidence/reference-profile-style-review.json').read_text())
        for case in record['cases']:
            if case['artifact_availability'] == 'distributed':
                target = (ROOT / case['output_ref']).resolve()
                self.assertTrue(target.is_relative_to(ROOT))
                data = target.read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), case['output_sha256'])
                self.assertEqual(list(struct.unpack('>II', data[16:24])), case['dimensions'])
                self.assertEqual(case['status'], 'partial')
            elif case['artifact_availability'] == 'not_generated':
                self.assertEqual(case['status'], 'TOOL_BLOCKED')
                self.assertFalse(case['image_returned'])
                self.assertNotIn('output_ref', case)
                self.assertNotIn('output_sha256', case)
                self.assertNotIn('dimensions', case)
            else:
                self.assertNotIn('output_ref', case)
                self.assertFalse(Path(case['local_artifact_locator']).is_absolute())


if __name__ == '__main__':
    unittest.main()
