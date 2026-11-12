"""Small JSON Schema subset validator used to keep the tool standalone."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from stability import STATUS_COMPLETE, STATUS_ERROR, write_json


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def _validate_node(value: Any, schema: dict, path: str, errors: list[dict]) -> None:
    expected_type = schema.get("type")
    if expected_type:
        allowed = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_type_matches(value, item) for item in allowed):
            errors.append(
                {
                    "path": path,
                    "message": f"Expected type {allowed}, got {type(value).__name__}.",
                }
            )
            return

    if "enum" in schema and value not in schema["enum"]:
        errors.append({"path": path, "message": f"Value {value!r} is not one of {schema['enum']}."})

    if isinstance(value, dict):
        for required_key in schema.get("required", []):
            if required_key not in value:
                errors.append({"path": path, "message": f"Missing required key: {required_key}."})

        properties = schema.get("properties", {})
        for key, child_schema in properties.items():
            if key in value:
                _validate_node(value[key], child_schema, f"{path}.{key}", errors)

        if schema.get("additionalProperties") is False:
            allowed_keys = set(properties)
            for key in value:
                if key not in allowed_keys:
                    errors.append({"path": path, "message": f"Unexpected key: {key}."})

    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            _validate_node(item, schema["items"], f"{path}[{index}]", errors)


def validate_against_schema(data: dict, schema_path: Path) -> dict:
    with schema_path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)

    errors: list[dict] = []
    _validate_node(data, schema, "$", errors)
    return {
        "validation_status": STATUS_COMPLETE if not errors else STATUS_ERROR,
        "schema_path": str(schema_path),
        "error_count": len(errors),
        "errors": errors,
    }


def write_validation_report(report: dict, output_dir: Path, evidence_dir: Path) -> None:
    write_json(output_dir / "validation_report.json", report)
    write_json(evidence_dir / "schema_validation_results.json", report)
