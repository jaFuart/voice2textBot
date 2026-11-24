import os
from functools import lru_cache
from threading import Lock

from faster_whisper import WhisperModel

_model_lock = Lock()


@lru_cache(maxsize=1)
def _model():
    return WhisperModel(
        "small",
        device="cpu",
        compute_type="int8",
        download_root=os.getenv("WHISPER_MODEL_CACHE") or None,
    )


def transcribe_file(path: str) -> str:
    with _model_lock:
        segments, _ = _model().transcribe(path, beam_size=1)
        return "".join(segment.text for segment in segments).strip()
