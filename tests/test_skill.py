"""Regression tests for 镜造 Image Forge."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
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
capsule_validator = _load_module("capsule_validator", SCRIPTS / "validate_style_capsule.py")
capsule_creator = _load_module("capsule_creator", SCRIPTS / "create_style_capsule.py")
reference_delivery = _load_module("reference_delivery", SCRIPTS / "reference_delivery.py")
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
        spec = copy.deepcopy(self.template)
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
        valid_sizes = ("auto", "1024x1024", "1536x864", "1792x768", "3840x2160")
        for value in valid_sizes:
            with self.subTest(valid=value):
                spec = copy.deepcopy(self.template)
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
        spec["inputs"] = [self._attached_image("observed_reference", "Actual reference image.")]
        self.assertEqual([], validator.validate_spec(spec))

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
        content, _, flags = result["prompt"].partition(" --ar 16:9")
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


if __name__ == "__main__":
    unittest.main()
