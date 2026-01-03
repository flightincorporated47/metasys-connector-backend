# src/local_api/server.py
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

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


# ----------------------------
# Helpers
# ----------------------------
def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _proj_dir(project_id: str) -> Path:
    p = DATA_DIR / project_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def _config_path(project_id: str) -> Path:
    return _proj_dir(project_id) / "config.json"


def _meta_path(project_id: str) -> Path:
    return _proj_dir(project_id) / "meta.json"


def _default_meta(project_id: str) -> Dict[str, Any]:
    return {
        "project_id": project_id,
        "name": project_id,
        "updated_at": _utc_now(),
        "publishing_enabled": False,
        "last_scan_at": None,
        "device_count": None,
    }


def _read_json(path: Path) -> Dict[str, Any]:
    """
    BOM-safe read: some Windows editors write UTF-8 with BOM.
    """
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8-sig")
    text = text.strip()
    if not text:
        return {}
    return json.loads(text)


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def _delete_tree(p: Path) -> None:
    """
    Delete a directory tree safely (files first, then dirs).
    """
    if not p.exists():
        return
    if p.is_file():
        p.unlink()
        return
    for child in p.rglob("*"):
        if child.is_file():
            child.unlink()
    for child in sorted(p.rglob("*"), reverse=True):
        if child.is_dir():
            child.rmdir()
    p.rmdir()


# ----------------------------
# Models
# ----------------------------
class SaveConfigBody(BaseModel):
    config_json: Dict[str, Any]


class GenerateYamlBody(BaseModel):
    write_to_disk: bool = True


class CreateProjectBody(BaseModel):
    project_id: str
    name: str


# ----------------------------
# Routes
# ----------------------------
@app.get("/api/v1/health")
def health():
    return {"ok": True}


@app.get("/api/v1/projects")
def list_projects():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    projects = []

    for p in sorted(DATA_DIR.iterdir()):
        if not p.is_dir():
            continue
        if p.name.startswith("_"):
            continue

        project_id = p.name
        meta_path = p / "meta.json"
        cfg_path = p / "config.json"

        meta = _read_json(meta_path) if meta_path.exists() else _default_meta(project_id)

        # read version from config.json if present
        version = 0
        if cfg_path.exists():
            try:
                cfg = _read_json(cfg_path)
                version = int(cfg.get("_version", 0))
            except Exception:
                version = 0

        # normalize expected fields
        meta.setdefault("name", project_id)
        meta.setdefault("updated_at", _utc_now())
        meta.setdefault("publishing_enabled", False)
        meta.setdefault("last_scan_at", None)
        meta.setdefault("device_count", None)

        projects.append(
            {
                "project_id": project_id,
                "name": meta.get("name", project_id),
                "updated_at": meta.get("updated_at", _utc_now()),
                "publishing_enabled": bool(meta.get("publishing_enabled", False)),
                "last_scan_at": meta.get("last_scan_at"),
                "device_count": meta.get("device_count"),
                "version": version,
            }
        )

    return {"projects": projects}


@app.post("/api/v1/projects")
def create_project(body: CreateProjectBody):
    project_id = body.project_id.strip()
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id required")

    # create directory
    _proj_dir(project_id)

    # write meta.json
    meta = _default_meta(project_id)
    meta["name"] = (body.name or "").strip() or project_id
    meta["updated_at"] = _utc_now()
    _write_json(_meta_path(project_id), meta)

    # do NOT overwrite config.json automatically
    return {"ok": True, "project": meta}


@app.delete("/api/v1/projects/{project_id}")
def delete_project(project_id: str):
    p = DATA_DIR / project_id
    if not p.exists():
        return {"ok": True}
    if p.name.startswith("_"):
        raise HTTPException(status_code=400, detail="Refusing to delete protected project folder.")
    _delete_tree(p)
    return {"ok": True}


@app.get("/api/v1/projects/{project_id}/connector/config")
def get_connector_config(project_id: str):
    path = _config_path(project_id)
    config_json = _read_json(path) if path.exists() else {"connector": {}}

    version = int(config_json.get("_version", 0))
    cleaned = {k: v for k, v in config_json.items() if k != "_version"}

    return {"config_json": cleaned, "version": version}


@app.put("/api/v1/projects/{project_id}/connector/config")
def save_connector_config(project_id: str, body: SaveConfigBody):
    if body.config_json is None or body.config_json == {}:
        raise HTTPException(status_code=400, detail="config_json cannot be empty")

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

