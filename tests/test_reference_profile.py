import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.reference_profile import (
    FACET_IDS,
    apply_reference_profile,
    validate_reference_profile,
)


def facet(
    facet_id,
    *,
    source_ids=None,
    evidence="observed",
    decision="omit",
    observation="visible evidence",
    prompt="",
    reason="",
    review_check="",
):
    if source_ids is None:
        source_ids = ["ref-1"] if evidence in {"observed", "partial"} else []
    if decision == "omit" and not reason:
        reason = "该可见项不服务当前目标。"
    return {
        "id": facet_id,
        "source_ids": source_ids,
        "evidence": evidence,
        "observation": observation,
        "decision": decision,
        "prompt": prompt,
        "reason": reason,
        "review_check": review_check,
    }


def profile(*, mode="attached"):
    facets = {item: facet(item) for item in FACET_IDS}
    facets["hair"] = facet(
        "hair",
        decision="preserve",
        prompt="柔和的深色发束保持清晰方向。",
        review_check="发束方向与柔和高光可见。",
    )
    facets["body"] = facet(
        "body",
        evidence="partial",
        decision="adapt",
        observation="只见肩线和部分躯干。",
        prompt="目标人物采用自然、协调的躯干比例。",
        reason="未见部分由目标设计。",
        review_check="躯干比例在目标构图中可读。",
    )
    facets["wardrobe"] = facet("wardrobe", evidence="unknown", decision="unknown", observation="", reason="服装被裁切遮挡。")
    facets["action"] = facet("action", evidence="not_applicable", decision="not_applicable", observation="")
    return {
        "reference_profile": "1.0",
        "id": "editorial-portrait",
        "reference_mode": mode,
        "source_ids": ["ref-1"],
        "facets": [facets[item] for item in sorted(FACET_IDS)],
    }


def spec():
    root = Path(__file__).resolve().parents[1]
    value = json.loads((root / "templates" / "visual-spec.json").read_text(encoding="utf-8"))
    value["intent"] = "原创成年人时装写真。"
    value["inputs"] = [
        {
            "id": "ref-1",
            "type": "image",
            "role": "style",
            "description": "Attached portrait reference.",
            "source_kind": "conversation_image",
            "source_ref": "Image 1",
            "must_attach": True,
        }
    ]
    value["scene"]["summary"] = "柔和棚拍背景。"
    value["subjects"][0]["id"] = "original-adult"
    value["subjects"][0]["description"] = "原创成年人。"
    return value


class ReferenceProfileTests(unittest.TestCase):
    def test_complete_profile_projects_only_adopted_prompt_and_preserves_input(self):
        value = spec()
        before = copy.deepcopy(value)
        result, audit = apply_reference_profile(value, profile())
        self.assertEqual(value, before)
        self.assertIn("柔和的深色发束保持清晰方向。", result["scene"]["summary"])
        self.assertIn("目标人物采用自然、协调的躯干比例。", result["scene"]["summary"])
        self.assertNotIn("visible evidence", result["scene"]["summary"])
        self.assertNotIn("preserve", result["scene"]["summary"])
        self.assertNotIn("服装被裁切遮挡", result["scene"]["summary"])
        self.assertEqual(result["subjects"], before["subjects"])
        self.assertEqual(audit["metadata"]["attachment_status"], "declared_must_attach")
        hair_audit = next(item for item in audit["facets"] if item["facet"] == "hair")
        self.assertEqual(hair_audit["source_ids"], ["ref-1"])
        self.assertEqual(hair_audit["review_check"], "发束方向与柔和高光可见。")
        self.assertEqual(hair_audit["observation"], "visible evidence")
        self.assertEqual(hair_audit["reason"], "")
        self.assertEqual(len(audit["facets"]), len(FACET_IDS))

    def test_missing_or_duplicate_facets_are_rejected(self):
        value = profile()
        value["facets"] = value["facets"][:-1]
        self.assertTrue(any("missing required facets" in error for error in validate_reference_profile(value)))
        value = profile()
        value["facets"][-1]["id"] = value["facets"][0]["id"]
        errors = validate_reference_profile(value)
        self.assertTrue(any("facet ids must be unique" in error for error in errors))

    def test_unknown_cannot_preserve_and_adapt_requires_reason(self):
        value = profile()
        item = next(f for f in value["facets"] if f["id"] == "wardrobe")
        item.update(decision="preserve", prompt="不应采用。", reason="")
        errors = validate_reference_profile(value)
        self.assertTrue(any("unknown evidence cannot be preserved" in error for error in errors))
        value = profile()
        item = next(f for f in value["facets"] if f["id"] == "wardrobe")
        item.update(decision="adapt", prompt="不应采用。", reason="目标设计。", review_check="不应出现。")
        errors = validate_reference_profile(value)
        self.assertTrue(any("unknown evidence cannot be adapted" in error for error in errors))
        value = profile()
        item = next(f for f in value["facets"] if f["id"] == "body")
        item["reason"] = ""
        self.assertTrue(any("required for adapt" in error for error in validate_reference_profile(value)))
        self.assertEqual(validate_reference_profile(profile()), [])  # Partial body evidence may still adapt its observed scope.

    def test_observed_sources_and_adopted_review_checks_are_required(self):
        value = profile()
        item = next(f for f in value["facets"] if f["id"] == "hair")
        item["source_ids"] = []
        self.assertTrue(any("required for observed or partial evidence" in error for error in validate_reference_profile(value)))
        value = profile()
        item = next(f for f in value["facets"] if f["id"] == "hair")
        item["source_ids"] = ["other-ref"]
        self.assertTrue(any("subset" in error for error in validate_reference_profile(value)))
        value = profile()
        item = next(f for f in value["facets"] if f["id"] == "hair")
        item["review_check"] = ""
        self.assertTrue(any("review_check: required" in error for error in validate_reference_profile(value)))

    def test_attached_source_requires_one_must_attach_input_and_source_ids_are_unique(self):
        value = profile()
        with self.assertRaisesRegex(ValueError, "missing attached source"):
            apply_reference_profile({**spec(), "inputs": []}, value)
        without_attach = spec()
        without_attach["inputs"][0]["must_attach"] = False
        with self.assertRaisesRegex(ValueError, "must_attach=true"):
            apply_reference_profile(without_attach, value)
        duplicate_input = spec()
        duplicate_input["inputs"].append(copy.deepcopy(duplicate_input["inputs"][0]))
        with self.assertRaisesRegex(ValueError, "must occur once"):
            apply_reference_profile(duplicate_input, value)
        value = profile()
        value["source_ids"] = ["ref-1", "ref-1"]
        self.assertTrue(any("duplicate source ids" in error for error in validate_reference_profile(value)))

    def test_text_transfer_does_not_claim_attachment(self):
        value = profile(mode="text_transfer")
        target = spec()
        target.pop("inputs")
        _, audit = apply_reference_profile(target, value)
        self.assertEqual(audit["metadata"]["attachment_status"], "text_transfer_no_attachment_claimed")

    def test_invalid_container_types_return_errors_without_crashing(self):
        self.assertTrue(validate_reference_profile(["not", "a", "profile"]))
        value = profile()
        value["facets"] = {"hair": "not-a-list"}
        self.assertTrue(any("expected a list" in error for error in validate_reference_profile(value)))

    def test_invalid_enum_and_source_json_types_return_errors_without_crashing(self):
        invalid_values = [[], {}, None, 1, True]
        for field in ("reference_mode", "source_ids"):
            for invalid in invalid_values:
                with self.subTest(profile_field=field, invalid=repr(invalid)):
                    value = profile()
                    value[field] = copy.deepcopy(invalid)
                    self.assertTrue(validate_reference_profile(value))
        for field in ("id", "evidence", "decision", "source_ids"):
            for invalid in invalid_values:
                with self.subTest(facet_field=field, invalid=repr(invalid)):
                    value = profile()
                    item = next(f for f in value["facets"] if f["id"] == "hair")
                    item[field] = copy.deepcopy(invalid)
                    self.assertTrue(validate_reference_profile(value))

    def test_exact_duplicate_prompt_is_not_appended_twice(self):
        value = profile()
        duplicate = next(f for f in value["facets"] if f["id"] == "body")
        duplicate["prompt"] = "柔和的深色发束保持清晰方向。"
        result, audit = apply_reference_profile(spec(), value)
        self.assertEqual(result["scene"]["summary"].count("柔和的深色发束保持清晰方向。"), 1)
        statuses = {item["facet"]: item["projection_status"] for item in audit["facets"]}
        self.assertEqual(statuses["hair"], "already_present")

    def test_substring_in_a_negative_clause_does_not_suppress_adopted_prompt_and_apply_is_idempotent(self):
        value = profile()
        hair = next(f for f in value["facets"] if f["id"] == "hair")
        hair["prompt"] = "黑色头发"
        target = spec()
        target["scene"]["summary"] = "不要黑色头发。"
        first, _ = apply_reference_profile(target, value)
        self.assertIn("不要黑色头发。\n", first["scene"]["summary"])
        self.assertTrue(first["scene"]["summary"].endswith("\n黑色头发"))
        second, audit = apply_reference_profile(first, value)
        self.assertEqual(second["scene"]["summary"], first["scene"]["summary"])
        self.assertEqual(next(item for item in audit["facets"] if item["facet"] == "hair")["projection_status"], "already_present")

    def test_cli_emits_spec_and_audit_and_uses_exit_two_for_contract_errors(self):
        root = Path(__file__).resolve().parents[1]
        script = root / "scripts" / "reference_profile.py"
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            profile_path = base / "profile.json"
            spec_path = base / "spec.json"
            profile_path.write_text(json.dumps(profile(), ensure_ascii=False), encoding="utf-8")
            spec_path.write_text(json.dumps(spec(), ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(script), str(profile_path), "--spec", str(spec_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout)
            result = json.loads(completed.stdout)
            self.assertIn("spec", result)
            self.assertIn("audit", result)
            invalid_spec = spec()
            invalid_spec["mode"] = "invalid"
            spec_path.write_text(json.dumps(invalid_spec, ensure_ascii=False), encoding="utf-8")
            invalid_result = subprocess.run(
                [sys.executable, str(script), str(profile_path), "--spec", str(spec_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(invalid_result.returncode, 2)
            self.assertIn("invalid projected spec", json.loads(invalid_result.stdout)["errors"][0])
            spec_path.write_text(json.dumps(spec(), ensure_ascii=False), encoding="utf-8")
            profile_path.write_text("[]", encoding="utf-8")
            failed = subprocess.run(
                [sys.executable, str(script), str(profile_path), "--spec", str(spec_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(failed.returncode, 2)


if __name__ == "__main__":
    unittest.main()
