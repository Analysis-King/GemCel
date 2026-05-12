"""
Command Guard v6.11 — execute_command için Güvenlik Filtresi

Bu modül, shell komutlarını metin bazlı desen (pattern) analizi ile denetler.
Yasaklı işlemler tespit edildiğinde komutun icrasını durdurur.

Kapsanan Kategoriler:
  1. Sistem yıkıcı işlemler (rm -rf, dd, fork bomb)
  2. Yetki yükseltme (sudo, su)
  3. İndirme ve çalıştırma (curl | sh, wget | sh)
  4. Sistem dosyalarına müdahale (/etc/, /root/ vb.)
  5. Ağ manipülasyonu (iptables, ifconfig)
"""
import re
from typing import Tuple, List

# Kesinlikle engellenen tehlikeli desenler (Regex)
DANGEROUS_PATTERNS = [
    # --- Sistem Yıkıcı Komutlar ---
    (r"\brm\s+-rf\s+/", "rm -rf / — Kök dizin silme girişimi"),
    (r"\brm\s+-rf\s+~", "rm -rf ~ — Kullanıcı dizini silme girişimi"),
    (r"\brm\s+-rf\s+\$HOME", "rm -rf $HOME — Home dizini silme girişimi"),
    (r"\bdd\s+if=", "dd komutu — Doğrudan disk yazma işlemi yasak"),
    (r"\bmkfs\b", "mkfs — Disk formatlama işlemi yasak"),
    (r":\s*\(\s*\)\s*\{[^}]*:\s*\|\s*:\s*&", "Fork bomb — Sistem kaynaklarını tüketme girişimi"),

    # --- Yetki Yükseltme (Privilege Escalation) ---
    (r"\bsudo\b", "sudo — Yetki yükseltme (root yetkisi) yasak"),
    (r"^su\s", "su — Kullanıcı değiştirme yasak"),
    (r"\bsu\s+-", "su - — Root oturumu açma girişimi yasak"),

    # --- Uzaktan Kod İndirme ve Çalıştırma ---
    (r"curl[^|]*\|\s*(sh|bash|python|zsh|python3)", "curl | shell — Uzaktan indirilip doğrudan kod çalıştırma yasak"),
    (r"wget[^|]*\|\s*(sh|bash|python|zsh|python3)", "wget | shell — Uzaktan indirilip doğrudan kod çalıştırma yasak"),
    (r"curl[^>]*>\s*/(?:tmp|var|etc|usr|bin|sbin)", "curl ile sistem dizinlerine dosya indirme yasak"),

    # --- Kritik Sistem Dosyalarına Müdahale ---
    (r"echo[^>]*>\s*/etc/", "/etc/ altındaki konfigürasyonlara müdahale yasak"),
    (r">\s*/etc/passwd", "/etc/passwd dosyasını değiştirme girişimi"),
    (r">\s*/etc/shadow", "/etc/shadow dosyasını değiştirme girişimi"),
    (r"\bchattr\b", "Dosya özniteliklerini değiştirme (immutable vb.) yasak"),

    # --- Ağ ve Güvenlik Manipülasyonu ---
    (r"\biptables\s+(-A|-D|-I|-F|-P|-N|-X)", "iptables — Güvenlik duvarı kurallarını değiştirme yasak"),
    (r"\bifconfig\s+\w+\s+(up|down)", "Ağ arayüzü durumunu değiştirme yasak"),
    (r"\buwf\s+", "UWF kurallarına müdahale yasak"),

    # --- Zamanlanmış Görevler ---
    (r"\bcrontab\s+(-r|-e)", "Kullanıcı crontab dosyasını silme veya düzenleme yasak"),

    # --- SSH Yetkilendirme ---
    (r">>\s*~/\.ssh/authorized_keys", "SSH yetkili anahtar ekleme girişimi"),
    (r">\s*~/\.ssh/", "SSH yapılandırma dosyalarını değiştirme girişimi"),
]

# Şüpheli bulunan ama tamamen yasaklanmayan desenler (Sadece uyarı verilir)
SUSPICIOUS_PATTERNS = [
    (r"\bchmod\s+777", "chmod 777 — Aşırı geniş (tehlikeli) izin tanımlaması"),
    (r"\bchown\s+", "chown — Dosya sahipliği değiştirme girişimi"),
    (r"^kill\s+-9", "kill -9 — Süreçleri zorla sonlandırma"),
    (r"\bnmap\b", "nmap — Ağ tarama aracı kullanımı (Denetlenmelidir)"),
]

class CommandViolation:
    def __init__(self, pattern: str, reason: str, severity: str = "high"):
        self.pattern = pattern
        self.reason = reason
        self.severity = severity  # "high" = Kesin blok, "medium" = Uyarı

    def __repr__(self):
        return f"[{self.severity.upper()}] {self.reason}"

def analyze(command: str) -> List[CommandViolation]:
    """
    Verilen komutu tüm güvenlik desenleri üzerinden tarar.
    İhlalleri liste olarak döner.
    """
    violations = []

    # Yüksek riskli (High) kontroller
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            violations.append(CommandViolation(pattern, reason, "high"))

    # Orta riskli (Medium) kontroller
    for pattern, reason in SUSPICIOUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            violations.append(CommandViolation(pattern, reason, "medium"))

    return violations

def is_safe(command: str) -> Tuple[bool, str]:
    """
    Orchestrator tarafından çağrılan ana kontrol fonksiyonu.
    
    Eğer 'high' severity ihlal varsa: False döner (Komut engellenir).
    Eğer sadece 'medium' ihlal varsa: True döner ama uyarı mesajı eklenir.
    """
    violations = analyze(command)

    # Kesin engellenmesi gereken ihlalleri ayıkla
    high_severity = [v for v in violations if v.severity == "high"]
    if high_severity:
        summary = "🛡️ GÜVENLİK ENGELİ: " + "; ".join(str(v) for v in high_severity)
        return False, summary

    # Sadece şüpheli işlemler varsa izin ver ama uyar
    if violations:
        summary = "⚠️ UYARI: " + "; ".join(str(v) for v in violations)
        return True, summary

    # Tertemiz komut
    return True, ""