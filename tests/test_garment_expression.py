"""Expression fidelity is distinct from provider image acceptance."""
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


class GarmentExpressionTests(unittest.TestCase):
    def test_explicit_opening_and_coverage_survive_compilation(self):
        record = json.loads((ROOT / 'tests/forward-evidence/female-garment-expression-review.json').read_text())
        case = record['compilation_case']
        spec = json.loads((ROOT / case['spec_ref']).read_text())
        capsule = json.loads((ROOT / case['capsule_ref']).read_text())
        self.assertEqual(validate_spec(spec), [])
        original = copy.deepcopy(spec)
        for platform in ('openai', 'flux', 'midjourney', 'generic'):
            with self.subTest(platform=platform):
                result = compile_spec(spec, platform, capsule)
                serialized = json.dumps(result, ensure_ascii=False)
                for clause in spec['subjects'][0]['appearance'][:2]:
                    self.assertIn(clause.rstrip('.'), serialized)
                self.assertEqual(spec, original)
        result = compile_spec(spec, 'openai', capsule)
        if result['prompt_review']['status'] == 'review_required':
            self.assertEqual(result['prompt_review']['reasons'], ['length_over_target'])
            result = compile_spec(spec, 'openai', capsule, review_approved=True)
        self.assertEqual(lint_compiled_result(result), [])
        self.assertEqual(hashlib.sha256((result['prompt'] + case['prompt_suffix']).encode()).hexdigest(),
                         case['prompt_sha256'])

    def test_source_success_is_not_overwritten_by_local_blocks(self):
        record = json.loads((ROOT / 'tests/forward-evidence/female-garment-expression-review.json').read_text())
        self.assertTrue(record['source_evidence']['submitted_original_observed'])
        self.assertTrue(record['source_evidence']['user_confirmed_generation_success'])
        self.assertFalse(record['source_evidence']['result_image_available_for_local_inspection'])
        local = record['local_execution']
        self.assertEqual(local['returned_images'], 0)
        self.assertEqual(local['attempt_count'], len(local['attempts']))
        for attempt in local['attempts']:
            self.assertEqual(attempt['status'], 'moderation_blocked')
            self.assertEqual(attempt['moderation_stage'], 'output')
            self.assertFalse(attempt['image_returned'])
            self.assertNotIn('output_ref', attempt)
            self.assertNotIn('output_sha256', attempt)
        self.assertIn('user-confirmed-original', [a['case'] for a in local['attempts']])


    def test_peer_success_does_not_relabel_this_task_failures(self):
        record = json.loads((ROOT / 'tests/forward-evidence/female-garment-expression-review.json').read_text())
        peer = record['peer_native_evidence']
        self.assertTrue(peer['image_returned'])
        self.assertTrue(peer['image_inspected_locally'])
        self.assertTrue(peer['reference_file_hash_verified'])
        self.assertEqual(peer['reported_reference_image_count'], 1)
        self.assertEqual(record['diagnostic_findings']['explicit_local_image_inputs'], 0)
        self.assertEqual(peer['source_prompt_sha256'], record['source_evidence']['original_prompt_sha256'])
        self.assertEqual(record['local_execution']['returned_images'], 0)
        self.assertEqual(peer['artifact_availability'], 'local_only_not_distributed')
        self.assertNotIn('output_ref', peer)


if __name__ == '__main__':
    unittest.main()
