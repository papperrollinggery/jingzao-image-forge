#!/usr/bin/env python3
"""Validate a 镜造 Image Forge visual specification."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


MODES = {"create", "reconstruct", "edit", "restyle", "expand", "styleboard"}
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
SHOT_FUNCTIONS = {"establish", "introduce", "observe", "follow", "emphasize", "react", "transition", "resolve"}
EFFECT_INTENSITIES = {"minor", "medium", "hero"}
STYLEBOARD_PRESENTATIONS = {"line_art", "hand_drawn", "cinematic_frame", "mixed"}
STYLEBOARD_STRATEGIES = {"auto", "sheet_direct", "independent_frames", "hybrid"}
STYLEBOARD_REFERENCE_ROLES = {"identity", "wardrobe", "scene", "prop", "camera_action", "style", "layout", "palette"}
STYLEBOARD_READING_ORDERS = {"left_to_right_top_to_bottom", "top_to_bottom_left_to_right"}
ACTION_PHASES = {"prepare", "initiate", "contact", "response", "hold"}
ASPECT_RATIO_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)\s*$")
GRID_LAYOUT_RE = re.compile(r"^\s*(\d+)\s*[x×]\s*(\d+)\s*$", re.IGNORECASE)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


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
    _validate_percent(value.get("x_percent"), f"{path}.x_percent", errors)
    _validate_percent(value.get("y_percent"), f"{path}.y_percent", errors)


def _validate_region(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected an object")
        return
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


def _walk_controls(value: Any, path: str, errors: list[str]) -> None:
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
        for key, child in value.items():
            if key != "control":
                _walk_controls(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_controls(child, f"{path}[{index}]", errors)


def _validate_platform_options(value: Any, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        errors.append("$.platform_options: expected an object")
        return

    openai = value.get("openai")
    if openai is not None:
        if not isinstance(openai, dict):
            errors.append("$.platform_options.openai: expected an object")
        else:
            if openai.get("quality") not in {None, "low", "medium", "high", "auto"}:
                errors.append("$.platform_options.openai.quality: expected low, medium, high, or auto")
            for key in ("model", "size"):
                if key in openai:
                    _require_string(openai.get(key), f"$.platform_options.openai.{key}", errors)

    flux = value.get("flux")
    if flux is not None:
        if not isinstance(flux, dict):
            errors.append("$.platform_options.flux: expected an object")
        else:
            if flux.get("prompt_format") not in {None, "natural_language", "json"}:
                errors.append("$.platform_options.flux.prompt_format: expected natural_language or json")
            if "prompt_upsampling" in flux and not isinstance(flux.get("prompt_upsampling"), bool):
                errors.append("$.platform_options.flux.prompt_upsampling: expected a boolean")

    midjourney = value.get("midjourney")
    if midjourney is not None:
        if not isinstance(midjourney, dict):
            errors.append("$.platform_options.midjourney: expected an object")
        else:
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
            refs = midjourney.get("style_reference")
            if refs is not None and not isinstance(refs, list):
                errors.append("$.platform_options.midjourney.style_reference: expected a list")


def validate_spec(spec: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(spec, dict):
        return ["$: expected a JSON object"]

    if spec.get("visual_generation_spec") != "1.0":
        errors.append("$.visual_generation_spec: expected \"1.0\"")

    mode = spec.get("mode")
    if mode not in MODES:
        errors.append(f"$.mode: expected one of {sorted(MODES)}")
    _require_string(spec.get("intent"), "$.intent", errors)

    platform = spec.get("platform", "auto")
    if platform not in PLATFORMS:
        errors.append(f"$.platform: expected one of {sorted(PLATFORMS)}")

    language = spec.get("language", "en")
    if language not in SPEC_LANGUAGES:
        errors.append(f"$.language: expected one of {sorted(SPEC_LANGUAGES)}")

    canvas = spec.get("canvas")
    canvas_ratio_value: float | None = None
    if not isinstance(canvas, dict):
        errors.append("$.canvas: expected an object")
    else:
        canvas_profile = canvas.get("profile", "auto")
        if canvas_profile not in CANVAS_PROFILES:
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
                for key in ("width", "height"):
                    value = dimensions.get(key)
                    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                        errors.append(f"$.canvas.dimensions.{key}: expected a positive integer")

    constraints = spec.get("constraints")
    if not isinstance(constraints, dict):
        errors.append("$.constraints: expected an object")
    else:
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
        for key in ("id", "type", "role", "description"):
            _require_string(item.get(key), f"{path}.{key}", errors)
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
            _require_string(item.get("name"), f"{path}.name", errors)
            if "context" in item:
                _require_string(item.get("context"), f"{path}.context", errors)
            strategy = item.get("strategy", "auto")
            if strategy not in KNOWLEDGE_STRATEGIES:
                errors.append(f"{path}.strategy: expected one of {sorted(KNOWLEDGE_STRATEGIES)}")
            verification = item.get("verification", "unverified")
            if verification not in KNOWLEDGE_VERIFICATIONS:
                errors.append(f"{path}.verification: expected one of {sorted(KNOWLEDGE_VERIFICATIONS)}")
            reference_ids = item.get("reference_ids", [])
            _validate_string_list(reference_ids, f"{path}.reference_ids", errors)
            if isinstance(reference_ids, list):
                for reference_id in reference_ids:
                    if isinstance(reference_id, str) and reference_id not in input_ids:
                        errors.append(f"{path}.reference_ids: unknown input id {reference_id!r}")
            if strategy in {"reference", "hybrid"} and not reference_ids:
                errors.append(f"{path}.reference_ids: strategy={strategy!r} requires at least one input reference")

    direction = spec.get("direction")
    direction_deliverable = "auto"
    if direction is not None:
        if not isinstance(direction, dict):
            errors.append("$.direction: expected an object")
        else:
            direction_deliverable = direction.get("deliverable", "auto")
            if direction_deliverable not in DIRECTION_DELIVERABLES:
                errors.append(f"$.direction.deliverable: expected one of {sorted(DIRECTION_DELIVERABLES)}")
            if direction.get("treatment", "auto") not in DIRECTION_TREATMENTS:
                errors.append(f"$.direction.treatment: expected one of {sorted(DIRECTION_TREATMENTS)}")
            if direction.get("spectacle_scale", "dramatic") not in SPECTACLE_SCALES:
                errors.append(f"$.direction.spectacle_scale: expected one of {sorted(SPECTACLE_SCALES)}")
            if direction.get("camera_freedom", "physical") not in CAMERA_FREEDOMS:
                errors.append(f"$.direction.camera_freedom: expected one of {sorted(CAMERA_FREEDOMS)}")
            _validate_optional_string_fields(direction, ("genre", "world_rule", "visual_goal"), "$.direction", errors)

    cinematic = spec.get("cinematic")
    cinematic_profile = "auto"
    if cinematic is not None:
        if not isinstance(cinematic, dict):
            errors.append("$.cinematic: expected an object")
        else:
            cinematic_profile = cinematic.get("profile", "auto")
            if cinematic_profile not in DIRECTION_DELIVERABLES:
                errors.append(f"$.cinematic.profile: expected one of {sorted(DIRECTION_DELIVERABLES)}")
            shot_function = cinematic.get("shot_function")
            if shot_function is not None and shot_function not in SHOT_FUNCTIONS:
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
            _validate_optional_string_fields(
                staging,
                ("primary_relationship", "eyeline_logic", "screen_direction", "axis", "occlusion", "attention_path"),
                "$.staging",
                errors,
            )
            _validate_string_list(staging.get("subject_positions", []), "$.staging.subject_positions", errors)

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
            for key in (
                "function",
                "owner_source",
                "trigger_formation",
                "material_shape",
                "path_layer",
                "operation_contact",
                "receiver_environment_response",
                "decay_residue",
            ):
                _require_string(effect.get(key), f"{path}.{key}", errors)
            if effect.get("intensity") not in EFFECT_INTENSITIES:
                errors.append(f"{path}.intensity: expected one of {sorted(EFFECT_INTENSITIES)}")

    styleboard = spec.get("styleboard")
    if styleboard is not None:
        if not isinstance(styleboard, dict):
            errors.append("$.styleboard: expected an object")
        else:
            _require_string(styleboard.get("layout"), "$.styleboard.layout", errors)
            frame_count = styleboard.get("frame_count")
            if not isinstance(frame_count, int) or isinstance(frame_count, bool) or frame_count <= 0:
                errors.append("$.styleboard.frame_count: expected a positive integer")
            frame_aspect = styleboard.get("frame_aspect_ratio")
            frame_match = ASPECT_RATIO_RE.match(frame_aspect) if isinstance(frame_aspect, str) else None
            if frame_match is None or float(frame_match.group(1)) <= 0 or float(frame_match.group(2)) <= 0:
                errors.append("$.styleboard.frame_aspect_ratio: expected a positive ratio such as \"16:9\"")
            if styleboard.get("presentation") not in STYLEBOARD_PRESENTATIONS:
                errors.append(f"$.styleboard.presentation: expected one of {sorted(STYLEBOARD_PRESENTATIONS)}")
            generation_strategy = styleboard.get("generation_strategy", "auto")
            if generation_strategy not in STYLEBOARD_STRATEGIES:
                errors.append(f"$.styleboard.generation_strategy: expected one of {sorted(STYLEBOARD_STRATEGIES)}")
            if styleboard.get("reading_order", "left_to_right_top_to_bottom") not in STYLEBOARD_READING_ORDERS:
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
                    input_id = assignment.get("input_id")
                    _require_string(input_id, f"{path}.input_id", errors)
                    if isinstance(input_id, str):
                        if input_id not in input_ids:
                            errors.append(f"{path}.input_id: unknown input id {input_id!r}")
                        if input_id in assigned_inputs:
                            errors.append(f"{path}.input_id: each reference needs one primary assignment")
                        assigned_inputs.add(input_id)
                    if assignment.get("role") not in STYLEBOARD_REFERENCE_ROLES:
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
                            if secondary_role not in STYLEBOARD_REFERENCE_ROLES:
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
                    for key in ("id", "story_moment", "primary_action", "shot_size", "camera_height", "composition"):
                        _require_string(frame.get(key), f"{path}.{key}", errors)
                    frame_id = frame.get("id")
                    if isinstance(frame_id, str):
                        if frame_id in frame_ids:
                            errors.append(f"{path}.id: duplicate id {frame_id!r}")
                        frame_ids.add(frame_id)
                    if frame.get("shot_function") not in SHOT_FUNCTIONS:
                        errors.append(f"{path}.shot_function: expected one of {sorted(SHOT_FUNCTIONS)}")
                    if frame.get("action_phase") not in ACTION_PHASES:
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
                generation_strategy in {"sheet_direct", "hybrid"}
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

    if mode in {"reconstruct", "edit", "restyle", "expand", "styleboard"} and not inputs:
        errors.append(f"$.inputs: mode={mode!r} requires at least one input")
    if mode == "edit":
        must_change = constraints.get("must_change", []) if isinstance(constraints, dict) else []
        must_preserve = constraints.get("must_preserve", []) if isinstance(constraints, dict) else []
        if not spatial_edits and not must_change:
            errors.append("$: edit mode requires spatial_edits or constraints.must_change")
        if not must_preserve:
            errors.append("$.constraints.must_preserve: edit mode requires explicit invariants")
    if mode in {"restyle", "expand"} and isinstance(constraints, dict) and not constraints.get("must_preserve"):
        errors.append(f"$.constraints.must_preserve: mode={mode!r} requires explicit invariants")
    if mode == "styleboard" and not isinstance(styleboard, dict):
        errors.append("$.styleboard: mode=\"styleboard\" requires a styleboard object")

    scene = spec.get("scene")
    if scene is not None:
        if not isinstance(scene, dict):
            errors.append("$.scene: expected an object")
        else:
            _validate_optional_string_fields(scene, ("summary", "setting", "time"), "$.scene", errors)
            _validate_string_list(scene.get("atmosphere", []), "$.scene.atmosphere", errors)

    composition = spec.get("composition")
    if composition is not None:
        if not isinstance(composition, dict):
            errors.append("$.composition: expected an object")
        else:
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
            _require_string(material.get("target"), f"{path}.target", errors)
            _require_string(material.get("description"), f"{path}.description", errors)
            _validate_string_list(material.get("physical_properties"), f"{path}.physical_properties", errors)

    color = spec.get("color")
    if color is not None:
        if not isinstance(color, dict):
            errors.append("$.color: expected an object")
        else:
            _validate_string_list(color.get("palette", []), "$.color.palette", errors)
            _validate_optional_string_fields(color, ("grade", "contrast", "saturation"), "$.color", errors)

    optics = spec.get("optics")
    if optics is not None:
        if not isinstance(optics, dict):
            errors.append("$.optics: expected an object")
        else:
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
            _validate_optional_string_fields(style, ("medium", "realism", "era"), "$.style", errors)
            for key in ("visual_traits", "references", "excluded_traits"):
                _validate_string_list(style.get(key, []), f"$.style.{key}", errors)

    render = spec.get("render")
    if render is not None:
        if not isinstance(render, dict):
            errors.append("$.render: expected an object")
        else:
            _validate_optional_string_fields(render, ("quality",), "$.render", errors)
            _validate_string_list(render.get("detail_priority", []), "$.render.detail_priority", errors)
            artifact_budget = render.get("artifact_budget")
            if artifact_budget is not None and artifact_budget not in ARTIFACT_BUDGETS:
                errors.append(f"$.render.artifact_budget: expected one of {sorted(ARTIFACT_BUDGETS)}")
            _validate_string_list(render.get("quality_controls", []), "$.render.quality_controls", errors)

    _validate_platform_options(spec.get("platform_options"), errors)
    _walk_controls(spec, "$", errors)
    return errors


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to a visual specification JSON file")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emit machine-readable validation output")
    args = parser.parse_args()

    try:
        spec = load_json(args.spec)
    except FileNotFoundError:
        errors = [f"file not found: {args.spec}"]
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
