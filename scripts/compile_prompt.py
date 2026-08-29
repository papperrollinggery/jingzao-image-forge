#!/usr/bin/env python3
"""Compile a visual specification into a platform-ready image prompt."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

try:
    from reference_delivery import (
        build_attachment_manifest,
        build_imagegen_call_plan,
        build_reference_handoff,
        reference_delivery_warnings,
    )
    from validate_spec import load_json, validate_spec
    from validate_style_capsule import (
        lint_style_capsule_content,
        validate_style_capsule,
    )
except ModuleNotFoundError:  # Support `python -m scripts.compile_prompt` from the repository root.
    from scripts.reference_delivery import (
        build_attachment_manifest,
        build_imagegen_call_plan,
        build_reference_handoff,
        reference_delivery_warnings,
    )
    from scripts.validate_spec import load_json, validate_spec
    from scripts.validate_style_capsule import (
        lint_style_capsule_content,
        validate_style_capsule,
    )


SUPPORTED_PLATFORMS = {"openai", "flux", "midjourney", "generic"}
PROMPT_TARGET_WORDS = {"openai": 1300, "flux": 1000, "midjourney": 500, "generic": 1600}
CONTEXT_RESIDUE_MARKERS = (
    "same as the previous version",
    "different from the previous version",
    "continue to keep",
    "the image above",
    "上一版",
    "之前那版",
    "上一个画面",
    "继续保持",
)
TEMPLATE_PLACEHOLDERS = {
    "Describe the intended image and its use.",
    "Describe the overall scene.",
    "Describe the environment.",
    "Describe time or period when relevant.",
    "Describe the primary subject.",
    "Describe the action.",
    "Describe the pose when relevant.",
    "Describe gaze when relevant.",
    "Describe relative scale.",
    "Describe the visual hierarchy and crop.",
    "Describe intentional negative space.",
    "Describe the lighting system.",
    "Describe the requested visual medium without changing it implicitly.",
    "Describe the requested realism or stylization.",
}
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
    "clean_reset": (
        "clean-slate surface rebuild; 3-7 dominant low-frequency shape groups; one or two camera-readable focal-detail "
        "clusters; at least one continuous calm surface; texture only where camera scale and named light reveal it; "
        "background edge frequency and microtexture below the focal zone; material classes separated by roughness, "
        "highlight width, reflection, translucency, and edge response; strict wet/dry and matte/gloss boundaries; "
        "localized contact shadows only at real seams, overlaps, and support points; clean low-noise gradients; "
        "protected highlight texture with smooth rolloff; readable shadow floor"
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
    text = value.strip() if isinstance(value, str) else ""
    return "" if text in TEMPLATE_PLACEHOLDERS else text


def _explicit(value: Any) -> str:
    text = _text(value)
    return text if text not in {"", "auto", "custom"} else ""


def _items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _join(parts: Iterable[str], separator: str = "; ") -> str:
    return separator.join(part for part in parts if part)


def _clean_json_prompt_value(value: Any) -> Any:
    if isinstance(value, str):
        return value if value.strip() else None
    if isinstance(value, list):
        cleaned = [_clean_json_prompt_value(item) for item in value]
        cleaned = [item for item in cleaned if item is not None]
        return cleaned or None
    if isinstance(value, dict):
        cleaned = {key: item for key, raw in value.items() if (item := _clean_json_prompt_value(raw)) is not None}
        return cleaned or None
    return value


def _reviewable_source_strings(value: Any, path: tuple[str | int, ...] = ()) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for index, item in enumerate(value):
            result.extend(_reviewable_source_strings(item, (*path, index)))
        return result
    if isinstance(value, dict):
        result = []
        for key, item in value.items():
            next_path = (*path, key)
            if len(next_path) >= 3 and next_path[0] == "text_elements" and next_path[-1] == "content":
                continue
            result.extend(_reviewable_source_strings(item, next_path))
        return result
    return []


def context_residue_hits_from_sources(
    spec: dict[str, Any],
    style_capsule: dict[str, Any] | None = None,
) -> list[str]:
    review_strings = _reviewable_source_strings(spec)
    if isinstance(style_capsule, dict):
        review_strings.extend(
            _reviewable_source_strings(
                {
                    "id": style_capsule.get("id"),
                    "name": style_capsule.get("name"),
                    "visual_rules": style_capsule.get("visual_rules"),
                    "transfer_rules": style_capsule.get("transfer_rules"),
                    "forbidden_transfer": style_capsule.get("forbidden_transfer"),
                }
            )
        )
    scan = "\n".join(review_strings).lower()
    return [marker for marker in CONTEXT_RESIDUE_MARKERS if marker.lower() in scan]


def _prompt_metrics(prompt: str) -> dict[str, int]:
    return {
        "characters": len(prompt),
        "words": len(prompt.split()),
        "lines": prompt.count("\n") + 1 if prompt else 0,
    }


def _platform_options(spec: dict[str, Any], key: str) -> dict[str, Any]:
    all_options = spec.get("platform_options")
    options = all_options.get(key) if isinstance(all_options, dict) else None
    return options if isinstance(options, dict) else {}


def _sanitize_midjourney_text(value: str) -> str:
    return " ".join(value.replace("--", "—").replace("::", ": :").split())


def _learn_style_warning(spec: dict[str, Any]) -> str | None:
    if spec.get("mode") != "learn_style":
        return None
    return (
        "Analysis record only: the deliverable is a validated style_capsule. "
        "Do not submit this compiled prompt for image generation."
    )


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
            f"deliverable: {_explicit(section.get('deliverable'))}" if _explicit(section.get("deliverable")) else "",
            f"treatment: {_explicit(section.get('treatment'))}" if _explicit(section.get("treatment")) else "",
            f"spectacle scale: {_explicit(section.get('spectacle_scale'))}"
            if _explicit(section.get("spectacle_scale"))
            else "",
            f"camera freedom: {_explicit(section.get('camera_freedom'))}"
            if _explicit(section.get("camera_freedom"))
            else "",
            f"genre: {_text(section.get('genre'))}" if _text(section.get("genre")) else "",
            f"world rule: {_text(section.get('world_rule'))}" if _text(section.get("world_rule")) else "",
            f"visual goal: {_text(section.get('visual_goal'))}" if _text(section.get("visual_goal")) else "",
        ]
    )


def _creative_routing_line(spec: dict[str, Any]) -> str:
    section = spec.get("creative_routing") if isinstance(spec.get("creative_routing"), dict) else {}
    scene_archetypes = _items(section.get("scene_archetypes"))
    forbidden_drift = _items(section.get("forbidden_drift"))
    tone_locks = _items(section.get("tone_locks"))

    def routed_value(key: str, custom_key: str) -> str:
        value = _text(section.get(key))
        if value == "custom":
            return _text(section.get(custom_key))
        return _explicit(value)

    return _join(
        [
            f"scenario profile: {routed_value('scenario_profile', 'custom_scenario')}"
            if routed_value("scenario_profile", "custom_scenario")
            else "",
            f"genre family: {routed_value('genre_family', 'custom_genre')}"
            if routed_value("genre_family", "custom_genre")
            else "",
            f"primary aesthetic: {routed_value('aesthetic_family', 'custom_aesthetic')}"
            if routed_value("aesthetic_family", "custom_aesthetic")
            else "",
            f"capture or render method: {routed_value('capture_or_render_method', 'custom_method')}"
            if routed_value("capture_or_render_method", "custom_method")
            else "",
            f"scene archetypes: {', '.join(scene_archetypes)}" if scene_archetypes else "",
            f"audience effect: {_text(section.get('audience_effect'))}"
            if _text(section.get("audience_effect"))
            else "",
            f"delivery context: {_text(section.get('delivery_context'))}"
            if _text(section.get("delivery_context"))
            else "",
            f"design priority: {_text(section.get('design_priority'))}"
            if _text(section.get("design_priority"))
            else "",
            f"cultural context: {_text(section.get('cultural_context'))}"
            if _text(section.get("cultural_context"))
            else "",
            f"secondary influence: {_text(section.get('secondary_influence'))}"
            if _text(section.get("secondary_influence"))
            else "",
            f"mix rule: {_text(section.get('mix_rule'))}" if _text(section.get("mix_rule")) else "",
            f"style authority: {_explicit(section.get('style_authority'))}"
            if _explicit(section.get("style_authority"))
            else "",
            f"adaptation rule: {_text(section.get('adaptation_rule'))}"
            if _text(section.get("adaptation_rule"))
            else "",
            f"tone locks: {', '.join(tone_locks)}" if tone_locks else "",
            f"forbidden drift: {', '.join(forbidden_drift)}" if forbidden_drift else "",
        ]
    )


def _style_learning_line(spec: dict[str, Any]) -> str:
    section = spec.get("style_learning") if isinstance(spec.get("style_learning"), dict) else {}
    observed = section.get("observed") if isinstance(section.get("observed"), dict) else {}
    return _join(
        [
            f"profile: {_text(section.get('profile_name'))} ({_text(section.get('profile_id'))})"
            if _text(section.get("profile_name"))
            else "",
            f"status: {_text(section.get('status'))}" if _text(section.get("status")) else "",
            f"medium behavior: {_text(observed.get('medium_behavior'))}"
            if _text(observed.get("medium_behavior"))
            else "",
            f"palette logic: {', '.join(_items(observed.get('palette_logic')))}"
            if _items(observed.get("palette_logic"))
            else "",
            f"shape and line: {_text(observed.get('shape_line_language'))}"
            if _text(observed.get("shape_line_language"))
            else "",
            f"texture and material: {', '.join(_items(observed.get('texture_material_logic')))}"
            if _items(observed.get("texture_material_logic"))
            else "",
            f"lighting: {_text(observed.get('lighting_logic'))}" if _text(observed.get("lighting_logic")) else "",
            f"composition: {', '.join(_items(observed.get('composition_logic')))}"
            if _items(observed.get("composition_logic"))
            else "",
            f"optics and rendering: {_text(observed.get('optics_rendering_logic'))}"
            if _text(observed.get("optics_rendering_logic"))
            else "",
            f"transfer rules: {', '.join(_items(section.get('transfer_rules')))}"
            if _items(section.get("transfer_rules"))
            else "",
            f"forbidden transfer: {', '.join(_items(section.get('forbidden_transfer')))}"
            if _items(section.get("forbidden_transfer"))
            else "",
        ]
    )


def _reference_analysis_line(spec: dict[str, Any]) -> str:
    section = spec.get("reference_analysis") if isinstance(spec.get("reference_analysis"), dict) else {}
    observed = _items(section.get("observed"))
    inferred = _items(section.get("inferred"))
    unknowns = _items(section.get("unknowns"))
    return _join(
        [
            f"reconstruction target: {_text(section.get('target'))}" if _text(section.get("target")) else "",
            f"observed facts: {', '.join(observed)}" if observed else "",
            f"inferred and unverified: {', '.join(inferred)}" if inferred else "",
            f"unknowns: {', '.join(unknowns)}" if unknowns else "",
        ]
    )


def _style_capsule_line(capsule: dict[str, Any] | None) -> str:
    if not isinstance(capsule, dict):
        return ""
    rules = capsule.get("visual_rules") if isinstance(capsule.get("visual_rules"), dict) else {}
    return _join(
        [
            f"style capsule: {_text(capsule.get('name'))} ({_text(capsule.get('id'))})",
            "target specification remains authoritative for subject, scene, layout, text, and production method",
            f"surface influence: {_text(rules.get('medium_behavior'))}" if _text(rules.get("medium_behavior")) else "",
            f"palette logic: {', '.join(_items(rules.get('palette_logic')))}"
            if _items(rules.get("palette_logic"))
            else "",
            f"shape and line: {_text(rules.get('shape_line_language'))}"
            if _text(rules.get("shape_line_language"))
            else "",
            f"texture and material: {', '.join(_items(rules.get('texture_material_logic')))}"
            if _items(rules.get("texture_material_logic"))
            else "",
            f"lighting: {_text(rules.get('lighting_logic'))}" if _text(rules.get("lighting_logic")) else "",
            f"adaptable composition tendencies: {', '.join(_items(rules.get('composition_logic')))}"
            if _items(rules.get("composition_logic"))
            else "",
            f"typography when the target contains text: {', '.join(_items(rules.get('typography_logic')))}"
            if _items(rules.get("typography_logic"))
            else "",
            f"optics and rendering: {_text(rules.get('optics_rendering_logic'))}"
            if _text(rules.get("optics_rendering_logic"))
            else "",
            f"optional motifs, use only when semantically relevant: {', '.join(_items(rules.get('motifs')))}"
            if _items(rules.get("motifs"))
            else "",
            f"transfer rules: {', '.join(_items(capsule.get('transfer_rules')))}"
            if _items(capsule.get("transfer_rules"))
            else "",
            f"forbidden transfer: {', '.join(_items(capsule.get('forbidden_transfer')))}"
            if _items(capsule.get("forbidden_transfer"))
            else "",
        ]
    )


def _cinematic_line(spec: dict[str, Any]) -> str:
    section = spec.get("cinematic") if isinstance(spec.get("cinematic"), dict) else {}
    return _join(
        [
            f"profile: {_explicit(section.get('profile'))}" if _explicit(section.get("profile")) else "",
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


def _spatial_dynamics_line(spec: dict[str, Any]) -> str:
    section = spec.get("spatial_dynamics") if isinstance(spec.get("spatial_dynamics"), dict) else {}
    motion_evidence = _items(section.get("motion_evidence"))
    return _join(
        [
            f"dominant read: {_text(section.get('dominant_read'))}" if _text(section.get("dominant_read")) else "",
            f"secondary read: {_text(section.get('secondary_read'))}" if _text(section.get("secondary_read")) else "",
            f"beauty mechanism: {_text(section.get('beauty_mechanism'))}"
            if _text(section.get("beauty_mechanism"))
            else "",
            f"tension source: {_text(section.get('tension_source'))}" if _text(section.get("tension_source")) else "",
            f"exaggeration budget: {_explicit(section.get('exaggeration_budget'))}"
            if _explicit(section.get("exaggeration_budget"))
            else "",
            f"distortion strategy: {_explicit(section.get('distortion_strategy'))}"
            if _explicit(section.get("distortion_strategy"))
            else "",
            f"realism anchor: {_text(section.get('realism_anchor'))}" if _text(section.get("realism_anchor")) else "",
            f"action vector: {_text(section.get('action_vector'))}" if _text(section.get("action_vector")) else "",
            f"counterforce: {_text(section.get('counterforce'))}" if _text(section.get("counterforce")) else "",
            f"foreground role: {_text(section.get('foreground_role'))}"
            if _text(section.get("foreground_role"))
            else "",
            f"midground role: {_text(section.get('midground_role'))}"
            if _text(section.get("midground_role"))
            else "",
            f"background role: {_text(section.get('background_role'))}"
            if _text(section.get("background_role"))
            else "",
            f"depth transition: {_text(section.get('depth_transition'))}"
            if _text(section.get("depth_transition"))
            else "",
            f"parallax logic: {_text(section.get('parallax_logic'))}" if _text(section.get("parallax_logic")) else "",
            f"motion evidence: {', '.join(motion_evidence)}" if motion_evidence else "",
            f"readability guard: {_text(section.get('readability_guard'))}"
            if _text(section.get("readability_guard"))
            else "",
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
            f"camera pitch: {_text(section.get('camera_pitch'))}" if _text(section.get("camera_pitch")) else "",
            f"camera yaw: {_text(section.get('camera_yaw'))}" if _text(section.get("camera_yaw")) else "",
            f"camera roll: {_text(section.get('camera_roll'))}" if _text(section.get("camera_roll")) else "",
            f"lens projection: {_text(section.get('lens_projection'))}"
            if _text(section.get("lens_projection"))
            else "",
            f"perspective distortion: {_text(section.get('perspective_distortion'))}"
            if _text(section.get("perspective_distortion"))
            else "",
            f"edge behavior: {_text(section.get('edge_behavior'))}" if _text(section.get("edge_behavior")) else "",
            f"crop pressure: {_text(section.get('crop_pressure'))}" if _text(section.get("crop_pressure")) else "",
            f"camera state: {_text(section.get('camera_state'))}" if _text(section.get("camera_state")) else "",
            f"action readability: {_text(section.get('action_readability'))}"
            if _text(section.get("action_readability"))
            else "",
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
                f"microstructure: {_text(item.get('microstructure'))}" if _text(item.get("microstructure")) else "",
                f"roughness: {_text(item.get('roughness'))}" if _text(item.get("roughness")) else "",
                f"specular response: {_text(item.get('specular_response'))}"
                if _text(item.get("specular_response"))
                else "",
                f"transmission: {_text(item.get('transmission'))}" if _text(item.get("transmission")) else "",
                f"subsurface: {_text(item.get('subsurface_behavior'))}"
                if _text(item.get("subsurface_behavior"))
                else "",
                f"anisotropy: {_text(item.get('anisotropy'))}" if _text(item.get("anisotropy")) else "",
                f"wear/patina: {_text(item.get('wear_patina'))}" if _text(item.get("wear_patina")) else "",
                f"contact/deformation: {_text(item.get('contact_deformation'))}"
                if _text(item.get("contact_deformation"))
                else "",
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
                    f"resistance/cost: {_text(item.get('resistance_cost'))}"
                    if _text(item.get("resistance_cost"))
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
    has_pipeline = bool(_color_pipeline_line(spec))
    palette = _items(section.get("palette"))
    return _join(
        [
            f"palette: {', '.join(palette)}" if palette else "",
            f"grade: {_text(section.get('grade'))}"
            if not has_pipeline and _text(section.get("grade"))
            else "",
            f"contrast: {_text(section.get('contrast'))}"
            if not has_pipeline and _text(section.get("contrast"))
            else "",
            f"saturation: {_text(section.get('saturation'))}"
            if not has_pipeline and _text(section.get("saturation"))
            else "",
        ]
    )


def _color_pipeline_line(spec: dict[str, Any]) -> str:
    section = spec.get("color_pipeline") if isinstance(spec.get("color_pipeline"), dict) else {}
    film = section.get("film_emulation") if isinstance(section.get("film_emulation"), dict) else {}
    intent = _text(section.get("intent"))
    if intent == "custom":
        intent = _text(section.get("custom_intent"))
    else:
        intent = _explicit(intent)
    continuity_locks = _items(section.get("continuity_locks"))
    forbidden_casts = _items(section.get("forbidden_casts"))
    return _join(
        [
            f"intent: {intent}" if intent else "",
            f"color science: {_text(section.get('color_science'))}" if _text(section.get("color_science")) else "",
            f"display target: {_text(section.get('display_target'))}" if _text(section.get("display_target")) else "",
            f"exposure strategy: {_text(section.get('exposure_strategy'))}"
            if _text(section.get("exposure_strategy"))
            else "",
            f"tonal curve: {_text(section.get('tonal_curve'))}" if _text(section.get("tonal_curve")) else "",
            f"black point: {_text(section.get('black_point'))}" if _text(section.get("black_point")) else "",
            f"white point: {_text(section.get('white_point'))}" if _text(section.get("white_point")) else "",
            f"highlight rolloff: {_text(section.get('highlight_rolloff'))}"
            if _text(section.get("highlight_rolloff"))
            else "",
            f"shadow floor: {_text(section.get('shadow_floor'))}" if _text(section.get("shadow_floor")) else "",
            f"midtone density: {_text(section.get('midtone_density'))}"
            if _text(section.get("midtone_density"))
            else "",
            f"white balance: {_text(section.get('white_balance'))}" if _text(section.get("white_balance")) else "",
            f"color separation: {_text(section.get('color_separation'))}"
            if _text(section.get("color_separation"))
            else "",
            f"shadow bias: {_text(section.get('shadow_bias'))}" if _text(section.get("shadow_bias")) else "",
            f"midtone bias: {_text(section.get('midtone_bias'))}" if _text(section.get("midtone_bias")) else "",
            f"highlight bias: {_text(section.get('highlight_bias'))}" if _text(section.get("highlight_bias")) else "",
            f"skin-tone policy: {_text(section.get('skin_tone_policy'))}"
            if _text(section.get("skin_tone_policy"))
            else "",
            f"saturation policy: {_text(section.get('saturation_policy'))}"
            if _text(section.get("saturation_policy"))
            else "",
            f"gamut policy: {_text(section.get('gamut_policy'))}" if _text(section.get("gamut_policy")) else "",
            f"film negative/reversal character: {_text(film.get('negative_or_reversal_character'))}"
            if _text(film.get("negative_or_reversal_character"))
            else "",
            f"film print/display character: {_text(film.get('print_or_display_character'))}"
            if _text(film.get("print_or_display_character"))
            else "",
            f"grain: {_text(film.get('grain'))}" if _text(film.get("grain")) else "",
            f"halation: {_text(film.get('halation'))}" if _text(film.get("halation")) else "",
            f"bloom: {_text(film.get('bloom'))}" if _text(film.get("bloom")) else "",
            f"gate weave: {_text(film.get('gate_weave'))}" if _text(film.get("gate_weave")) else "",
            f"vignette: {_text(film.get('vignette'))}" if _text(film.get("vignette")) else "",
            f"shot matching: {_text(section.get('shot_matching'))}" if _text(section.get("shot_matching")) else "",
            f"continuity locks: {', '.join(continuity_locks)}" if continuity_locks else "",
            f"forbidden casts: {', '.join(forbidden_casts)}" if forbidden_casts else "",
        ]
    )


def _render_pipeline_line(spec: dict[str, Any]) -> str:
    section = spec.get("render_pipeline") if isinstance(spec.get("render_pipeline"), dict) else {}
    domain = _text(section.get("domain"))
    if domain == "custom":
        domain = _text(section.get("custom_domain"))
    else:
        domain = _explicit(domain)
    engine_reference = _text(section.get("engine_reference"))
    engine_scope = _text(section.get("engine_reference_scope"))
    render_passes = _items(section.get("render_passes"))
    forbidden_artifacts = _items(section.get("forbidden_artifacts"))
    return _join(
        [
            f"domain: {domain}" if domain else "",
            f"engine reference ({engine_scope.replace('_', ' ')} only): {engine_reference}"
            if engine_reference and engine_scope == "appearance_reference"
            else (f"actual pipeline: {engine_reference}" if engine_reference else ""),
            f"lighting transport: {_text(section.get('lighting_transport'))}"
            if _text(section.get("lighting_transport"))
            else "",
            f"global illumination: {_text(section.get('global_illumination'))}"
            if _text(section.get("global_illumination"))
            else "",
            f"ray tracing: {_text(section.get('ray_tracing'))}" if _text(section.get("ray_tracing")) else "",
            f"reflection model: {_text(section.get('reflection_model'))}"
            if _text(section.get("reflection_model"))
            else "",
            f"shadow model: {_text(section.get('shadow_model'))}" if _text(section.get("shadow_model")) else "",
            f"ambient occlusion: {_text(section.get('ambient_occlusion'))}"
            if _text(section.get("ambient_occlusion"))
            else "",
            f"volumetrics: {_text(section.get('volumetrics'))}" if _text(section.get("volumetrics")) else "",
            f"material workflow: {_text(section.get('material_workflow'))}"
            if _text(section.get("material_workflow"))
            else "",
            f"subsurface scattering: {_text(section.get('subsurface_scattering'))}"
            if _text(section.get("subsurface_scattering"))
            else "",
            f"transmission/refraction: {_text(section.get('transmission_refraction'))}"
            if _text(section.get("transmission_refraction"))
            else "",
            f"caustics: {_text(section.get('caustics'))}" if _text(section.get("caustics")) else "",
            f"displacement/normal: {_text(section.get('displacement_normal'))}"
            if _text(section.get("displacement_normal"))
            else "",
            f"texture scale: {_text(section.get('texture_scale'))}" if _text(section.get("texture_scale")) else "",
            f"sampling/denoise: {_text(section.get('sampling_denoise'))}"
            if _text(section.get("sampling_denoise"))
            else "",
            f"render passes: {', '.join(render_passes)}" if render_passes else "",
            f"performance/fidelity tradeoff: {_text(section.get('performance_fidelity_tradeoff'))}"
            if _text(section.get("performance_fidelity_tradeoff"))
            else "",
            f"NPR strategy: {_text(section.get('npr_strategy'))}" if _text(section.get("npr_strategy")) else "",
            f"forbidden render artifacts: {', '.join(forbidden_artifacts)}" if forbidden_artifacts else "",
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
    image_index = 0
    for item in inputs:
        if not isinstance(item, dict) or item.get("type") != "image":
            continue
        image_index += 1
        result.append(
            _join(
                [
                    f"Image {image_index} ({_text(item.get('id'))})"
                    if _text(item.get("id"))
                    else f"Image {image_index}",
                    f"role: {_text(item.get('role'))}" if _text(item.get("role")) else "",
                    _text(item.get("description")),
                    "actual image attachment required; description is not a substitute"
                    if item.get("must_attach") is True
                    else "",
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
        literal = json.dumps(_text(item.get("content")), ensure_ascii=False)
        result.append(
            _join(
                [
                    f"{literal} exactly",
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


def _common_sections(
    spec: dict[str, Any],
    *,
    platform: str,
    model_knowledge_hint: bool = False,
    style_capsule: dict[str, Any] | None = None,
) -> dict[str, Any]:
    subjects = spec.get("subjects") if isinstance(spec.get("subjects"), list) else []
    mode = spec.get("mode")
    sections = {
        "knowledge_anchors": _knowledge_anchor_lines(spec, model_knowledge_hint=model_knowledge_hint),
        "goal": _text(spec.get("intent")),
        "creative_routing": _creative_routing_line(spec),
        "reference_analysis": _reference_analysis_line(spec) if mode == "reconstruct" else "",
        "style_learning": _style_learning_line(spec) if mode == "learn_style" else "",
        "learned_style_capsule": _style_capsule_line(style_capsule) if mode != "learn_style" else "",
        "direction": _direction_line(spec),
        "cinematic": _cinematic_line(spec),
        "inputs": _input_lines(spec),
        "scene": _scene_line(spec),
        "subjects": [_subject_line(item) for item in subjects if isinstance(item, dict)],
        "staging": _staging_line(spec),
        "spatial_dynamics": _spatial_dynamics_line(spec),
        "composition": _composition_line(spec),
        "lighting": _lighting_line(spec),
        "materials": _materials_line(spec),
        "effects": _effect_lines(spec),
        "color": _color_line(spec),
        "color_pipeline": _color_pipeline_line(spec),
        "render_pipeline": _render_pipeline_line(spec),
        "optics": _optics_line(spec),
        "style": _style_line(spec),
        "render": _render_line(spec),
        "text": _text_lines(spec),
        "edits": _edit_lines(spec),
        "styleboard": _styleboard_lines(spec) if mode == "styleboard" else [],
    }
    return sections


def _labeled_prompt(sections: dict[str, Any], preserve: list[str], change: list[str], exclude: list[str]) -> str:
    labels = [
        ("Canonical knowledge anchors", "\n".join(f"- {item}" for item in sections["knowledge_anchors"])),
        ("Goal", sections["goal"]),
        ("Creative route and art direction", sections["creative_routing"]),
        ("Reference reconstruction analysis", sections["reference_analysis"]),
        ("Style learning record", sections["style_learning"]),
        ("Applied learned style capsule", sections["learned_style_capsule"]),
        ("Visual direction", sections["direction"]),
        ("Cinematic shot contract", sections["cinematic"]),
        ("Inputs", "\n".join(f"- {item}" for item in sections["inputs"])),
        ("Scene", sections["scene"]),
        ("Subjects", "\n".join(f"- {item}" for item in sections["subjects"] if item)),
        ("Staging and relationship geometry", sections["staging"]),
        ("Spatial dynamics and visual tension", sections["spatial_dynamics"]),
        ("Composition", sections["composition"]),
        ("Lighting", sections["lighting"]),
        ("Materials", sections["materials"]),
        ("Causal effects", "\n".join(f"- {item}" for item in sections["effects"])),
        ("Color", sections["color"]),
        ("Color pipeline and finishing", sections["color_pipeline"]),
        ("Render pipeline and material transport", sections["render_pipeline"]),
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


def compile_openai(spec: dict[str, Any], style_capsule: dict[str, Any] | None = None) -> dict[str, Any]:
    sections = _common_sections(spec, platform="openai", model_knowledge_hint=True, style_capsule=style_capsule)
    preserve, change, exclude = _constraints(spec)
    options = _platform_options(spec, "openai")
    parameters = (
        {}
        if spec.get("mode") == "learn_style"
        else {
            "model": options.get("model", "gpt-image-2"),
            "quality": options.get("quality", "medium"),
            "size": options.get("size") or _canvas_size(spec),
        }
    )
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
    normalized = item.lower().strip().strip(".,;:")
    for prefix in ("no ", "without "):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :].strip()
            break
    aliases = {
        "logos": "logo",
        "watermarks": "watermark",
        "people": "people",
        "persons": "people",
        "plastic cgi sheen": "plastic cgi",
        "new text": "extra text",
    }
    normalized = aliases.get(normalized, normalized)
    mappings = {
        "blur": "sharp focus throughout",
        "people": "an empty environment",
        "plastic cgi": "physically plausible materials with natural surface variation",
        "extra text": "only the specified literal text appears",
        "watermark": "clean image containing only the requested visual content",
        "logo": "unbranded scene containing only the requested visual content",
        "global gloss": "material-specific matte and reflective response with no uniform sheen",
    }
    return mappings.get(normalized)


def compile_flux(spec: dict[str, Any], style_capsule: dict[str, Any] | None = None) -> dict[str, Any]:
    sections = _common_sections(spec, platform="flux", style_capsule=style_capsule)
    preserve, change, exclude = _constraints(spec)
    options = _platform_options(spec, "flux")
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
            "creative_routing": sections["creative_routing"],
            "reference_analysis": sections["reference_analysis"],
            "style_learning_record": sections["style_learning"],
            "learned_style_capsule": sections["learned_style_capsule"],
            "visual_direction": sections["direction"],
            "cinematic_shot_contract": sections["cinematic"],
            "inputs": sections["inputs"],
            "scene": sections["scene"],
            "subjects": sections["subjects"],
            "staging": sections["staging"],
            "spatial_dynamics": sections["spatial_dynamics"],
            "composition": sections["composition"],
            "lighting": sections["lighting"],
            "materials": sections["materials"],
            "causal_effects": sections["effects"],
            "color": sections["color"],
            "color_pipeline": sections["color_pipeline"],
            "render_pipeline": sections["render_pipeline"],
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
        cleaned_payload = {
            key: cleaned
            for key, value in payload.items()
            if (cleaned := _clean_json_prompt_value(value)) is not None
        }
        prompt = json.dumps(cleaned_payload, ensure_ascii=False, indent=2) if cleaned_payload else ""
    else:
        ordered = [
            "Canonical knowledge anchors: " + "; ".join(sections["knowledge_anchors"]) if sections["knowledge_anchors"] else "",
            sections["goal"],
            sections["creative_routing"],
            sections["reference_analysis"],
            sections["style_learning"],
            sections["learned_style_capsule"],
            sections["direction"],
            sections["cinematic"],
            "Inputs: " + "; ".join(sections["inputs"]) if sections["inputs"] else "",
            sections["scene"],
            " ".join(sections["subjects"]),
            sections["staging"],
            sections["spatial_dynamics"],
            sections["composition"],
            sections["lighting"],
            sections["materials"],
            "Causal effects: " + "; ".join(sections["effects"]) if sections["effects"] else "",
            sections["color"],
            sections["color_pipeline"],
            sections["render_pipeline"],
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
        prompt = ". ".join(part.rstrip(". ") for part in ordered if part)
        if prompt:
            prompt += "."

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
        "parameters": {}
        if spec.get("mode") == "learn_style"
        else {
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


def _midjourney_execution_route(spec: dict[str, Any], options: dict[str, Any]) -> str:
    if spec.get("mode") in {"edit", "restyle", "expand"}:
        return "editor_required"
    inputs = spec.get("inputs") if isinstance(spec.get("inputs"), list) else []
    roles = " ".join(
        _text(item.get("role")).lower()
        for item in inputs
        if isinstance(item, dict) and item.get("type") == "image"
    )
    has_style = bool(_midjourney_style_refs(options.get("style_reference")))
    if any(token in roles for token in ("identity", "character", "person", "product", "object", "vehicle")):
        return "omni_reference_with_style_reference" if has_style else "omni_reference"
    if inputs:
        return "image_prompt_with_style_reference" if has_style else "image_prompt"
    if has_style:
        return "style_reference"
    return "imagine"


def compile_midjourney(spec: dict[str, Any], style_capsule: dict[str, Any] | None = None) -> dict[str, Any]:
    sections = _common_sections(spec, platform="midjourney", style_capsule=style_capsule)
    preserve, change, exclude = _constraints(spec)
    options = _platform_options(spec, "midjourney")
    content_parts = [
        " ".join(sections["knowledge_anchors"]), sections["goal"], sections["creative_routing"],
        sections["reference_analysis"],
        sections["style_learning"], sections["learned_style_capsule"],
        sections["direction"], sections["cinematic"],
        " ".join(sections["inputs"]), sections["scene"], " ".join(sections["subjects"]), sections["staging"],
        sections["spatial_dynamics"],
        sections["composition"], sections["lighting"], sections["materials"],
        " ".join(sections["effects"]), sections["color"], sections["color_pipeline"], sections["render_pipeline"],
        sections["optics"],
        sections["style"], sections["render"],
        "exact visible text " + "; ".join(sections["text"]) if sections["text"] else "",
        " ".join(sections["edits"]),
        "preserve " + "; ".join(preserve) if preserve else "",
        "required change " + "; ".join(change) if change else "",
        " ".join(sections["styleboard"]),
    ]
    content = _sanitize_midjourney_text(", ".join(part.strip(" ,.") for part in content_parts if part))

    canvas = spec.get("canvas") if isinstance(spec.get("canvas"), dict) else {}
    flags: list[str] = []
    if spec.get("mode") != "learn_style":
        aspect = options.get("aspect_ratio") or canvas.get("aspect_ratio")
        if aspect and aspect != "auto":
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
            flags.extend(["--no", _sanitize_midjourney_text(", ".join(exclude))])

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
        "execution_route": _midjourney_execution_route(spec, options),
        "prompt": content + (" " + " ".join(flags) if flags else ""),
        "negative_prompt": "",
        "parameters": {} if spec.get("mode") == "learn_style" else {"flags": flags},
        "warnings": warnings,
        "language": spec.get("language", "en"),
        "source_spec_version": spec.get("visual_generation_spec"),
    }


def compile_generic(spec: dict[str, Any], style_capsule: dict[str, Any] | None = None) -> dict[str, Any]:
    sections = _common_sections(spec, platform="generic", style_capsule=style_capsule)
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


def compile_spec(
    spec: dict[str, Any],
    platform: str | None = None,
    style_capsule: dict[str, Any] | None = None,
    *,
    review_approved: bool = False,
) -> dict[str, Any]:
    if style_capsule is not None:
        capsule_errors = validate_style_capsule(style_capsule)
        if capsule_errors:
            raise ValueError("Style capsule validation failed:\n" + "\n".join(f"- {error}" for error in capsule_errors))
    target = platform or spec.get("platform", "auto")
    if target == "auto":
        target = "generic"
    if target not in SUPPORTED_PLATFORMS:
        raise ValueError(f"unsupported platform: {target}")
    result = {
        "openai": compile_openai,
        "flux": compile_flux,
        "midjourney": compile_midjourney,
        "generic": compile_generic,
    }[target](spec, style_capsule)
    learn_warning = _learn_style_warning(spec)
    if learn_warning:
        result["warnings"].append(learn_warning)
    if style_capsule is not None:
        result["warnings"].extend(
            "Style capsule content review: " + warning for warning in lint_style_capsule_content(style_capsule)
        )
    metrics = _prompt_metrics(result["prompt"])
    result["prompt_metrics"] = metrics
    target_words = PROMPT_TARGET_WORDS[target]
    review_reasons: list[str] = []
    semantic_prompt = result["prompt"]
    if target == "midjourney":
        semantic_prompt = semantic_prompt.split(" --", 1)[0]
    is_empty_prompt = not semantic_prompt.strip().strip(".")
    if is_empty_prompt:
        review_reasons.append("empty_prompt")
        result["warnings"].append("Prompt review blocked an empty prompt with no semantic generation content.")
    if metrics["words"] > target_words:
        review_reasons.append("length_over_target")
        result["warnings"].append(
            f"Compiled prompt remains above the {target} review target: "
            f"{metrics['words']} words > {target_words}"
        )
    result["attachments"] = build_attachment_manifest(spec)
    required_reference_count = sum(1 for item in result["attachments"] if item.get("must_attach"))
    if required_reference_count >= 4:
        review_reasons.append("high_reference_count")
    residue_hits = context_residue_hits_from_sources(spec, style_capsule)
    review_reasons.extend(f"context_residue:{marker}" for marker in residue_hits)
    has_blocking_contamination = bool(residue_hits) or is_empty_prompt
    if residue_hits:
        result["warnings"].append(
            "Prompt review blocked conversation-dependent residue outside exact visible text: "
            + ", ".join(residue_hits)
        )
    if has_blocking_contamination:
        review_status = "blocked"
    elif review_reasons and review_approved:
        review_status = "approved"
    elif review_reasons:
        review_status = "review_required"
    else:
        review_status = "ready"
    result["prompt_review"] = {
        "status": review_status,
        "target_words": target_words,
        "reasons": review_reasons,
        "required_reference_count": required_reference_count,
        "approval_scope": "length_and_reference_complexity_only" if review_status == "approved" else "none",
    }
    if required_reference_count >= 4:
        result["warnings"].append(
            "High reference-role count: verify that every required image serves the brief; attachment count must not "
            "become a requirement to show every role simultaneously."
        )
    result["reference_handoff"] = build_reference_handoff(spec)
    result["imagegen_call_plan"] = build_imagegen_call_plan(spec)
    result["imagegen_call_plan"]["prompt_review_status"] = review_status
    if result["imagegen_call_plan"]["status"] == "ready" and review_status in {"blocked", "review_required"}:
        result["imagegen_call_plan"]["status"] = review_status
        result["imagegen_call_plan"]["errors"].append(
            "compiled prompt must pass prompt_review before ImageGen execution"
        )
    if result["imagegen_call_plan"]["status"] == "blocked" and result["attachments"]:
        result["warnings"].append(
            "Codex ImageGen execution is blocked until the imagegen_call_plan errors are resolved or the "
            "conversation-image window is confirmed immediately before the call."
        )
    result["warnings"].extend(reference_delivery_warnings(spec))
    return result


def _format_text(result: dict[str, Any]) -> str:
    parts = [f"PLATFORM\n{result['platform']}", f"PROMPT\n{result['prompt']}"]
    if result.get("negative_prompt"):
        parts.append(f"NEGATIVE PROMPT\n{result['negative_prompt']}")
    parts.append("PARAMETERS\n" + json.dumps(result.get("parameters", {}), ensure_ascii=False, indent=2))
    parts.append("PROMPT METRICS\n" + json.dumps(result.get("prompt_metrics", {}), ensure_ascii=False, indent=2))
    parts.append("PROMPT REVIEW\n" + json.dumps(result.get("prompt_review", {}), ensure_ascii=False, indent=2))
    if result.get("attachments"):
        parts.append("ATTACHMENTS\n" + json.dumps(result["attachments"], ensure_ascii=False, indent=2))
    if result.get("reference_handoff", {}).get("required_attachment_count"):
        parts.append("REFERENCE HANDOFF\n" + json.dumps(result["reference_handoff"], ensure_ascii=False, indent=2))
        parts.append("IMAGEGEN CALL PLAN\n" + json.dumps(result["imagegen_call_plan"], ensure_ascii=False, indent=2))
    if result.get("warnings"):
        parts.append("WARNINGS\n" + "\n".join(f"- {item}" for item in result["warnings"]))
    return "\n\n".join(parts)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to a visual specification JSON file")
    parser.add_argument("--platform", choices=sorted(SUPPORTED_PLATFORMS), help="Override the platform in the spec")
    parser.add_argument("--style-capsule", type=Path, help="Optional validated reusable style capsule JSON")
    parser.add_argument(
        "--approve-review",
        action="store_true",
        help="Approve length/reference-complexity review; context residue remains blocked",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json", dest="output_format")
    args = parser.parse_args()

    try:
        spec = load_json(args.spec)
        style_capsule = load_json(args.style_capsule) if args.style_capsule else None
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_spec(spec)
    if errors:
        print("INVALID SPEC", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    try:
        result = compile_spec(spec, args.platform, style_capsule, review_approved=args.approve_review)
    except ValueError as exc:
        print(f"INVALID STYLE CAPSULE\n{exc}", file=sys.stderr)
        return 2
    print(_format_text(result) if args.output_format == "text" else json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
