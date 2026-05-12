"""
Kod Çalıştırma Motoru v6.7 — ToolExecutor Class-Based Structure

server.py'nin beklediği 'ToolExecutor(registry)' yapısı eklendi.
ToolRegistry'nin beklediği 'run_python' ve 'execute_command' fonksiyonları korundu.
"""
import subprocess
import sys
import uuid
from pathlib import Path
from config import WORKSPACE, EXEC_TIMEOUT, MAX_OBSERVATION_LEN

# Güvenlik katmanları
try:
    from tools.security.ast_guard import is_safe as is_python_safe
    from tools.security.command_guard import is_safe as is_command_safe
    from tools.security.path_validator import (
        is_command_path_safe,
        is_python_path_safe,
    )
    from tools.security.resource_limits import apply_limits
except ImportError:
    # Güvenlik modülleri eksikse (hata almamak için placeholder)
    def is_python_safe(c): return True, ""
    def is_command_safe(c): return True, ""
    def is_python_path_safe(c): return True, ""
    def is_command_path_safe(c): return True, ""
    def apply_limits(): pass


def _truncate(text: str, limit: int = MAX_OBSERVATION_LEN) -> str:
    """Çıktıyı bağlam penceresine sığması için keser."""
    if len(text) <= limit:
        return text
    half = limit // 2
    return f"{text[:half]}\n... [TRUNCATED {len(text) - limit} chars] ...\n{text[-half:]}"


def run_python(code: str) -> str:
    """Python kodunu sandbox içinde çalıştırır."""
    if not code or not code.strip():
        return "HATA: Boş kod gönderildi."

    # Güvenlik denetimleri
    safe, reason = is_python_safe(code)
    if not safe: return f"🛡️ GÜVENLİK ENGELİ (AST): {reason}"
    
    safe, reason = is_python_path_safe(code)
    if not safe: return f"🛡️ GÜVENLİK ENGELİ (PATH): {reason}"

    filename = WORKSPACE / f"_run_{uuid.uuid4().hex[:8]}.py"
    filename.write_text(code, encoding="utf-8")

    try:
        # Resource limitleri preexec_fn ile alt sürece uygulanır
        result = subprocess.run(
            [sys.executable, str(filename)],
            capture_output=True,
            text=True,
            timeout=EXEC_TIMEOUT,
            cwd=str(WORKSPACE),
            preexec_fn=apply_limits # Linux/WSL ortamı için kritik
        )

        output = []
        if result.stdout: output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr: output.append(f"STDERR:\n{result.stderr}")
        if result.returncode != 0: output.append(f"EXIT_CODE: {result.returncode}")

        return _truncate("\n".join(output) or "(çıktı yok)")

    except subprocess.TimeoutExpired:
        return f"HATA: Kod {EXEC_TIMEOUT}s içinde tamamlanamadı (Zaman aşımı)."
    except Exception as e:
        return f"SİSTEM HATASI: {str(e)}"
    finally:
        try: filename.unlink()
        except: pass


def execute_command(command: str) -> str:
    """Shell komutlarını güvenlik filtresiyle çalıştırır."""
    if not command or not command.strip():
        return "HATA: Boş komut gönderildi."

    # Güvenlik denetimleri
    safe, msg = is_command_safe(command)
    if not safe: return f"🛡️ GÜVENLİK ENGELİ (CMD): {msg}"

    safe, reason = is_command_path_safe(command)
    if not safe: return f"🛡️ GÜVENLİK ENGELİ (PATH): {reason}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=EXEC_TIMEOUT,
            cwd=str(WORKSPACE),
            preexec_fn=apply_limits
        )

        output = []
        if result.stdout: output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr: output.append(f"STDERR:\n{result.stderr}")
        if result.returncode != 0: output.append(f"EXIT_CODE: {result.returncode}")

        return _truncate("\n".join(output) or "(çıktı yok)")

    except subprocess.TimeoutExpired:
        return f"HATA: Komut {EXEC_TIMEOUT}s içinde tamamlanamadı."
    except Exception as e:
        return f"SİSTEM HATASI: {str(e)}"


class ToolExecutor:
    """
    server.py ve OOP tabanlı yapılar için sarmalayıcı sınıf.
    """
    def __init__(self, registry):
        # FIX: server.py'den gelen registry argümanı artık kabul ediliyor.
        self.registry = registry

    def run_python(self, code: str) -> str:
        return run_python(code)

    def execute_command(self, command: str) -> str:
        return execute_command(command)