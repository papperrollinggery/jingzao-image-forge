"""Regression tests for 镜造 Image Forge."""

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
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = _load_module("validator", SCRIPTS / "validate_spec.py")
capsule_validator = _load_module("capsule_validator", SCRIPTS / "validate_style_capsule.py")
capsule_creator = _load_module("capsule_creator", SCRIPTS / "create_style_capsule.py")
reference_delivery = _load_module("reference_delivery", SCRIPTS / "reference_delivery.py")
compiler = _load_module("compiler", SCRIPTS / "compile_prompt.py")
prompt_lint = _load_module("prompt_lint", SCRIPTS / "prompt_lint.py")
forward_test_validator = _load_module("forward_test_validator", SCRIPTS / "validate_forward_tests.py")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def make_narrative_spec():
    spec = load_json(ROOT / "templates" / "visual-spec.json")
    spec["canvas"] = {
        "profile": "cinematic_ultrawide",
        "aspect_ratio": "21:9",
        "dimensions": {"width": 1792, "height": 768},
    }
    spec["direction"] = {
        "deliverable": "narrative_film_frame",
        "treatment": "grounded_cinematic",
        "spectacle_scale": "intimate",
        "camera_freedom": "physical",
        "genre": "relationship drama",
        "world_rule": "ordinary contemporary space",
        "visual_goal": "show a decision through distance and object behavior",
    }
    spec["cinematic"] = {
        "profile": "narrative_film_frame",
        "shot_function": "observe",
        "visible_event": "one character releases a shared object before the other reaches it",
        "relationship_pressure": "the characters avoid direct eye contact",
        "viewer_task": "infer that the decision to leave has already been made",
        "viewer_position": "seated at the far end of the same table",
        "frozen_moment": "the released object stops between both hands",
        "withheld_information": "the destination remains offscreen",
        "posterization_guard": True,
    }
    spec["staging"] = {
        "primary_relationship": "A withdraws from B across a table",
        "subject_positions": ["A screen-left foreground", "B screen-right midground"],
        "eyeline_logic": "A looks toward the exit while B watches A's hand",
        "screen_direction": "attention moves left to right toward the unseen exit",
        "axis": "table and eyeline axis remains readable",
        "occlusion": "a chair edge partially blocks B",
        "attention_path": "released object to A's hand to B's gaze to empty doorway",
    }
    spec["composition"].update(
        {
            "camera_motivation": "place the viewer inside the shared but separating space",
            "camera_height": "seated eye level",
            "camera_distance": "far enough to keep both hands and the empty doorway readable",
            "point_of_view": "same-table observer",
            "focal_length_mm": 40,
            "lens_rationale": "natural two-person relation with enough environment to hold the exit",
            "subject_frame_ratio": "people occupy about half the frame; space carries the remaining pressure",
            "foreground_logic": "chair edge proves the viewer's constrained position",
        }
    )
    spec["lighting"].update(
        {
            "motivation": "one side window and a practical lamp reflected by the table",
            "narrative_function": "the doorway stays dim while the released object receives the clearest light",
        }
    )
    return spec


def make_styleboard_spec():
    spec = load_json(ROOT / "templates" / "visual-spec.json")
    spec["mode"] = "styleboard"
    spec["canvas"] = {
        "profile": "standard_widescreen",
        "aspect_ratio": "16:9",
        "dimensions": {"width": 1536, "height": 864},
    }
    spec["inputs"] = [
        {
            "id": "style-reference",
            "type": "image",
            "role": "style_reference",
            "description": "User-supplied hand-drawn storyboard finish reference.",
            "source_kind": "conversation_image",
            "source_ref": "Image 1 in the active conversation",
            "must_attach": True,
        }
    ]
    spec["styleboard"] = {
        "layout": "3x3",
        "frame_count": 9,
        "frame_aspect_ratio": "16:9",
        "presentation": "hand_drawn",
        "generation_strategy": "hybrid",
        "reading_order": "left_to_right_top_to_bottom",
        "continuity_locks": ["character identity", "wardrobe", "location", "light direction"],
        "allowed_variation": ["shot size", "camera angle", "action phase"],
        "reference_assignments": [
            {
                "input_id": "style-reference",
                "role": "style",
                "secondary_roles": [],
                "use": "line weight, paper texture, controlled gray values",
                "ignore": "identity, costume, location, pose",
            }
        ],
        "frames": [
            {
                "id": f"frame-{index:02d}",
                "shot_function": "establish" if index == 1 else "observe",
                "story_moment": f"story beat {index}",
                "primary_action": "the subject pauses at the threshold",
                "action_phase": "hold",
                "shot_size": "wide" if index == 1 else "medium",
                "camera_height": "eye level",
                "focal_length_mm": 35 if index == 1 else 50,
                "composition": "single readable moment with foreground, subject, and spatial exit",
                "reference_ids": ["style-reference"],
            }
            for index in range(1, 10)
        ],
    }
    return spec


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.template = load_json(ROOT / "templates" / "visual-spec.json")
        self.example = load_json(ROOT / "examples" / "atomic-cyber-live-action.json")

    @staticmethod
    def _attached_image(role: str, description: str):
        return {
            "id": "source",
            "type": "image",
            "role": role,
            "description": description,
            "source_kind": "conversation_image",
            "source_ref": "Image 1 in the active conversation",
            "must_attach": True,
        }

    def test_template_is_valid(self):
        self.assertEqual([], validator.validate_spec(self.template))

    def test_atomic_cyber_example_is_valid(self):
        self.assertEqual([], validator.validate_spec(self.example))

    def test_narrative_film_frame_example_is_valid(self):
        spec = load_json(ROOT / "examples" / "narrative-film-frame.json")
        self.assertEqual([], validator.validate_spec(spec))

    def test_styleboard_3x3_example_is_valid(self):
        spec = load_json(ROOT / "examples" / "styleboard-3x3.json")
        self.assertEqual([], validator.validate_spec(spec))

    def test_ui_motion_storyboard_example_is_valid(self):
        spec = load_json(ROOT / "examples" / "ui-motion-storyboard.json")
        self.assertEqual([], validator.validate_spec(spec))

    def test_style_learning_example_is_valid(self):
        spec = load_json(ROOT / "examples" / "style-learning-graphite-copper.json")
        self.assertEqual([], validator.validate_spec(spec))

    def test_tactile_product_example_is_valid(self):
        spec = load_json(ROOT / "examples" / "tactile-stop-motion-product.json")
        self.assertEqual([], validator.validate_spec(spec))

    def test_architecture_exhibition_example_is_valid(self):
        spec = load_json(ROOT / "examples" / "architecture-exhibition.json")
        self.assertEqual([], validator.validate_spec(spec))

    def test_causal_fantasy_effect_example_is_valid(self):
        spec = load_json(ROOT / "examples" / "causal-fantasy-effect.json")
        self.assertEqual([], validator.validate_spec(spec))

    def test_reconstruct_restyle_expand_examples_are_valid(self):
        for name in (
            "reconstruct-architecture-reference.json",
            "restyle-risograph-editorial.json",
            "expand-roadside-outpaint.json",
        ):
            with self.subTest(name=name):
                spec = load_json(ROOT / "examples" / name)
                self.assertEqual([], validator.validate_spec(spec))

    def test_style_capsule_example_is_valid(self):
        capsule = load_json(ROOT / "examples" / "style-capsule-graphite-copper.json")
        self.assertEqual([], capsule_validator.validate_style_capsule(capsule))

    def test_adopted_crimson_nocturne_capsule_is_valid(self):
        capsule = load_json(
            ROOT / "references" / "style-capsules" / "crimson-nocturne-wuxia-montage.json"
        )
        self.assertEqual([], capsule_validator.validate_style_capsule(capsule))
        self.assertEqual("adopted", capsule["status"])
        self.assertTrue(capsule["adoption_approved"])
        self.assertFalse(capsule["source_summary"]["raw_images_stored"])

    def test_validated_capsule_requires_two_scenario_evidence_records(self):
        capsule = load_json(ROOT / "examples" / "style-capsule-graphite-copper.json")
        capsule["validation"]["evidence"] = capsule["validation"]["evidence"][:1]
        errors = capsule_validator.validate_style_capsule(capsule)
        self.assertTrue(any("two different scenario evidence" in item for item in errors))

    def test_forward_test_manifest_is_current_and_traceable(self):
        manifest = load_json(ROOT / "tests" / "forward-test-manifest.json")
        self.assertEqual([], forward_test_validator.validate_forward_test_manifest(manifest, ROOT))

    def test_forward_test_manifest_rejects_output_hash_drift(self):
        manifest = load_json(ROOT / "tests" / "forward-test-manifest.json")
        manifest["cases"][0]["output_sha256"] = "0" * 64
        errors = forward_test_validator.validate_forward_test_manifest(manifest, ROOT)
        self.assertTrue(any("output_sha256" in item for item in errors))

    def test_forward_test_manifest_requires_receipt_for_attached_inputs(self):
        manifest = load_json(ROOT / "tests" / "forward-test-manifest.json")
        restyle = next(case for case in manifest["cases"] if case["case_id"] == "restyle-risograph-service-station")
        restyle.pop("execution_receipt")
        errors = forward_test_validator.validate_forward_test_manifest(manifest, ROOT)
        self.assertTrue(any("required for 1 must_attach" in item for item in errors))

    def test_forward_test_manifest_rejects_sensitive_public_receipt_fields(self):
        receipt = {
            "receipt_version": "1.0",
            "mechanism": "referenced_image_paths",
            "sent_input_ids": ["product"],
            "sent_count": 1,
            "tool_call_id_sha256": "0" * 64,
            "output_ref": "assets/gallery/output.jpg",
            "source_path": "/Users/example/private.png",
        }
        errors = forward_test_validator._validate_public_receipt(receipt, "$.receipt", ROOT)
        self.assertTrue(any("unsupported or sensitive public keys" in item for item in errors))

    def test_public_receipt_rejects_traversal_nested_values_and_bad_hashes(self):
        receipt = {
            "receipt_version": "2.0",
            "mechanism": "referenced_image_paths",
            "sent_input_ids": ["product"],
            "sent_count": 1,
            "tool_call_id_sha256": "not-a-hash",
            "output_ref": "../outside.jpg",
            "raw_output_sha256": "bad",
            "review": {"token": "/tmp/private"},
        }
        errors = forward_test_validator._validate_public_receipt(receipt, "$.receipt", ROOT)
        for marker in (
            "receipt_version",
            "tool_call_id_sha256",
            "parent traversal",
            "raw_output_sha256",
            "nested public receipt values",
        ):
            self.assertTrue(any(marker in item for item in errors), marker)

    def test_public_receipt_rejects_generic_uris_and_runtime_paths(self):
        receipt = {
            "receipt_version": "1.0",
            "mechanism": "referenced_image_paths",
            "sent_input_ids": [r"C:\\private\\asset.png"],
            "sent_count": 1,
            "tool_call_id_sha256": "a" * 64,
            "output_ref": "assets/gallery/output.jpg",
            "execution_prompt_note": "file://localhost/private/var/tmp/prompt.txt",
            "review": "s3://private-bucket/result",
        }
        errors = forward_test_validator._validate_public_receipt(receipt, "$.receipt", ROOT)
        self.assertGreaterEqual(sum("local/runtime identifier or URI" in item for item in errors), 3)

    def test_public_receipt_rejects_embedded_backslashes_and_punctuated_absolute_paths(self):
        receipt = {
            "receipt_version": "1.0",
            "mechanism": "referenced_image_paths",
            "sent_input_ids": [r"private\asset.png"],
            "sent_count": 1,
            "tool_call_id_sha256": "a" * 64,
            "output_ref": "assets/gallery/output.jpg",
            "execution_prompt_note": r"copied from \\server\share\asset.png",
            "review": "path:/srv/team/asset.png",
        }
        errors = forward_test_validator._validate_public_receipt(receipt, "$.receipt", ROOT)
        self.assertGreaterEqual(sum("local/runtime identifier or URI" in item for item in errors), 3)

    def test_manifest_rejects_absolute_non_image_output(self):
        manifest = load_json(ROOT / "tests" / "forward-test-manifest.json")
        manifest["cases"][0]["output"] = str(ROOT / "README.md")
        manifest["cases"][0]["output_sha256"] = "0" * 64
        errors = forward_test_validator.validate_forward_test_manifest(manifest, ROOT)
        self.assertTrue(any("repository-relative" in item for item in errors))

    def test_manifest_rejects_unknown_fields_and_boolean_prompt_index(self):
        manifest = load_json(ROOT / "tests" / "forward-test-manifest.json")
        manifest["private_token"] = "secret"
        manifest["cases"][0]["runtime_path"] = "/private/var/output.jpg"
        capsule_case = next(case for case in manifest["cases"] if case["prompt_source"]["type"] == "capsule_validation_prompt")
        capsule_case["prompt_source"]["prompt_index"] = True
        capsule_case["prompt_source"]["session_id"] = "session-private"
        errors = forward_test_validator.validate_forward_test_manifest(manifest, ROOT)
        for marker in ("unknown fields", "prompt_index", "local/runtime identifier or URI"):
            self.assertTrue(any(marker in item for item in errors), marker)

    def test_public_path_resolver_rejects_symlink_escape(self):
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as outside_dir:
            public_root = Path(root_dir)
            outside = Path(outside_dir) / "outside.jpg"
            outside.write_bytes(b"outside")
            (public_root / "link.jpg").symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "escapes repository root"):
                forward_test_validator._resolve(public_root, "link.jpg")

    def test_adopted_crimson_nocturne_capsule_compiles_with_transfer_boundaries(self):
        spec = load_json(ROOT / "examples" / "tactile-stop-motion-product.json")
        capsule = load_json(
            ROOT / "references" / "style-capsules" / "crimson-nocturne-wuxia-montage.json"
        )
        result = compiler.compile_spec(spec, "openai", capsule)
        prompt = result["prompt"]
        self.assertIn("Crimson Nocturne Wuxia Print Montage", prompt)
        self.assertIn("target specification remains authoritative", prompt)
        self.assertIn("source faces or likenesses", prompt)
        self.assertIn("source signature or watermark", prompt)

    def test_all_scenario_profiles_are_valid(self):
        for value in validator.SCENARIO_PROFILES:
            with self.subTest(value=value):
                spec = copy.deepcopy(self.template)
                spec["creative_routing"]["scenario_profile"] = value
                if value == "custom":
                    spec["creative_routing"]["custom_scenario"] = "custom scenario"
                self.assertEqual([], validator.validate_spec(spec))

    def test_all_genre_families_are_valid(self):
        for value in validator.GENRE_FAMILIES:
            with self.subTest(value=value):
                spec = copy.deepcopy(self.template)
                spec["creative_routing"]["genre_family"] = value
                if value == "custom":
                    spec["creative_routing"]["custom_genre"] = "custom genre"
                self.assertEqual([], validator.validate_spec(spec))

    def test_all_aesthetic_families_are_valid(self):
        for value in validator.AESTHETIC_FAMILIES:
            with self.subTest(value=value):
                spec = copy.deepcopy(self.template)
                spec["creative_routing"]["aesthetic_family"] = value
                if value == "custom":
                    spec["creative_routing"]["custom_aesthetic"] = "custom aesthetic"
                self.assertEqual([], validator.validate_spec(spec))

    def test_all_capture_or_render_methods_are_valid(self):
        for value in validator.CAPTURE_OR_RENDER_METHODS:
            with self.subTest(value=value):
                spec = copy.deepcopy(self.template)
                spec["creative_routing"]["capture_or_render_method"] = value
                if value == "custom":
                    spec["creative_routing"]["custom_method"] = "custom method"
                self.assertEqual([], validator.validate_spec(spec))

    def test_unknown_creative_routing_enums_are_rejected(self):
        fields = ("scenario_profile", "genre_family", "aesthetic_family", "capture_or_render_method")
        for field in fields:
            with self.subTest(field=field):
                spec = copy.deepcopy(self.template)
                spec["creative_routing"][field] = "style-magic"
                errors = validator.validate_spec(spec)
                self.assertTrue(any(f"creative_routing.{field}" in item for item in errors))

    def test_creative_routing_limits_scene_archetypes(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["creative_routing"]["scene_archetypes"] = ["one", "two", "three", "four"]
        errors = validator.validate_spec(spec)
        self.assertTrue(any("at most three" in item for item in errors))

    def test_secondary_influence_requires_mix_rule(self):
        spec = copy.deepcopy(self.template)
        spec["creative_routing"]["secondary_influence"] = "tactile paper"
        errors = validator.validate_spec(spec)
        self.assertTrue(any("mix_rule" in item for item in errors))

    def test_mix_rule_requires_secondary_influence(self):
        spec = copy.deepcopy(self.template)
        spec["creative_routing"]["mix_rule"] = "paper controls only the background"
        errors = validator.validate_spec(spec)
        self.assertTrue(any("secondary_influence" in item for item in errors))

    def test_validated_style_learning_requires_transfer_tests_and_notes(self):
        spec = load_json(ROOT / "examples" / "style-learning-graphite-copper.json")
        spec["style_learning"]["status"] = "validated"
        spec["style_learning"]["validation_prompts"] = ["one test"]
        spec["style_learning"]["verification_notes"] = ""
        errors = validator.validate_spec(spec)
        self.assertTrue(any("at least two transfer tests" in item for item in errors))
        self.assertTrue(any("visual review notes" in item for item in errors))

    def test_style_learning_rejects_unknown_source_input(self):
        spec = load_json(ROOT / "examples" / "style-learning-graphite-copper.json")
        spec["style_learning"]["source_input_ids"] = ["missing-reference"]
        errors = validator.validate_spec(spec)
        self.assertTrue(any("unknown input id" in item for item in errors))

    def test_style_capsule_export_strips_raw_source_content(self):
        spec = load_json(ROOT / "examples" / "style-learning-graphite-copper.json")
        capsule = capsule_creator.create_style_capsule(spec)
        self.assertFalse(capsule["source_summary"]["raw_images_stored"])
        self.assertNotIn("inputs", capsule)
        self.assertEqual([], capsule_validator.validate_style_capsule(capsule))

    def test_style_capsule_rejects_embedded_raw_source_flag(self):
        capsule = load_json(ROOT / "examples" / "style-capsule-graphite-copper.json")
        capsule["source_summary"]["raw_images_stored"] = True
        errors = capsule_validator.validate_style_capsule(capsule)
        self.assertTrue(any("expected false" in item for item in errors))

    def test_unhashable_enum_fields_return_errors_without_traceback(self):
        cases = (
            ("mode",),
            ("platform",),
            ("language",),
            ("canvas", "profile"),
            ("creative_routing", "scenario_profile"),
            ("platform_options", "openai", "quality"),
            ("platform_options", "flux", "prompt_format"),
        )
        for path in cases:
            for malformed in ({"bad": []}, [[]]):
                with self.subTest(path=path, malformed=type(malformed).__name__):
                    spec = copy.deepcopy(self.template)
                    node = spec
                    for key in path[:-1]:
                        node = node[key]
                    node[path[-1]] = malformed
                    errors = validator.validate_spec(spec)
                    self.assertTrue(errors)

    def test_nonfinite_numbers_are_rejected(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                spec = copy.deepcopy(self.template)
                spec["subjects"][0]["position"]["x_percent"] = value
                errors = validator.validate_spec(spec)
                self.assertTrue(any("x_percent" in item for item in errors))

    def test_unknown_fields_are_rejected(self):
        spec = copy.deepcopy(self.template)
        spec["lightning"] = {}
        spec["constraints"]["exlude"] = ["logo"]
        spec["subjects"][0]["apperance"] = ["red"]
        spec["creative_routing"]["scenario_prof"] = "product_tabletop"
        errors = validator.validate_spec(spec)
        for field in ("lightning", "exlude", "apperance", "scenario_prof"):
            self.assertTrue(any(field in item and "unknown field" in item for item in errors))

    def test_openai_flexible_size_constraints_are_validated(self):
        valid_sizes = {
            "auto": self.template["canvas"],
            "1024x1024": {"profile": "square", "aspect_ratio": "1:1", "dimensions": {"width": 1024, "height": 1024}},
            "1536x864": {"profile": "standard_widescreen", "aspect_ratio": "16:9", "dimensions": {"width": 1536, "height": 864}},
            "1792x768": {"profile": "cinematic_ultrawide", "aspect_ratio": "21:9", "dimensions": {"width": 1792, "height": 768}},
            "3840x2160": {"profile": "standard_widescreen", "aspect_ratio": "16:9", "dimensions": {"width": 3840, "height": 2160}},
        }
        for value, canvas in valid_sizes.items():
            with self.subTest(valid=value):
                spec = copy.deepcopy(self.template)
                spec["canvas"] = copy.deepcopy(canvas)
                spec["platform_options"]["openai"]["size"] = value
                self.assertEqual([], validator.validate_spec(spec))
        invalid_sizes = ("858x1834", "3856x1024", "2048x512", "640x640", "not-a-size")
        for value in invalid_sizes:
            with self.subTest(invalid=value):
                spec = copy.deepcopy(self.template)
                spec["platform_options"]["openai"]["size"] = value
                self.assertTrue(any("openai.size" in item for item in validator.validate_spec(spec)))

    def test_custom_creative_route_requires_and_accepts_description(self):
        spec = copy.deepcopy(self.template)
        spec["creative_routing"]["scenario_profile"] = "custom"
        errors = validator.validate_spec(spec)
        self.assertTrue(any("custom_scenario" in item for item in errors))
        spec["creative_routing"]["custom_scenario"] = "museum conservation plate"
        self.assertEqual([], validator.validate_spec(spec))

    def test_adopted_style_learning_requires_explicit_approval(self):
        spec = load_json(ROOT / "examples" / "style-learning-graphite-copper.json")
        spec["style_learning"]["status"] = "adopted"
        errors = validator.validate_spec(spec)
        self.assertTrue(any("adoption_approved" in item for item in errors))
        spec["style_learning"]["adoption_approved"] = True
        self.assertEqual([], validator.validate_spec(spec))

    def test_adopted_capsule_requires_explicit_approval(self):
        capsule = load_json(ROOT / "examples" / "style-capsule-graphite-copper.json")
        capsule["status"] = "adopted"
        errors = capsule_validator.validate_style_capsule(capsule)
        self.assertTrue(any("adoption_approved" in item for item in errors))
        capsule["adoption_approved"] = True
        self.assertEqual([], capsule_validator.validate_style_capsule(capsule))

    def test_capsule_content_linter_flags_copy_risks(self):
        capsule = load_json(ROOT / "examples" / "style-capsule-graphite-copper.json")
        capsule["visual_rules"]["typography_logic"] = ['title reads "ACME"', "copy the logo"]
        capsule["visual_rules"]["composition_logic"] = ["place at (x:16.5%, y:16.4%)"]
        warnings = capsule_validator.lint_style_capsule_content(capsule)
        self.assertTrue(any("quoted literal" in item for item in warnings))
        self.assertTrue(any("brand or signature" in item for item in warnings))
        self.assertTrue(any("coordinate-like" in item for item in warnings))

    def test_capsule_export_is_deep_copied(self):
        spec = load_json(ROOT / "examples" / "style-learning-graphite-copper.json")
        capsule = capsule_creator.create_style_capsule(spec)
        capsule["visual_rules"]["palette_logic"].append("new mutation")
        self.assertNotIn("new mutation", spec["style_learning"]["observed"]["palette_logic"])

    def test_legacy_material_key_is_rejected_even_with_canonical_key(self):
        spec = copy.deepcopy(self.template)
        spec["materials"] = [
            {
                "target": "skin",
                "description": "natural skin",
                "physical_properties": ["matte base"],
                "properties": ["legacy value"],
            }
        ]
        self.assertTrue(any("legacy key" in item for item in validator.validate_spec(spec)))

    def test_midjourney_version_rejects_boolean(self):
        spec = copy.deepcopy(self.template)
        spec["platform_options"]["midjourney"]["version"] = True
        self.assertTrue(any("midjourney.version" in item for item in validator.validate_spec(spec)))

    def test_mode_specific_sections_do_not_cross_modes(self):
        spec = copy.deepcopy(self.template)
        spec["style_learning"] = load_json(ROOT / "examples" / "style-learning-graphite-copper.json")["style_learning"]
        self.assertTrue(any("allowed only" in item for item in validator.validate_spec(spec)))
        spec = copy.deepcopy(self.template)
        spec["styleboard"] = make_styleboard_spec()["styleboard"]
        self.assertTrue(any("allowed only" in item for item in validator.validate_spec(spec)))

    def test_effect_requires_resistance_cost(self):
        spec = load_json(ROOT / "examples" / "causal-fantasy-effect.json")
        del spec["effects"][0]["resistance_cost"]
        self.assertTrue(any("resistance_cost" in item for item in validator.validate_spec(spec)))

    def test_color_pipeline_custom_intent_contract(self):
        spec = copy.deepcopy(self.template)
        spec["color_pipeline"]["intent"] = "custom"
        self.assertTrue(any("custom_intent" in item for item in validator.validate_spec(spec)))
        spec["color_pipeline"]["custom_intent"] = "silver-rich monochrome print"
        self.assertEqual([], validator.validate_spec(spec))

    def test_render_pipeline_engine_scope_and_custom_domain_contract(self):
        spec = copy.deepcopy(self.template)
        spec["render_pipeline"]["engine_reference"] = "Blender Cycles"
        spec["render_pipeline"]["engine_reference_scope"] = "pretend_execution"
        self.assertTrue(any("engine_reference_scope" in item for item in validator.validate_spec(spec)))
        spec["render_pipeline"]["engine_reference_scope"] = "appearance_reference"
        spec["render_pipeline"]["domain"] = "custom"
        self.assertTrue(any("custom_domain" in item for item in validator.validate_spec(spec)))
        spec["render_pipeline"]["custom_domain"] = "spectral research renderer"
        self.assertEqual([], validator.validate_spec(spec))

    def test_render_pipeline_rejects_post_generation_compositing_control(self):
        spec = copy.deepcopy(self.template)
        spec["render_pipeline"]["compositing"] = "assemble the generated result afterward"
        errors = validator.validate_spec(spec)
        self.assertIn("$.render_pipeline.compositing: unknown field", errors)
        self.assertNotIn("hybrid_composite", validator.RENDER_DOMAINS)

    def test_advanced_material_response_fields_are_valid(self):
        spec = load_json(ROOT / "examples" / "causal-fantasy-effect.json")
        material = spec["materials"][0]
        for key in (
            "microstructure",
            "roughness",
            "specular_response",
            "transmission",
            "subsurface_behavior",
            "anisotropy",
            "wear_patina",
            "contact_deformation",
        ):
            self.assertTrue(material[key])
        self.assertEqual([], validator.validate_spec(spec))

    def test_must_attach_input_requires_actual_source(self):
        spec = copy.deepcopy(self.template)
        spec["inputs"] = [
            {
                "id": "logo-reference",
                "type": "image",
                "role": "logo reference",
                "description": "Actual logo supplied by the user.",
                "source_kind": "unspecified",
                "source_ref": "",
                "must_attach": True,
            }
        ]
        self.assertTrue(any("actual source reference" in item for item in validator.validate_spec(spec)))

    def test_reference_led_modes_require_an_attached_image(self):
        for mode in ("reconstruct", "edit", "restyle", "expand", "learn_style"):
            with self.subTest(mode=mode):
                spec = copy.deepcopy(self.template)
                spec["mode"] = mode
                spec["inputs"] = [
                    {
                        "id": "source",
                        "type": "image",
                        "role": "base_image",
                        "description": "A described source that was not attached.",
                        "source_kind": "unspecified",
                        "source_ref": "",
                        "must_attach": False,
                    }
                ]
                errors = validator.validate_spec(spec)
                self.assertIn(f"$.inputs: mode={mode!r} requires at least one image with must_attach=true", errors)

    def test_reference_preflight_resolves_local_asset(self):
        spec = load_json(ROOT / "examples" / "style-learning-graphite-copper.json")
        result = reference_delivery.preflight_reference_delivery(spec, ROOT / "examples")
        self.assertTrue(result["valid"])
        self.assertEqual("ready", result["attachments"][0]["preflight"])

    def test_conversation_references_remain_runtime_required(self):
        spec = load_json(ROOT / "examples" / "styleboard-3x3.json")
        result = reference_delivery.preflight_reference_delivery(spec, ROOT / "examples")
        self.assertTrue(result["valid"])
        self.assertEqual(["image-1", "image-2"], result["runtime_required"])

    def test_codex_imagegen_reference_limit_and_mechanism_are_fail_closed(self):
        spec = copy.deepcopy(self.template)
        spec["inputs"] = [
            {
                "id": f"image-{index}",
                "type": "image",
                "role": "reference",
                "description": "required local reference",
                "source_kind": "local_path",
                "source_ref": "../assets/jingzao-image-forge-hero-en.png",
                "must_attach": True,
            }
            for index in range(1, 6)
        ]
        ready = reference_delivery.build_imagegen_call_plan(spec)
        self.assertEqual("ready", ready["status"])
        self.assertEqual("referenced_image_paths", ready["mechanism"])
        spec["inputs"].append(copy.deepcopy(spec["inputs"][-1]))
        spec["inputs"][-1]["id"] = "image-6"
        blocked = reference_delivery.build_imagegen_call_plan(spec)
        self.assertEqual("blocked", blocked["status"])
        self.assertTrue(any("at most 5" in error for error in blocked["errors"]))

    def test_codex_imagegen_rejects_mixed_attachment_mechanisms(self):
        spec = copy.deepcopy(self.template)
        spec["inputs"] = [
            self._attached_image("identity", "conversation identity"),
            {
                "id": "local-product",
                "type": "image",
                "role": "product",
                "description": "local product",
                "source_kind": "local_path",
                "source_ref": "../assets/jingzao-image-forge-hero-en.png",
                "must_attach": True,
            },
        ]
        plan = reference_delivery.build_imagegen_call_plan(spec, conversation_window_confirmed=True)
        self.assertEqual("blocked", plan["status"])
        self.assertTrue(any("cannot combine" in error for error in plan["errors"]))

    def test_conversation_image_window_requires_execution_time_confirmation(self):
        spec = make_styleboard_spec()
        blocked = reference_delivery.build_imagegen_call_plan(spec)
        self.assertEqual("blocked", blocked["status"])
        ready = reference_delivery.build_imagegen_call_plan(spec, conversation_window_confirmed=True)
        self.assertEqual("ready", ready["status"])
        self.assertEqual("num_last_images_to_include", ready["mechanism"])
        self.assertEqual(1, ready["argument"])

    def test_execution_receipt_must_match_call_plan(self):
        spec = load_json(ROOT / "examples" / "style-learning-graphite-copper.json")
        plan = reference_delivery.build_imagegen_call_plan(spec)
        receipt = {
            "mechanism": "referenced_image_paths",
            "sent_input_ids": ["style-reference"],
            "sent_count": 1,
            "tool_call_id": "call-1",
            "output_ref": "output.png",
        }
        self.assertEqual([], reference_delivery.validate_execution_receipt(plan, receipt))
        receipt["sent_input_ids"] = []
        self.assertTrue(reference_delivery.validate_execution_receipt(plan, receipt))

    def test_hashed_tool_call_identifier_is_valid_receipt_evidence(self):
        spec = load_json(ROOT / "examples" / "style-learning-graphite-copper.json")
        plan = reference_delivery.build_imagegen_call_plan(spec)
        receipt = {
            "mechanism": "referenced_image_paths",
            "sent_input_ids": ["style-reference"],
            "sent_count": 1,
            "tool_call_id_sha256": "a" * 64,
            "output_ref": "assets/gallery/output.jpg",
        }
        self.assertEqual([], reference_delivery.validate_execution_receipt(plan, receipt))

    def test_attachment_image_index_counts_images_only(self):
        spec = copy.deepcopy(self.template)
        spec["inputs"] = [
            {"id": "note", "type": "text", "role": "note", "description": "not an image"},
            self._attached_image("identity", "first image"),
            {**self._attached_image("wardrobe", "second image"), "id": "second-image"},
        ]
        manifest = reference_delivery.build_attachment_manifest(spec)
        self.assertEqual([1, 2], [item["image_index"] for item in manifest])

    def test_region_cannot_escape_canvas(self):
        spec = copy.deepcopy(self.example)
        spec["spatial_edits"][0]["region"]["x_percent"] = 90.0
        errors = validator.validate_spec(spec)
        self.assertTrue(any("x_percent + width_percent" in item for item in errors))

    def test_locked_control_requires_zero_variance(self):
        spec = copy.deepcopy(self.template)
        spec["composition"]["control"] = {"weight": 1.0, "lock": True, "variance": 0.2}
        errors = validator.validate_spec(spec)
        self.assertTrue(any("lock=true requires variance=0" in item for item in errors))

    def test_edit_requires_preserve_constraints(self):
        spec = copy.deepcopy(self.example)
        spec["constraints"]["must_preserve"] = []
        errors = validator.validate_spec(spec)
        self.assertTrue(any("requires explicit invariants" in item for item in errors))

    def test_unknown_flux_prompt_format_is_rejected(self):
        spec = copy.deepcopy(self.template)
        spec["platform_options"]["flux"]["prompt_format"] = "magic"
        errors = validator.validate_spec(spec)
        self.assertTrue(any("prompt_format" in item for item in errors))

    def test_midjourney_numeric_ranges_are_validated(self):
        cases = [("stylize", 1001), ("chaos", 101), ("style_weight", -1), ("quality", 0)]
        for key, value in cases:
            with self.subTest(key=key):
                spec = copy.deepcopy(self.template)
                spec["platform_options"]["midjourney"][key] = value
                errors = validator.validate_spec(spec)
                self.assertTrue(any(f"midjourney.{key}" in item for item in errors))

    def test_canvas_and_provider_geometry_must_agree(self):
        spec = copy.deepcopy(self.template)
        spec["canvas"] = {
            "profile": "standard_widescreen",
            "aspect_ratio": "16:9",
            "dimensions": {"width": 1536, "height": 864},
        }
        spec["platform_options"]["openai"]["size"] = "1024x1024"
        self.assertTrue(any("must match canvas.dimensions" in item for item in validator.validate_spec(spec)))
        spec = copy.deepcopy(self.template)
        spec["canvas"] = {
            "profile": "standard_widescreen",
            "aspect_ratio": "16:9",
            "dimensions": {"width": 1536, "height": 864},
        }
        spec["platform_options"]["midjourney"]["aspect_ratio"] = "1:1"
        self.assertTrue(any("must match canvas.aspect_ratio" in item for item in validator.validate_spec(spec)))

    def test_midjourney_style_reference_items_are_validated(self):
        invalid_items = [123, "", {"bad": True}, {"url": ""}, {"url": "https://example.com/a.png", "weight": 0}]
        for item in invalid_items:
            with self.subTest(item=item):
                spec = copy.deepcopy(self.template)
                spec["platform_options"]["midjourney"]["style_reference"] = [item]
                errors = validator.validate_spec(spec)
                self.assertTrue(any("midjourney.style_reference[0]" in error for error in errors))

    def test_midjourney_style_reference_weights_compile(self):
        spec = copy.deepcopy(self.template)
        spec["platform_options"]["midjourney"]["style_reference"] = [
            "https://example.com/a.png",
            {"url": "https://example.com/b.png", "weight": 2},
        ]
        self.assertEqual([], validator.validate_spec(spec))
        result = compiler.compile_spec(spec, "midjourney")
        self.assertIn("--sref https://example.com/a.png https://example.com/b.png::2", result["prompt"])

    def test_unknown_knowledge_strategy_is_rejected(self):
        spec = copy.deepcopy(self.template)
        spec["knowledge_anchors"] = [{"name": "Known entity", "strategy": "magic"}]
        errors = validator.validate_spec(spec)
        self.assertTrue(any("knowledge_anchors[0].strategy" in item for item in errors))

    def test_reference_knowledge_strategy_requires_known_input(self):
        spec = copy.deepcopy(self.template)
        spec["knowledge_anchors"] = [
            {"name": "Known entity", "strategy": "reference", "reference_ids": ["missing-reference"]}
        ]
        errors = validator.validate_spec(spec)
        self.assertTrue(any("unknown input id" in item for item in errors))

    def test_unknown_artifact_budget_is_rejected(self):
        spec = copy.deepcopy(self.template)
        spec["render"]["artifact_budget"] = "maximum-clean-magic"
        errors = validator.validate_spec(spec)
        self.assertTrue(any("render.artifact_budget" in item for item in errors))

    def test_provider_quality_is_rejected_inside_visual_render_layer(self):
        spec = copy.deepcopy(self.template)
        spec["render"]["quality"] = "high"
        errors = validator.validate_spec(spec)
        self.assertIn("$.render.quality: unknown field", errors)

    def test_legacy_material_properties_field_is_rejected(self):
        spec = copy.deepcopy(self.template)
        spec["materials"] = [
            {
                "target": "skin",
                "description": "Natural portrait skin.",
                "properties": ["matte base", "localized highlights"],
            }
        ]
        errors = validator.validate_spec(spec)
        self.assertTrue(any("materials[0].physical_properties" in item for item in errors))

    def test_subject_relationships_must_be_a_list(self):
        spec = copy.deepcopy(self.template)
        spec["subjects"][0]["relationships"] = "behind subject two"
        errors = validator.validate_spec(spec)
        self.assertTrue(any("subjects[0].relationships" in item for item in errors))

    def test_openai_quality_auto_is_valid(self):
        spec = copy.deepcopy(self.template)
        spec["platform_options"]["openai"]["quality"] = "auto"
        self.assertEqual([], validator.validate_spec(spec))

    def test_cinematic_ultrawide_rejects_standard_ratio(self):
        spec = copy.deepcopy(self.template)
        spec["canvas"]["profile"] = "cinematic_ultrawide"
        spec["canvas"]["aspect_ratio"] = "16:9"
        errors = validator.validate_spec(spec)
        self.assertTrue(any("cinematic_ultrawide" in item for item in errors))

    def test_narrative_film_frame_requires_full_contract(self):
        spec = copy.deepcopy(self.template)
        spec["cinematic"] = {"profile": "narrative_film_frame"}
        errors = validator.validate_spec(spec)
        self.assertTrue(any("cinematic.visible_event" in item for item in errors))
        self.assertTrue(any("staging" in item for item in errors))
        self.assertTrue(any("camera_motivation" in item for item in errors))

    def test_complete_narrative_film_frame_is_valid(self):
        self.assertEqual([], validator.validate_spec(make_narrative_spec()))

    def test_styleboard_requires_inputs_and_board_contract(self):
        spec = copy.deepcopy(self.template)
        spec["mode"] = "styleboard"
        errors = validator.validate_spec(spec)
        self.assertTrue(any("requires at least one input" in item for item in errors))
        self.assertTrue(any("requires a styleboard object" in item for item in errors))

    def test_unknown_styleboard_generation_strategy_is_rejected(self):
        spec = make_styleboard_spec()
        spec["styleboard"]["generation_strategy"] = "always-one-click"
        errors = validator.validate_spec(spec)
        self.assertTrue(any("styleboard.generation_strategy" in item for item in errors))

    def test_unknown_styleboard_hierarchy_profile_is_rejected(self):
        for invalid in ("everything-equal", [], {}):
            with self.subTest(invalid=invalid):
                spec = make_styleboard_spec()
                spec["styleboard"]["hierarchy_profile"] = invalid
                errors = validator.validate_spec(spec)
                self.assertTrue(any("styleboard.hierarchy_profile" in item for item in errors))

    def test_layered_styleboard_requires_hierarchy_for_every_frame(self):
        spec = make_styleboard_spec()
        spec["styleboard"]["hierarchy_profile"] = "layered_editorial"
        errors = validator.validate_spec(spec)
        self.assertTrue(any("frames[0].hierarchy" in item for item in errors))

    def test_layered_styleboard_requires_continuity_and_ambient_layers(self):
        spec = make_styleboard_spec()
        spec["styleboard"]["hierarchy_profile"] = "layered_editorial"
        for frame in spec["styleboard"]["frames"]:
            frame["hierarchy"] = {
                "l0_primary_focus": "one dominant action",
                "l1_proof": ["one visible result"],
                "l2_continuity": [],
                "l3_ambient_scaffold": [],
                "calm_zone": "upper-left text-safe field",
                "accent_owner": "none",
                "silenced_elements": ["all unrelated controls"],
            }
        errors = validator.validate_spec(spec)
        self.assertTrue(any("l2_continuity: expected at least one item" in item for item in errors))
        self.assertTrue(any("l3_ambient_scaffold: expected at least one item" in item for item in errors))

    def test_layered_styleboard_requires_explicit_accent_owner(self):
        spec = load_json(ROOT / "examples" / "ui-motion-storyboard.json")
        del spec["styleboard"]["frames"][0]["hierarchy"]["accent_owner"]
        errors = validator.validate_spec(spec)
        self.assertTrue(any("frames[0].hierarchy.accent_owner" in item for item in errors))

    def test_minimal_state_allows_quiet_continuity_and_ambient_layers(self):
        spec = make_styleboard_spec()
        spec["styleboard"]["hierarchy_profile"] = "minimal_state"
        for frame in spec["styleboard"]["frames"]:
            frame["hierarchy"] = {
                "l0_primary_focus": "one selected button",
                "l1_proof": ["one exact functional label"],
                "l2_continuity": [],
                "l3_ambient_scaffold": [],
                "calm_zone": "all space outside the control",
                "accent_owner": "the selected outline only",
                "silenced_elements": [],
            }
        self.assertEqual([], validator.validate_spec(spec))

    def test_unknown_styleboard_secondary_role_is_rejected(self):
        spec = make_styleboard_spec()
        spec["styleboard"]["reference_assignments"][0]["secondary_roles"] = ["mood_magic"]
        errors = validator.validate_spec(spec)
        self.assertTrue(any("secondary_roles[0]" in item for item in errors))

    def test_duplicate_styleboard_secondary_role_is_rejected(self):
        spec = make_styleboard_spec()
        spec["styleboard"]["reference_assignments"][0]["secondary_roles"] = ["palette", "palette"]
        errors = validator.validate_spec(spec)
        self.assertTrue(any("secondary_roles[1]: duplicate role" in item for item in errors))

    def test_unhashable_styleboard_secondary_role_returns_error(self):
        spec = make_styleboard_spec()
        spec["styleboard"]["reference_assignments"][0]["secondary_roles"] = [["palette"]]
        errors = validator.validate_spec(spec)
        self.assertTrue(any("secondary_roles[0]: expected one of" in item for item in errors))

    def test_non_list_styleboard_frames_returns_error(self):
        spec = make_styleboard_spec()
        spec["styleboard"]["frames"] = "not-a-list"
        errors = validator.validate_spec(spec)
        self.assertTrue(any("styleboard.frames: expected a list" in item for item in errors))

    def test_direct_styleboard_requires_matching_board_and_cell_ratio(self):
        spec = make_styleboard_spec()
        spec["styleboard"]["generation_strategy"] = "sheet_direct"
        spec["styleboard"]["frame_aspect_ratio"] = "9:16"
        errors = validator.validate_spec(spec)
        self.assertTrue(any("board_ratio" in item for item in errors))

    def test_direct_triptych_uses_grid_geometry_for_board_ratio(self):
        spec = make_styleboard_spec()
        spec["canvas"] = {
            "profile": "custom",
            "aspect_ratio": "16:3",
            "dimensions": {"width": 2048, "height": 384},
        }
        spec["styleboard"]["layout"] = "3x1"
        spec["styleboard"]["frame_count"] = 3
        spec["styleboard"]["generation_strategy"] = "sheet_direct"
        spec["styleboard"]["frames"] = spec["styleboard"]["frames"][:3]
        self.assertEqual([], validator.validate_spec(spec))

    def test_direction_deliverable_triggers_narrative_contract(self):
        spec = copy.deepcopy(self.template)
        spec["direction"] = {"deliverable": "narrative_film_frame"}
        spec["cinematic"] = {"profile": "auto"}
        errors = validator.validate_spec(spec)
        self.assertTrue(any("cinematic.visible_event" in item for item in errors))
        self.assertTrue(any("staging" in item for item in errors))

    def test_direction_and_cinematic_profiles_cannot_conflict(self):
        spec = make_narrative_spec()
        spec["direction"]["deliverable"] = "poster"
        errors = validator.validate_spec(spec)
        self.assertTrue(any("must agree" in item for item in errors))

    def test_unknown_spec_language_is_rejected(self):
        spec = copy.deepcopy(self.template)
        spec["language"] = "fr"
        errors = validator.validate_spec(spec)
        self.assertTrue(any("$.language" in item for item in errors))
        spec["language"] = "zh-CN"
        self.assertEqual([], validator.validate_spec(spec))

    def test_reconstruct_mode_accepts_observed_image_input(self):
        spec = copy.deepcopy(self.template)
        spec["mode"] = "reconstruct"
        spec["inputs"] = [self._attached_image("observed_reference", "Actual reference image.")]
        spec["reference_analysis"] = {
            "target": "reconstruct the observable image without claiming hidden-prompt recovery",
            "observed": ["one subject", "eye-level camera", "matte material"],
            "inferred": ["possible studio key light"],
            "unknowns": ["original lens", "original software", "hidden prompt"],
        }
        self.assertEqual([], validator.validate_spec(spec))

    def test_reconstruct_requires_observed_and_unknown_analysis(self):
        spec = copy.deepcopy(self.template)
        spec["mode"] = "reconstruct"
        spec["inputs"] = [self._attached_image("observed_reference", "Actual reference image.")]
        errors = validator.validate_spec(spec)
        self.assertTrue(any("reference_analysis" in item for item in errors))

    def test_restyle_mode_requires_and_accepts_preservation_contract(self):
        spec = copy.deepcopy(self.template)
        spec["mode"] = "restyle"
        spec["inputs"] = [self._attached_image("base_image", "Image to restyle.")]
        spec["constraints"]["must_preserve"] = ["identity", "pose", "layout", "text"]
        spec["constraints"]["must_change"] = ["visual treatment only"]
        self.assertEqual([], validator.validate_spec(spec))

    def test_expand_mode_requires_and_accepts_preservation_contract(self):
        spec = copy.deepcopy(self.template)
        spec["mode"] = "expand"
        spec["inputs"] = [self._attached_image("base_image", "Image to expand.")]
        spec["constraints"]["must_preserve"] = ["original content", "subject scale", "relative position"]
        spec["constraints"]["must_change"] = ["extend both sides"]
        self.assertEqual([], validator.validate_spec(spec))

    def test_restyle_and_expand_require_explicit_change(self):
        for mode in ("restyle", "expand"):
            with self.subTest(mode=mode):
                spec = copy.deepcopy(self.template)
                spec["mode"] = mode
                spec["inputs"] = [self._attached_image("base_image", f"Image to {mode}.")]
                spec["constraints"]["must_preserve"] = ["identity", "geometry"]
                errors = validator.validate_spec(spec)
                self.assertTrue(any("must_change" in item for item in errors))

    def test_edit_mode_accepts_must_change_without_spatial_edit(self):
        spec = copy.deepcopy(self.template)
        spec["mode"] = "edit"
        spec["inputs"] = [self._attached_image("base_image", "Image to edit.")]
        spec["constraints"]["must_preserve"] = ["camera", "layout"]
        spec["constraints"]["must_change"] = ["replace the background"]
        spec["spatial_edits"] = []
        self.assertEqual([], validator.validate_spec(spec))

    def test_square_vertical_and_custom_canvas_profiles(self):
        cases = [
            ("square", "1:1", {"width": 1024, "height": 1024}),
            ("vertical_story", "9:16", {"width": 864, "height": 1536}),
            ("custom", "3:2", {"width": 1536, "height": 1024}),
        ]
        for profile, ratio, dimensions in cases:
            with self.subTest(profile=profile):
                spec = copy.deepcopy(self.template)
                spec["canvas"] = {"profile": profile, "aspect_ratio": ratio, "dimensions": dimensions}
                self.assertEqual([], validator.validate_spec(spec))

    def test_subject_position_depth_must_be_string(self):
        spec = copy.deepcopy(self.template)
        spec["subjects"][0]["position"]["depth"] = 2
        errors = validator.validate_spec(spec)
        self.assertTrue(any("position.depth" in item for item in errors))

    def test_region_width_must_be_greater_than_zero(self):
        spec = copy.deepcopy(self.example)
        spec["spatial_edits"][0]["region"]["width_percent"] = 0
        errors = validator.validate_spec(spec)
        self.assertTrue(any("greater than 0 and at most 100" in item for item in errors))

    def test_styleboard_guidance_keeps_direct_sheet_as_valid_strategy(self):
        for relative_path in ("SKILL.md", "references/prompt-compiler.md"):
            with self.subTest(path=relative_path):
                guidance = (ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn("sheet_direct", guidance)
                self.assertIn("independent_frames", guidance)
                self.assertIn("hybrid", guidance)
                self.assertNotIn("do not ask one image generation to invent a precise multi-frame board", guidance)


class CompilerTests(unittest.TestCase):
    def setUp(self):
        self.example = load_json(ROOT / "examples" / "atomic-cyber-live-action.json")

    def test_openai_compiler_emits_surgical_edit_contract(self):
        result = compiler.compile_spec(self.example, "openai")
        self.assertEqual("gpt-image-2", result["parameters"]["model"])
        self.assertIn("Change only", result["prompt"])
        self.assertIn("Inputs:", result["prompt"])
        self.assertIn("Preserve:", result["prompt"])
        self.assertIn("16.5% from left", result["prompt"])
        self.assertIn("painterly illustration", result["prompt"])

    def test_flux_compiler_does_not_emit_negative_prompt(self):
        result = compiler.compile_spec(self.example, "flux")
        self.assertEqual("", result["negative_prompt"])
        self.assertTrue(any("no negative-prompt channel" in item for item in result["warnings"]))
        self.assertNotIn("--no", result["prompt"])

    def test_flux_exclusion_does_not_force_medium_change(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["style"]["medium"] = "watercolor illustration"
        spec["style"]["realism"] = "stylized"
        spec["style"]["excluded_traits"] = ["painterly illustration"]
        result = compiler.compile_spec(spec, "flux")
        self.assertIn("watercolor illustration", result["prompt"])
        self.assertNotIn("photorealistic live-action rendering", result["prompt"])
        self.assertTrue(any("painterly illustration" in item for item in result["warnings"]))

    def test_midjourney_parameters_are_at_end(self):
        result = compiler.compile_spec(self.example, "midjourney")
        prompt = result["prompt"]
        self.assertIn("--ar 16:9", prompt)
        self.assertIn("--raw", prompt)
        self.assertIn("--no", prompt)
        self.assertIn("painterly illustration", prompt)
        self.assertGreater(prompt.index("--ar"), prompt.index("physically fractured"))
        self.assertTrue(any("not pixel-accurate" in item for item in result["warnings"]))
        self.assertTrue(any("multi-word exclusions" in item for item in result["warnings"]))
        self.assertTrue(any("quality values are version-specific" in item for item in result["warnings"]))

    def test_auto_platform_is_generic(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        result = compiler.compile_spec(spec)
        self.assertEqual("generic", result["platform"])
        self.assertTrue(result["warnings"])

    def test_compiler_preserves_spec_language_metadata(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["language"] = "zh-CN"
        result = compiler.compile_spec(spec, "openai")
        self.assertEqual("zh-CN", result["language"])

    def test_openai_compiler_frontloads_world_knowledge_anchor(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["intent"] = "Create the named animated character in one new scene."
        name = "Known canonical animated character, specified incarnation"
        spec["knowledge_anchors"] = [
            {
                "name": name,
                "context": "canonical animated-series identity",
                "strategy": "model_knowledge",
                "verification": "unverified",
            }
        ]
        result = compiler.compile_spec(spec, "openai")
        self.assertLess(result["prompt"].index(name), result["prompt"].index("Goal:"))
        self.assertIn("use existing model knowledge", result["prompt"])
        self.assertTrue(any("must be visually verified" in item for item in result["warnings"]))

    def test_auto_knowledge_strategy_becomes_hybrid_with_reference(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["inputs"] = [
            {
                "id": "identity-reference",
                "type": "image",
                "role": "identity_reference",
                "description": "Version-matched canonical identity reference.",
            }
        ]
        spec["knowledge_anchors"] = [
            {
                "name": "Known canonical entity",
                "strategy": "auto",
                "reference_ids": ["identity-reference"],
            }
        ]
        result = compiler.compile_spec(spec, "openai")
        self.assertIn("combine existing model knowledge with the referenced inputs", result["prompt"])

    def test_named_entity_survives_every_compiler(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        name = "Known canonical entity"
        spec["knowledge_anchors"] = [{"name": name, "strategy": "auto"}]
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = compiler.compile_spec(spec, platform)
                self.assertIn(name, result["prompt"])

    def test_strict_artifact_budget_compiles_positive_quality_controls(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["render"]["artifact_budget"] = "strict"
        spec["render"]["quality_controls"] = ["matte skin with localized soft specular highlights"]
        result = compiler.compile_spec(spec, "openai")
        self.assertIn("clean low-noise tonal fields", result["prompt"])
        self.assertIn("matte skin with localized soft specular highlights", result["prompt"])

    def test_clean_reset_budget_compiles_surface_ownership_across_platforms(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["intent"] = "Rebuild a premium portrait from a clean specification after repeated oily noise."
        spec["render"]["artifact_budget"] = "clean_reset"
        self.assertEqual([], validator.validate_spec(spec))
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                prompt = compiler.compile_spec(spec, platform)["prompt"]
                for marker in (
                    "3-7 dominant low-frequency shape groups",
                    "one or two camera-readable focal-detail clusters",
                    "at least one continuous calm surface",
                    "localized contact shadows only at real seams",
                    "strict wet/dry and matte/gloss boundaries",
                    "readable shadow floor",
                ):
                    self.assertIn(marker, prompt)

    def test_source_matched_budget_preserves_source_artifact_profile(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["render"]["artifact_budget"] = "source_matched"
        result = compiler.compile_spec(spec, "generic")
        self.assertIn("match source noise or grain, bloom, flare, sharpness, and surface response", result["prompt"])

    def test_narrative_compiler_frontloads_story_camera_and_staging(self):
        result = compiler.compile_spec(make_narrative_spec(), "openai")
        prompt = result["prompt"]
        self.assertLess(prompt.index("Cinematic shot contract:"), prompt.index("Staging and relationship geometry:"))
        self.assertIn("camera motivation", prompt)
        self.assertIn("40mm lens intent", prompt)
        self.assertIn("avoid poster-style simultaneous showcase", prompt)

    def test_valid_nine_grid_styleboard_compiles_all_frames(self):
        spec = make_styleboard_spec()
        self.assertEqual([], validator.validate_spec(spec))
        result = compiler.compile_spec(spec, "openai")
        self.assertIn("frame frame-01", result["prompt"])
        self.assertIn("frame frame-09", result["prompt"])
        self.assertTrue(any("rapid exploration" in item for item in result["warnings"]))

    def test_ui_motion_storyboard_compiles_exact_text_and_semantic_accent(self):
        spec = load_json(ROOT / "examples" / "ui-motion-storyboard.json")
        result = compiler.compile_spec(spec, "openai")
        prompt = result["prompt"]
        self.assertIn('"开始设置" exactly', prompt)
        self.assertIn('"分析中 68%" exactly', prompt)
        self.assertIn("#FF6A2A owns only the active state", prompt)
        self.assertIn("no full dashboard", prompt)
        self.assertIn("mouse pointer for desktop interaction", prompt)
        self.assertIn("hand or finger cursor", prompt)
        self.assertIn("all introductory or inactive elements remain charcoal or gray", prompt)
        self.assertIn("visible shot numbers, frame IDs, duration labels, review arrows or production annotations", prompt)
        self.assertIn("hierarchy profile: layered editorial", prompt)
        self.assertIn("L0 primary focus:", prompt)
        self.assertIn("L1 proof layer:", prompt)
        self.assertIn("L2 continuity layer:", prompt)
        self.assertIn("L3 ambient scaffold:", prompt)
        self.assertIn("calm zone:", prompt)
        self.assertIn("silence competitors:", prompt)
        self.assertEqual("sequence", result["prompt_review"]["detail_mode"])
        self.assertEqual(4, result["prompt_review"]["complexity_signals"]["styleboard_frame_count"])
        self.assertGreater(result["prompt_review"]["complexity_signals"]["hierarchy_layer_count"], 12)

    def test_ui_motion_hierarchy_compiles_for_every_platform(self):
        spec = load_json(ROOT / "examples" / "ui-motion-storyboard.json")
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = compiler.compile_spec(spec, platform)
                self.assertIn("hierarchy profile: layered editorial", result["prompt"])
                self.assertIn("L0 primary focus:", result["prompt"])
                self.assertIn("L1 proof layer:", result["prompt"])
                self.assertIn("L2 continuity layer:", result["prompt"])
                self.assertIn("L3 ambient scaffold:", result["prompt"])
                self.assertIn("calm zone:", result["prompt"])
                self.assertIn("accent owner:", result["prompt"])
                self.assertIn("silence competitors:", result["prompt"])
                self.assertEqual(
                    28,
                    result["prompt_review"]["complexity_signals"]["hierarchy_layer_count"],
                )

    def test_duplicate_hierarchy_layers_do_not_inflate_budget_signal(self):
        spec = make_styleboard_spec()
        spec["styleboard"]["hierarchy_profile"] = "layered_editorial"
        for frame in spec["styleboard"]["frames"]:
            frame["hierarchy"] = {
                "l0_primary_focus": "same element",
                "l1_proof": ["same element"],
                "l2_continuity": ["same element"],
                "l3_ambient_scaffold": ["same element"],
                "calm_zone": "same calm zone",
                "accent_owner": "none",
                "silenced_elements": ["same competitor"],
            }
        result = compiler.compile_spec(spec, "openai")
        self.assertEqual(
            4,
            result["prompt_review"]["complexity_signals"]["hierarchy_layer_count"],
        )

    def test_creative_routing_compiles_for_every_platform(self):
        spec = load_json(ROOT / "examples" / "tactile-stop-motion-product.json")
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = compiler.compile_spec(spec, platform)
                self.assertIn("product_tabletop", result["prompt"])
                self.assertIn("tactile_handcrafted", result["prompt"])
                self.assertIn("stop_motion", result["prompt"])

    def test_style_capsule_compiles_for_every_platform(self):
        spec = load_json(ROOT / "examples" / "tactile-stop-motion-product.json")
        capsule = load_json(ROOT / "examples" / "style-capsule-graphite-copper.json")
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = compiler.compile_spec(spec, platform, capsule)
                self.assertIn("Graphite Copper Editorial", result["prompt"])
                self.assertIn("forbidden transfer", result["prompt"])

    def test_style_capsule_keeps_target_spec_authoritative(self):
        spec = load_json(ROOT / "examples" / "tactile-stop-motion-product.json")
        capsule = load_json(ROOT / "examples" / "style-capsule-graphite-copper.json")
        result = compiler.compile_spec(spec, "openai", capsule)
        self.assertIn("target specification remains authoritative", result["prompt"])
        self.assertLess(result["prompt"].index("product_tabletop"), result["prompt"].index("Graphite Copper Editorial"))

    def test_invalid_style_capsule_is_rejected_before_compilation(self):
        spec = load_json(ROOT / "examples" / "tactile-stop-motion-product.json")
        capsule = load_json(ROOT / "examples" / "style-capsule-graphite-copper.json")
        capsule["source_summary"]["raw_images_stored"] = True
        with self.assertRaisesRegex(ValueError, "Style capsule validation failed"):
            compiler.compile_spec(spec, "openai", capsule)

    def test_auto_creative_routing_fields_do_not_clutter_prompt(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        result = compiler.compile_spec(spec, "openai")
        self.assertNotIn("scenario profile: auto", result["prompt"])
        self.assertNotIn("primary aesthetic: auto", result["prompt"])

    def test_neutral_template_does_not_invent_canvas_camera_position_or_finish(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        self.assertEqual([], validator.validate_spec(spec))
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = compiler.compile_spec(spec, platform)
                content = result["prompt"].split(" --", 1)[0]
                self.assertEqual("", content)
                self.assertNotIn("--ar", result["prompt"])
                self.assertNotIn("size", result.get("parameters", {}))
                self.assertNotIn("aspect_ratio", result.get("parameters", {}))
                self.assertEqual("blocked", result["prompt_review"]["status"])
                self.assertIn("empty_prompt", result["prompt_review"]["reasons"])
                self.assertEqual("blocked", result["imagegen_call_plan"]["status"])
                approved = compiler.compile_spec(spec, platform, review_approved=True)
                self.assertEqual("blocked", approved["prompt_review"]["status"])

    def test_auto_artifact_budget_is_valid_and_emits_no_aesthetic_prior(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["render"]["artifact_budget"] = "auto"
        self.assertEqual([], validator.validate_spec(spec))
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = compiler.compile_spec(spec, platform)
                self.assertNotIn("artifact budget", result["prompt"])
                self.assertNotIn("grain", result["prompt"])
                self.assertNotIn("bloom", result["prompt"])
                self.assertNotIn("flare", result["prompt"])
                self.assertNotIn("particles", result["prompt"])

    def test_nonempty_auto_prompt_gets_adaptive_clean_base_across_platforms(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["intent"] = "Create a rain-soaked 35mm documentary street portrait."
        spec["subjects"][0]["description"] = "one cyclist waiting under a shop awning"
        spec["style"]["medium"] = "35mm documentary photography with intentional fine film grain"
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = compiler.compile_spec(spec, platform)
                prompt = result["prompt"]
                self.assertIn("preventive clean base", prompt)
                self.assertIn("every texture belongs to the requested medium or a named material", prompt)
                self.assertIn("localized texture or surface variation has an explicit spatial owner", prompt)
                self.assertIn("stays inside its named region", prompt)
                self.assertIn("preserve intentional medium traits required by the brief or source", prompt)
                self.assertIn("intentional fine film grain", prompt)
                self.assertNotIn("clean-slate surface rebuild", prompt)
                review = result["prompt_review"]
                self.assertLessEqual(review["min_review_target_words"], review["target_words"])
                self.assertLessEqual(review["target_words"], review["max_review_target_words"])

        full_frame = load_json(ROOT / "templates" / "visual-spec.json")
        full_frame["intent"] = "Create a watercolor landscape on cold-press paper."
        full_frame["style"]["medium"] = (
            "transparent watercolor with continuous cold-press paper tooth visible across the whole image"
        )
        full_frame_prompt = compiler.compile_spec(full_frame, "openai")["prompt"]
        self.assertIn("continuous cold-press paper tooth visible across the whole image", full_frame_prompt)
        self.assertIn("localized texture or surface variation has an explicit spatial owner", full_frame_prompt)
        self.assertNotIn("every texture belongs to the requested medium or a named material, has", full_frame_prompt)

    def test_explicit_artifact_budget_replaces_auto_clean_base(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["intent"] = "Create one restrained premium product image."
        spec["render"]["artifact_budget"] = "strict"
        result = compiler.compile_spec(spec, "openai")
        self.assertIn("artifact budget (strict)", result["prompt"])
        self.assertNotIn("preventive clean base", result["prompt"])

    def test_simple_create_uses_only_brief_grounded_core_content(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["intent"] = "Create a clean catalog image of one red ceramic mug."
        spec["scene"]["summary"] = "The mug stands on a plain warm-gray tabletop."
        spec["subjects"][0]["description"] = "red ceramic mug"
        spec["style"]["medium"] = "natural product photography"
        result = compiler.compile_spec(spec, "openai")
        self.assertLessEqual(result["prompt_metrics"]["words"], 110)
        self.assertIn("preventive clean base", result["prompt"])
        for absent in (
            "Cinematic shot contract",
            "Spatial dynamics and visual tension",
            "Color pipeline and finishing",
            "Render pipeline and material transport",
            "grain",
            "bloom",
            "flare",
            "particles",
        ):
            self.assertNotIn(absent, result["prompt"])

    def test_explicit_professional_controls_survive_minimal_intervention(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["composition"].update(
            {
                "shot_size": "medium close-up",
                "camera_angle": "low angle",
                "focal_length_mm": 32,
                "camera_roll": "8 degrees clockwise",
                "perspective_distortion": "controlled near-field expansion",
            }
        )
        spec["color_pipeline"].update(
            {
                "intent": "film_emulation",
                "highlight_rolloff": "long shoulder with contained practicals",
            }
        )
        spec["color_pipeline"]["film_emulation"]["grain"] = "fine irregular 35mm grain"
        spec["render_pipeline"].update(
            {
                "domain": "path_traced",
                "global_illumination": "multi-bounce indirect light",
            }
        )
        spec["render"]["artifact_budget"] = "expressive"
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = compiler.compile_spec(spec, platform, review_approved=True)
                for required in (
                    "medium close-up",
                    "low angle",
                    "32mm lens intent",
                    "8 degrees clockwise",
                    "controlled near-field expansion",
                    "film_emulation",
                    "long shoulder with contained practicals",
                    "fine irregular 35mm grain",
                    "path_traced",
                    "multi-bounce indirect light",
                    "artifact budget (expressive)",
                ):
                    self.assertIn(required, result["prompt"])

    def test_template_placeholders_do_not_reach_compiled_prompt(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = compiler.compile_spec(spec, platform)
                self.assertNotIn("Describe the", result["prompt"])

    def test_prompt_review_preserves_full_causal_fixture_without_silent_compaction(self):
        spec = load_json(ROOT / "examples" / "causal-fantasy-effect.json")
        result = compiler.compile_spec(spec, "openai")
        self.assertEqual("dynamic_semantic_review", result["prompt_review"]["budget_policy"])
        self.assertEqual("complex", result["prompt_review"]["detail_mode"])
        self.assertGreater(result["prompt_review"]["target_words"], 1300)
        self.assertEqual("ready", result["prompt_review"]["status"])
        for required in (
            "one adult cultivator",
            "owner/source",
            "operation/contact",
            "resistance/cost",
            "response:",
            "decay/residue",
            "24mm lens intent",
        ):
            self.assertIn(required, result["prompt"])
        self.assertFalse(any("Prompt normalization compacted" in item for item in result["warnings"]))

    def test_dynamic_prompt_budget_scales_with_semantic_complexity(self):
        simple = load_json(ROOT / "templates" / "visual-spec.json")
        simple["intent"] = "Create one red ceramic mug on a plain tabletop."
        simple["subjects"][0]["description"] = "one red ceramic mug"
        complex_spec = load_json(ROOT / "examples" / "causal-fantasy-effect.json")
        simple_result = compiler.compile_spec(simple, "openai")
        complex_result = compiler.compile_spec(complex_spec, "openai")
        simple_review = simple_result["prompt_review"]
        complex_review = complex_result["prompt_review"]
        self.assertEqual("concise", simple_review["detail_mode"])
        self.assertEqual("complex", complex_review["detail_mode"])
        self.assertLess(simple_review["complexity_units"], complex_review["complexity_units"])
        self.assertLess(simple_review["target_words"], complex_review["target_words"])
        self.assertLessEqual(complex_review["target_words"], complex_review["max_review_target_words"])

    def test_dynamic_budget_caps_review_target_without_truncating_prompt(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["intent"] = " ".join(["CURRENT_LONG_FACT"] * 4000) + " KEEP_FINAL_MARKER"
        spec["text_elements"] = [
            {
                "content": f"LABEL {index}",
                "case_sensitive": True,
                "placement": f"grid cell {index}",
                "typography": "plain sans serif",
                "color": "black",
            }
            for index in range(50)
        ]
        result = compiler.compile_spec(spec, "openai")
        review = result["prompt_review"]
        self.assertEqual(review["max_review_target_words"], review["target_words"])
        self.assertEqual("review_required", review["status"])
        self.assertIn("length_over_target", review["reasons"])
        self.assertIn("KEEP_FINAL_MARKER", result["prompt"])

    def test_cjk_review_units_block_long_unspaced_prompt(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["intent"] = "当前事实" * 4000
        result = compiler.compile_spec(spec, "openai")
        self.assertGreater(result["prompt_metrics"]["cjk_characters"], 10000)
        self.assertGreater(result["prompt_metrics"]["review_units"], result["prompt_review"]["target_review_units"])
        self.assertEqual("review_required", result["prompt_review"]["status"])
        self.assertIn("length_over_target", result["prompt_review"]["reasons"])

    def test_duplicate_semantic_entries_do_not_inflate_budget(self):
        base = load_json(ROOT / "templates" / "visual-spec.json")
        base["intent"] = "Create a labeled educational card."
        text_item = {
            "content": "ONE LABEL",
            "case_sensitive": True,
            "placement": "center",
            "typography": "plain sans serif",
            "color": "black",
        }
        base["text_elements"] = [text_item]
        baseline_review = compiler.compile_spec(base, "openai")["prompt_review"]
        duplicated = copy.deepcopy(base)
        duplicated["text_elements"] = [copy.deepcopy(text_item) for _ in range(50)]
        duplicated_review = compiler.compile_spec(duplicated, "openai")["prompt_review"]
        self.assertEqual(baseline_review["complexity_units"], duplicated_review["complexity_units"])
        self.assertEqual(baseline_review["target_words"], duplicated_review["target_words"])

    def test_styleboard_uses_sequence_budget_mode(self):
        spec = load_json(ROOT / "examples" / "continuous-nine-shot-ferry.json")
        review = compiler.compile_spec(spec, "openai")["prompt_review"]
        self.assertEqual("sequence", review["detail_mode"])
        self.assertEqual(9, review["complexity_signals"]["styleboard_frame_count"])

    def test_length_review_uses_final_prompt_without_deleting_explicit_fields(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        long_clause = " ".join(f"detail{index}" for index in range(130))
        spec["lighting"] = {
            "summary": long_clause,
            "motivation": long_clause,
            "narrative_function": long_clause,
            "key": long_clause,
            "fill": long_clause,
            "rim": long_clause,
            "direction": long_clause,
            "contrast": long_clause,
            "color_temperature": "KEEP_EXPLICIT_TEMPERATURE " + long_clause,
            "practicals": [],
        }
        spec["constraints"]["must_preserve"] = [" ".join(["constraint"] * 250)]
        result = compiler.compile_spec(spec, "openai")
        self.assertEqual("review_required", result["prompt_review"]["status"])
        self.assertIn("KEEP_EXPLICIT_TEMPERATURE", result["prompt"])
        self.assertFalse(any("Prompt normalization compacted" in item for item in result["warnings"]))

    def test_prompt_normalization_preserves_style_tension_fields(self):
        cases = (
            ROOT / "examples" / "causal-fantasy-effect.json",
            ROOT / "tests" / "forward-specs" / "cg-fashion-rain-platform.json",
        )
        for path in cases:
            with self.subTest(path=path.name):
                result = compiler.compile_spec(load_json(path), "openai", review_approved=True)
                for marker in (
                    "style authority:",
                    "adaptation rule:",
                    "tone locks:",
                    "forbidden drift:",
                    "depth transition:",
                    "parallax logic:",
                    "motion evidence:",
                    "readability guard:",
                ):
                    self.assertIn(marker, result["prompt"])
        causal = compiler.compile_spec(load_json(cases[0]), "openai", review_approved=True)["prompt"]
        for marker in ("grain:", "halation:", "NPR strategy:", "forbidden render artifacts:"):
            self.assertIn(marker, causal)

    def test_all_explicit_fields_preserve_semicolon_continuations(self):
        spec = load_json(ROOT / "examples" / "causal-fantasy-effect.json")
        spec["intent"] += " " + "current-style-density " * 500
        spec["creative_routing"]["adaptation_rule"] = "KEEP_ADAPT_A; KEEP_ADAPT_B"
        spec["spatial_dynamics"]["depth_transition"] = "KEEP_DEPTH_A; KEEP_DEPTH_B"
        spec["color_pipeline"]["film_emulation"]["grain"] = "KEEP_GRAIN_A; KEEP_GRAIN_B"
        spec["render_pipeline"]["npr_strategy"] = "KEEP_NPR_A; KEEP_NPR_B"
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = compiler.compile_spec(spec, platform, review_approved=True)
                self.assertFalse(any("Prompt normalization compacted" in item for item in result["warnings"]))
                prompt = result["prompt"]
                for marker in ("KEEP_ADAPT_B", "KEEP_DEPTH_B", "KEEP_GRAIN_B", "KEEP_NPR_B"):
                    self.assertIn(marker, prompt)

    def test_rich_forward_specs_keep_explicit_controls_in_provider_projections(self):
        bridge = load_json(ROOT / "tests" / "forward-specs" / "cinematic-bridge-rescue.json")
        bridge_prompt = compiler.compile_spec(bridge, "openai", review_approved=True)["prompt"]
        for marker in (
            "saturation policy: restrained except for the small amber contact cue",
            "film negative/reversal character: fine-grained 35mm dramatic negative response",
            "temperature: cold blue-gray environment with localized dim amber",
            "practicals: one gate lantern at far left",
        ):
            self.assertIn(marker, bridge_prompt)

        koi = load_json(ROOT / "tests" / "forward-specs" / "path-traced-koi-automaton.json")
        koi_prompt = compiler.compile_spec(koi, "midjourney", review_approved=True)["prompt"]
        for marker in (
            "reflection model:",
            "shadow model:",
            "ambient occlusion:",
            "volumetrics:",
            "material workflow:",
            "subsurface scattering:",
            "transmission/refraction:",
            "caustics:",
            "displacement/normal:",
            "texture scale:",
            "sampling/denoise:",
            "performance/fidelity tradeoff:",
        ):
            self.assertIn(marker, koi_prompt)

    def test_prompt_lint_blocks_placeholder_and_fixture_regression(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        result = compiler.compile_spec(spec, "openai")
        self.assertIn("prompt_review is blocked", prompt_lint.lint_compiled_result(result, max_words=1200))
        bad = copy.deepcopy(result)
        bad["prompt"] = "Describe the scene with control.weight; keep it different from the previous version"
        bad["prompt_metrics"] = {"words": 1300}
        errors = prompt_lint.lint_compiled_result(bad, max_words=1200)
        self.assertGreaterEqual(len(errors), 3)

    def test_prompt_lint_rejects_empty_semantic_prompt_for_every_platform(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = compiler.compile_spec(spec, platform)
                errors = prompt_lint.lint_compiled_result(result)
                self.assertIn("compiled prompt has no semantic content", errors)
                self.assertIn("prompt_review is blocked", errors)
        constraints_only = load_json(ROOT / "templates" / "visual-spec.json")
        constraints_only["constraints"]["exclude"] = ["watermark"]
        result = compiler.compile_spec(constraints_only, "openai", review_approved=True)
        self.assertEqual("blocked", result["prompt_review"]["status"])
        self.assertIn("empty_prompt", result["prompt_review"]["reasons"])
        self.assertNotIn("preventive clean base", result["prompt"])

    def test_flux_json_empty_template_is_blocked_without_empty_subject_payload(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["platform_options"]["flux"]["prompt_format"] = "json"
        result = compiler.compile_spec(spec, "flux", review_approved=True)
        self.assertEqual("", result["prompt"])
        self.assertEqual("blocked", result["prompt_review"]["status"])
        self.assertIn("empty_prompt", result["prompt_review"]["reasons"])
        self.assertEqual("blocked", result["imagegen_call_plan"]["status"])
        self.assertIn("compiled prompt has no semantic content", prompt_lint.lint_compiled_result(result))

    def test_prompt_review_requires_semantic_audit_above_target(self):
        baseline = load_json(ROOT / "templates" / "visual-spec.json")
        baseline["intent"] = "distinct-current-fact"
        baseline_target = compiler.compile_spec(baseline, "openai")["prompt_review"]["target_words"]
        spec = copy.deepcopy(baseline)
        spec["intent"] = " ".join(["distinct-current-fact"] * 1400)
        result = compiler.compile_spec(spec, "openai")
        self.assertEqual(baseline_target, result["prompt_review"]["target_words"])
        self.assertEqual("review_required", result["prompt_review"]["status"])
        self.assertTrue(result["prompt_review"]["reasons"])
        self.assertEqual("review_required", result["imagegen_call_plan"]["status"])
        self.assertTrue(prompt_lint.lint_compiled_result(result))
        approved = compiler.compile_spec(spec, "openai", review_approved=True)
        self.assertEqual("approved", approved["prompt_review"]["status"])
        self.assertEqual("length_and_reference_complexity_only", approved["prompt_review"]["approval_scope"])
        self.assertEqual("ready", approved["imagegen_call_plan"]["status"])
        self.assertEqual([], prompt_lint.lint_compiled_result(approved))

    def test_surface_risk_language_requires_review_but_exact_copy_is_exempt(self):
        risky = load_json(ROOT / "templates" / "visual-spec.json")
        risky["intent"] = "Create an ultra detailed product image with wet glossy surfaces，超级细节，湿润油亮。"
        result = compiler.compile_spec(risky, "openai")
        self.assertEqual("review_required", result["prompt_review"]["status"])
        self.assertIn("surface_risk_language:ultra detailed", result["prompt_review"]["reasons"])
        self.assertIn("surface_risk_language:wet glossy", result["prompt_review"]["reasons"])
        self.assertIn("surface_risk_language:超级细节", result["prompt_review"]["reasons"])
        self.assertIn("surface_risk_language:湿润油亮", result["prompt_review"]["reasons"])
        self.assertEqual(
            "selective camera-readable detail on focal surfaces",
            result["prompt_review"]["surface_risk_rewrites"]["ultra detailed"],
        )
        approved = compiler.compile_spec(risky, "openai", review_approved=True)
        self.assertEqual("approved", approved["prompt_review"]["status"])
        self.assertEqual(
            "surface_risk_length_and_reference_complexity",
            approved["prompt_review"]["approval_scope"],
        )

        punctuated = load_json(ROOT / "templates" / "visual-spec.json")
        punctuated["intent"] = (
            "Create an ultra-detailed, hyper_detailed image with micro-detail everywhere and wet, glossy surfaces."
        )
        punctuated_review = compiler.compile_spec(punctuated, "openai")["prompt_review"]
        for phrase in ("ultra detailed", "hyper detailed", "micro detail everywhere", "wet glossy"):
            self.assertIn(f"surface_risk_language:{phrase}", punctuated_review["reasons"])

        literal = load_json(ROOT / "templates" / "visual-spec.json")
        literal["text_elements"] = [
            {
                "content": "ULTRA DETAILED",
                "case_sensitive": True,
                "placement": "center",
                "typography": "bold sans serif",
                "color": "white",
            }
        ]
        literal_result = compiler.compile_spec(literal, "openai")
        self.assertEqual([], literal_result["prompt_review"]["surface_risk_hits"])

    def test_high_reference_count_requires_review_without_dropping_inputs(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["inputs"] = [
            {
                "id": f"reference-{index}",
                "type": "image",
                "role": f"role {index}",
                "description": f"current reference {index}",
                "source_kind": "conversation_image",
                "source_ref": f"Image {index}",
                "must_attach": True,
            }
            for index in range(1, 5)
        ]
        result = compiler.compile_spec(spec, "openai")
        self.assertEqual(4, result["prompt_review"]["required_reference_count"])
        self.assertEqual("review_required", result["prompt_review"]["status"])
        self.assertEqual("blocked", result["imagegen_call_plan"]["status"])
        self.assertTrue(any("High reference-role count" in item for item in result["warnings"]))

    def test_context_residue_blocks_execution_but_exact_copy_is_exempt(self):
        contaminated = load_json(ROOT / "templates" / "visual-spec.json")
        contaminated["intent"] = "Continue to keep the same as the previous version"
        literal = load_json(ROOT / "templates" / "visual-spec.json")
        literal["text_elements"] = [
            {
                "content": "继续保持上一版",
                "case_sensitive": True,
                "placement": "center",
                "typography": "bold sans serif",
                "color": "white",
            }
        ]
        literal["platform_options"]["flux"]["prompt_format"] = "json"
        same_form_prose = copy.deepcopy(literal)
        same_form_prose["intent"] = 'Render "继续保持上一版" exactly, same as the previous version'
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform, case="contaminated"):
                result = compiler.compile_spec(contaminated, platform, review_approved=True)
                self.assertEqual("blocked", result["prompt_review"]["status"])
                self.assertEqual("blocked", result["imagegen_call_plan"]["status"])
                self.assertTrue(prompt_lint.lint_compiled_result(result))
            with self.subTest(platform=platform, case="literal"):
                literal_result = compiler.compile_spec(literal, platform)
                self.assertEqual("ready", literal_result["prompt_review"]["status"])
                self.assertEqual([], prompt_lint.lint_compiled_result(literal_result))
            with self.subTest(platform=platform, case="same_form_prose"):
                mixed_result = compiler.compile_spec(same_form_prose, platform, review_approved=True)
                self.assertEqual("blocked", mixed_result["prompt_review"]["status"])

    def test_style_capsule_identity_is_in_context_residue_review(self):
        spec = load_json(ROOT / "examples" / "tactile-stop-motion-product.json")
        capsule = load_json(ROOT / "examples" / "style-capsule-graphite-copper.json")
        capsule["name"] = "Same as the previous version"
        result = compiler.compile_spec(spec, "openai", capsule, review_approved=True)
        self.assertEqual("blocked", result["prompt_review"]["status"])

    def test_midjourney_execution_route_matches_mode_and_reference_role(self):
        edit = compiler.compile_spec(self.example, "midjourney")
        self.assertEqual("editor_required", edit["execution_route"])
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["platform_options"]["midjourney"]["style_reference"] = ["https://example.com/style.png"]
        result = compiler.compile_spec(spec, "midjourney")
        self.assertEqual("style_reference", result["execution_route"])

    def test_platform_options_null_compiles_every_platform(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["platform_options"] = None
        self.assertEqual([], validator.validate_spec(spec))
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = compiler.compile_spec(spec, platform)
                self.assertEqual(platform, result["platform"])

    def test_learn_style_compile_is_analysis_only(self):
        spec = load_json(ROOT / "examples" / "style-learning-graphite-copper.json")
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = compiler.compile_spec(spec, platform)
                self.assertTrue(any("Analysis record only" in item for item in result["warnings"]))
                self.assertEqual({}, result["parameters"])
                self.assertNotIn("preventive clean base", result["prompt"])
                self.assertEqual("analysis", result["prompt_review"]["detail_mode"])
                if platform == "midjourney":
                    self.assertNotIn("--ar", result["prompt"])

    def test_flux_exclusion_normalization_handles_docs_and_plurals(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["constraints"]["exclude"] = [
            "no plastic CGI",
            "no extra text",
            "logos",
            "watermarks",
            "global gloss",
        ]
        result = compiler.compile_spec(spec, "flux")
        self.assertIn("physically plausible materials", result["prompt"])
        self.assertIn("only the specified literal text", result["prompt"])
        self.assertIn("unbranded scene", result["prompt"])
        self.assertIn("material-specific matte", result["prompt"])
        self.assertFalse(any("Review unconverted" in item for item in result["warnings"]))

    def test_midjourney_sanitizes_parameter_injection_from_prose(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["intent"] = "A calm portrait --v 7 --stylize 900"
        spec["style"]["visual_traits"] = ["editorial finish ::2"]
        spec["constraints"]["exclude"] = ["blur --ar 1:1"]
        result = compiler.compile_spec(spec, "midjourney")
        content, _, flags = result["prompt"].partition(" --s 100")
        self.assertNotIn("--", content)
        self.assertNotIn("::", content)
        self.assertNotIn("--ar 1:1", flags)

    def test_exact_text_escapes_quotes_and_newlines(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["text_elements"] = [
            {
                "content": 'He said "STOP"\nnow',
                "case_sensitive": True,
                "placement": "center",
                "typography": "bold sans serif",
                "color": "white",
            }
        ]
        result = compiler.compile_spec(spec, "openai")
        self.assertIn(r'"He said \"STOP\"\nnow" exactly', result["prompt"])

    def test_causal_effect_compiles_resistance_and_cost(self):
        spec = load_json(ROOT / "examples" / "causal-fantasy-effect.json")
        result = compiler.compile_spec(spec, "openai")
        self.assertIn("resistance/cost", result["prompt"])
        self.assertIn("one knee sinks into water", result["prompt"])

    def test_capsule_lint_warnings_surface_in_compiler(self):
        spec = load_json(ROOT / "examples" / "tactile-stop-motion-product.json")
        capsule = load_json(ROOT / "examples" / "style-capsule-graphite-copper.json")
        capsule["visual_rules"]["typography_logic"] = ['copy the logo "ACME"']
        result = compiler.compile_spec(spec, "openai", capsule)
        self.assertTrue(any("Style capsule content review" in item for item in result["warnings"]))

    def test_auto_direction_and_cinematic_profiles_do_not_clutter_prompt(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["direction"] = {
            "deliverable": "auto",
            "treatment": "auto",
            "spectacle_scale": "dramatic",
            "camera_freedom": "physical",
        }
        spec["cinematic"] = {"profile": "auto"}
        result = compiler.compile_spec(spec, "openai")
        self.assertNotIn("deliverable: auto", result["prompt"])
        self.assertNotIn("treatment: auto", result["prompt"])
        self.assertNotIn("profile: auto", result["prompt"])

    def test_color_pipeline_compiles_for_every_platform(self):
        spec = load_json(ROOT / "examples" / "narrative-film-frame.json")
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = compiler.compile_spec(spec, platform)
                self.assertIn("film_emulation", result["prompt"])
                self.assertIn("highlight rolloff", result["prompt"])
                if platform != "midjourney":
                    self.assertIn("fine irregular grain", result["prompt"])
                    self.assertIn("global teal-orange", result["prompt"])

    def test_render_pipeline_and_spatial_dynamics_compile_for_every_platform(self):
        spec = load_json(ROOT / "examples" / "causal-fantasy-effect.json")
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                result = compiler.compile_spec(spec, platform)
                self.assertIn("Blender Cycles", result["prompt"])
                self.assertIn("global illumination", result["prompt"])
                self.assertIn("exaggeration budget", result["prompt"])
                self.assertIn("foreground role", result["prompt"])

    def test_module_invocation_compiles_without_import_error(self):
        result = subprocess.run(
            [sys.executable, "-m", "scripts.compile_prompt", "examples/tactile-stop-motion-product.json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_directory_input_returns_clean_error(self):
        for script in ("validate_spec.py", "compile_prompt.py"):
            with self.subTest(script=script):
                result = subprocess.run(
                    [sys.executable, str(SCRIPTS / script), str(ROOT / "examples")],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertNotEqual(0, result.returncode)
                self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_compiler_emits_actual_attachment_handoff(self):
        spec = load_json(ROOT / "examples" / "styleboard-3x3.json")
        result = compiler.compile_spec(spec, "openai")
        self.assertEqual(2, len(result["attachments"]))
        self.assertTrue(all(item["must_attach"] for item in result["attachments"]))
        self.assertEqual(2, result["reference_handoff"]["required_attachment_count"])
        self.assertIn("Never replace an attachment", result["reference_handoff"]["imagegen_contract"])
        self.assertTrue(any("Actual image attachments are mandatory" in item for item in result["warnings"]))
        self.assertNotIn("post_composite", json.dumps(result, ensure_ascii=False))

    def test_product_without_text_elements_blocks_invented_copy(self):
        spec = load_json(ROOT / "examples" / "tactile-stop-motion-product.json")
        result = compiler.compile_spec(spec, "openai")
        self.assertIn("no lettering", result["prompt"])
        self.assertIn("Do not add or show: new text", result["prompt"])


class SkillMetadataTests(unittest.TestCase):
    def test_description_survives_host_catalog_normalization(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]
        description_line = next(
            line for line in frontmatter.splitlines() if line.startswith("description:")
        )
        description = description_line.split(":", 1)[1].strip().strip('"')

        self.assertTrue(description.startswith("Use when"))
        self.assertLessEqual(len(description), 150)
        self.assertFalse(description.endswith("..."))
        for trigger in (
            "visual_generation_spec",
            "reference-aware prompt compilation",
            "artifact cleanup",
            "style learning",
            "multi-frame continuity",
        ):
            with self.subTest(trigger=trigger):
                self.assertIn(trigger, description)

    def test_session_improvement_requires_post_install_parity_check(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        for phrase in (
            "scripts/verify_install.py",
            "release install or sync from a resolved commit or tag",
            "installed payload matches",
            "does not prove automatic adoption",
            "Development working-tree copies are not release-parity evidence",
        ):
            with self.subTest(phrase=phrase):
                self.assertTrue(phrase in text, f"SKILL.md is missing: {phrase}")


if __name__ == "__main__":
    unittest.main()
