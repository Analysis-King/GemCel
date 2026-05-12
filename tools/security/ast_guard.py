"""
AST Guard v6.9 — Akıllı Engelleme ve Alternatif Önerisi

Yenilikler:
  - Engellenen çağrılar için ALTERNATİF araç önerileri eklendi.
  - Yasaklanan eylemler için ajana net bir çıkış yolu (web_fetch, execute_command vb.) gösterilir.
  - Bu yapı, ajanı kısırdöngüye (loop) girmekten kurtarır.
"""
import ast
from typing import List, Tuple

# Yasaklı (modül, fonksiyon) çiftleri
DANGEROUS_CALLS = {
    # Sistem komutları (Doğrudan erişim yasak, execute_command kullanılmalı)
    ("os", "system"), ("os", "popen"),
    ("os", "execv"), ("os", "execve"), ("os", "execvp"), ("os", "execvpe"),
    ("os", "spawnv"), ("os", "spawnve"), ("os", "spawnvp"), ("os", "spawnvpe"),

    # Subprocess (Doğrudan erişim yasak)
    ("subprocess", "run"), ("subprocess", "call"), ("subprocess", "Popen"),
    ("subprocess", "check_output"), ("subprocess", "check_call"),
    ("subprocess", "getoutput"), ("subprocess", "getstatusoutput"),

    # Dosya Sistemi (Tehlikeli silme işlemleri)
    ("shutil", "rmtree"),
    ("os", "remove"), ("os", "unlink"), ("os", "rmdir"), ("os", "removedirs"),

    # Network (Doğrudan kütüphane erişimi yasak, web_fetch kullanılmalı)
    ("socket", "socket"),
    ("urllib.request", "urlopen"),
    ("requests", "get"), ("requests", "post"), ("requests", "put"), ("requests", "delete"),
    ("httpx", "get"), ("httpx", "post"),
}

DANGEROUS_BUILTINS = {
    "exec", "eval", "compile", "__import__",
}

DANGEROUS_IMPORTS = {
    "ctypes", "ptrace",
}

# Alternatif öneriler — Yasaklı çağrı yerine hangi TOOL kullanılmalı?
ALTERNATIVES = {
    # Network → web_fetch tool
    "requests.get": "web_fetch aracını kullan: {'action': 'web_fetch', 'input': {'url': '...'}}",
    "requests.post": "web_fetch sadece GET destekler. Yazma/Gönderme istekleri kısıtlıdır.",
    "requests.put": "Yazma istekleri desteklenmez.",
    "requests.delete": "Silme istekleri desteklenmez.",
    "httpx.get": "web_fetch aracını kullan.",
    "httpx.post": "web_fetch sadece GET destekler.",
    "urllib.request.urlopen": "web_fetch aracını kullan.",
    "socket.socket": "Düşük seviye ağ erişimi desteklenmez. web_fetch deneyin.",

    # Sistem komutları → execute_command
    "os.system": "execute_command aracını kullan: {'action': 'execute_command', 'input': {'command': '...'}}",
    "os.popen": "execute_command aracını kullan.",
    "subprocess.run": "execute_command aracını kullan.",
    "subprocess.call": "execute_command aracını kullan.",
    "subprocess.Popen": "execute_command aracını kullan.",
    "subprocess.check_output": "execute_command aracını kullan.",

    # Dinamik çalıştırma
    "exec": "Dinamik kod çalıştırma yasak. Lütfen statik kod yazın.",
    "eval": "eval() yerine güvenli veri işleme için ast.literal_eval() veya statik kod kullanın.",

    # Dosya işlemleri
    "shutil.rmtree": "Workspace dışı silme yasak. Workspace içi için os.unlink + os.rmdir kullanın.",
    "os.remove": "Dosya silmek için os.unlink() kullanın (Workspace içinde).",
}

class ASTViolation:
    def __init__(self, line: int, code: str, reason: str, alternative: str = ""):
        self.line = line
        self.code = code
        self.reason = reason
        self.alternative = alternative

    def __repr__(self):
        msg = f"Satır {self.line}: {self.reason}"
        if self.alternative:
            msg += f"\n   💡 ÖNERİ: {self.alternative}"
        return msg

def _get_call_target(node: ast.Call) -> Tuple[str, str]:
    """Fonksiyon çağrısının modülünü ve adını belirler."""
    func = node.func
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Name):
            return (func.value.id, func.attr)
        elif isinstance(func.value, ast.Attribute):
            return (func.value.attr, func.attr)
        else:
            return ("", func.attr)
    elif isinstance(func, ast.Name):
        return ("", func.id)
    return ("", "")

def _alternative_for(module: str, func: str) -> str:
    """Yasaklı çağrı için sistemdeki uygun aracı (tool) önerir."""
    full = f"{module}.{func}" if module else func
    return ALTERNATIVES.get(full, "")

def analyze(code: str) -> List[ASTViolation]:
    """Python kodunu analiz eder ve ihlalleri listeler."""
    violations = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        # Import kontrolleri
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in DANGEROUS_IMPORTS:
                    violations.append(ASTViolation(
                        line=node.lineno,
                        code=f"import {alias.name}",
                        reason=f"Yasaklı modül tespiti: {alias.name}"
                    ))

        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module in DANGEROUS_IMPORTS:
                violations.append(ASTViolation(
                    line=node.lineno,
                    code=f"from {node.module} import ...",
                    reason=f"Yasaklı modül tespiti: {node.module}"
                ))

        # Fonksiyon çağrı kontrolleri
        elif isinstance(node, ast.Call):
            module, func = _get_call_target(node)

            # Built-in kontrolleri
            if not module and func in DANGEROUS_BUILTINS:
                alt = _alternative_for("", func)
                violations.append(ASTViolation(
                    line=node.lineno,
                    code=f"{func}(...)",
                    reason=f"Güvenli olmayan yerleşik fonksiyon: {func}",
                    alternative=alt
                ))

            # Modül çağrı kontrolleri
            elif (module, func) in DANGEROUS_CALLS:
                alt = _alternative_for(module, func)
                violations.append(ASTViolation(
                    line=node.lineno,
                    code=f"{module}.{func}(...)",
                    reason=f"Güvenli olmayan kütüphane çağrısı: {module}.{func}",
                    alternative=alt
                ))

    return violations

def is_safe(code: str) -> Tuple[bool, str]:
    """
    Dış dünyadan çağrılan ana kontrol fonksiyonu.
    Dönüş: (güvenli_mi, rapor_metni)
    """
    violations = analyze(code)

    if not violations:
        return True, ""

    # İlk 3 ihlali raporla (ajana çok fazla bilgi yığmamak için)
    parts = [str(v) for v in violations[:3]]
    summary = "\n".join(parts)
    
    if len(violations) > 3:
        summary += f"\n... ve {len(violations) - 3} ihlal daha tespit edildi."

    return False, summary