#!/usr/bin/env python3
"""Compile a visual specification into a platform-ready image prompt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

from validate_spec import load_json, validate_spec


SUPPORTED_PLATFORMS = {"openai", "flux", "midjourney", "generic"}
ARTIFACT_PRESETS = {
    "strict": (
        "clean low-noise tonal fields and gradients; contained highlights with smooth rolloff; "
        "clear air; material-specific roughness; selective detail without sharpening halos"
    ),
    "balanced": (
        "controlled noise or medium-motivated grain; restrained bloom and flare only from visible light sources; "
        "natural material-specific roughness and specular response; selective focal detail with natural microcontrast; "
        "sparse scene-motivated particles"
    ),
    "expressive": (
        "intentional grain, bloom, flare, particles, and gloss only where coherent with the requested medium or visible "
        "light sources; preserve focal hierarchy and material separation"
    ),
    "source_matched": (
        "match source noise or grain, bloom, flare, sharpness, and surface response; introduce no new artifact classes "
        "outside the requested change"
    ),
}


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _join(parts: Iterable[str], separator: str = "; ") -> str:
    return separator.join(part for part in parts if part)


def _format_region(region: dict[str, Any]) -> str:
    return (
        f"x={region.get('x_percent'):g}%, y={region.get('y_percent'):g}%, "
        f"w={region.get('width_percent'):g}%, h={region.get('height_percent'):g}%"
    )


def _subject_line(subject: dict[str, Any]) -> str:
    position = subject.get("position") if isinstance(subject.get("position"), dict) else {}
    position_bits: list[str] = []
    x, y = position.get("x_percent"), position.get("y_percent")
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        position_bits.append(f"anchor at {x:g}% from left and {y:g}% from top")
    if _text(position.get("depth")):
        position_bits.append(_text(position.get("depth")))
    if isinstance(position.get("region"), dict):
        position_bits.append("approximate region " + _format_region(position["region"]))

    appearance = _items(subject.get("appearance"))
    relationships = _items(subject.get("relationships"))
    description = _text(subject.get("description"))
    count = subject.get("count", 1)
    return _join(
        [
            f"{count} × {description}" if description else "",
            f"appearance: {', '.join(appearance)}" if appearance else "",
            f"action: {_text(subject.get('action'))}" if _text(subject.get("action")) else "",
            f"pose: {_text(subject.get('pose'))}" if _text(subject.get("pose")) else "",
            f"gaze: {_text(subject.get('gaze'))}" if _text(subject.get("gaze")) not in {"", "not applicable"} else "",
            f"position: {', '.join(position_bits)}" if position_bits else "",
            f"scale: {_text(subject.get('scale'))}" if _text(subject.get("scale")) else "",
            f"relationships: {', '.join(relationships)}" if relationships else "",
        ]
    )


def _scene_line(spec: dict[str, Any]) -> str:
    scene = spec.get("scene") if isinstance(spec.get("scene"), dict) else {}
    atmosphere = _items(scene.get("atmosphere"))
    return _join(
        [
            _text(scene.get("summary")),
            f"setting: {_text(scene.get('setting'))}" if _text(scene.get("setting")) else "",
            f"time: {_text(scene.get('time'))}" if _text(scene.get("time")) else "",
            f"atmosphere: {', '.join(atmosphere)}" if atmosphere else "",
        ]
    )


def _direction_line(spec: dict[str, Any]) -> str:
    section = spec.get("direction") if isinstance(spec.get("direction"), dict) else {}
    return _join(
        [
            f"deliverable: {_text(section.get('deliverable'))}" if _text(section.get("deliverable")) else "",
            f"treatment: {_text(section.get('treatment'))}" if _text(section.get("treatment")) else "",
            f"spectacle scale: {_text(section.get('spectacle_scale'))}" if _text(section.get("spectacle_scale")) else "",
            f"camera freedom: {_text(section.get('camera_freedom'))}" if _text(section.get("camera_freedom")) else "",
            f"genre: {_text(section.get('genre'))}" if _text(section.get("genre")) else "",
            f"world rule: {_text(section.get('world_rule'))}" if _text(section.get("world_rule")) else "",
            f"visual goal: {_text(section.get('visual_goal'))}" if _text(section.get("visual_goal")) else "",
        ]
    )


def _cinematic_line(spec: dict[str, Any]) -> str:
    section = spec.get("cinematic") if isinstance(spec.get("cinematic"), dict) else {}
    return _join(
        [
            f"profile: {_text(section.get('profile'))}" if _text(section.get("profile")) else "",
            f"shot function: {_text(section.get('shot_function'))}" if _text(section.get("shot_function")) else "",
            f"visible event: {_text(section.get('visible_event'))}" if _text(section.get("visible_event")) else "",
            f"relationship pressure: {_text(section.get('relationship_pressure'))}"
            if _text(section.get("relationship_pressure"))
            else "",
            f"viewer task: {_text(section.get('viewer_task'))}" if _text(section.get("viewer_task")) else "",
            f"viewer position: {_text(section.get('viewer_position'))}" if _text(section.get("viewer_position")) else "",
            f"frozen moment: {_text(section.get('frozen_moment'))}" if _text(section.get("frozen_moment")) else "",
            f"withheld information: {_text(section.get('withheld_information'))}"
            if _text(section.get("withheld_information"))
            else "",
            "avoid poster-style simultaneous showcase" if section.get("posterization_guard") else "",
        ]
    )


def _staging_line(spec: dict[str, Any]) -> str:
    section = spec.get("staging") if isinstance(spec.get("staging"), dict) else {}
    positions = _items(section.get("subject_positions"))
    return _join(
        [
            f"primary relationship: {_text(section.get('primary_relationship'))}"
            if _text(section.get("primary_relationship"))
            else "",
            f"positions: {', '.join(positions)}" if positions else "",
            f"eyelines: {_text(section.get('eyeline_logic'))}" if _text(section.get("eyeline_logic")) else "",
            f"screen direction: {_text(section.get('screen_direction'))}" if _text(section.get("screen_direction")) else "",
            f"axis: {_text(section.get('axis'))}" if _text(section.get("axis")) else "",
            f"occlusion: {_text(section.get('occlusion'))}" if _text(section.get("occlusion")) else "",
            f"attention path: {_text(section.get('attention_path'))}" if _text(section.get("attention_path")) else "",
        ]
    )


def _composition_line(spec: dict[str, Any]) -> str:
    section = spec.get("composition") if isinstance(spec.get("composition"), dict) else {}
    depth = _items(section.get("depth_layers"))
    focal = section.get("focal_length_mm")
    return _join(
        [
            _text(section.get("shot_size")),
            _text(section.get("camera_angle")),
            _text(section.get("perspective")),
            f"viewer POV: {_text(section.get('point_of_view'))}" if _text(section.get("point_of_view")) else "",
            f"camera motivation: {_text(section.get('camera_motivation'))}"
            if _text(section.get("camera_motivation"))
            else "",
            f"camera height: {_text(section.get('camera_height'))}" if _text(section.get("camera_height")) else "",
            f"camera distance: {_text(section.get('camera_distance'))}" if _text(section.get("camera_distance")) else "",
            f"{focal:g}mm lens intent" if isinstance(focal, (int, float)) else "",
            f"lens rationale: {_text(section.get('lens_rationale'))}" if _text(section.get("lens_rationale")) else "",
            f"subject/frame ratio: {_text(section.get('subject_frame_ratio'))}"
            if _text(section.get("subject_frame_ratio"))
            else "",
            _text(section.get("framing")),
            f"foreground logic: {_text(section.get('foreground_logic'))}" if _text(section.get("foreground_logic")) else "",
            f"negative space: {_text(section.get('negative_space'))}" if _text(section.get("negative_space")) else "",
            f"depth: {', '.join(depth)}" if depth else "",
        ]
    )


def _lighting_line(spec: dict[str, Any]) -> str:
    section = spec.get("lighting") if isinstance(spec.get("lighting"), dict) else {}
    practicals = _items(section.get("practicals"))
    return _join(
        [
            _text(section.get("summary")),
            f"motivation: {_text(section.get('motivation'))}" if _text(section.get("motivation")) else "",
            f"narrative function: {_text(section.get('narrative_function'))}"
            if _text(section.get("narrative_function"))
            else "",
            f"key: {_text(section.get('key'))}" if _text(section.get("key")) else "",
            f"fill: {_text(section.get('fill'))}" if _text(section.get("fill")) else "",
            f"rim: {_text(section.get('rim'))}" if _text(section.get("rim")) else "",
            f"direction: {_text(section.get('direction'))}" if _text(section.get("direction")) else "",
            f"contrast: {_text(section.get('contrast'))}" if _text(section.get("contrast")) else "",
            f"temperature: {_text(section.get('color_temperature'))}" if _text(section.get("color_temperature")) else "",
            f"practicals: {', '.join(practicals)}" if practicals else "",
        ]
    )


def _materials_line(spec: dict[str, Any]) -> str:
    materials = spec.get("materials") if isinstance(spec.get("materials"), list) else []
    lines: list[str] = []
    for item in materials:
        if not isinstance(item, dict):
            continue
        properties = _items(item.get("physical_properties"))
        line = _join(
            [
                _text(item.get("target")),
                _text(item.get("description")),
                ", ".join(properties),
            ],
            separator=": ",
        )
        if line:
            lines.append(line)
    return " | ".join(lines)


def _effect_lines(spec: dict[str, Any]) -> list[str]:
    effects = spec.get("effects") if isinstance(spec.get("effects"), list) else []
    result: list[str] = []
    for item in effects:
        if not isinstance(item, dict):
            continue
        result.append(
            _join(
                [
                    f"function: {_text(item.get('function'))}" if _text(item.get("function")) else "",
                    f"owner/source: {_text(item.get('owner_source'))}" if _text(item.get("owner_source")) else "",
                    f"trigger/formation: {_text(item.get('trigger_formation'))}"
                    if _text(item.get("trigger_formation"))
                    else "",
                    f"material/shape: {_text(item.get('material_shape'))}" if _text(item.get("material_shape")) else "",
                    f"path/layer: {_text(item.get('path_layer'))}" if _text(item.get("path_layer")) else "",
                    f"operation/contact: {_text(item.get('operation_contact'))}"
                    if _text(item.get("operation_contact"))
                    else "",
                    f"response: {_text(item.get('receiver_environment_response'))}"
                    if _text(item.get("receiver_environment_response"))
                    else "",
                    f"intensity: {_text(item.get('intensity'))}" if _text(item.get("intensity")) else "",
                    f"decay/residue: {_text(item.get('decay_residue'))}" if _text(item.get("decay_residue")) else "",
                ]
            )
        )
    return result


def _color_line(spec: dict[str, Any]) -> str:
    section = spec.get("color") if isinstance(spec.get("color"), dict) else {}
    palette = _items(section.get("palette"))
    return _join(
        [
            f"palette: {', '.join(palette)}" if palette else "",
            f"grade: {_text(section.get('grade'))}" if _text(section.get("grade")) else "",
            f"contrast: {_text(section.get('contrast'))}" if _text(section.get("contrast")) else "",
            f"saturation: {_text(section.get('saturation'))}" if _text(section.get("saturation")) else "",
        ]
    )


def _optics_line(spec: dict[str, Any]) -> str:
    section = spec.get("optics") if isinstance(spec.get("optics"), dict) else {}
    artifacts = _items(section.get("artifacts"))
    return _join(
        [
            f"depth of field: {_text(section.get('depth_of_field'))}" if _text(section.get("depth_of_field")) else "",
            f"focus: {_text(section.get('focus_target'))}" if _text(section.get("focus_target")) else "",
            f"motion: {_text(section.get('motion_blur'))}" if _text(section.get("motion_blur")) else "",
            f"lens character: {_text(section.get('lens_character'))}" if _text(section.get("lens_character")) else "",
            f"artifacts: {', '.join(artifacts)}" if artifacts else "",
        ]
    )


def _style_line(spec: dict[str, Any]) -> str:
    section = spec.get("style") if isinstance(spec.get("style"), dict) else {}
    traits = _items(section.get("visual_traits"))
    references = _items(section.get("references"))
    return _join(
        [
            _text(section.get("medium")),
            _text(section.get("realism")),
            _text(section.get("era")),
            ", ".join(traits),
            f"references: {', '.join(references)}" if references else "",
        ]
    )


def _input_lines(spec: dict[str, Any]) -> list[str]:
    inputs = spec.get("inputs") if isinstance(spec.get("inputs"), list) else []
    result: list[str] = []
    for index, item in enumerate(inputs, start=1):
        if not isinstance(item, dict):
            continue
        result.append(
            _join(
                [
                    f"Image {index} ({_text(item.get('id'))})" if _text(item.get("id")) else f"Image {index}",
                    f"role: {_text(item.get('role'))}" if _text(item.get("role")) else "",
                    _text(item.get("description")),
                ]
            )
        )
    return result


def _knowledge_anchor_lines(spec: dict[str, Any], *, model_knowledge_hint: bool = False) -> list[str]:
    anchors = spec.get("knowledge_anchors") if isinstance(spec.get("knowledge_anchors"), list) else []
    result: list[str] = []
    for item in anchors:
        if not isinstance(item, dict) or not _text(item.get("name")):
            continue
        strategy = item.get("strategy", "auto")
        reference_ids = _items(item.get("reference_ids"))
        if strategy == "auto":
            strategy = "hybrid" if reference_ids else "model_knowledge"
        if strategy == "reference":
            grounding = "ground canonical identity and appearance in the referenced inputs"
        elif strategy == "hybrid":
            grounding = (
                "combine existing model knowledge with the referenced inputs"
                if model_knowledge_hint
                else "combine the exact named entity with the referenced inputs"
            )
        else:
            grounding = (
                "use existing model knowledge of this exact named entity"
                if model_knowledge_hint
                else "preserve this exact named entity and canonical context"
            )
        result.append(
            _join(
                [
                    _text(item.get("name")),
                    f"canonical context: {_text(item.get('context'))}" if _text(item.get("context")) else "",
                    grounding,
                    f"reference inputs: {', '.join(reference_ids)}" if reference_ids else "",
                ]
            )
        )
    return result


def _render_line(spec: dict[str, Any]) -> str:
    render = spec.get("render") if isinstance(spec.get("render"), dict) else {}
    priorities = _items(render.get("detail_priority"))
    quality_controls = _items(render.get("quality_controls"))
    artifact_budget = _text(render.get("artifact_budget"))
    return _join(
        [
            f"quality intent: {_text(render.get('quality'))}" if _text(render.get("quality")) else "",
            f"detail priorities: {', '.join(priorities)}" if priorities else "",
            f"artifact budget ({artifact_budget}): {ARTIFACT_PRESETS[artifact_budget]}"
            if artifact_budget in ARTIFACT_PRESETS
            else "",
            f"shot-specific quality controls: {', '.join(quality_controls)}" if quality_controls else "",
        ]
    )


def _styleboard_lines(spec: dict[str, Any]) -> list[str]:
    board = spec.get("styleboard") if isinstance(spec.get("styleboard"), dict) else {}
    if not board:
        return []
    result = [
        _join(
            [
                f"layout: {_text(board.get('layout'))}" if _text(board.get("layout")) else "",
                f"frame count: {board.get('frame_count')}" if isinstance(board.get("frame_count"), int) else "",
                f"frame ratio: {_text(board.get('frame_aspect_ratio'))}"
                if _text(board.get("frame_aspect_ratio"))
                else "",
                f"presentation: {_text(board.get('presentation'))}" if _text(board.get("presentation")) else "",
                f"generation strategy: {_text(board.get('generation_strategy'))}"
                if _text(board.get("generation_strategy"))
                else "",
                f"reading order: {_text(board.get('reading_order'))}" if _text(board.get("reading_order")) else "",
                f"continuity locks: {', '.join(_items(board.get('continuity_locks')))}"
                if _items(board.get("continuity_locks"))
                else "",
                f"allowed variation: {', '.join(_items(board.get('allowed_variation')))}"
                if _items(board.get("allowed_variation"))
                else "",
            ]
        )
    ]
    assignments = board.get("reference_assignments") if isinstance(board.get("reference_assignments"), list) else []
    for item in assignments:
        if isinstance(item, dict):
            result.append(
                _join(
                    [
                        f"reference {_text(item.get('input_id'))}",
                        f"role: {_text(item.get('role'))}",
                        f"secondary roles: {', '.join(_items(item.get('secondary_roles')))}"
                        if _items(item.get("secondary_roles"))
                        else "",
                        f"use: {_text(item.get('use'))}",
                        f"ignore: {_text(item.get('ignore'))}",
                    ]
                )
            )
    frames = board.get("frames") if isinstance(board.get("frames"), list) else []
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        focal = frame.get("focal_length_mm")
        result.append(
            _join(
                [
                    f"frame {_text(frame.get('id'))}",
                    f"function: {_text(frame.get('shot_function'))}",
                    f"story: {_text(frame.get('story_moment'))}",
                    f"action: {_text(frame.get('primary_action'))}",
                    f"phase: {_text(frame.get('action_phase'))}",
                    f"shot: {_text(frame.get('shot_size'))}",
                    f"camera height: {_text(frame.get('camera_height'))}",
                    f"{focal:g}mm" if isinstance(focal, (int, float)) else "",
                    f"composition: {_text(frame.get('composition'))}",
                    f"reference inputs: {', '.join(_items(frame.get('reference_ids')))}"
                    if _items(frame.get("reference_ids"))
                    else "",
                ]
            )
        )
    return result


def _styleboard_warning(spec: dict[str, Any]) -> str | None:
    if spec.get("mode") != "styleboard":
        return None
    board = spec.get("styleboard") if isinstance(spec.get("styleboard"), dict) else {}
    strategy = board.get("generation_strategy", "auto")
    if strategy == "sheet_direct":
        return "Direct sheet generation is fastest; verify panel ratio, identity, continuity, and crop geometry before final use."
    if strategy == "independent_frames":
        return "Generate native-ratio frames independently, review them, then assemble the approved board."
    if strategy == "hybrid":
        return "Generate a direct sheet for rapid exploration, then regenerate only selected or failed frames independently before final assembly."
    return "Choose direct-sheet, independent-frame, or hybrid execution from the board's speed and continuity risk."


def _text_lines(spec: dict[str, Any]) -> list[str]:
    elements = spec.get("text_elements") if isinstance(spec.get("text_elements"), list) else []
    result: list[str] = []
    for item in elements:
        if not isinstance(item, dict) or not _text(item.get("content")):
            continue
        result.append(
            _join(
                [
                    f'"{_text(item.get("content"))}" exactly',
                    _text(item.get("placement")),
                    _text(item.get("typography")),
                    _text(item.get("color")),
                    "preserve exact case" if item.get("case_sensitive") else "",
                ]
            )
        )
    return result


def _edit_lines(spec: dict[str, Any]) -> list[str]:
    edits = spec.get("spatial_edits") if isinstance(spec.get("spatial_edits"), list) else []
    result: list[str] = []
    for edit in edits:
        if not isinstance(edit, dict):
            continue
        bits = [_text(edit.get("instruction"))]
        point = edit.get("point")
        if isinstance(point, dict):
            bits.append(f"anchor: {point.get('x_percent'):g}% from left, {point.get('y_percent'):g}% from top")
        if isinstance(edit.get("region"), dict):
            bits.append("approximate region: " + _format_region(edit["region"]))
        if edit.get("preserve_surroundings"):
            bits.append("preserve the surroundings")
        result.append(_join(bits))
    return result


def _constraints(spec: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    section = spec.get("constraints") if isinstance(spec.get("constraints"), dict) else {}
    style = spec.get("style") if isinstance(spec.get("style"), dict) else {}
    exclusions = _items(section.get("exclude")) + _items(style.get("excluded_traits"))
    exclusions = list(dict.fromkeys(exclusions))
    return (
        _items(section.get("must_preserve")),
        _items(section.get("must_change")),
        exclusions,
    )


def _common_sections(spec: dict[str, Any], *, model_knowledge_hint: bool = False) -> dict[str, Any]:
    subjects = spec.get("subjects") if isinstance(spec.get("subjects"), list) else []
    return {
        "knowledge_anchors": _knowledge_anchor_lines(spec, model_knowledge_hint=model_knowledge_hint),
        "goal": _text(spec.get("intent")),
        "direction": _direction_line(spec),
        "cinematic": _cinematic_line(spec),
        "inputs": _input_lines(spec),
        "scene": _scene_line(spec),
        "subjects": [_subject_line(item) for item in subjects if isinstance(item, dict)],
        "staging": _staging_line(spec),
        "composition": _composition_line(spec),
        "lighting": _lighting_line(spec),
        "materials": _materials_line(spec),
        "effects": _effect_lines(spec),
        "color": _color_line(spec),
        "optics": _optics_line(spec),
        "style": _style_line(spec),
        "render": _render_line(spec),
        "text": _text_lines(spec),
        "edits": _edit_lines(spec),
        "styleboard": _styleboard_lines(spec),
    }


def _labeled_prompt(sections: dict[str, Any], preserve: list[str], change: list[str], exclude: list[str]) -> str:
    labels = [
        ("Canonical knowledge anchors", "\n".join(f"- {item}" for item in sections["knowledge_anchors"])),
        ("Goal", sections["goal"]),
        ("Visual direction", sections["direction"]),
        ("Cinematic shot contract", sections["cinematic"]),
        ("Inputs", "\n".join(f"- {item}" for item in sections["inputs"])),
        ("Scene", sections["scene"]),
        ("Subjects", "\n".join(f"- {item}" for item in sections["subjects"] if item)),
        ("Staging and relationship geometry", sections["staging"]),
        ("Composition", sections["composition"]),
        ("Lighting", sections["lighting"]),
        ("Materials", sections["materials"]),
        ("Causal effects", "\n".join(f"- {item}" for item in sections["effects"])),
        ("Color", sections["color"]),
        ("Optics", sections["optics"]),
        ("Style", sections["style"]),
        ("Render intent", sections["render"]),
        ("Exact visible text", "\n".join(f"- {item}" for item in sections["text"])),
        ("Edit", "\n".join(f"- Change only: {item}" for item in sections["edits"])),
        ("Required changes", "\n".join(f"- {item}" for item in change)),
        ("Styleboard package", "\n".join(f"- {item}" for item in sections["styleboard"])),
        ("Preserve", "\n".join(f"- {item}" for item in preserve)),
        ("Constraints", "\n".join(f"- Do not add or show: {item}" for item in exclude)),
    ]
    return "\n\n".join(f"{label}:\n{value}" for label, value in labels if value)


def _canvas_size(spec: dict[str, Any]) -> str | None:
    canvas = spec.get("canvas") if isinstance(spec.get("canvas"), dict) else {}
    dimensions = canvas.get("dimensions") if isinstance(canvas.get("dimensions"), dict) else {}
    width, height = dimensions.get("width"), dimensions.get("height")
    if isinstance(width, int) and isinstance(height, int):
        return f"{width}x{height}"
    return None


def compile_openai(spec: dict[str, Any]) -> dict[str, Any]:
    sections = _common_sections(spec, model_knowledge_hint=True)
    preserve, change, exclude = _constraints(spec)
    options = spec.get("platform_options", {}).get("openai", {})
    options = options if isinstance(options, dict) else {}
    parameters = {
        "model": options.get("model", "gpt-image-2"),
        "quality": options.get("quality", "medium"),
        "size": options.get("size") or _canvas_size(spec),
    }
    warnings = []
    anchors = spec.get("knowledge_anchors") if isinstance(spec.get("knowledge_anchors"), list) else []
    if any(isinstance(item, dict) and item.get("verification", "unverified") == "unverified" for item in anchors):
        warnings.append("Named-entity accuracy relies on model knowledge and must be visually verified against a trusted reference or by the user.")
    styleboard_warning = _styleboard_warning(spec)
    if styleboard_warning:
        warnings.append(styleboard_warning)
    return {
        "platform": "openai",
        "prompt": _labeled_prompt(sections, preserve, change, exclude),
        "negative_prompt": "",
        "parameters": {key: value for key, value in parameters.items() if value is not None},
        "warnings": warnings,
        "language": spec.get("language", "en"),
        "source_spec_version": spec.get("visual_generation_spec"),
    }


def _flux_positive_constraint(item: str) -> str | None:
    mappings = {
        "no blur": "sharp focus throughout",
        "no people": "an empty environment",
        "plastic cgi sheen": "physically plausible materials with natural surface variation",
        "new text": "only the specified literal text appears",
        "watermark": "clean image containing only the requested visual content",
        "logo": "unbranded scene containing only the requested visual content",
    }
    return mappings.get(item.lower().strip())


def compile_flux(spec: dict[str, Any]) -> dict[str, Any]:
    sections = _common_sections(spec)
    preserve, change, exclude = _constraints(spec)
    options = spec.get("platform_options", {}).get("flux", {})
    options = options if isinstance(options, dict) else {}
    positive_constraints: list[str] = []
    unconverted: list[str] = []
    for item in exclude:
        converted = _flux_positive_constraint(item)
        if converted and converted not in positive_constraints:
            positive_constraints.append(converted)
        else:
            unconverted.append(item)

    if options.get("prompt_format", "natural_language") == "json":
        payload = {
            "knowledge_anchors": sections["knowledge_anchors"],
            "goal": sections["goal"],
            "visual_direction": sections["direction"],
            "cinematic_shot_contract": sections["cinematic"],
            "inputs": sections["inputs"],
            "scene": sections["scene"],
            "subjects": sections["subjects"],
            "staging": sections["staging"],
            "composition": sections["composition"],
            "lighting": sections["lighting"],
            "materials": sections["materials"],
            "causal_effects": sections["effects"],
            "color": sections["color"],
            "optics": sections["optics"],
            "style": sections["style"],
            "render_intent": sections["render"],
            "exact_visible_text": sections["text"],
            "requested_edits": sections["edits"],
            "must_preserve": preserve,
            "must_change": change,
            "desired_state_constraints": positive_constraints,
            "styleboard_package": sections["styleboard"],
        }
        prompt = json.dumps({key: value for key, value in payload.items() if value}, ensure_ascii=False, indent=2)
    else:
        ordered = [
            "Canonical knowledge anchors: " + "; ".join(sections["knowledge_anchors"]) if sections["knowledge_anchors"] else "",
            sections["goal"],
            sections["direction"],
            sections["cinematic"],
            "Inputs: " + "; ".join(sections["inputs"]) if sections["inputs"] else "",
            sections["scene"],
            " ".join(sections["subjects"]),
            sections["staging"],
            sections["composition"],
            sections["lighting"],
            sections["materials"],
            "Causal effects: " + "; ".join(sections["effects"]) if sections["effects"] else "",
            sections["color"],
            sections["optics"],
            sections["style"],
            sections["render"],
            "Exact visible text: " + "; ".join(sections["text"]) if sections["text"] else "",
            "Requested edit: " + "; ".join(sections["edits"]) if sections["edits"] else "",
            "Preserve: " + "; ".join(preserve) if preserve else "",
            "Required changes: " + "; ".join(change) if change else "",
            "Desired visible state: " + "; ".join(positive_constraints) if positive_constraints else "",
            "Styleboard package: " + "; ".join(sections["styleboard"]) if sections["styleboard"] else "",
        ]
        prompt = ". ".join(part.rstrip(". ") for part in ordered if part) + "."

    warnings = []
    if exclude:
        warnings.append("FLUX.2 has no negative-prompt channel; exclusions were converted to positive targets when possible.")
    if unconverted:
        warnings.append("Review unconverted exclusions manually: " + "; ".join(unconverted))
    if spec.get("mode") in {"edit", "restyle", "expand"}:
        warnings.append("Reference images or masks must be supplied separately at execution time.")
    styleboard_warning = _styleboard_warning(spec)
    if styleboard_warning:
        warnings.append(styleboard_warning)
    return {
        "platform": "flux",
        "prompt": prompt,
        "negative_prompt": "",
        "parameters": {
            "model_family": options.get("model_family", "FLUX.2"),
            "prompt_upsampling": bool(options.get("prompt_upsampling", False)),
        },
        "warnings": warnings,
        "language": spec.get("language", "en"),
        "source_spec_version": spec.get("visual_generation_spec"),
    }


def _midjourney_style_refs(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
        elif isinstance(item, dict):
            url = _text(item.get("url"))
            weight = item.get("weight")
            if url:
                result.append(f"{url}::{weight:g}" if isinstance(weight, (int, float)) else url)
    return result


def compile_midjourney(spec: dict[str, Any]) -> dict[str, Any]:
    sections = _common_sections(spec)
    preserve, change, exclude = _constraints(spec)
    options = spec.get("platform_options", {}).get("midjourney", {})
    options = options if isinstance(options, dict) else {}
    content_parts = [
        " ".join(sections["knowledge_anchors"]), sections["goal"], sections["direction"], sections["cinematic"],
        " ".join(sections["inputs"]), sections["scene"], " ".join(sections["subjects"]), sections["staging"],
        sections["composition"], sections["lighting"], sections["materials"],
        " ".join(sections["effects"]), sections["color"], sections["optics"], sections["style"], sections["render"],
        "exact visible text " + "; ".join(sections["text"]) if sections["text"] else "",
        " ".join(sections["edits"]),
        "preserve " + "; ".join(preserve) if preserve else "",
        "required change " + "; ".join(change) if change else "",
        " ".join(sections["styleboard"]),
    ]
    content = ", ".join(part.strip(" ,.") for part in content_parts if part)

    canvas = spec.get("canvas") if isinstance(spec.get("canvas"), dict) else {}
    flags: list[str] = []
    aspect = options.get("aspect_ratio") or canvas.get("aspect_ratio")
    if aspect:
        flags.extend(["--ar", str(aspect)])
    if options.get("stylize") is not None:
        flags.extend(["--s", str(options["stylize"])])
    if options.get("chaos") is not None:
        flags.extend(["--c", str(options["chaos"])])
    if options.get("quality") is not None:
        flags.extend(["--q", str(options["quality"])])
    if options.get("raw"):
        flags.append("--raw")
    if options.get("seed") is not None:
        flags.extend(["--seed", str(options["seed"])])
    if options.get("version") is not None:
        flags.extend(["--v", str(options["version"])])
    style_refs = _midjourney_style_refs(options.get("style_reference"))
    if style_refs:
        flags.extend(["--sref", *style_refs])
        if options.get("style_weight") is not None:
            flags.extend(["--sw", str(options["style_weight"])])
    if exclude:
        flags.extend(["--no", ", ".join(exclude)])

    warnings = []
    if spec.get("mode") in {"edit", "restyle", "expand"} or sections["edits"]:
        warnings.append("Prompt coordinates are semantic anchors, not pixel-accurate edit masks; use an editor region or mask for surgical changes.")
    if preserve:
        warnings.append("Prompt-only preservation constraints are best-effort and should be visually verified.")
    if any(" " in item.strip() for item in exclude):
        warnings.append("Midjourney --no handling for multi-word exclusions is best-effort; visually verify each excluded concept.")
    if options.get("quality") is not None and options.get("version") is None:
        warnings.append("Midjourney quality values are version-specific; verify --q against the active model version.")
    styleboard_warning = _styleboard_warning(spec)
    if styleboard_warning:
        warnings.append(styleboard_warning)
    return {
        "platform": "midjourney",
        "prompt": content + (" " + " ".join(flags) if flags else ""),
        "negative_prompt": "",
        "parameters": {"flags": flags},
        "warnings": warnings,
        "language": spec.get("language", "en"),
        "source_spec_version": spec.get("visual_generation_spec"),
    }


def compile_generic(spec: dict[str, Any]) -> dict[str, Any]:
    sections = _common_sections(spec)
    preserve, change, exclude = _constraints(spec)
    warnings = ["Provider-specific syntax and parameter support are unverified."]
    styleboard_warning = _styleboard_warning(spec)
    if styleboard_warning:
        warnings.append(styleboard_warning)
    return {
        "platform": "generic",
        "prompt": _labeled_prompt(sections, preserve, change, []),
        "negative_prompt": ", ".join(exclude),
        "parameters": {},
        "warnings": warnings,
        "language": spec.get("language", "en"),
        "source_spec_version": spec.get("visual_generation_spec"),
    }


def compile_spec(spec: dict[str, Any], platform: str | None = None) -> dict[str, Any]:
    target = platform or spec.get("platform", "auto")
    if target == "auto":
        target = "generic"
    if target not in SUPPORTED_PLATFORMS:
        raise ValueError(f"unsupported platform: {target}")
    return {
        "openai": compile_openai,
        "flux": compile_flux,
        "midjourney": compile_midjourney,
        "generic": compile_generic,
    }[target](spec)


def _format_text(result: dict[str, Any]) -> str:
    parts = [f"PLATFORM\n{result['platform']}", f"PROMPT\n{result['prompt']}"]
    if result.get("negative_prompt"):
        parts.append(f"NEGATIVE PROMPT\n{result['negative_prompt']}")
    parts.append("PARAMETERS\n" + json.dumps(result.get("parameters", {}), ensure_ascii=False, indent=2))
    if result.get("warnings"):
        parts.append("WARNINGS\n" + "\n".join(f"- {item}" for item in result["warnings"]))
    return "\n\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to a visual specification JSON file")
    parser.add_argument("--platform", choices=sorted(SUPPORTED_PLATFORMS), help="Override the platform in the spec")
    parser.add_argument("--format", choices=("json", "text"), default="json", dest="output_format")
    args = parser.parse_args()

    try:
        spec = load_json(args.spec)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_spec(spec)
    if errors:
        print("INVALID SPEC", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    result = compile_spec(spec, args.platform)
    print(_format_text(result) if args.output_format == "text" else json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
