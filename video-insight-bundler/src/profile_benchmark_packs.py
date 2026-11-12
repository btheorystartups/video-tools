"""Heuristic editorial benchmark profile pack scaffolding."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


PROFILE_NAMES = ["philosophical_monologue", "educational_explainer", "podcast_conversation", "documentary_narration", "keynote_talk", "tutorial_instruction", "cinematic_storytelling", "social_short_form", "interview_format"]


def build_profile_benchmark_packs(outputs: dict) -> dict:
    packs = []
    for index, name in enumerate(PROFILE_NAMES):
        packs.append(
            {
                "profile_id": name,
                "profile_pack_id": deterministic_id("PBPACK", name),
                "description": "Heuristic editorial benchmark profile for deterministic human review.",
                "guidance": {
                    "speech_pacing": "Review pacing against the format context; avoid universal good/bad claims.",
                    "pause_density": "Use pauses as editorial rhythm evidence.",
                    "silence_ratio": "Treat silence as a possible intentional device.",
                    "visual_reset_frequency": "Review whether visual resets support comprehension.",
                    "abstraction_tolerance": "Higher tolerance" if name in {"philosophical_monologue", "cinematic_storytelling"} else "Moderate tolerance",
                    "example_density": "Prefer concrete examples when instructional clarity is the goal.",
                    "rhetorical_pressure_tolerance": "Higher tolerance for keynote or short-form emphasis; lower for tutorial clarity.",
                    "topic_drift_tolerance": "Directional heuristic only; human review required.",
                    "segment_duration": "Compare against local corpus medians before action.",
                    "acoustic_variability": "Energy variation may suggest review priority; it does not diagnose emotion.",
                    "emotional_intensity_arc_contrast": "Editorial intensity contrast only, not actual emotion detection.",
                    "governance_caution_notes": "Do not infer identity, demographics, personality, diagnosis, or viewer behavior.",
                },
                "limitations": [LIMITATION, "Profile packs are heuristic editorial benchmark scaffolds, not universal standards."],
            }
        )
    videos = (outputs.get("corpus_index") or {}).get("videos") or []
    assignments = []
    for video in videos:
        assignments.append({"source_video": video.get("source_video"), "default_profile": "generic_editorial_review", "candidate_profiles": [{"profile_id": "philosophical_monologue", "confidence": 0.35}, {"profile_id": "educational_explainer", "confidence": 0.3}], "assignment_status": "weak_evidence_default_retained"})
    packs_artifact = base_artifact(method="deterministic_profile_benchmark_packs_v1")
    packs_artifact.update({"profile_benchmark_packs_id": deterministic_id("PBREG", PROFILE_NAMES), "profile_packs": packs, "summary": {"profile_pack_count": len(packs)}, "limitations": [LIMITATION, "Profiles are optional scaffolds and are not forced when evidence is weak."]})
    registry = base_artifact(method="deterministic_profile_benchmark_registry_v1")
    registry.update({"profile_benchmark_registry_id": deterministic_id("PBIDX", PROFILE_NAMES), "profiles": [{"profile_id": row["profile_id"], "profile_pack_id": row["profile_pack_id"]} for row in packs], "summary": {"profile_count": len(packs)}, "limitations": packs_artifact["limitations"]})
    assignment_artifact = base_artifact(method="deterministic_benchmark_profile_assignments_v1")
    assignment_artifact.update({"benchmark_profile_assignments_id": deterministic_id("PBASSIGN", assignments), "assignments": assignments, "summary": {"assignment_count": len(assignments)}, "limitations": packs_artifact["limitations"]})
    guidance = base_artifact(method="deterministic_benchmark_profile_guidance_v1")
    guidance.update({"benchmark_profile_guidance_id": deterministic_id("PBGUIDE", PROFILE_NAMES), "guidance": [{"profile_id": row["profile_id"], "guidance": row["guidance"]} for row in packs], "summary": {"guidance_count": len(packs)}, "limitations": packs_artifact["limitations"]})
    return {"profile_benchmark_packs": packs_artifact, "profile_benchmark_registry": registry, "benchmark_profile_assignments": assignment_artifact, "benchmark_profile_guidance": guidance}

