"""Local dependency diagnostics for reproducible runs."""

from __future__ import annotations

import importlib.metadata
import importlib.util
import importlib
import shutil
import subprocess
from pathlib import Path

from stability import write_json


def _first_line(text: str) -> str | None:
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _check_executable(name: str, capabilities: list[str]) -> dict:
    path = shutil.which(name)
    result = {
        "available": bool(path),
        "path": path,
        "detected_version": None,
        "capabilities": capabilities if path else [],
    }
    if not path:
        result["reason"] = f"{name} executable was not found on PATH."
        return result

    try:
        completed = subprocess.run(
            [path, "-version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception as exc:
        result["available"] = False
        result["reason"] = f"{name} version check failed: {exc}"
        result["capabilities"] = []
        return result

    result["detected_version"] = _first_line(completed.stdout) or _first_line(completed.stderr)
    result["version_check_exit_code"] = completed.returncode
    return result


def _check_faster_whisper() -> dict:
    spec = importlib.util.find_spec("faster_whisper")
    result = {
        "available": spec is not None,
        "path": None,
        "detected_version": None,
        "capabilities": [],
    }
    if not spec:
        result["reason"] = "faster_whisper is not installed in this Python environment."
        return result

    result["path"] = spec.origin
    result["capabilities"] = ["local_transcription"]
    try:
        importlib.import_module("faster_whisper")
    except Exception as exc:
        result["available"] = False
        result["reason"] = f"faster_whisper could not be imported: {exc}"
        result["capabilities"] = []
        return result

    try:
        result["detected_version"] = importlib.metadata.version("faster-whisper")
    except importlib.metadata.PackageNotFoundError:
        result["detected_version"] = "installed_version_unknown"
    return result


def _check_python_package(import_name: str, distribution_name: str, capabilities: list[str], required: bool = False) -> dict:
    spec = importlib.util.find_spec(import_name)
    result = {
        "available": spec is not None,
        "path": spec.origin if spec else None,
        "detected_version": None,
        "capabilities": capabilities if spec else [],
        "required": required,
    }
    if not spec:
        result["reason"] = f"{distribution_name} is not installed in this Python environment."
        return result
    try:
        result["detected_version"] = importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        result["detected_version"] = "installed_version_unknown"
    return result


def build_dependency_report() -> dict:
    dependencies = {
        "ffmpeg": _check_executable("ffmpeg", ["audio_extract", "visual_sampling"]),
        "ffprobe": _check_executable("ffprobe", ["media_probe"]),
        "faster_whisper": _check_faster_whisper(),
        "matplotlib": _check_python_package("matplotlib", "matplotlib", ["static_graph_generation"], True),
        "jinja2": _check_python_package("jinja2", "jinja2", ["html_template_rendering"], False),
        "wordcloud": _check_python_package("wordcloud", "wordcloud", ["wordcloud_graph"], False),
        "networkx": _check_python_package("networkx", "networkx", ["rhetorical_network_graph"], False),
        "textstat": _check_python_package("textstat", "textstat", ["readability_statistics"], False),
        "pandas": _check_python_package("pandas", "pandas", ["future_table_analysis"], False),
        "numpy": _check_python_package("numpy", "numpy", ["future_numeric_analysis"], False),
        "opencv": _check_python_package("cv2", "opencv-python", ["local_visual_structure", "shot_boundary_detection"], False),
        "scipy": _check_python_package("scipy", "scipy", ["future_signal_statistics"], False),
        "plotly": _check_python_package("plotly", "plotly", ["self_contained_interactive_charts"], False),
        "pyvis": _check_python_package("pyvis", "pyvis", ["future_interactive_networks"], False),
        "seaborn": _check_python_package("seaborn", "seaborn", ["future_statistical_graphs"], False),
        "sklearn": _check_python_package("sklearn", "scikit-learn", ["local_topic_analysis"], False),
        "PIL": _check_python_package("PIL", "pillow", ["frame_contact_sheet"], False),
        "librosa": _check_python_package("librosa", "librosa", ["local_acoustic_energy_analysis"], False),
    }
    return {
        "report_version": "1.0",
        "dependencies": dependencies,
    }


def dependency_versions(report: dict) -> dict:
    return {
        name: details.get("detected_version")
        for name, details in report.get("dependencies", {}).items()
    }


def write_dependency_report(report: dict, output_dir: Path, evidence_dir: Path) -> None:
    write_json(output_dir / "dependency_report.json", report)
    write_json(evidence_dir / "dependency_report.json", report)
