import json
from jsonschema import Draft202012Validator


def validate_config(config: dict, schema_path: str) -> None:
    """
    Validate loaded YAML config against a JSON Schema.
    Raises ValueError with a readable error list if invalid.
    """
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(config), key=lambda e: list(e.path))

    if errors:
        lines = []
        for e in errors[:50]:
            path = ".".join([str(p) for p in e.path]) or "<root>"
            lines.append(f"- {path}: {e.message}")
        raise ValueError("Config validation failed:\n" + "\n".join(lines))

