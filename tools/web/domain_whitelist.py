"""
Domain Whitelist — sadece izinli sitelere istek yapılabilir.

Subdomain matching var: "wikipedia.org" whitelist'teyse,
"en.wikipedia.org" ve "tr.wikipedia.org" da otomatik kabul edilir.

Yeni site eklemek için ALLOWED_DOMAINS listesine ekle.
"""
from urllib.parse import urlparse


ALLOWED_DOMAINS = [
    # Bilgi
    "wikipedia.org",

    # Kod / Geliştirici
    "github.com",
    "raw.githubusercontent.com",
    "api.github.com",
    "gitlab.com",
    "stackoverflow.com",
    "stackexchange.com",
    "developer.mozilla.org",

    # Dokümantasyon
    "docs.python.org",
    "pypi.org",
    "readthedocs.io",
    "readthedocs.org",

    # Akademik
    "arxiv.org",
    "doi.org",

    # Topluluk / İçerik
    "news.ycombinator.com",
    "reddit.com",
    "medium.com",
    "dev.to",

    # Test
    "httpbin.org",

    # Crypto / Finance API'ler
    "api.binance.com",
    "api.coingecko.com",
]


def is_allowed(url: str) -> tuple[bool, str]:
    """
    URL'in whitelist'te olup olmadığını kontrol et.
    Subdomain matching: en.wikipedia.org → wikipedia.org match.

    Return: (allowed, reason_with_alternatives)
    """
    if not url or not isinstance(url, str):
        return False, "Geçersiz URL"

    # Schema kontrolü — sadece http/https
    if not url.startswith(("http://", "https://")):
        return False, f"Sadece http/https desteklenir: {url[:50]}"

    try:
        parsed = urlparse(url)
        host = parsed.hostname
        if not host:
            return False, "URL'de host yok"
    except Exception as e:
        return False, f"URL parse edilemedi: {e}"

    # Whitelist'te tam veya subdomain eşleşmesi
    host_lower = host.lower()
    for allowed in ALLOWED_DOMAINS:
        if host_lower == allowed or host_lower.endswith("." + allowed):
            return True, ""

    # 🆕 Reddedildi — kategoriye göre alternatif öner
    suggestion = _suggest_alternative(host_lower)
    base_msg = f"Domain whitelist'te değil: {host}"
    if suggestion:
        return False, f"{base_msg}\n💡 Alternatif (whitelist'te var): {suggestion}"
    return False, base_msg


def _suggest_alternative(host: str) -> str:
    """Bilinen reddedilen domain'ler için whitelist'teki alternatifleri öner."""
    # Kripto/finans alternatifleri
    crypto_keywords = ["coindesk", "cointelegraph", "coinmarketcap", "blockchain", "crypto", "btc", "bitcoin", "ethereum"]
    if any(kw in host for kw in crypto_keywords):
        return "api.coingecko.com (örn: /api/v3/simple/price?ids=bitcoin&vs_currencies=usd) veya api.binance.com (örn: /api/v3/ticker/price?symbol=BTCUSDT)"

    # News alternatifleri
    news_keywords = ["nytimes", "bbc", "cnn", "reuters", "bloomberg"]
    if any(kw in host for kw in news_keywords):
        return "news.ycombinator.com veya reddit.com/r/news/.json"

    # Code/dev alternatifleri
    if any(kw in host for kw in ["bitbucket", "sourceforge", "codeberg"]):
        return "github.com veya gitlab.com"

    # Genel kategori
    if "wiki" in host:
        return "wikipedia.org (use API: en.wikipedia.org/w/api.php)"

    return ""


def list_allowed() -> list[str]:
    """Whitelist'i döndür (debug/help için)."""
    return list(ALLOWED_DOMAINS)
