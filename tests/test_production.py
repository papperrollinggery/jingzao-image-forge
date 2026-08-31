"""Tests for the production-frame manifest compiler."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load_module(name: str, path: Path):
    module_spec = importlib.util.spec_from_file_location(name, path)
    assert module_spec and module_spec.loader
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


production = _load_module("compile_production", SCRIPTS / "compile_production.py")


def frame_spec(intent: str, *, aspect_ratio: str = "1:1") -> dict:
    spec = json.loads((ROOT / "templates" / "visual-spec.json").read_text(encoding="utf-8"))
    spec["intent"] = intent
    spec["canvas"] = {"profile": "square", "aspect_ratio": aspect_ratio, "dimensions": {"width": 1024, "height": 1024}}
    spec["scene"]["summary"] = intent
    spec["subjects"][0]["description"] = "one ceramic amber cup"
    spec["style"]["medium"] = "restrained editorial product photography"
    return spec


def manifest(specs: list[dict] | None = None) -> dict:
    specs = specs or [frame_spec("FRAME_A_LITERAL")]
    frames = [
        {"id": f"frame-{index}", "shot_id": f"shot-{index}", "purpose": f"purpose {index}", "spec": spec}
        for index, spec in enumerate(specs, 1)
    ]
    return {
        "production_manifest": "1.0",
        "coverage": [
            {"shot_id": frame["shot_id"], "requirement": f"requirement {index}", "frame_ids": [frame["id"]]}
            for index, frame in enumerate(frames, 1)
        ],
        "frames": frames,
    }


class ProductionManifestValidationTests(unittest.TestCase):
    def test_valid_manifest_has_no_errors(self):
        self.assertEqual([], production.validate_manifest(manifest()))

    def test_root_requires_exact_known_keys(self):
        value = manifest()
        value["unexpected"] = True
        errors = production.validate_manifest(value)
        self.assertTrue(any("$.unexpected: unknown field" == error for error in errors))

    def test_malformed_root_does_not_crash(self):
        self.assertTrue(production.validate_manifest(None))
        self.assertTrue(production.validate_manifest({"production_manifest": "1.0", "coverage": "bad", "frames": []}))

    def test_coverage_requires_unique_nonempty_shot_ids(self):
        value = manifest()
        value["coverage"].append(copy.deepcopy(value["coverage"][0]))
        value["coverage"][1]["frame_ids"] = []
        value["coverage"][1]["video_only_reason"] = "motion only"
        errors = production.validate_manifest(value)
        self.assertTrue(any("duplicate shot_id" in error for error in errors))

    def test_video_only_coverage_requires_a_reason(self):
        value = manifest()
        value["coverage"][0]["frame_ids"] = []
        errors = production.validate_manifest(value)
        self.assertTrue(any("video_only_reason" in error for error in errors))

    def test_frame_coverage_rejects_unknown_duplicate_or_orphan_ids(self):
        value = manifest()
        value["coverage"][0]["frame_ids"] = ["frame-1", "frame-1", "missing"]
        errors = production.validate_manifest(value)
        self.assertTrue(any("duplicate frame_id" in error for error in errors))
        self.assertTrue(any("unknown frame_id" in error for error in errors))

    def test_frame_coverage_rejects_cross_shot_mismatch_and_orphan(self):
        value = manifest([frame_spec("A"), frame_spec("B")])
        value["coverage"][0]["frame_ids"] = ["frame-2"]
        value["coverage"][1]["frame_ids"] = []
        value["coverage"][1]["video_only_reason"] = "only movement"
        errors = production.validate_manifest(value)
        self.assertTrue(any("does not match" in error for error in errors))

    def test_frame_rejects_unknown_fields_and_duplicate_ids(self):
        value = manifest()
        duplicate = copy.deepcopy(value["frames"][0])
        duplicate["shot_id"] = "another-shot"
        duplicate["extra"] = "no"
        value["frames"].append(duplicate)
        value["coverage"].append({"shot_id": "another-shot", "requirement": "second", "frame_ids": ["frame-1"]})
        errors = production.validate_manifest(value)
        self.assertTrue(any("unknown field" in error for error in errors))
        self.assertTrue(any("duplicate frame id" in error for error in errors))

    def test_frame_requires_native_non_auto_aspect_ratio(self):
        value = manifest()
        value["frames"][0]["spec"]["canvas"] = {"profile": "auto", "aspect_ratio": "auto", "dimensions": None}
        errors = production.validate_manifest(value)
        self.assertTrue(any("native non-auto canvas.aspect_ratio" in error for error in errors))

    def test_frame_rejects_styleboard_and_styleboard_contamination(self):
        for mode, contamination in (("styleboard", False), ("create", True), ("learn_style", False)):
            with self.subTest(mode=mode, contamination=contamination):
                value = manifest()
                value["frames"][0]["spec"]["mode"] = mode
                if contamination:
                    value["frames"][0]["spec"]["styleboard"] = {"layout": "2x2"}
                errors = production.validate_manifest(value)
                self.assertTrue(any("styleboard" in error or "learn_style" in error for error in errors))

    def test_validate_spec_errors_are_included(self):
        value = manifest()
        value["frames"][0]["spec"]["visual_generation_spec"] = "broken"
        errors = production.validate_manifest(value)
        self.assertTrue(any("visual_generation_spec" in error for error in errors))


class ProductionManifestCompilationTests(unittest.TestCase):
    def test_compiles_one_independent_frame_and_retains_literal_style_and_clean_base(self):
        value = manifest()
        result = production.compile_manifest(value, ROOT, "openai")
        frame = result["frames"][0]
        self.assertEqual("ready", result["status"])
        self.assertEqual("frame-1", frame["id"])
        self.assertIn("FRAME_A_LITERAL", frame["compiled"]["prompt"])
        self.assertIn("restrained editorial product photography", frame["compiled"]["prompt"])
        self.assertIn("preventive clean base", frame["compiled"]["prompt"])
        self.assertEqual("codex_imagegen", frame["preflight"]["target"])
        self.assertTrue(any("does not approve visual or video" in warning for warning in result["warnings"]))

    def test_compiles_all_four_platform_adapters(self):
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = production.compile_manifest(manifest(), ROOT, platform)
                self.assertEqual(platform, result["frames"][0]["compiled"]["platform"])

    def test_ratio_only_canvas_is_retained_in_each_platform_frame_envelope(self):
        spec = frame_spec("RATIO_ONLY_LITERAL")
        spec["canvas"] = {"aspect_ratio": "16:9"}
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = production.compile_manifest(manifest([spec]), ROOT, platform)
                self.assertEqual({"aspect_ratio": "16:9"}, result["frames"][0]["canvas"])

    def test_canvas_is_deep_copied_without_mutating_the_input(self):
        spec = frame_spec("CANVAS_COPY_LITERAL")
        spec["canvas"] = {"profile": "standard_widescreen", "aspect_ratio": "16:9", "dimensions": {"width": 1536, "height": 864}}
        value = manifest([spec])
        original = copy.deepcopy(value)
        result = production.compile_manifest(value, ROOT, "generic")
        result["frames"][0]["canvas"]["dimensions"]["width"] = 1
        self.assertEqual(original, value)
        self.assertEqual(1536, value["frames"][0]["spec"]["canvas"]["dimensions"]["width"])

    def test_uses_each_frame_spec_platform_when_no_override_is_supplied(self):
        spec = frame_spec("FRAME_PLATFORM_LITERAL")
        spec["platform"] = "flux"
        result = production.compile_manifest(manifest([spec]), ROOT)
        self.assertEqual("flux", result["frames"][0]["compiled"]["platform"])

    def test_frames_are_isolated_from_each_others_prompt_content(self):
        value = manifest([frame_spec("ALPHA_ONLY_LITERAL"), frame_spec("BETA_ONLY_LITERAL")])
        result = production.compile_manifest(value, ROOT, "openai")
        prompts = {frame["id"]: frame["compiled"]["prompt"] for frame in result["frames"]}
        self.assertIn("ALPHA_ONLY_LITERAL", prompts["frame-1"])
        self.assertNotIn("BETA_ONLY_LITERAL", prompts["frame-1"])
        self.assertIn("BETA_ONLY_LITERAL", prompts["frame-2"])
        self.assertNotIn("ALPHA_ONLY_LITERAL", prompts["frame-2"])

    def test_input_object_is_not_mutated(self):
        value = manifest()
        original = copy.deepcopy(value)
        production.compile_manifest(value, ROOT, "openai")
        self.assertEqual(original, value)

    def test_video_only_manifest_outputs_no_frames(self):
        value = {"production_manifest": "1.0", "coverage": [{"shot_id": "shot-video", "requirement": "whip pan", "frame_ids": [], "video_only_reason": "motion cannot be represented"}], "frames": []}
        result = production.compile_manifest(value, ROOT, "openai")
        self.assertEqual([], result["frames"])
        self.assertEqual("ready", result["status"])

    def test_missing_relative_local_reference_blocks_openai_and_resolves_from_manifest_dir(self):
        value = manifest()
        value["frames"][0]["spec"]["inputs"] = [{"id": "ref", "type": "image", "role": "product", "description": "required product", "source_kind": "local_path", "source_ref": "assets/missing.png", "must_attach": True}]
        with tempfile.TemporaryDirectory() as directory:
            base_dir = Path(directory)
            result = production.compile_manifest(value, base_dir, "openai")
        self.assertEqual("blocked", result["status"])
        preflight = result["frames"][0]["preflight"]
        self.assertIn(str(base_dir / "assets" / "missing.png"), preflight["errors"][0])
        self.assertEqual("blocked", result["frames"][0]["compiled"]["imagegen_call_plan"]["status"])

    def test_portable_platform_does_not_apply_codex_attachment_restrictions(self):
        value = manifest()
        value["frames"][0]["spec"]["inputs"] = [{"id": "remote", "type": "image", "role": "style", "description": "remote style", "source_kind": "remote_url", "source_ref": "https://example.invalid/ref.png", "must_attach": True}]
        result = production.compile_manifest(value, ROOT, "flux")
        self.assertEqual("ready", result["status"])
        self.assertEqual("portable", result["frames"][0]["preflight"]["target"])

    def test_portable_frames_omit_codex_only_imagegen_call_plan(self):
        for platform in ("flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = production.compile_manifest(manifest(), ROOT, platform)
                self.assertNotIn("imagegen_call_plan", result["frames"][0]["compiled"])

    def test_portable_remote_references_drop_only_the_stale_codex_execution_warning(self):
        value = manifest()
        value["frames"][0]["spec"]["inputs"] = [
            {
                "id": "remote",
                "type": "image",
                "role": "style",
                "description": "remote style",
                "source_kind": "remote_url",
                "source_ref": "https://example.invalid/ref.png",
                "must_attach": True,
            }
        ]
        stale_warning_prefix = "Codex ImageGen execution is blocked until the imagegen_call_plan errors are resolved"
        for platform in ("flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = production.compile_manifest(value, ROOT, platform)
                frame = result["frames"][0]
                self.assertFalse(any(warning.startswith(stale_warning_prefix) for warning in frame["compiled"]["warnings"]))
                self.assertFalse(any(stale_warning_prefix in warning for warning in result["warnings"]))
                self.assertTrue(any("Structural coverage does not approve" in warning for warning in result["warnings"]))
                self.assertTrue(any("Actual image attachments are mandatory" in warning for warning in frame["compiled"]["warnings"]))
                self.assertEqual(["remote"], frame["preflight"]["runtime_required"])
                self.assertEqual(1, frame["compiled"]["reference_handoff"]["required_attachment_count"])

    def test_portable_warning_filter_preserves_previous_frame_diagnostics(self):
        value = manifest([frame_spec("FIRST_FRAME"), frame_spec("SECOND_FRAME")])
        value["frames"][0]["spec"]["inputs"] = [{
            "id": "missing", "type": "image", "role": "product",
            "description": "required source", "source_kind": "local_path",
            "source_ref": "missing.png", "must_attach": True,
        }]
        with tempfile.TemporaryDirectory() as directory:
            result = production.compile_manifest(value, Path(directory), "generic")
        self.assertEqual("blocked", result["status"])
        self.assertTrue(any("Structural coverage does not approve" in warning for warning in result["warnings"]))
        self.assertTrue(any("frame-1:" in warning and "required local image not found" in warning for warning in result["warnings"]))

    def test_conversation_image_requires_runtime_confirmation_and_blocks_execution(self):
        value = manifest()
        value["frames"][0]["spec"]["inputs"] = [{"id": "conversation", "type": "image", "role": "identity", "description": "conversation image", "source_kind": "conversation_image", "source_ref": "Image 1", "must_attach": True}]
        result = production.compile_manifest(value, ROOT, "openai")
        self.assertEqual("blocked", result["status"])
        self.assertEqual(["conversation"], result["frames"][0]["preflight"]["runtime_required"])

    def test_blocked_prompt_stays_blocked_when_review_is_approved(self):
        value = manifest()
        value["frames"][0]["spec"]["intent"] = "same as the previous version"
        result = production.compile_manifest(value, ROOT, "openai", review_approved=True)
        self.assertEqual("blocked", result["status"])
        compiled = result["frames"][0]["compiled"]
        self.assertEqual("blocked", compiled["prompt_review"]["status"])
        self.assertEqual("blocked", compiled["imagegen_call_plan"]["status"])

    def test_review_required_returns_json_result_and_status(self):
        value = manifest()
        value["frames"][0]["spec"]["inputs"] = [
            {"id": f"ref-{index}", "type": "image", "role": "style", "description": "local style", "source_kind": "local_path", "source_ref": "tests/fixtures/continuous-nine-shot-master.jpg", "must_attach": True}
            for index in range(1, 5)
        ]
        result = production.compile_manifest(value, ROOT, "openai")
        self.assertEqual("review_required", result["status"])
        self.assertEqual("review_required", result["frames"][0]["compiled"]["prompt_review"]["status"])

    def test_backstage_coverage_metadata_never_enters_the_frame_prompt(self):
        value = manifest()
        value["coverage"][0]["requirement"] = "BACKSTAGE_REQUIREMENT_ONLY"
        value["frames"][0]["purpose"] = "BACKSTAGE_PURPOSE_ONLY"
        value["coverage"].append(
            {
                "shot_id": "video-only",
                "requirement": "separate movement",
                "frame_ids": [],
                "video_only_reason": "BACKSTAGE_VIDEO_ONLY_REASON",
            }
        )
        prompt = production.compile_manifest(value, ROOT, "openai")["frames"][0]["compiled"]["prompt"]
        for backstage_value in ("BACKSTAGE_REQUIREMENT_ONLY", "BACKSTAGE_PURPOSE_ONLY", "BACKSTAGE_VIDEO_ONLY_REASON"):
            self.assertNotIn(backstage_value, prompt)


class ProductionManifestCliTests(unittest.TestCase):
    def test_cli_writes_json_and_frame_selection_uses_selected_status(self):
        value = manifest([frame_spec("CLI_A"), frame_spec("CLI_B")])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            command = [sys.executable, str(SCRIPTS / "compile_production.py"), str(path), "--platform", "openai", "--frame-id", "frame-2"]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual("frame-2", result["id"])
        self.assertEqual("shot-2", result["shot_id"])
        self.assertEqual(value["frames"][1]["spec"]["canvas"], result["canvas"])
        self.assertIn("compiled", result)
        self.assertIn("preflight", result)
        self.assertEqual("ready", result["status"])
        self.assertNotIn("frames", result)

    def test_cli_rejects_malformed_json_directory_and_unknown_frame_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            base_dir = Path(directory)
            malformed = base_dir / "bad.json"
            malformed.write_text("{", encoding="utf-8")
            for path, extra in ((malformed, []), (base_dir, []), (base_dir / "valid.json", ["--frame-id", "unknown"])):
                if path.name == "valid.json":
                    path.write_text(json.dumps(manifest()), encoding="utf-8")
                completed = subprocess.run([sys.executable, str(SCRIPTS / "compile_production.py"), str(path), *extra], capture_output=True, text=True, check=False)
                self.assertEqual(2, completed.returncode)
                self.assertNotIn("Traceback", completed.stderr)

    def test_cli_rejects_invalid_utf8_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-utf8.json"
            path.write_bytes(b"\xff")
            completed = subprocess.run(
                [sys.executable, str(SCRIPTS / "compile_production.py"), str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertNotIn("Traceback", completed.stderr)

    def test_cli_missing_required_reference_returns_blocked_json_exit_1(self):
        value = manifest()
        value["frames"][0]["spec"]["inputs"] = [{"id": "ref", "type": "image", "role": "product", "description": "required product", "source_kind": "local_path", "source_ref": "missing.png", "must_attach": True}]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            completed = subprocess.run([sys.executable, str(SCRIPTS / "compile_production.py"), str(path), "--platform", "openai"], capture_output=True, text=True, check=False)
        self.assertEqual(1, completed.returncode, completed.stderr)
        self.assertEqual("blocked", json.loads(completed.stdout)["status"])

    def test_cli_approve_review_cannot_bypass_context_residue(self):
        value = manifest()
        value["frames"][0]["spec"]["intent"] = "same as the previous version"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            completed = subprocess.run([sys.executable, str(SCRIPTS / "compile_production.py"), str(path), "--approve-review"], capture_output=True, text=True, check=False)
        self.assertEqual(1, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual("blocked", result["status"])
        self.assertEqual("blocked", result["frames"][0]["compiled"]["prompt_review"]["status"])


if __name__ == "__main__":
    unittest.main()
