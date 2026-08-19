#!/usr/bin/env python3
"""Regression tests for 镜造 Image Forge."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
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
compiler = _load_module("compiler", SCRIPTS / "compile_prompt.py")


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
    spec["inputs"] = [
        {
            "id": "style-reference",
            "type": "image",
            "role": "style_reference",
            "description": "User-supplied hand-drawn storyboard finish reference.",
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

    def test_region_cannot_escape_canvas(self):
        spec = copy.deepcopy(self.example)
        spec["spatial_edits"][0]["region"]["x_percent"] = 90.0
        errors = validator.validate_spec(spec)
        self.assertTrue(any("x_percent + width_percent" in item for item in errors))

    def test_locked_control_requires_zero_variance(self):
        spec = copy.deepcopy(self.template)
        spec["composition"]["control"]["lock"] = True
        spec["composition"]["control"]["variance"] = 0.2
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
        spec["inputs"] = [
            {"id": "source", "type": "image", "role": "observed_reference", "description": "Actual reference image."}
        ]
        self.assertEqual([], validator.validate_spec(spec))

    def test_restyle_mode_requires_and_accepts_preservation_contract(self):
        spec = copy.deepcopy(self.template)
        spec["mode"] = "restyle"
        spec["inputs"] = [
            {"id": "source", "type": "image", "role": "base_image", "description": "Image to restyle."}
        ]
        spec["constraints"]["must_preserve"] = ["identity", "pose", "layout", "text"]
        spec["constraints"]["must_change"] = ["visual treatment only"]
        self.assertEqual([], validator.validate_spec(spec))

    def test_expand_mode_requires_and_accepts_preservation_contract(self):
        spec = copy.deepcopy(self.template)
        spec["mode"] = "expand"
        spec["inputs"] = [
            {"id": "source", "type": "image", "role": "base_image", "description": "Image to expand."}
        ]
        spec["constraints"]["must_preserve"] = ["original content", "subject scale", "relative position"]
        spec["constraints"]["must_change"] = ["extend both sides"]
        self.assertEqual([], validator.validate_spec(spec))

    def test_edit_mode_accepts_must_change_without_spatial_edit(self):
        spec = copy.deepcopy(self.template)
        spec["mode"] = "edit"
        spec["inputs"] = [
            {"id": "source", "type": "image", "role": "base_image", "description": "Image to edit."}
        ]
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

    def test_source_matched_budget_preserves_source_artifact_profile(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        spec["render"]["artifact_budget"] = "source_matched"
        result = compiler.compile_spec(spec, "generic")
        self.assertIn("match source noise or grain, bloom, flare, sharpness, and surface response", result["prompt"])

    def test_narrative_compiler_frontloads_story_camera_and_staging(self):
        result = compiler.compile_spec(make_narrative_spec(), "openai")
        prompt = result["prompt"]
        self.assertLess(prompt.index("Cinematic shot contract:"), prompt.index("Scene:"))
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


if __name__ == "__main__":
    unittest.main()
