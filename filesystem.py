"""
Dosya sistemi toolları: read_file, write_file.

Path traversal saldırılarına karşı workspace dışına çıkmayı engeller.
"""
from pathlib import Path
from config import WORKSPACE, MAX_OBSERVATION_LEN


def _safe_path(path: str) -> Path:
    """
    Verilen path'i WORKSPACE içine kilitle.
    "../../../etc/passwd" gibi saldırılara karşı koruma.
    """
    target = (WORKSPACE / path).resolve()
    workspace_resolved = WORKSPACE.resolve()

    if not str(target).startswith(str(workspace_resolved)):
        raise ValueError(f"Path workspace dışında: {path}")

    return target


def read_file(path: str) -> str:
    """Workspace içindeki dosyayı oku."""
    try:
        target = _safe_path(path)
        if not target.exists():
            return f"ERROR: Dosya bulunamadı: {path}"
        if not target.is_file():
            return f"ERROR: '{path}' bir dosya değil."

        content = target.read_text(encoding="utf-8")
        if len(content) > MAX_OBSERVATION_LEN:
            return f"FILE: {path} (truncated)\n{content[:MAX_OBSERVATION_LEN]}\n... [{len(content) - MAX_OBSERVATION_LEN} chars more]"
        return f"FILE: {path}\n{content}"

    except UnicodeDecodeError:
        return f"ERROR: '{path}' UTF-8 olarak okunamadı (binary olabilir)."
    except Exception as e:
        return f"ERROR: {e}"


def write_file(path: str, content: str) -> str:
    """Workspace içine dosya yaz. Üst klasörler yoksa oluştur."""
    try:
        target = _safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"OK: {path} kaydedildi ({len(content)} bytes)."
    except Exception as e:
        return f"ERROR: {e}"