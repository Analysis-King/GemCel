"""
Rate Limiter — site başına istek sıklığı kontrolü.

Bot olarak banlanmak istemediğimiz için:
  - Site başına saatte max 30 istek (default)
  - Site başına ardışık iki istek arasında min 1 saniye

In-memory cache — process restart edilince sıfırlanır. Bu kabul edilebilir
çünkü asıl ban koruması ajan oturumları arası kalıcı değil.

Faz 5'te (daemon mode) bu state'i SQLite'a yazabiliriz.
"""
import time
from collections import defaultdict, deque
from threading import Lock


# Konfigürasyon
MAX_REQUESTS_PER_HOUR = 30
MIN_INTERVAL_SECONDS = 1.0


class RateLimiter:
    """Thread-safe rate limiter, host bazlı."""

    def __init__(self):
        # host → deque[float] (timestamps)
        self._requests: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def check(self, host: str) -> tuple[bool, str]:
        """
        Bu host'a istek yapılabilir mi?
        Return: (allowed, reason_if_not)
        """
        with self._lock:
            now = time.time()
            timestamps = self._requests[host]

            # 1 saatten eski timestamp'leri temizle
            cutoff = now - 3600
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()

            # Saatlik limit kontrolü
            if len(timestamps) >= MAX_REQUESTS_PER_HOUR:
                oldest = timestamps[0]
                wait_seconds = int(3600 - (now - oldest))
                return False, (
                    f"Saatlik limit aşıldı ({MAX_REQUESTS_PER_HOUR} istek/saat). "
                    f"{wait_seconds}s sonra tekrar dene."
                )

            # Ardışık istek arası minimum kontrolü
            if timestamps and (now - timestamps[-1]) < MIN_INTERVAL_SECONDS:
                wait = MIN_INTERVAL_SECONDS - (now - timestamps[-1])
                return False, (
                    f"Çok hızlı istek. {wait:.1f}s bekle."
                )

            return True, ""

    def record(self, host: str):
        """İsteği kayda al (başarılı olduğunda çağrılmalı)."""
        with self._lock:
            self._requests[host].append(time.time())

    def stats(self) -> dict:
        """Mevcut durum (debug için)."""
        with self._lock:
            now = time.time()
            cutoff = now - 3600
            return {
                host: sum(1 for t in ts if t >= cutoff)
                for host, ts in self._requests.items()
                if ts
            }


# Global instance
_limiter = RateLimiter()


def check_and_record(host: str) -> tuple[bool, str]:
    """
    Tek seferde kontrol + kayıt.
    Eğer izin varsa otomatik record çağrılır.
    """
    allowed, reason = _limiter.check(host)
    if allowed:
        _limiter.record(host)
    return allowed, reason


def get_stats() -> dict:
    return _limiter.stats()
