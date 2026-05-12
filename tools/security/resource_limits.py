"""
Resource Limits v1.0 — Linux ulimit benzeri sınırlar.

Bu modül subprocess.Popen'ın preexec_fn parametresine geçirilecek.
Çocuk process oluşturulduğunda, kod çalışmaya başlamadan ÖNCE
limitler set edilir. Sonsuz döngü, hafıza saldırısı, fork bomb
gibi zararları engeller.

NOT: Bu Linux'a özgüdür. Windows'ta `resource` modülü yoktur.
WSL Linux altında çalıştığı için sorunsuz çalışır.
"""
import os
import sys

# --- Varsayılan Limitler ---
DEFAULT_CPU_SECONDS = 30       # Maksimum CPU süresi (saniye)
DEFAULT_MEMORY_MB = 512        # Maksimum heap memory (MB)
DEFAULT_MAX_PROCESSES = 50     # Maksimum fork sayısı (fork bomb engeli)
DEFAULT_MAX_FILE_SIZE_MB = 100 # Maksimum yazılabilir dosya boyutu (MB)
DEFAULT_NO_CORE = True         # Core dump dosyası oluşturulmasın


def apply_limits(
    cpu_seconds: int = DEFAULT_CPU_SECONDS,
    memory_mb: int = DEFAULT_MEMORY_MB,
    max_processes: int = DEFAULT_MAX_PROCESSES,
    max_file_size_mb: int = DEFAULT_MAX_FILE_SIZE_MB,
    no_core: bool = DEFAULT_NO_CORE,
):
    """
    Bu fonksiyon SUBPROCESS İÇİNDE çağrılır.
    Parent process'i etkilemez — sadece yeni process'in limitlerini belirler.
    """
    # resource modülü Linux'a özgüdür
    if sys.platform == "win32":
        return  # Windows'ta işlem yapma

    try:
        import resource

        # CPU saniyesi (soft, hard)
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (cpu_seconds, cpu_seconds)
        )

        # Hafıza (bytes cinsinden)
        memory_bytes = memory_mb * 1024 * 1024
        resource.setrlimit(
            resource.RLIMIT_AS,
            (memory_bytes, memory_bytes)
        )

        # Proses sayısı (fork bomb engeli)
        resource.setrlimit(
            resource.RLIMIT_NPROC,
            (max_processes, max_processes)
        )

        # Dosya boyutu (disk dolmasını engelle)
        file_size_bytes = max_file_size_mb * 1024 * 1024
        resource.setrlimit(
            resource.RLIMIT_FSIZE,
            (file_size_bytes, file_size_bytes)
        )

        # Core dump engeli
        if no_core:
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    except (ImportError, ValueError, OSError):
        # Sessiz başarısız — bazı WSL sürümleri belirli limitleri desteklemeyebilir
        pass


def get_limit_summary() -> str:
    """Aktif limitleri insan okunur şekilde döndürür (debug için)."""
    return (
        f"CPU: {DEFAULT_CPU_SECONDS}s, "
        f"RAM: {DEFAULT_MEMORY_MB}MB, "
        f"Procs: {DEFAULT_MAX_PROCESSES}, "
        f"MaxFile: {DEFAULT_MAX_FILE_SIZE_MB}MB"
    )