"""Information density and visibility profile registries."""

from __future__ import annotations

from pathlib import Path

from stability import utc_now_iso, write_json


def build_review_ux_registries(package_root: Path, *, review_style: str = "balanced", dashboard_density: str = "balanced") -> dict:
    visibility_profiles = {
        "executive": {"show_audit": False, "show_advanced": False, "default_collapsed": True},
        "balanced": {"show_audit": False, "show_advanced": True, "default_collapsed": True},
        "audit_dense": {"show_audit": True, "show_advanced": True, "default_collapsed": False},
    }
    density = {
        "compact": {"max_top_items": 5, "progressive_disclosure": True, "graph_clustering": True},
        "balanced": {"max_top_items": 8, "progressive_disclosure": True, "graph_clustering": True},
        "expanded": {"max_top_items": 16, "progressive_disclosure": True, "graph_clustering": False},
    }
    ux = {"analysis_status": "complete", "method": "review_ux_registry_v78", "generated_at_utc": utc_now_iso(), "controls": ["compact_mode", "expanded_mode", "executive_mode", "audit_mode", "show_more", "advanced_audit_details"], "review_style": review_style}
    info = {"analysis_status": "complete", "method": "information_density_registry_v78", "generated_at_utc": utc_now_iso(), "dashboard_density": dashboard_density, "settings": density.get(dashboard_density, density["balanced"])}
    profiles = {"analysis_status": "complete", "method": "dashboard_visibility_profiles_v78", "generated_at_utc": utc_now_iso(), "active_profile": review_style, "profiles": visibility_profiles}
    for rel, payload in [("review_ux_registry.json", ux), ("information_density_registry.json", info), ("dashboard_visibility_profiles.json", profiles)]:
        write_json(package_root / rel, payload)
        write_json(package_root / "review" / rel, payload)
    return {"review_ux_registry": ux, "information_density_registry": info, "dashboard_visibility_profiles": profiles}
