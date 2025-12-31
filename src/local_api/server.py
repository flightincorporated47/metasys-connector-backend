# src/local_api/server.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

APP_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = APP_DIR / "projects"

app = FastAPI(title="Metasys Connector Local API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _proj_dir(project_id: str) -> Path:
    p = DATA_DIR / project_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def _config_path(project_id: str) -> Path:
    return _proj_dir(project_id) / "config.json"


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


class SaveConfigBody(BaseModel):
    config_json: Dict[str, Any]


class GenerateYamlBody(BaseModel):
    write_to_disk: bool = True


@app.get("/api/v1/projects/{project_id}/connector/config")
def get_connector_config(project_id: str):
    path = _config_path(project_id)
    config_json = _read_json(path) if path.exists() else {"connector": {}}
    version = int(config_json.get("_version", 0))
    cleaned = {k: v for k, v in config_json.items() if k != "_version"}
    return {"config_json": cleaned, "version": version}


@app.put("/api/v1/projects/{project_id}/connector/config")
def save_connector_config(project_id: str, body: SaveConfigBody):
    path = _config_path(project_id)
    existing = _read_json(path) if path.exists() else {}
    version = int(existing.get("_version", 0)) + 1
    to_save = dict(body.config_json)
    to_save["_version"] = version
    _write_json(path, to_save)
    cleaned = {k: v for k, v in to_save.items() if k != "_version"}
    return {"ok": True, "version": version, "config_json": cleaned}


@app.post("/api/v1/projects/{project_id}/connector/generate-yaml")
def generate_yaml(project_id: str, body: GenerateYamlBody):
    cfg = _read_json(_config_path(project_id))
    if not cfg:
        raise HTTPException(status_code=404, detail="No config saved for project yet.")

    try:
        import yaml  # type: ignore
        yaml_text = yaml.safe_dump(cfg, sort_keys=False)
    except Exception:
        yaml_text = json.dumps(cfg, indent=2)

    if body.write_to_disk:
        out_path = _proj_dir(project_id) / "generated.yml"
        out_path.write_text(yaml_text, encoding="utf-8")
        return {"yaml_text": yaml_text, "path": str(out_path)}

    return {"yaml_text": yaml_text}


@app.get("/api/v1/projects/{project_id}/connector/yaml-diff")
def yaml_diff(project_id: str):
    return {"diff_unified": ""}


@app.get("/api/v1/projects/{project_id}/secrets/{key}")
def secret_exists(project_id: str, key: str):
    return {"exists": bool(os.environ.get(key))}

