"""
Robots.txt Checker v6.7 — API bypass + zengin hata mesajları.

API endpoint'leri (Wikipedia API, Reddit JSON, vs.) robots.txt
kontrolünden muaf. Çünkü bunlar zaten botlar için tasarlanmış.

Scraping URL'leri (HTML sayfaları) reddedilirse, ajan'a API alternatifi
önerilir — kendi başına çözüm bulabilsin diye.
"""
import time
from urllib.parse import urlparse
from urllib import robotparser
from threading import Lock

from tools.web.api_endpoints import is_api_endpoint, suggest_api_for


USER_AGENT = "CelebiAgent/1.0"  # ASCII safe
CACHE_TTL_SECONDS = 3600


class RobotsCache:
    def __init__(self):
        self._cache: dict = {}
        self._lock = Lock()

    def _fetch(self, host: str, scheme: str = "https") -> robotparser.RobotFileParser:
        rp = robotparser.RobotFileParser()
        rp.set_url(f"{scheme}://{host}/robots.txt")
        try:
            rp.read()
        except Exception:
            # robots.txt erişilmiyorsa: standart davranış izin vermek
            # (RFC 9309)
            pass
        return rp

    def is_allowed(self, url: str) -> tuple[bool, str]:
        """URL'in robots.txt tarafından izinli olup olmadığını kontrol et."""

        # 🔑 BURASI YENİ: API endpoint ise robots.txt'yi atla
        if is_api_endpoint(url):
            return True, ""

        try:
            parsed = urlparse(url)
            host = parsed.hostname
            scheme = parsed.scheme or "https"
            if not host:
                return True, ""
        except Exception:
            return True, ""

        with self._lock:
            cached = self._cache.get(host)
            now = time.time()

            if not cached or (now - cached[1]) > CACHE_TTL_SECONDS:
                rp = self._fetch(host, scheme)
                self._cache[host] = (rp, now)
            else:
                rp = cached[0]

        try:
            allowed = rp.can_fetch(USER_AGENT, url)
            if allowed:
                return True, ""

            # Reddedildi — API önerisi ekle
            base_msg = f"robots.txt scraping'i reddediyor: {url}"
            api_suggestion = suggest_api_for(url)

            if api_suggestion:
                full_msg = (
                    f"{base_msg}\n\n"
                    f"💡 Çözüm: Bu site için resmi API kullan:\n"
                    f"{api_suggestion}\n\n"
                    f"API URL'lerine robots.txt kontrolü uygulanmaz."
                )
            else:
                full_msg = (
                    f"{base_msg}\n\n"
                    f"💡 Bu site botları reddediyor. "
                    f"Resmi API arayabilir veya başka kaynak kullanabilirsin."
                )

            return False, full_msg
        except Exception:
            # Parse hatası — varsayılan izin
            return True, ""


_cache = RobotsCache()


def is_allowed(url: str) -> tuple[bool, str]:
    return _cache.is_allowed(url)
