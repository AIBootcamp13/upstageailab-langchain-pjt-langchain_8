from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.config import DATA_DIR, TIMEZONE


ARTIFACTS_DIR = DATA_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    import re
    text = re.sub(r"[^a-zA-Z0-9가-힣\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text.lower() or "artifact"


@dataclass
class Artifact:
    id: str
    session_id: str
    name: str
    kind: str
    ext: str
    path: str
    created_at: str
    size: int

    @property
    def file_path(self) -> Path:
        return Path(self.path)


def _session_dir(session_id: str) -> Path:
    d = ARTIFACTS_DIR / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_artifact(session_id: str, name: str, content: str | bytes, *, kind: str = "generic", ext: str = "txt") -> Artifact:
    now = datetime.now(TIMEZONE)
    ts = now.strftime("%Y%m%d-%H%M%S")
    base = f"{ts}-{_slugify(name)}"
    filename = f"{base}.{ext}"
    folder = _session_dir(session_id)
    file_path = folder / filename

    # write file
    if isinstance(content, bytes):
        file_path.write_bytes(content)
    else:
        file_path.write_text(content, encoding="utf-8")

    meta = Artifact(
        id=base,
        session_id=session_id,
        name=name,
        kind=kind,
        ext=ext,
        path=str(file_path),
        created_at=now.isoformat(),
        size=os.path.getsize(file_path),
    )

    # write sidecar metadata
    (folder / f"{base}.json").write_text(json.dumps(asdict(meta), ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def list_artifacts(session_id: str) -> List[Artifact]:
    folder = _session_dir(session_id)
    items: List[Artifact] = []
    for meta_file in sorted(folder.glob("*.json")):
        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
            items.append(Artifact(**data))
        except Exception:
            continue
    # newest first
    items.sort(key=lambda a: a.created_at, reverse=True)
    return items
