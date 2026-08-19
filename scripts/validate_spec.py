#!/usr/bin/env python3
"""Validate a 镜造 Image Forge visual specification."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

MODES = {"create", "reconstruct", "edit", "restyle", "expand", "styleboard", "learn_style"}
PLATFORMS = {"auto", "openai", "flux", "midjourney", "generic"}
KNOWLEDGE_STRATEGIES = {"auto", "model_knowledge", "reference", "hybrid"}
KNOWLEDGE_VERIFICATIONS = {"unverified", "reference_checked", "user_confirmed"}
ARTIFACT_BUDGETS = {"strict", "balanced", "expressive", "source_matched"}
SPEC_LANGUAGES = {"en", "zh", "zh-CN"}
CANVAS_PROFILES = {"auto", "standard_widescreen", "cinematic_ultrawide", "vertical_story", "square", "custom"}
DIRECTION_DELIVERABLES = {"auto", "narrative_film_frame", "cinematic_key_art", "poster", "concept_art"}
DIRECTION_TREATMENTS = {"auto", "grounded_cinematic", "heightened_cinematic", "graphic_stylized"}
SPECTACLE_SCALES = {"intimate", "dramatic", "monumental", "mythic"}
CAMERA_FREEDOMS = {"physical", "heightened", "impossible"}
SCENARIO_PROFILES = {
    "auto",
    "custom",
    "narrative_scene",
    "character_portrait",
    "relationship_performance",
    "action_choreography",
    "key_art_campaign",
    "brand_identity",
    "product_tabletop",
    "fashion_beauty",
    "food_still_life",
    "architecture_interior",
    "landscape_environment",
    "vehicle_mecha",
    "creature_design",
    "historical_documentary",
    "scientific_educational",
    "editorial_infographic",
    "interface_mockup",
    "game_asset",
    "event_experience",
    "social_content",
    "experimental_art",
}
GENRE_FAMILIES = {
    "auto",
    "drama",
    "romance",
    "comedy",
    "thriller",
    "horror",
    "crime_noir",
    "action_adventure",
    "fantasy_mythic",
    "science_fiction",
    "historical_period",
    "documentary",
    "children_family",
    "commercial_editorial",
    "experimental_surreal",
    "custom",
}
AESTHETIC_FAMILIES = {
    "auto",
    "cinematic_naturalism",
    "noir_chiaroscuro",
    "heightened_expressionism",
    "surreal_oneiric",
    "romantic_sublime",
    "graphic_modernism",
    "retro_analog",
    "luxury_editorial",
    "tactile_handcrafted",
    "painterly_illustrative",
    "animation_stylized",
    "documentary_observational",
    "speculative_worldbuilding",
    "minimal_object_study",
    "archival_historical",
    "mixed_media",
    "custom",
}
CAPTURE_OR_RENDER_METHODS = {
    "auto",
    "photography",
    "live_action_cinema",
    "photoreal_cg",
    "stylized_3d",
    "2d_animation",
    "illustration",
    "ink_wash",
    "watercolor_gouache",
    "oil_paint",
    "printmaking",
    "collage_photomontage",
    "stop_motion",
    "miniature_practical",
    "paper_craft",
    "archival_composite",
    "interface_graphic",
    "mixed_media",
    "custom",
}
COLOR_PIPELINE_INTENTS = {
    "auto",
    "neutral_digital",
    "cinematic_color",
    "film_emulation",
    "print_emulation",
    "bleach_bypass",
    "black_and_white",
    "cross_processed",
    "archival_reproduction",
    "custom",
}
STYLE_AUTHORITIES = {"auto", "user_brief", "source_reference", "style_capsule", "source_matched"}
EXAGGERATION_BUDGETS = {"auto", "none", "restrained", "strong", "extreme"}
DISTORTION_STRATEGIES = {"auto", "none", "optical", "perspective", "spatial", "motion", "graphic"}
RENDER_DOMAINS = {
    "auto",
    "physically_based_offline",
    "real_time",
    "path_traced",
    "rasterized",
    "npr",
    "hybrid_layered",
    "custom",
}
ENGINE_REFERENCE_SCOPES = {"appearance_reference", "actual_pipeline"}
REFERENCE_SOURCE_KINDS = {"unspecified", "local_path", "conversation_image", "remote_url", "platform_asset"}
STYLE_LEARNING_SCOPES = {"session", "project", "skill_candidate"}
STYLE_LEARNING_STATUSES = {"draft", "validated", "adopted"}
SHOT_FUNCTIONS = {"establish", "introduce", "observe", "follow", "emphasize", "react", "transition", "resolve"}
EFFECT_INTENSITIES = {"minor", "medium", "hero"}
STYLEBOARD_PRESENTATIONS = {"line_art", "hand_drawn", "cinematic_frame", "mixed"}
STYLEBOARD_STRATEGIES = {"auto", "sheet_direct", "independent_frames", "hybrid"}
STYLEBOARD_REFERENCE_ROLES = {"identity", "wardrobe", "scene", "prop", "camera_action", "style", "layout", "palette"}
STYLEBOARD_READING_ORDERS = {"left_to_right_top_to_bottom", "top_to_bottom_left_to_right"}
ACTION_PHASES = {"prepare", "initiate", "contact", "response", "hold"}
ASPECT_RATIO_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)\s*$")
GRID_LAYOUT_RE = re.compile(r"^\s*(\d+)\s*[x×]\s*(\d+)\s*$", re.IGNORECASE)
PROFILE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
OPENAI_SIZE_RE = re.compile(r"^(\d+)x(\d+)$")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _is_allowed(value: Any, allowed: set[Any]) -> bool:
    try:
        return value in allowed
    except TypeError:
        return False


def _validate_enum(value: Any, allowed: set[Any], path: str, errors: list[str]) -> None:
    if not _is_allowed(value, allowed):
        errors.append(f"{path}: expected one of {sorted(item for item in allowed if item is not None)}")


def _validate_openai_size(value: Any, path: str, errors: list[str]) -> None:
    if value is None or value == "auto":
        return
    if not isinstance(value, str):
        errors.append(f"{path}: expected auto or WIDTHxHEIGHT")
        return
    match = OPENAI_SIZE_RE.match(value)
    if match is None:
        errors.append(f"{path}: expected auto or WIDTHxHEIGHT")
        return
    width, height = int(match.group(1)), int(match.group(2))
    long_edge, short_edge = max(width, height), min(width, height)
    pixels = width * height
    if long_edge > 3840:
        errors.append(f"{path}: maximum edge length is 3840")
    if width % 16 or height % 16:
        errors.append(f"{path}: both edges must be multiples of 16")
    if short_edge == 0 or long_edge / short_edge > 3.0:
        errors.append(f"{path}: long-to-short edge ratio must not exceed 3:1")
    if not 655_360 <= pixels <= 8_294_400:
        errors.append(f"{path}: total pixels must be between 655360 and 8294400")


def _require_string(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: expected a non-empty string")


def _validate_string_list(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{path}: expected a list")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{path}[{index}]: expected a non-empty string")


def _validate_optional_string_fields(value: dict[str, Any], keys: tuple[str, ...], path: str, errors: list[str]) -> None:
    for key in keys:
        if key in value and not isinstance(value.get(key), str):
            errors.append(f"{path}.{key}: expected a string")


def _validate_known_keys(value: dict[str, Any], allowed: set[str], path: str, errors: list[str]) -> None:
    for key in value:
        if key not in allowed:
            errors.append(f"{path}.{key}: unknown field")


def _validate_percent(value: Any, path: str, errors: list[str], *, positive: bool = False) -> None:
    if not _is_number(value):
        errors.append(f"{path}: expected a number")
        return
    if positive:
        if value <= 0.0 or value > 100.0:
            errors.append(f"{path}: expected greater than 0 and at most 100")
    elif value < 0.0 or value > 100.0:
        errors.append(f"{path}: expected between 0 and 100")


def _validate_point(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected an object")
        return
    _validate_known_keys(value, {"x_percent", "y_percent"}, path, errors)
    _validate_percent(value.get("x_percent"), f"{path}.x_percent", errors)
    _validate_percent(value.get("y_percent"), f"{path}.y_percent", errors)


def _validate_region(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected an object")
        return
    _validate_known_keys(value, {"x_percent", "y_percent", "width_percent", "height_percent"}, path, errors)
    x = value.get("x_percent")
    y = value.get("y_percent")
    width = value.get("width_percent")
    height = value.get("height_percent")
    _validate_percent(x, f"{path}.x_percent", errors)
    _validate_percent(y, f"{path}.y_percent", errors)
    _validate_percent(width, f"{path}.width_percent", errors, positive=True)
    _validate_percent(height, f"{path}.height_percent", errors, positive=True)
    if all(_is_number(item) for item in (x, y, width, height)):
        if x + width > 100.0:
            errors.append(f"{path}: x_percent + width_percent must not exceed 100")
        if y + height > 100.0:
            errors.append(f"{path}: y_percent + height_percent must not exceed 100")


def _walk_controls(value: Any, path: str, errors: list[str], depth: int = 0) -> None:
    if depth > 100:
        errors.append(f"{path}: nesting exceeds the supported depth of 100")
        return
    if isinstance(value, dict):
        control = value.get("control")
        if control is not None:
            if not isinstance(control, dict):
                errors.append(f"{path}.control: expected an object")
            else:
                weight = control.get("weight")
                lock = control.get("lock")
                variance = control.get("variance")
                if not _is_number(weight) or not 0.0 <= weight <= 1.0:
                    errors.append(f"{path}.control.weight: expected a number from 0 to 1")
                if not isinstance(lock, bool):
                    errors.append(f"{path}.control.lock: expected a boolean")
                if not _is_number(variance) or not 0.0 <= variance <= 1.0:
                    errors.append(f"{path}.control.variance: expected a number from 0 to 1")
                if lock is True and _is_number(variance) and variance != 0.0:
                    errors.append(f"{path}.control: lock=true requires variance=0")
                _validate_known_keys(control, {"weight", "lock", "variance"}, f"{path}.control", errors)
        for key, child in value.items():
            if key != "control":
                _walk_controls(child, f"{path}.{key}", errors, depth + 1)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_controls(child, f"{path}[{index}]", errors, depth + 1)


def _validate_platform_options(value: Any, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        errors.append("$.platform_options: expected an object")
        return
    _validate_known_keys(value, {"openai", "flux", "midjourney"}, "$.platform_options", errors)

    openai = value.get("openai")
    if openai is not None:
        if not isinstance(openai, dict):
            errors.append("$.platform_options.openai: expected an object")
        else:
            _validate_known_keys(openai, {"model", "quality", "size"}, "$.platform_options.openai", errors)
            if not _is_allowed(openai.get("quality"), {None, "low", "medium", "high", "auto"}):
                errors.append("$.platform_options.openai.quality: expected low, medium, high, or auto")
            if "model" in openai:
                _require_string(openai.get("model"), "$.platform_options.openai.model", errors)
            _validate_openai_size(openai.get("size"), "$.platform_options.openai.size", errors)

    flux = value.get("flux")
    if flux is not None:
        if not isinstance(flux, dict):
            errors.append("$.platform_options.flux: expected an object")
        else:
            _validate_known_keys(
                flux,
                {"model_family", "prompt_format", "prompt_upsampling"},
                "$.platform_options.flux",
                errors,
            )
            if not _is_allowed(flux.get("prompt_format"), {None, "natural_language", "json"}):
                errors.append("$.platform_options.flux.prompt_format: expected natural_language or json")
            if "prompt_upsampling" in flux and not isinstance(flux.get("prompt_upsampling"), bool):
                errors.append("$.platform_options.flux.prompt_upsampling: expected a boolean")

    midjourney = value.get("midjourney")
    if midjourney is not None:
        if not isinstance(midjourney, dict):
            errors.append("$.platform_options.midjourney: expected an object")
        else:
            _validate_known_keys(
                midjourney,
                {
                    "aspect_ratio",
                    "stylize",
                    "chaos",
                    "quality",
                    "style_weight",
                    "raw",
                    "seed",
                    "version",
                    "style_reference",
                },
                "$.platform_options.midjourney",
                errors,
            )
            aspect = midjourney.get("aspect_ratio")
            if aspect is not None and (not isinstance(aspect, str) or ASPECT_RATIO_RE.match(aspect) is None):
                errors.append("$.platform_options.midjourney.aspect_ratio: expected a ratio such as \"16:9\"")
            for key in ("stylize", "chaos", "quality", "style_weight"):
                if key in midjourney and midjourney.get(key) is not None and not _is_number(midjourney.get(key)):
                    errors.append(f"$.platform_options.midjourney.{key}: expected a number")
            stylize = midjourney.get("stylize")
            if _is_number(stylize) and not 0 <= stylize <= 1000:
                errors.append("$.platform_options.midjourney.stylize: expected 0 to 1000")
            chaos = midjourney.get("chaos")
            if _is_number(chaos) and not 0 <= chaos <= 100:
                errors.append("$.platform_options.midjourney.chaos: expected 0 to 100")
            style_weight = midjourney.get("style_weight")
            if _is_number(style_weight) and not 0 <= style_weight <= 1000:
                errors.append("$.platform_options.midjourney.style_weight: expected 0 to 1000")
            quality = midjourney.get("quality")
            if _is_number(quality) and quality <= 0:
                errors.append("$.platform_options.midjourney.quality: expected a positive version-compatible value")
            if "raw" in midjourney and not isinstance(midjourney.get("raw"), bool):
                errors.append("$.platform_options.midjourney.raw: expected a boolean")
            if "seed" in midjourney and midjourney.get("seed") is not None:
                seed = midjourney.get("seed")
                if not isinstance(seed, int) or isinstance(seed, bool):
                    errors.append("$.platform_options.midjourney.seed: expected an integer")
            version = midjourney.get("version")
            if version is not None:
                if isinstance(version, bool) or not isinstance(version, (str, int, float)):
                    errors.append("$.platform_options.midjourney.version: expected a string or number")
                elif isinstance(version, str) and (not version.strip() or re.fullmatch(r"\d+(?:\.\d+)?", version) is None):
                    errors.append("$.platform_options.midjourney.version: expected a numeric version string")
            refs = midjourney.get("style_reference")
            if refs is not None:
                if not isinstance(refs, list):
                    errors.append("$.platform_options.midjourney.style_reference: expected a list")
                else:
                    for index, item in enumerate(refs):
                        path = f"$.platform_options.midjourney.style_reference[{index}]"
                        if isinstance(item, str):
                            if not item.strip():
                                errors.append(f"{path}: expected a non-empty URL or style code")
                        elif isinstance(item, dict):
                            _validate_known_keys(item, {"url", "weight"}, path, errors)
                            _require_string(item.get("url"), f"{path}.url", errors)
                            weight = item.get("weight")
                            if weight is not None and (not _is_number(weight) or weight <= 0):
                                errors.append(f"{path}.weight: expected a positive number")
                        else:
                            errors.append(f"{path}: expected a string or an object with url and optional weight")


def validate_spec(spec: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(spec, dict):
        return ["$: expected a JSON object"]

    _validate_known_keys(
        spec,
        {
            "visual_generation_spec",
            "mode",
            "intent",
            "platform",
            "language",
            "canvas",
            "inputs",
            "knowledge_anchors",
            "creative_routing",
            "reference_analysis",
            "style_learning",
            "direction",
            "cinematic",
            "staging",
            "spatial_dynamics",
            "scene",
            "subjects",
            "composition",
            "lighting",
            "color_pipeline",
            "render_pipeline",
            "materials",
            "effects",
            "color",
            "optics",
            "style",
            "text_elements",
            "spatial_edits",
            "styleboard",
            "constraints",
            "render",
            "platform_options",
        },
        "$",
        errors,
    )

    if spec.get("visual_generation_spec") != "1.0":
        errors.append("$.visual_generation_spec: expected \"1.0\"")

    mode = spec.get("mode")
    if not _is_allowed(mode, MODES):
        errors.append(f"$.mode: expected one of {sorted(MODES)}")
    _require_string(spec.get("intent"), "$.intent", errors)

    platform = spec.get("platform", "auto")
    if not _is_allowed(platform, PLATFORMS):
        errors.append(f"$.platform: expected one of {sorted(PLATFORMS)}")

    language = spec.get("language", "en")
    if not _is_allowed(language, SPEC_LANGUAGES):
        errors.append(f"$.language: expected one of {sorted(SPEC_LANGUAGES)}")

    canvas = spec.get("canvas")
    canvas_ratio_value: float | None = None
    if not isinstance(canvas, dict):
        errors.append("$.canvas: expected an object")
    else:
        _validate_known_keys(canvas, {"profile", "aspect_ratio", "dimensions", "control"}, "$.canvas", errors)
        canvas_profile = canvas.get("profile", "auto")
        if not _is_allowed(canvas_profile, CANVAS_PROFILES):
            errors.append(f"$.canvas.profile: expected one of {sorted(CANVAS_PROFILES)}")
        aspect_ratio = canvas.get("aspect_ratio")
        match = ASPECT_RATIO_RE.match(aspect_ratio) if isinstance(aspect_ratio, str) else None
        if match is None:
            errors.append("$.canvas.aspect_ratio: expected a ratio such as \"16:9\"")
        elif float(match.group(1)) <= 0 or float(match.group(2)) <= 0:
            errors.append("$.canvas.aspect_ratio: both ratio values must be greater than 0")
        else:
            ratio_value = float(match.group(1)) / float(match.group(2))
            canvas_ratio_value = ratio_value
            if canvas_profile == "standard_widescreen" and not 1.7 <= ratio_value <= 1.85:
                errors.append("$.canvas.aspect_ratio: standard_widescreen expects a 16:9-class ratio")
            if canvas_profile == "cinematic_ultrawide" and not 2.25 <= ratio_value <= 2.45:
                errors.append("$.canvas.aspect_ratio: cinematic_ultrawide expects 21:9, 2.35:1, or 2.39:1 class")
            if canvas_profile == "vertical_story" and not 0.54 <= ratio_value <= 0.58:
                errors.append("$.canvas.aspect_ratio: vertical_story expects a 9:16-class ratio")
            if canvas_profile == "square" and not 0.98 <= ratio_value <= 1.02:
                errors.append("$.canvas.aspect_ratio: square expects a 1:1-class ratio")
        dimensions = canvas.get("dimensions")
        if dimensions is not None:
            if not isinstance(dimensions, dict):
                errors.append("$.canvas.dimensions: expected an object")
            else:
                _validate_known_keys(dimensions, {"width", "height"}, "$.canvas.dimensions", errors)
                for key in ("width", "height"):
                    value = dimensions.get(key)
                    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                        errors.append(f"$.canvas.dimensions.{key}: expected a positive integer")

    constraints = spec.get("constraints")
    if not isinstance(constraints, dict):
        errors.append("$.constraints: expected an object")
    else:
        _validate_known_keys(constraints, {"must_preserve", "must_change", "exclude"}, "$.constraints", errors)
        for key in ("must_preserve", "must_change", "exclude"):
            _validate_string_list(constraints.get(key, []), f"$.constraints.{key}", errors)

    inputs = spec.get("inputs", [])
    if not isinstance(inputs, list):
        errors.append("$.inputs: expected a list")
        inputs = []
    input_ids: set[str] = set()
    for index, item in enumerate(inputs):
        path = f"$.inputs[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path}: expected an object")
            continue
        _validate_known_keys(
            item,
            {
                "id",
                "type",
                "role",
                "description",
                "source_kind",
                "source_ref",
                "must_attach",
                "control",
            },
            path,
            errors,
        )
        for key in ("id", "type", "role", "description"):
            _require_string(item.get(key), f"{path}.{key}", errors)
        source_kind = item.get("source_kind", "unspecified")
        if not _is_allowed(source_kind, REFERENCE_SOURCE_KINDS):
            errors.append(f"{path}.source_kind: expected one of {sorted(REFERENCE_SOURCE_KINDS)}")
        if "source_ref" in item and not isinstance(item.get("source_ref"), str):
            errors.append(f"{path}.source_ref: expected a string")
        must_attach = item.get("must_attach", False)
        if not isinstance(must_attach, bool):
            errors.append(f"{path}.must_attach: expected a boolean")
        if must_attach and (
            source_kind == "unspecified"
            or not isinstance(item.get("source_ref"), str)
            or not item.get("source_ref", "").strip()
        ):
            errors.append(f"{path}.source_ref: must_attach inputs need an actual source reference")
        item_id = item.get("id")
        if isinstance(item_id, str):
            if item_id in input_ids:
                errors.append(f"{path}.id: duplicate id {item_id!r}")
            input_ids.add(item_id)


    knowledge_anchors = spec.get("knowledge_anchors", [])
    if not isinstance(knowledge_anchors, list):
        errors.append("$.knowledge_anchors: expected a list")
    else:
        for index, item in enumerate(knowledge_anchors):
            path = f"$.knowledge_anchors[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{path}: expected an object")
                continue
            _validate_known_keys(
                item,
                {"name", "context", "strategy", "reference_ids", "verification", "control"},
                path,
                errors,
            )
            _require_string(item.get("name"), f"{path}.name", errors)
            if "context" in item:
                _require_string(item.get("context"), f"{path}.context", errors)
            strategy = item.get("strategy", "auto")
            if not _is_allowed(strategy, KNOWLEDGE_STRATEGIES):
                errors.append(f"{path}.strategy: expected one of {sorted(KNOWLEDGE_STRATEGIES)}")
            verification = item.get("verification", "unverified")
            if not _is_allowed(verification, KNOWLEDGE_VERIFICATIONS):
                errors.append(f"{path}.verification: expected one of {sorted(KNOWLEDGE_VERIFICATIONS)}")
            reference_ids = item.get("reference_ids", [])
            _validate_string_list(reference_ids, f"{path}.reference_ids", errors)
            if isinstance(reference_ids, list):
                for reference_id in reference_ids:
                    if isinstance(reference_id, str) and reference_id not in input_ids:
                        errors.append(f"{path}.reference_ids: unknown input id {reference_id!r}")
            if _is_allowed(strategy, {"reference", "hybrid"}) and not reference_ids:
                errors.append(f"{path}.reference_ids: strategy={strategy!r} requires at least one input reference")

    creative_routing = spec.get("creative_routing")
    if creative_routing is not None:
        if not isinstance(creative_routing, dict):
            errors.append("$.creative_routing: expected an object")
        else:
            _validate_known_keys(
                creative_routing,
                {
                    "scenario_profile",
                    "genre_family",
                    "aesthetic_family",
                    "capture_or_render_method",
                    "custom_scenario",
                    "custom_genre",
                    "custom_aesthetic",
                    "custom_method",
                    "scene_archetypes",
                    "audience_effect",
                    "delivery_context",
                    "design_priority",
                    "cultural_context",
                    "secondary_influence",
                    "mix_rule",
                    "style_authority",
                    "adaptation_rule",
                    "tone_locks",
                    "forbidden_drift",
                    "control",
                },
                "$.creative_routing",
                errors,
            )
            enum_fields = (
                ("scenario_profile", SCENARIO_PROFILES),
                ("genre_family", GENRE_FAMILIES),
                ("aesthetic_family", AESTHETIC_FAMILIES),
                ("capture_or_render_method", CAPTURE_OR_RENDER_METHODS),
            )
            for key, allowed in enum_fields:
                if not _is_allowed(creative_routing.get(key, "auto"), allowed):
                    errors.append(f"$.creative_routing.{key}: expected one of {sorted(allowed)}")
            _validate_optional_string_fields(
                creative_routing,
                (
                    "audience_effect",
                    "delivery_context",
                    "design_priority",
                    "cultural_context",
                    "secondary_influence",
                    "mix_rule",
                    "adaptation_rule",
                    "custom_scenario",
                    "custom_genre",
                    "custom_aesthetic",
                    "custom_method",
                ),
                "$.creative_routing",
                errors,
            )
            scene_archetypes = creative_routing.get("scene_archetypes", [])
            _validate_string_list(scene_archetypes, "$.creative_routing.scene_archetypes", errors)
            if isinstance(scene_archetypes, list) and len(scene_archetypes) > 3:
                errors.append("$.creative_routing.scene_archetypes: use at most three primary scene archetypes")
            _validate_string_list(
                creative_routing.get("forbidden_drift", []),
                "$.creative_routing.forbidden_drift",
                errors,
            )
            if not _is_allowed(creative_routing.get("style_authority", "auto"), STYLE_AUTHORITIES):
                errors.append(f"$.creative_routing.style_authority: expected one of {sorted(STYLE_AUTHORITIES)}")
            _validate_string_list(creative_routing.get("tone_locks", []), "$.creative_routing.tone_locks", errors)
            secondary_influence = creative_routing.get("secondary_influence", "")
            mix_rule = creative_routing.get("mix_rule", "")
            has_secondary = isinstance(secondary_influence, str) and bool(secondary_influence.strip())
            has_mix_rule = isinstance(mix_rule, str) and bool(mix_rule.strip())
            if has_secondary and not has_mix_rule:
                errors.append("$.creative_routing.mix_rule: secondary_influence requires an explicit division of labor")
            if has_mix_rule and not has_secondary:
                errors.append("$.creative_routing.secondary_influence: mix_rule requires a secondary influence")
            custom_fields = (
                ("scenario_profile", "custom_scenario"),
                ("genre_family", "custom_genre"),
                ("aesthetic_family", "custom_aesthetic"),
                ("capture_or_render_method", "custom_method"),
            )
            for enum_key, custom_key in custom_fields:
                enum_value = creative_routing.get(enum_key, "auto")
                custom_value = creative_routing.get(custom_key, "")
                has_custom_value = isinstance(custom_value, str) and bool(custom_value.strip())
                if enum_value == "custom" and not has_custom_value:
                    errors.append(f"$.creative_routing.{custom_key}: {enum_key}=\"custom\" requires a description")
                if enum_value != "custom" and has_custom_value:
                    errors.append(f"$.creative_routing.{custom_key}: allowed only when {enum_key}=\"custom\"")

    style_learning = spec.get("style_learning")
    if style_learning is not None:
        if not isinstance(style_learning, dict):
            errors.append("$.style_learning: expected an object")
        else:
            _validate_known_keys(
                style_learning,
                {
                    "profile_id",
                    "profile_name",
                    "scope",
                    "status",
                    "adoption_approved",
                    "source_input_ids",
                    "provenance",
                    "observed",
                    "inferred_traits",
                    "unknowns",
                    "transfer_rules",
                    "forbidden_transfer",
                    "validation_prompts",
                    "validation_evidence",
                    "verification_notes",
                    "control",
                },
                "$.style_learning",
                errors,
            )
            profile_id = style_learning.get("profile_id")
            _require_string(profile_id, "$.style_learning.profile_id", errors)
            if isinstance(profile_id, str) and profile_id.strip() and PROFILE_ID_RE.match(profile_id) is None:
                errors.append("$.style_learning.profile_id: use lowercase letters, digits, and single hyphens")
            _require_string(style_learning.get("profile_name"), "$.style_learning.profile_name", errors)
            if not _is_allowed(style_learning.get("scope", "session"), STYLE_LEARNING_SCOPES):
                errors.append(f"$.style_learning.scope: expected one of {sorted(STYLE_LEARNING_SCOPES)}")
            learning_status = style_learning.get("status", "draft")
            if not _is_allowed(learning_status, STYLE_LEARNING_STATUSES):
                errors.append(f"$.style_learning.status: expected one of {sorted(STYLE_LEARNING_STATUSES)}")
            adoption_approved = style_learning.get("adoption_approved", False)
            if not isinstance(adoption_approved, bool):
                errors.append("$.style_learning.adoption_approved: expected a boolean")
            if learning_status == "adopted" and adoption_approved is not True:
                errors.append("$.style_learning.adoption_approved: adopted styles require explicit approval")
            _validate_optional_string_fields(
                style_learning,
                ("provenance", "verification_notes"),
                "$.style_learning",
                errors,
            )
            source_input_ids = style_learning.get("source_input_ids", [])
            _validate_string_list(source_input_ids, "$.style_learning.source_input_ids", errors)
            if isinstance(source_input_ids, list):
                if not source_input_ids:
                    errors.append("$.style_learning.source_input_ids: expected at least one reference image")
                for source_input_id in source_input_ids:
                    if isinstance(source_input_id, str) and source_input_id not in input_ids:
                        errors.append(f"$.style_learning.source_input_ids: unknown input id {source_input_id!r}")

            observed = style_learning.get("observed")
            if not isinstance(observed, dict):
                errors.append("$.style_learning.observed: expected an object")
            else:
                _validate_known_keys(
                    observed,
                    {
                        "medium_behavior",
                        "palette_logic",
                        "shape_line_language",
                        "texture_material_logic",
                        "lighting_logic",
                        "composition_logic",
                        "typography_logic",
                        "optics_rendering_logic",
                        "motifs",
                    },
                    "$.style_learning.observed",
                    errors,
                )
                for key in ("medium_behavior", "shape_line_language", "lighting_logic", "optics_rendering_logic"):
                    _require_string(observed.get(key), f"$.style_learning.observed.{key}", errors)
                for key in (
                    "palette_logic",
                    "texture_material_logic",
                    "composition_logic",
                    "typography_logic",
                    "motifs",
                ):
                    _validate_string_list(observed.get(key, []), f"$.style_learning.observed.{key}", errors)

            for key in (
                "inferred_traits",
                "unknowns",
                "transfer_rules",
                "forbidden_transfer",
                "validation_prompts",
            ):
                _validate_string_list(style_learning.get(key, []), f"$.style_learning.{key}", errors)
            for key in ("transfer_rules", "forbidden_transfer"):
                value = style_learning.get(key, [])
                if isinstance(value, list) and not value:
                    errors.append(f"$.style_learning.{key}: expected at least one rule")
            validation_prompts = style_learning.get("validation_prompts", [])
            validation_evidence = style_learning.get("validation_evidence", [])
            verification_notes = style_learning.get("verification_notes", "")
            if not isinstance(validation_evidence, list):
                errors.append("$.style_learning.validation_evidence: expected a list")
                validation_evidence = []
            evidence_scenarios: set[str] = set()
            for index, item in enumerate(validation_evidence):
                path = f"$.style_learning.validation_evidence[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{path}: expected an object")
                    continue
                _validate_known_keys(
                    item,
                    {"case_id", "prompt_index", "scenario", "evidence_ref", "review"},
                    path,
                    errors,
                )
                for key in ("case_id", "scenario", "evidence_ref", "review"):
                    _require_string(item.get(key), f"{path}.{key}", errors)
                prompt_index = item.get("prompt_index")
                if not isinstance(prompt_index, int) or isinstance(prompt_index, bool) or prompt_index < 0:
                    errors.append(f"{path}.prompt_index: expected a non-negative integer")
                scenario = item.get("scenario")
                if isinstance(scenario, str) and scenario.strip():
                    evidence_scenarios.add(scenario.strip())
            if _is_allowed(learning_status, {"validated", "adopted"}):
                if not isinstance(validation_prompts, list) or len(validation_prompts) < 2:
                    errors.append(
                        "$.style_learning.validation_prompts: validated or adopted styles require at least two transfer tests"
                    )
                if not isinstance(verification_notes, str) or not verification_notes.strip():
                    errors.append(
                        "$.style_learning.verification_notes: validated or adopted styles require visual review notes"
                    )
                if len(validation_evidence) < 2 or len(evidence_scenarios) < 2:
                    errors.append(
                        "$.style_learning.validation_evidence: validated or adopted styles require two scenario evidence records"
                    )

    reference_analysis = spec.get("reference_analysis")
    if reference_analysis is not None:
        if not isinstance(reference_analysis, dict):
            errors.append("$.reference_analysis: expected an object")
        else:
            _validate_known_keys(
                reference_analysis,
                {"target", "observed", "inferred", "unknowns"},
                "$.reference_analysis",
                errors,
            )
            _require_string(reference_analysis.get("target"), "$.reference_analysis.target", errors)
            for key in ("observed", "inferred", "unknowns"):
                _validate_string_list(reference_analysis.get(key, []), f"$.reference_analysis.{key}", errors)
            if not reference_analysis.get("observed"):
                errors.append("$.reference_analysis.observed: reconstruct requires directly observed facts")
            if not reference_analysis.get("unknowns"):
                errors.append("$.reference_analysis.unknowns: reconstruct requires explicit unknowns")

    direction = spec.get("direction")
    direction_deliverable = "auto"
    if direction is not None:
        if not isinstance(direction, dict):
            errors.append("$.direction: expected an object")
        else:
            _validate_known_keys(
                direction,
                {"deliverable", "treatment", "spectacle_scale", "camera_freedom", "genre", "world_rule", "visual_goal", "control"},
                "$.direction",
                errors,
            )
            direction_deliverable = direction.get("deliverable", "auto")
            if not _is_allowed(direction_deliverable, DIRECTION_DELIVERABLES):
                errors.append(f"$.direction.deliverable: expected one of {sorted(DIRECTION_DELIVERABLES)}")
            if not _is_allowed(direction.get("treatment", "auto"), DIRECTION_TREATMENTS):
                errors.append(f"$.direction.treatment: expected one of {sorted(DIRECTION_TREATMENTS)}")
            if not _is_allowed(direction.get("spectacle_scale", "dramatic"), SPECTACLE_SCALES):
                errors.append(f"$.direction.spectacle_scale: expected one of {sorted(SPECTACLE_SCALES)}")
            if not _is_allowed(direction.get("camera_freedom", "physical"), CAMERA_FREEDOMS):
                errors.append(f"$.direction.camera_freedom: expected one of {sorted(CAMERA_FREEDOMS)}")
            _validate_optional_string_fields(direction, ("genre", "world_rule", "visual_goal"), "$.direction", errors)

    cinematic = spec.get("cinematic")
    cinematic_profile = "auto"
    if cinematic is not None:
        if not isinstance(cinematic, dict):
            errors.append("$.cinematic: expected an object")
        else:
            _validate_known_keys(
                cinematic,
                {
                    "profile",
                    "shot_function",
                    "visible_event",
                    "relationship_pressure",
                    "viewer_task",
                    "viewer_position",
                    "frozen_moment",
                    "withheld_information",
                    "posterization_guard",
                    "control",
                },
                "$.cinematic",
                errors,
            )
            cinematic_profile = cinematic.get("profile", "auto")
            if not _is_allowed(cinematic_profile, DIRECTION_DELIVERABLES):
                errors.append(f"$.cinematic.profile: expected one of {sorted(DIRECTION_DELIVERABLES)}")
            shot_function = cinematic.get("shot_function")
            if shot_function is not None and not _is_allowed(shot_function, SHOT_FUNCTIONS):
                errors.append(f"$.cinematic.shot_function: expected one of {sorted(SHOT_FUNCTIONS)}")
            _validate_optional_string_fields(
                cinematic,
                (
                    "visible_event",
                    "relationship_pressure",
                    "viewer_task",
                    "viewer_position",
                    "frozen_moment",
                    "withheld_information",
                ),
                "$.cinematic",
                errors,
            )
            if "posterization_guard" in cinematic and not isinstance(cinematic.get("posterization_guard"), bool):
                errors.append("$.cinematic.posterization_guard: expected a boolean")

    staging = spec.get("staging")
    if staging is not None:
        if not isinstance(staging, dict):
            errors.append("$.staging: expected an object")
        else:
            _validate_known_keys(
                staging,
                {"primary_relationship", "subject_positions", "eyeline_logic", "screen_direction", "axis", "occlusion", "attention_path", "control"},
                "$.staging",
                errors,
            )
            _validate_optional_string_fields(
                staging,
                ("primary_relationship", "eyeline_logic", "screen_direction", "axis", "occlusion", "attention_path"),
                "$.staging",
                errors,
            )
            _validate_string_list(staging.get("subject_positions", []), "$.staging.subject_positions", errors)

    spatial_dynamics = spec.get("spatial_dynamics")
    if spatial_dynamics is not None:
        if not isinstance(spatial_dynamics, dict):
            errors.append("$.spatial_dynamics: expected an object")
        else:
            _validate_known_keys(
                spatial_dynamics,
                {
                    "dominant_read",
                    "secondary_read",
                    "beauty_mechanism",
                    "tension_source",
                    "exaggeration_budget",
                    "distortion_strategy",
                    "realism_anchor",
                    "action_vector",
                    "counterforce",
                    "foreground_role",
                    "midground_role",
                    "background_role",
                    "depth_transition",
                    "parallax_logic",
                    "motion_evidence",
                    "readability_guard",
                    "control",
                },
                "$.spatial_dynamics",
                errors,
            )
            _validate_optional_string_fields(
                spatial_dynamics,
                (
                    "dominant_read",
                    "secondary_read",
                    "beauty_mechanism",
                    "tension_source",
                    "realism_anchor",
                    "action_vector",
                    "counterforce",
                    "foreground_role",
                    "midground_role",
                    "background_role",
                    "depth_transition",
                    "parallax_logic",
                    "readability_guard",
                ),
                "$.spatial_dynamics",
                errors,
            )
            if not _is_allowed(spatial_dynamics.get("exaggeration_budget", "auto"), EXAGGERATION_BUDGETS):
                errors.append(
                    f"$.spatial_dynamics.exaggeration_budget: expected one of {sorted(EXAGGERATION_BUDGETS)}"
                )
            if not _is_allowed(spatial_dynamics.get("distortion_strategy", "auto"), DISTORTION_STRATEGIES):
                errors.append(
                    f"$.spatial_dynamics.distortion_strategy: expected one of {sorted(DISTORTION_STRATEGIES)}"
                )
            _validate_string_list(spatial_dynamics.get("motion_evidence", []), "$.spatial_dynamics.motion_evidence", errors)

    subjects = spec.get("subjects", [])
    if not isinstance(subjects, list):
        errors.append("$.subjects: expected a list")
        subjects = []
    subject_ids: set[str] = set()
    for index, subject in enumerate(subjects):
        path = f"$.subjects[{index}]"
        if not isinstance(subject, dict):
            errors.append(f"{path}: expected an object")
            continue
        _validate_known_keys(
            subject,
            {"id", "description", "count", "appearance", "action", "pose", "gaze", "position", "scale", "relationships", "control"},
            path,
            errors,
        )
        _require_string(subject.get("id"), f"{path}.id", errors)
        _require_string(subject.get("description"), f"{path}.description", errors)
        count = subject.get("count", 1)
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            errors.append(f"{path}.count: expected a positive integer")
        _validate_string_list(subject.get("appearance", []), f"{path}.appearance", errors)
        _validate_string_list(subject.get("relationships", []), f"{path}.relationships", errors)
        _validate_optional_string_fields(subject, ("action", "pose", "gaze", "scale"), path, errors)
        subject_id = subject.get("id")
        if isinstance(subject_id, str):
            if subject_id in subject_ids:
                errors.append(f"{path}.id: duplicate id {subject_id!r}")
            subject_ids.add(subject_id)
        position = subject.get("position")
        if position is not None:
            if not isinstance(position, dict):
                errors.append(f"{path}.position: expected an object")
            else:
                _validate_known_keys(position, {"x_percent", "y_percent", "depth", "region"}, f"{path}.position", errors)
                if "x_percent" in position:
                    _validate_percent(position.get("x_percent"), f"{path}.position.x_percent", errors)
                if "y_percent" in position:
                    _validate_percent(position.get("y_percent"), f"{path}.position.y_percent", errors)
                if "region" in position:
                    _validate_region(position.get("region"), f"{path}.position.region", errors)
                if "depth" in position and not isinstance(position.get("depth"), str):
                    errors.append(f"{path}.position.depth: expected a string")

    text_elements = spec.get("text_elements", [])
    if not isinstance(text_elements, list):
        errors.append("$.text_elements: expected a list")
    else:
        for index, item in enumerate(text_elements):
            path = f"$.text_elements[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{path}: expected an object")
                continue
            _validate_known_keys(item, {"content", "case_sensitive", "placement", "typography", "color", "control"}, path, errors)
            _require_string(item.get("content"), f"{path}.content", errors)
            _validate_optional_string_fields(item, ("placement", "typography", "color"), path, errors)
            if "case_sensitive" in item and not isinstance(item.get("case_sensitive"), bool):
                errors.append(f"{path}.case_sensitive: expected a boolean")

    spatial_edits = spec.get("spatial_edits", [])
    if not isinstance(spatial_edits, list):
        errors.append("$.spatial_edits: expected a list")
        spatial_edits = []
    for index, edit in enumerate(spatial_edits):
        path = f"$.spatial_edits[{index}]"
        if not isinstance(edit, dict):
            errors.append(f"{path}: expected an object")
            continue
        _validate_known_keys(
            edit,
            {"target", "instruction", "point", "region", "preserve_surroundings", "control"},
            path,
            errors,
        )
        _require_string(edit.get("target"), f"{path}.target", errors)
        _require_string(edit.get("instruction"), f"{path}.instruction", errors)
        if "point" in edit:
            _validate_point(edit.get("point"), f"{path}.point", errors)
        if "region" in edit:
            _validate_region(edit.get("region"), f"{path}.region", errors)
        if "preserve_surroundings" in edit and not isinstance(edit.get("preserve_surroundings"), bool):
            errors.append(f"{path}.preserve_surroundings: expected a boolean")

    effects = spec.get("effects", [])
    if not isinstance(effects, list):
        errors.append("$.effects: expected a list")
    else:
        for index, effect in enumerate(effects):
            path = f"$.effects[{index}]"
            if not isinstance(effect, dict):
                errors.append(f"{path}: expected an object")
                continue
            _validate_known_keys(
                effect,
                {
                    "function",
                    "owner_source",
                    "trigger_formation",
                    "material_shape",
                    "path_layer",
                    "operation_contact",
                    "resistance_cost",
                    "receiver_environment_response",
                    "intensity",
                    "decay_residue",
                    "control",
                },
                path,
                errors,
            )
            for key in (
                "function",
                "owner_source",
                "trigger_formation",
                "material_shape",
                "path_layer",
                "operation_contact",
                "resistance_cost",
                "receiver_environment_response",
                "decay_residue",
            ):
                _require_string(effect.get(key), f"{path}.{key}", errors)
            if not _is_allowed(effect.get("intensity"), EFFECT_INTENSITIES):
                errors.append(f"{path}.intensity: expected one of {sorted(EFFECT_INTENSITIES)}")

    styleboard = spec.get("styleboard")
    if styleboard is not None:
        if not isinstance(styleboard, dict):
            errors.append("$.styleboard: expected an object")
        else:
            _validate_known_keys(
                styleboard,
                {
                    "layout",
                    "frame_count",
                    "frame_aspect_ratio",
                    "presentation",
                    "generation_strategy",
                    "reading_order",
                    "continuity_locks",
                    "allowed_variation",
                    "reference_assignments",
                    "frames",
                    "control",
                },
                "$.styleboard",
                errors,
            )
            _require_string(styleboard.get("layout"), "$.styleboard.layout", errors)
            frame_count = styleboard.get("frame_count")
            if not isinstance(frame_count, int) or isinstance(frame_count, bool) or frame_count <= 0:
                errors.append("$.styleboard.frame_count: expected a positive integer")
            frame_aspect = styleboard.get("frame_aspect_ratio")
            frame_match = ASPECT_RATIO_RE.match(frame_aspect) if isinstance(frame_aspect, str) else None
            if frame_match is None or float(frame_match.group(1)) <= 0 or float(frame_match.group(2)) <= 0:
                errors.append("$.styleboard.frame_aspect_ratio: expected a positive ratio such as \"16:9\"")
            if not _is_allowed(styleboard.get("presentation"), STYLEBOARD_PRESENTATIONS):
                errors.append(f"$.styleboard.presentation: expected one of {sorted(STYLEBOARD_PRESENTATIONS)}")
            generation_strategy = styleboard.get("generation_strategy", "auto")
            if not _is_allowed(generation_strategy, STYLEBOARD_STRATEGIES):
                errors.append(f"$.styleboard.generation_strategy: expected one of {sorted(STYLEBOARD_STRATEGIES)}")
            if not _is_allowed(styleboard.get("reading_order", "left_to_right_top_to_bottom"), STYLEBOARD_READING_ORDERS):
                errors.append(f"$.styleboard.reading_order: expected one of {sorted(STYLEBOARD_READING_ORDERS)}")
            _validate_string_list(styleboard.get("continuity_locks", []), "$.styleboard.continuity_locks", errors)
            _validate_string_list(styleboard.get("allowed_variation", []), "$.styleboard.allowed_variation", errors)

            assignments = styleboard.get("reference_assignments", [])
            if not isinstance(assignments, list):
                errors.append("$.styleboard.reference_assignments: expected a list")
            else:
                assigned_inputs: set[str] = set()
                for index, assignment in enumerate(assignments):
                    path = f"$.styleboard.reference_assignments[{index}]"
                    if not isinstance(assignment, dict):
                        errors.append(f"{path}: expected an object")
                        continue
                    _validate_known_keys(
                        assignment,
                        {"input_id", "role", "secondary_roles", "use", "ignore", "control"},
                        path,
                        errors,
                    )
                    input_id = assignment.get("input_id")
                    _require_string(input_id, f"{path}.input_id", errors)
                    if isinstance(input_id, str):
                        if input_id not in input_ids:
                            errors.append(f"{path}.input_id: unknown input id {input_id!r}")
                        if input_id in assigned_inputs:
                            errors.append(f"{path}.input_id: each reference needs one primary assignment")
                        assigned_inputs.add(input_id)
                    if not _is_allowed(assignment.get("role"), STYLEBOARD_REFERENCE_ROLES):
                        errors.append(f"{path}.role: expected one of {sorted(STYLEBOARD_REFERENCE_ROLES)}")
                    secondary_roles = assignment.get("secondary_roles", [])
                    if not isinstance(secondary_roles, list):
                        errors.append(f"{path}.secondary_roles: expected a list")
                    else:
                        seen_secondary_roles: set[str] = set()
                        for secondary_index, secondary_role in enumerate(secondary_roles):
                            if not isinstance(secondary_role, str):
                                errors.append(
                                    f"{path}.secondary_roles[{secondary_index}]: expected one of "
                                    f"{sorted(STYLEBOARD_REFERENCE_ROLES)}"
                                )
                                continue
                            if not _is_allowed(secondary_role, STYLEBOARD_REFERENCE_ROLES):
                                errors.append(
                                    f"{path}.secondary_roles[{secondary_index}]: expected one of "
                                    f"{sorted(STYLEBOARD_REFERENCE_ROLES)}"
                                )
                            if secondary_role == assignment.get("role"):
                                errors.append(f"{path}.secondary_roles[{secondary_index}]: duplicates primary role")
                            if secondary_role in seen_secondary_roles:
                                errors.append(f"{path}.secondary_roles[{secondary_index}]: duplicate role")
                            seen_secondary_roles.add(secondary_role)
                    _require_string(assignment.get("use"), f"{path}.use", errors)
                    _require_string(assignment.get("ignore"), f"{path}.ignore", errors)

            frames = styleboard.get("frames", [])
            columns = rows = None
            if not isinstance(frames, list):
                errors.append("$.styleboard.frames: expected a list")
            else:
                if isinstance(frame_count, int) and not isinstance(frame_count, bool) and frame_count != len(frames):
                    errors.append("$.styleboard.frames: length must equal frame_count")
                layout = styleboard.get("layout")
                grid_match = GRID_LAYOUT_RE.match(layout) if isinstance(layout, str) else None
                if grid_match is not None:
                    columns = int(grid_match.group(1))
                    rows = int(grid_match.group(2))
                    if columns <= 0 or rows <= 0:
                        errors.append("$.styleboard.layout: grid dimensions must be positive")
                    elif frame_count != columns * rows:
                        errors.append(
                            f"$.styleboard.frame_count: layout={layout!r} requires {columns * rows} frames"
                        )
                elif isinstance(layout, str) and layout.strip().lower() == "triptych":
                    columns, rows = 3, 1
                    if frame_count != 3:
                        errors.append("$.styleboard.frame_count: layout='triptych' requires 3 frames")
                else:
                    columns = rows = None
                frame_ids: set[str] = set()
                for index, frame in enumerate(frames):
                    path = f"$.styleboard.frames[{index}]"
                    if not isinstance(frame, dict):
                        errors.append(f"{path}: expected an object")
                        continue
                    _validate_known_keys(
                        frame,
                        {
                            "id",
                            "shot_function",
                            "story_moment",
                            "primary_action",
                            "action_phase",
                            "shot_size",
                            "camera_height",
                            "focal_length_mm",
                            "composition",
                            "reference_ids",
                            "control",
                        },
                        path,
                        errors,
                    )
                    for key in ("id", "story_moment", "primary_action", "shot_size", "camera_height", "composition"):
                        _require_string(frame.get(key), f"{path}.{key}", errors)
                    frame_id = frame.get("id")
                    if isinstance(frame_id, str):
                        if frame_id in frame_ids:
                            errors.append(f"{path}.id: duplicate id {frame_id!r}")
                        frame_ids.add(frame_id)
                    if not _is_allowed(frame.get("shot_function"), SHOT_FUNCTIONS):
                        errors.append(f"{path}.shot_function: expected one of {sorted(SHOT_FUNCTIONS)}")
                    if not _is_allowed(frame.get("action_phase"), ACTION_PHASES):
                        errors.append(f"{path}.action_phase: expected one of {sorted(ACTION_PHASES)}")
                    focal_length = frame.get("focal_length_mm")
                    if not _is_number(focal_length) or focal_length <= 0:
                        errors.append(f"{path}.focal_length_mm: expected a positive number")
                    frame_references = frame.get("reference_ids", [])
                    _validate_string_list(frame_references, f"{path}.reference_ids", errors)
                    if isinstance(frame_references, list):
                        for reference_id in frame_references:
                            if isinstance(reference_id, str) and reference_id not in input_ids:
                                errors.append(f"{path}.reference_ids: unknown input id {reference_id!r}")
            if (
                _is_allowed(generation_strategy, {"sheet_direct", "hybrid"})
                and frame_match is not None
                and canvas_ratio_value is not None
                and columns is not None
                and rows is not None
                and columns > 0
                and rows > 0
            ):
                frame_ratio_value = float(frame_match.group(1)) / float(frame_match.group(2))
                expected_board_ratio = frame_ratio_value * columns / rows
                tolerance = max(0.03, expected_board_ratio * 0.01)
                if abs(expected_board_ratio - canvas_ratio_value) > tolerance:
                    errors.append(
                        "$.styleboard.frame_aspect_ratio: direct equal-cell sheet generation expects "
                        "board_ratio = frame_ratio * columns / rows"
                    )

    if _is_allowed(mode, {"reconstruct", "edit", "restyle", "expand", "styleboard", "learn_style"}) and not inputs:
        errors.append(f"$.inputs: mode={mode!r} requires at least one input")
    if _is_allowed(mode, {"reconstruct", "edit", "restyle", "expand", "learn_style"}):
        has_required_image = any(
            isinstance(item, dict) and item.get("type") == "image" and item.get("must_attach") is True
            for item in inputs
        )
        if not has_required_image:
            errors.append(f"$.inputs: mode={mode!r} requires at least one image with must_attach=true")
    if mode == "edit":
        must_change = constraints.get("must_change", []) if isinstance(constraints, dict) else []
        must_preserve = constraints.get("must_preserve", []) if isinstance(constraints, dict) else []
        if not spatial_edits and not must_change:
            errors.append("$: edit mode requires spatial_edits or constraints.must_change")
        if not must_preserve:
            errors.append("$.constraints.must_preserve: edit mode requires explicit invariants")
    if _is_allowed(mode, {"restyle", "expand"}) and isinstance(constraints, dict) and not constraints.get("must_preserve"):
        errors.append(f"$.constraints.must_preserve: mode={mode!r} requires explicit invariants")
    if _is_allowed(mode, {"restyle", "expand"}) and isinstance(constraints, dict) and not constraints.get("must_change"):
        errors.append(f"$.constraints.must_change: mode={mode!r} requires an explicit requested change")
    if mode == "reconstruct" and not isinstance(reference_analysis, dict):
        errors.append("$.reference_analysis: mode=\"reconstruct\" requires observed/inferred/unknown analysis")
    if reference_analysis is not None and mode != "reconstruct":
        errors.append("$.reference_analysis: allowed only when mode=\"reconstruct\"")
    if mode == "styleboard" and not isinstance(styleboard, dict):
        errors.append("$.styleboard: mode=\"styleboard\" requires a styleboard object")
    if styleboard is not None and mode != "styleboard":
        errors.append("$.styleboard: allowed only when mode=\"styleboard\"")
    if mode == "learn_style" and not isinstance(style_learning, dict):
        errors.append("$.style_learning: mode=\"learn_style\" requires a style_learning object")
    if style_learning is not None and mode != "learn_style":
        errors.append("$.style_learning: allowed only when mode=\"learn_style\"")

    scene = spec.get("scene")
    if scene is not None:
        if not isinstance(scene, dict):
            errors.append("$.scene: expected an object")
        else:
            _validate_known_keys(scene, {"summary", "setting", "time", "atmosphere", "control"}, "$.scene", errors)
            _validate_optional_string_fields(scene, ("summary", "setting", "time"), "$.scene", errors)
            _validate_string_list(scene.get("atmosphere", []), "$.scene.atmosphere", errors)

    composition = spec.get("composition")
    if composition is not None:
        if not isinstance(composition, dict):
            errors.append("$.composition: expected an object")
        else:
            _validate_known_keys(
                composition,
                {
                    "shot_size",
                    "camera_angle",
                    "perspective",
                    "focal_length_mm",
                    "framing",
                    "negative_space",
                    "depth_layers",
                    "camera_motivation",
                    "camera_height",
                    "camera_distance",
                    "point_of_view",
                    "lens_rationale",
                    "subject_frame_ratio",
                    "foreground_logic",
                    "camera_pitch",
                    "camera_yaw",
                    "camera_roll",
                    "lens_projection",
                    "perspective_distortion",
                    "edge_behavior",
                    "crop_pressure",
                    "camera_state",
                    "action_readability",
                    "control",
                },
                "$.composition",
                errors,
            )
            _validate_optional_string_fields(
                composition,
                (
                    "shot_size",
                    "camera_angle",
                    "perspective",
                    "framing",
                    "negative_space",
                    "camera_motivation",
                    "camera_height",
                    "camera_distance",
                    "point_of_view",
                    "lens_rationale",
                    "subject_frame_ratio",
                    "foreground_logic",
                    "camera_pitch",
                    "camera_yaw",
                    "camera_roll",
                    "lens_projection",
                    "perspective_distortion",
                    "edge_behavior",
                    "crop_pressure",
                    "camera_state",
                    "action_readability",
                ),
                "$.composition",
                errors,
            )
            _validate_string_list(composition.get("depth_layers", []), "$.composition.depth_layers", errors)
            focal_length = composition.get("focal_length_mm")
            if focal_length is not None and (not _is_number(focal_length) or focal_length <= 0):
                errors.append("$.composition.focal_length_mm: expected a positive number or null")

    lighting = spec.get("lighting")
    if lighting is not None:
        if not isinstance(lighting, dict):
            errors.append("$.lighting: expected an object")
        else:
            _validate_known_keys(
                lighting,
                {
                    "summary",
                    "key",
                    "fill",
                    "rim",
                    "direction",
                    "contrast",
                    "color_temperature",
                    "practicals",
                    "motivation",
                    "narrative_function",
                    "control",
                },
                "$.lighting",
                errors,
            )
            _validate_optional_string_fields(
                lighting,
                (
                    "summary",
                    "key",
                    "fill",
                    "rim",
                    "direction",
                    "contrast",
                    "color_temperature",
                    "motivation",
                    "narrative_function",
                ),
                "$.lighting",
                errors,
            )
            _validate_string_list(lighting.get("practicals", []), "$.lighting.practicals", errors)

    color_pipeline = spec.get("color_pipeline")
    if color_pipeline is not None:
        if not isinstance(color_pipeline, dict):
            errors.append("$.color_pipeline: expected an object")
        else:
            _validate_known_keys(
                color_pipeline,
                {
                    "intent",
                    "custom_intent",
                    "color_science",
                    "display_target",
                    "exposure_strategy",
                    "tonal_curve",
                    "black_point",
                    "white_point",
                    "highlight_rolloff",
                    "shadow_floor",
                    "midtone_density",
                    "white_balance",
                    "color_separation",
                    "shadow_bias",
                    "midtone_bias",
                    "highlight_bias",
                    "skin_tone_policy",
                    "saturation_policy",
                    "gamut_policy",
                    "film_emulation",
                    "shot_matching",
                    "continuity_locks",
                    "forbidden_casts",
                    "control",
                },
                "$.color_pipeline",
                errors,
            )
            color_intent = color_pipeline.get("intent", "auto")
            if not _is_allowed(color_intent, COLOR_PIPELINE_INTENTS):
                errors.append(f"$.color_pipeline.intent: expected one of {sorted(COLOR_PIPELINE_INTENTS)}")
            _validate_optional_string_fields(
                color_pipeline,
                (
                    "custom_intent",
                    "color_science",
                    "display_target",
                    "exposure_strategy",
                    "tonal_curve",
                    "black_point",
                    "white_point",
                    "highlight_rolloff",
                    "shadow_floor",
                    "midtone_density",
                    "white_balance",
                    "color_separation",
                    "shadow_bias",
                    "midtone_bias",
                    "highlight_bias",
                    "skin_tone_policy",
                    "saturation_policy",
                    "gamut_policy",
                    "shot_matching",
                ),
                "$.color_pipeline",
                errors,
            )
            custom_intent = color_pipeline.get("custom_intent", "")
            has_custom_intent = isinstance(custom_intent, str) and bool(custom_intent.strip())
            if color_intent == "custom" and not has_custom_intent:
                errors.append("$.color_pipeline.custom_intent: intent=\"custom\" requires a description")
            if color_intent != "custom" and has_custom_intent:
                errors.append("$.color_pipeline.custom_intent: allowed only when intent=\"custom\"")
            film_emulation = color_pipeline.get("film_emulation")
            if film_emulation is not None:
                if not isinstance(film_emulation, dict):
                    errors.append("$.color_pipeline.film_emulation: expected an object")
                else:
                    _validate_known_keys(
                        film_emulation,
                        {
                            "negative_or_reversal_character",
                            "print_or_display_character",
                            "grain",
                            "halation",
                            "bloom",
                            "gate_weave",
                            "vignette",
                        },
                        "$.color_pipeline.film_emulation",
                        errors,
                    )
                    _validate_optional_string_fields(
                        film_emulation,
                        (
                            "negative_or_reversal_character",
                            "print_or_display_character",
                            "grain",
                            "halation",
                            "bloom",
                            "gate_weave",
                            "vignette",
                        ),
                        "$.color_pipeline.film_emulation",
                        errors,
                    )
            _validate_string_list(color_pipeline.get("continuity_locks", []), "$.color_pipeline.continuity_locks", errors)
            _validate_string_list(color_pipeline.get("forbidden_casts", []), "$.color_pipeline.forbidden_casts", errors)

    render_pipeline = spec.get("render_pipeline")
    if render_pipeline is not None:
        if not isinstance(render_pipeline, dict):
            errors.append("$.render_pipeline: expected an object")
        else:
            _validate_known_keys(
                render_pipeline,
                {
                    "domain",
                    "custom_domain",
                    "engine_reference",
                    "engine_reference_scope",
                    "lighting_transport",
                    "global_illumination",
                    "ray_tracing",
                    "reflection_model",
                    "shadow_model",
                    "ambient_occlusion",
                    "volumetrics",
                    "material_workflow",
                    "subsurface_scattering",
                    "transmission_refraction",
                    "caustics",
                    "displacement_normal",
                    "texture_scale",
                    "sampling_denoise",
                    "render_passes",
                    "performance_fidelity_tradeoff",
                    "npr_strategy",
                    "forbidden_artifacts",
                    "control",
                },
                "$.render_pipeline",
                errors,
            )
            render_domain = render_pipeline.get("domain", "auto")
            if not _is_allowed(render_domain, RENDER_DOMAINS):
                errors.append(f"$.render_pipeline.domain: expected one of {sorted(RENDER_DOMAINS)}")
            _validate_optional_string_fields(
                render_pipeline,
                (
                    "custom_domain",
                    "engine_reference",
                    "lighting_transport",
                    "global_illumination",
                    "ray_tracing",
                    "reflection_model",
                    "shadow_model",
                    "ambient_occlusion",
                    "volumetrics",
                    "material_workflow",
                    "subsurface_scattering",
                    "transmission_refraction",
                    "caustics",
                    "displacement_normal",
                    "texture_scale",
                    "sampling_denoise",
                    "performance_fidelity_tradeoff",
                    "npr_strategy",
                ),
                "$.render_pipeline",
                errors,
            )
            custom_domain = render_pipeline.get("custom_domain", "")
            has_custom_domain = isinstance(custom_domain, str) and bool(custom_domain.strip())
            if render_domain == "custom" and not has_custom_domain:
                errors.append("$.render_pipeline.custom_domain: domain=\"custom\" requires a description")
            if render_domain != "custom" and has_custom_domain:
                errors.append("$.render_pipeline.custom_domain: allowed only when domain=\"custom\"")
            engine_reference = render_pipeline.get("engine_reference", "")
            if isinstance(engine_reference, str) and engine_reference.strip():
                if not _is_allowed(render_pipeline.get("engine_reference_scope"), ENGINE_REFERENCE_SCOPES):
                    errors.append(
                        f"$.render_pipeline.engine_reference_scope: expected one of {sorted(ENGINE_REFERENCE_SCOPES)}"
                    )
            elif "engine_reference_scope" in render_pipeline and not _is_allowed(
                render_pipeline.get("engine_reference_scope"), ENGINE_REFERENCE_SCOPES
            ):
                errors.append(f"$.render_pipeline.engine_reference_scope: expected one of {sorted(ENGINE_REFERENCE_SCOPES)}")
            _validate_string_list(render_pipeline.get("render_passes", []), "$.render_pipeline.render_passes", errors)
            _validate_string_list(
                render_pipeline.get("forbidden_artifacts", []),
                "$.render_pipeline.forbidden_artifacts",
                errors,
            )

    if (
        direction_deliverable != "auto"
        and cinematic_profile != "auto"
        and direction_deliverable != cinematic_profile
    ):
        errors.append("$: direction.deliverable and cinematic.profile must agree when both are explicit")

    narrative_required = (
        direction_deliverable == "narrative_film_frame" or cinematic_profile == "narrative_film_frame"
    )
    if narrative_required:
        if not isinstance(cinematic, dict):
            errors.append("$.cinematic: narrative_film_frame requires a cinematic shot contract")
        else:
            for key in (
                "shot_function",
                "visible_event",
                "relationship_pressure",
                "viewer_task",
                "viewer_position",
                "frozen_moment",
                "withheld_information",
            ):
                _require_string(cinematic.get(key), f"$.cinematic.{key}", errors)
        if not isinstance(staging, dict):
            errors.append("$.staging: narrative_film_frame requires a staging object")
        else:
            for key in ("primary_relationship", "eyeline_logic", "screen_direction", "axis", "attention_path"):
                _require_string(staging.get(key), f"$.staging.{key}", errors)
            if not staging.get("subject_positions"):
                errors.append("$.staging.subject_positions: narrative_film_frame requires explicit positions")
        if not isinstance(composition, dict):
            errors.append("$.composition: narrative_film_frame requires camera design")
        else:
            for key in ("camera_motivation", "camera_height", "camera_distance", "lens_rationale"):
                _require_string(composition.get(key), f"$.composition.{key}", errors)
        if not isinstance(lighting, dict):
            errors.append("$.lighting: narrative_film_frame requires motivated lighting")
        else:
            for key in ("motivation", "narrative_function"):
                _require_string(lighting.get(key), f"$.lighting.{key}", errors)

    materials = spec.get("materials", [])
    if not isinstance(materials, list):
        errors.append("$.materials: expected a list")
    else:
        for index, material in enumerate(materials):
            path = f"$.materials[{index}]"
            if not isinstance(material, dict):
                errors.append(f"{path}: expected an object")
                continue
            _validate_known_keys(
                material,
                {
                    "target",
                    "description",
                    "physical_properties",
                    "microstructure",
                    "roughness",
                    "specular_response",
                    "transmission",
                    "subsurface_behavior",
                    "anisotropy",
                    "wear_patina",
                    "contact_deformation",
                    "properties",
                    "control",
                },
                path,
                errors,
            )
            _require_string(material.get("target"), f"{path}.target", errors)
            _require_string(material.get("description"), f"{path}.description", errors)
            _validate_string_list(material.get("physical_properties"), f"{path}.physical_properties", errors)
            _validate_optional_string_fields(
                material,
                (
                    "microstructure",
                    "roughness",
                    "specular_response",
                    "transmission",
                    "subsurface_behavior",
                    "anisotropy",
                    "wear_patina",
                    "contact_deformation",
                ),
                path,
                errors,
            )
            if "properties" in material:
                errors.append(f"{path}.properties: legacy key is not allowed; use physical_properties")

    color = spec.get("color")
    if color is not None:
        if not isinstance(color, dict):
            errors.append("$.color: expected an object")
        else:
            _validate_known_keys(color, {"palette", "grade", "contrast", "saturation", "control"}, "$.color", errors)
            _validate_string_list(color.get("palette", []), "$.color.palette", errors)
            _validate_optional_string_fields(color, ("grade", "contrast", "saturation"), "$.color", errors)

    optics = spec.get("optics")
    if optics is not None:
        if not isinstance(optics, dict):
            errors.append("$.optics: expected an object")
        else:
            _validate_known_keys(
                optics,
                {"depth_of_field", "focus_target", "motion_blur", "lens_character", "artifacts", "control"},
                "$.optics",
                errors,
            )
            _validate_optional_string_fields(
                optics,
                ("depth_of_field", "focus_target", "motion_blur", "lens_character"),
                "$.optics",
                errors,
            )
            _validate_string_list(optics.get("artifacts", []), "$.optics.artifacts", errors)

    style = spec.get("style")
    if style is not None:
        if not isinstance(style, dict):
            errors.append("$.style: expected an object")
        else:
            _validate_known_keys(
                style,
                {"medium", "realism", "visual_traits", "era", "references", "excluded_traits", "control"},
                "$.style",
                errors,
            )
            _validate_optional_string_fields(style, ("medium", "realism", "era"), "$.style", errors)
            for key in ("visual_traits", "references", "excluded_traits"):
                _validate_string_list(style.get(key, []), f"$.style.{key}", errors)

    render = spec.get("render")
    if render is not None:
        if not isinstance(render, dict):
            errors.append("$.render: expected an object")
        else:
            _validate_known_keys(
                render,
                {"detail_priority", "artifact_budget", "quality_controls", "control"},
                "$.render",
                errors,
            )
            _validate_string_list(render.get("detail_priority", []), "$.render.detail_priority", errors)
            artifact_budget = render.get("artifact_budget")
            if artifact_budget is not None and not _is_allowed(artifact_budget, ARTIFACT_BUDGETS):
                errors.append(f"$.render.artifact_budget: expected one of {sorted(ARTIFACT_BUDGETS)}")
            _validate_string_list(render.get("quality_controls", []), "$.render.quality_controls", errors)

    platform_options = spec.get("platform_options")
    _validate_platform_options(platform_options, errors)
    if isinstance(canvas, dict) and isinstance(platform_options, dict):
        dimensions = canvas.get("dimensions") if isinstance(canvas.get("dimensions"), dict) else {}
        openai = platform_options.get("openai") if isinstance(platform_options.get("openai"), dict) else {}
        size = openai.get("size")
        if isinstance(size, str) and re.fullmatch(r"\d+x\d+", size):
            width, height = (int(item) for item in size.split("x", 1))
            if dimensions.get("width") != width or dimensions.get("height") != height:
                errors.append("$.platform_options.openai.size: must match canvas.dimensions when both are supplied")
        midjourney = (
            platform_options.get("midjourney")
            if isinstance(platform_options.get("midjourney"), dict)
            else {}
        )
        mid_ratio = midjourney.get("aspect_ratio")
        mid_match = ASPECT_RATIO_RE.match(mid_ratio) if isinstance(mid_ratio, str) else None
        if mid_match is not None and canvas_ratio_value is not None:
            mid_ratio_value = float(mid_match.group(1)) / float(mid_match.group(2))
            if abs(mid_ratio_value - canvas_ratio_value) > 1e-6:
                errors.append(
                    "$.platform_options.midjourney.aspect_ratio: must match canvas.aspect_ratio when both are supplied"
                )
    _walk_controls(spec, "$", errors)
    return errors


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to a visual specification JSON file")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emit machine-readable validation output")
    args = parser.parse_args()

    try:
        spec = load_json(args.spec)
    except OSError as exc:
        errors = [f"cannot read {args.spec}: {exc}"]
    except json.JSONDecodeError as exc:
        errors = [f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"]
    else:
        errors = validate_spec(spec)

    if args.json_output:
        print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    elif errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
    else:
        print("VALID")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
