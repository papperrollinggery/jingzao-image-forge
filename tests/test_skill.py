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


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.template = load_json(ROOT / "templates" / "visual-spec.json")
        self.example = load_json(ROOT / "examples" / "atomic-cyber-live-action.json")

    def test_template_is_valid(self):
        self.assertEqual([], validator.validate_spec(self.template))

    def test_atomic_cyber_example_is_valid(self):
        self.assertEqual([], validator.validate_spec(self.example))

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

    def test_midjourney_parameters_are_at_end(self):
        result = compiler.compile_spec(self.example, "midjourney")
        prompt = result["prompt"]
        self.assertIn("--ar 16:9", prompt)
        self.assertIn("--raw", prompt)
        self.assertIn("--no", prompt)
        self.assertIn("painterly illustration", prompt)
        self.assertGreater(prompt.index("--ar"), prompt.index("physically fractured"))
        self.assertTrue(any("not pixel-accurate" in item for item in result["warnings"]))

    def test_auto_platform_is_generic(self):
        spec = load_json(ROOT / "templates" / "visual-spec.json")
        result = compiler.compile_spec(spec)
        self.assertEqual("generic", result["platform"])
        self.assertTrue(result["warnings"])

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


if __name__ == "__main__":
    unittest.main()
