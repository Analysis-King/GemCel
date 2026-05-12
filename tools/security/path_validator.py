"""
Path Validator v6.12 — Çalışma Alanı Güvenliği

Bu modül, bir komut veya kod parçasında geçen TÜM yazma ve silme
hedeflerini bulup, WORKSPACE dışına çıkılmasını engeller.

Whitelist yaklaşımı: Sadece WORKSPACE altına yazılabilir/silinebilir.
"""
import re
import ast
from pathlib import Path
from typing import List, Tuple, Optional
from config import WORKSPACE


def _is_inside_workspace(target_path: str) -> bool:
    """
    Verilen yolun fiziksel olarak WORKSPACE içinde kalıp kalmadığını denetler.
    Sembolik linkleri (resolve) ve kullanıcı dizini (~ expansion) durumlarını ele alır.
    """
    try:
        # ~ expansion (örn. ~/Gemini/file.txt)
        expanded = Path(target_path).expanduser()

        # Eğer göreli yol ise workspace'e bağla
        if not expanded.is_absolute():
            expanded = WORKSPACE / expanded

        # Mutlak yolu normalize et (sembolik linkleri çözer)
        # strict=False çünkü dosya henüz oluşturulmamış olabilir
        resolved = expanded.resolve(strict=False)
        workspace_resolved = WORKSPACE.resolve(strict=False)

        # Normalize edilmiş yolun, workspace yoluyla başlayıp başlamadığını kontrol et
        return str(resolved).startswith(str(workspace_resolved))
    except (OSError, ValueError):
        # Hatalı veya şüpheli yol formatı -> Güvensiz say
        return False


# ==================== SHELL KOMUT ANALİZİ (RegEx) ====================

# Shell'de dosya manipülasyonu içeren desenler
WRITE_PATTERNS = [
    # Çıktı yönlendirme: cmd > path veya cmd >> path
    (r"(?:^|\s|;|\|)\s*>\s*([^\s;|&<>]+)", "Çıktı yönlendirme (>)"),
    (r"(?:^|\s|;|\|)\s*>>\s*([^\s;|&<>]+)", "Ekleme yönlendirme (>>)"),
    # tee komutu
    (r"\btee\s+(?:-a\s+)?([^\s;|&<>]+)", "tee komutu"),
    # rm — Silme işlemi de yazma kadar tehlikelidir
    (r"\brm\s+(?:-[rRfv]+\s+)*([^\s;|&<>-][^\s;|&<>]*)", "rm — Silme işlemi"),
    # mv ve cp hedefleri
    (r"\bmv\s+\S+\s+([^\s;|&<>]+)", "mv hedef yolu"),
    (r"\bcp\s+(?:-[rR]+\s+)?\S+\s+([^\s;|&<>]+)", "cp hedef yolu"),
    # touch ve mkdir
    (r"\btouch\s+([^\s;|&<>]+)", "touch — Dosya oluşturma"),
    (r"\bmkdir\s+(?:-p\s+)?([^\s;|&<>]+)", "mkdir — Klasör oluşturma"),
    # Diğer manipülasyonlar
    (r"\brmdir\s+([^\s;|&<>]+)", "rmdir — Klasör silme"),
    (r"\bln\s+(?:-[sf]+\s+)?\S+\s+([^\s;|&<>]+)", "ln hedef yolu"),
]


def analyze_command_paths(command: str) -> List[Tuple[str, str]]:
    """
    Shell komutunda workspace dışı yazma/silme hedeflerini bulur.
    Dönüş: [(path, açıklama), ...]
    """
    violations = []

    for pattern, description in WRITE_PATTERNS:
        for match in re.finditer(pattern, command):
            target = match.group(1).strip()

            # Tırnakları temizle
            target = target.strip("'\"")

            # Boş veya değişken ($HOME vb.) ise değerlendirme dışı bırak (Zaten engellenecek)
            if not target or target.startswith("$"):
                continue

            if not _is_inside_workspace(target):
                violations.append((target, description))

    return violations


def is_command_path_safe(command: str) -> Tuple[bool, str]:
    """Hızlı kontrol: Komut workspace dışına müdahale ediyor mu?"""
    violations = analyze_command_paths(command)
    if not violations:
        return True, ""

    # İlk 3 ihlali raporla
    summary = "; ".join(
        f"'{path}' ({desc})" for path, desc in violations[:3]
    )
    return False, f"🛡️ GÜVENLİK ENGELİ: Workspace dışına erişim denemesi: {summary}"


# ==================== PYTHON KODU ANALİZİ (AST) ====================

class PathViolation:
    def __init__(self, line: int, target: str, reason: str):
        self.line = line
        self.target = target
        self.reason = reason

    def __repr__(self):
        return f"Satır {self.line}: '{self.target}' ({self.reason})"


def _extract_string_arg(node: ast.AST) -> Optional[str]:
    """AST node'undan string değerini çıkarır."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def analyze_python_paths(code: str) -> List[PathViolation]:
    """Python kodu içerisinde workspace dışı dosya erişimlerini bulur."""
    violations = []

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            func_name = ""
            if isinstance(func, ast.Name):
                func_name = func.id
            elif isinstance(func, ast.Attribute):
                func_name = func.attr

            # open() fonksiyon kontrolü
            if func_name == "open":
                if len(node.args) >= 1:
                    path_arg = _extract_string_arg(node.args[0])
                    mode = "r"  # Varsayılan mod
                    if len(node.args) >= 2:
                        mode_arg = _extract_string_arg(node.args[1])
                        if mode_arg:
                            mode = mode_arg

                    # Yazma modlarından biri mi? (w, a, x, +)
                    if path_arg and any(c in mode for c in ("w", "a", "x", "+")):
                        if not _is_inside_workspace(path_arg):
                            violations.append(PathViolation(
                                line=node.lineno,
                                target=path_arg,
                                reason=f"open() yazma modu: '{mode}'"
                            ))

            # Pathlib write_text / write_bytes kontrolü
            elif func_name in ("write_text", "write_bytes"):
                if isinstance(func, ast.Attribute):
                    parent = func.value
                    if isinstance(parent, ast.Call):
                        parent_func_name = ""
                        if isinstance(parent.func, ast.Name):
                            parent_func_name = parent.func.id
                        elif isinstance(parent.func, ast.Attribute):
                            parent_func_name = parent.func.attr

                        if parent_func_name == "Path" and parent.args:
                            path_arg = _extract_string_arg(parent.args[0])
                            if path_arg and not _is_inside_workspace(path_arg):
                                violations.append(PathViolation(
                                    line=node.lineno,
                                    target=path_arg,
                                    reason=f"Pathlib {func_name}() kullanımı"
                                ))

    return violations


def is_python_path_safe(code: str) -> Tuple[bool, str]:
    """Hızlı kontrol: Python kodu çalışma alanı dışına yazıyor mu?"""
    violations = analyze_python_paths(code)
    if not violations:
        return True, ""

    summary = "; ".join(str(v) for v in violations[:3])
    return False, f"🛡️ GÜVENLİK ENGELİ: Workspace dışına yazma denemesi: {summary}"