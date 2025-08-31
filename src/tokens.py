from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Dict, Optional

_tiktoken = None
try:
    import tiktoken  # type: ignore
    _tiktoken = tiktoken
except Exception:
    _tiktoken = None


def _approx_tokens(text: str) -> int:
    if not text:
        return 0
    # Simple heuristic: ~4 characters per token, add small overhead for structure
    chars = len(text)
    words = max(1, len(text.split()))
    est = int(math.ceil(chars / 4.0))
    return max(est, words)  # pick the larger of chars-based and words count


def _tiktoken_count(text: str, model: Optional[str]) -> Optional[int]:
    if not _tiktoken or not model:
        return None
    try:
        enc = _tiktoken.encoding_for_model(model)
    except Exception:
        try:
            enc = _tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None
    try:
        return len(enc.encode(text or ""))
    except Exception:
        return None


def estimate_tokens(text: str, *, model: Optional[str] = None) -> int:
    cnt = _tiktoken_count(text, model)
    if cnt is not None:
        return cnt
    return _approx_tokens(text)


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0

    def add(self, in_toks: int, out_toks: int):
        self.input_tokens += in_toks
        self.output_tokens += out_toks
        self.calls += 1

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens


_USAGE_BY_SESSION: Dict[str, Usage] = {}


def add_usage(session_id: str, in_tokens: int, out_tokens: int):
    u = _USAGE_BY_SESSION.get(session_id)
    if not u:
        u = Usage()
        _USAGE_BY_SESSION[session_id] = u
    u.add(in_tokens, out_tokens)


def get_usage(session_id: str) -> Usage:
    return _USAGE_BY_SESSION.get(session_id, Usage())


def format_usage_summary(session_id: str) -> str:
    u = get_usage(session_id)
    return (
        f"호출: {u.calls}회\n"
        f"입력 토큰: {u.input_tokens}\n"
        f"출력 토큰: {u.output_tokens}\n"
        f"합계: {u.total}"
    )
