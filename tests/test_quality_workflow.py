"""Regression tests for advisory cleanup wording and clean-reset protection."""

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
    module_spec = importlib.util.spec_from_file_location(name, path)
    assert module_spec and module_spec.loader
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


compiler = _load_module("compile_prompt_quality", SCRIPTS / "compile_prompt.py")
validator = _load_module("validate_spec_quality", SCRIPTS / "validate_spec.py")


def clean_reset_spec() -> dict:
    spec = json.loads((ROOT / "templates" / "visual-spec.json").read_text(encoding="utf-8"))
    spec["intent"] = "A watercolor pointillist study of a wet metal control panel."
    spec["scene"]["summary"] = "Wet brushed metal surrounds one interface control."
    spec["subjects"][0]["description"] = "one identity-critical control panel edge"
    spec["style"]["medium"] = "watercolor with deliberate pointillist marks"
    spec["materials"] = [
        {
            "target": "wet metal control panel",
            "description": "wet metal keeps shaped reflections only on its declared glossy surface",
            "physical_properties": ["brushed steel", "water-slick reflective region"],
        }
    ]
    spec["text_elements"] = [{"content": "SAVE", "case_sensitive": True, "placement": "center", "typography": "bold sans serif", "color": "white"}]
    spec["render"]["artifact_budget"] = "clean_reset"
    return spec


class QualityWorkflowTests(unittest.TestCase):
    def test_clean_reset_protects_declared_medium_surface_identity_and_exact_text_on_every_platform(self):
        spec = clean_reset_spec()
        self.assertEqual([], validator.validate_spec(spec))
        for platform in ("openai", "flux", "midjourney", "generic"):
            with self.subTest(platform=platform):
                prompt = compiler.compile_spec(spec, platform)["prompt"]
                for phrase in ("watercolor", "pointillist", "wet metal", "identity-critical", "SAVE", "preserve declared medium and surface traits", "identity-critical edges", "exact visible text"):
                    self.assertIn(phrase, prompt)
                self.assertEqual(1, prompt.count("artifact budget (clean_reset):"))
                self.assertNotIn("preventive clean base", prompt)

    def test_advisory_rewrites_preserve_medium_wet_gloss_and_focal_boundaries(self):
        expected = {
            "insanely detailed": "current medium",
            "极致细节": "当前媒介",
            "wet glossy": "declared wet or glossy areas",
            "湿润油亮": "已声明湿润或光泽区域",
            "cinematic bokeh everywhere": "declared out-of-focus regions",
            "满屏光斑": "已声明失焦区域",
        }
        for phrase, required in expected.items():
            with self.subTest(phrase=phrase):
                self.assertIn(required, compiler.SURFACE_RISK_REWRITES[phrase])

    def test_risk_rewrites_remain_advisory_and_literal_exact_copy_is_exempt(self):
        source = clean_reset_spec()
        source["render"]["artifact_budget"] = "auto"
        self.assertEqual([], validator.validate_spec(source))
        baseline = compiler.compile_spec(copy.deepcopy(source), "openai")["prompt"]
        literal = copy.deepcopy(source)
        literal["text_elements"] = [
            {"content": "wet glossy insanely detailed cinematic bokeh everywhere 湿润油亮 极致细节 满屏光斑", "case_sensitive": True, "placement": "center", "typography": "bold sans serif", "color": "white"}
        ]
        result = compiler.compile_spec(literal, "openai")
        self.assertEqual([], result["prompt_review"]["surface_risk_hits"])
        self.assertEqual("ready", result["prompt_review"]["status"])
        self.assertEqual(baseline.count("preventive clean base"), result["prompt"].count("preventive clean base"))
        self.assertEqual(
            "every texture belongs to the requested medium or a named material and appears only where camera scale and light "
            "reveal it; localized texture or surface variation has an explicit spatial owner and stays inside its named region "
            "instead of spreading as filler microtexture; highlights, reflections, and contact shadows follow surface geometry "
            "and motivated sources; focal detail stays selective; unassigned surfaces remain continuous and low-frequency; "
            "preserve intentional medium traits required by the brief or source",
            compiler.CLEAN_BASE_PRESET,
        )
        self.assertNotIn(compiler.SURFACE_RISK_REWRITES["wet glossy"], result["prompt"])


if __name__ == "__main__":
    unittest.main()
