"""
Bilinen API endpoint'leri.

Scraping (HTML çekme) ile API kullanımı arasındaki fark:
  - Scraping: bir HTML sayfasını byte byte indirip parse etmek. Çoğu site
    bunu robots.txt ile reddeder (botların aşırı trafik yaratmaması için).
  - API: site'ın botlar için açtığı resmi giriş noktası. Yapılandırılmış
    veri (JSON/XML) döner. Genelde rate limit'i daha makul.

Bu modül iki şey yapar:
  1. URL'in API endpoint'i olup olmadığını anlar (robots.txt'yi atla)
  2. Belirli sayfa için API alternatifi öner (Wikipedia → wiki API)
"""
from urllib.parse import urlparse, parse_qs


# Bilinen API endpoint pattern'ları
# Bu URL'lere giderken robots.txt kontrolü yapılmaz
API_PATTERNS = [
    # Wikipedia API
    "wikipedia.org/w/api.php",
    "wikipedia.org/api/rest_v1/",
    "wikidata.org/w/api.php",

    # Reddit JSON
    "reddit.com/.json",
    "reddit.com/r/",  # /r/<sub>/.json formatı
    "old.reddit.com",

    # Stack Exchange
    "api.stackexchange.com",

    # GitHub API
    "api.github.com",

    # ArXiv API
    "export.arxiv.org/api",

    # CoinGecko API
    "api.coingecko.com",

    # Binance API
    "api.binance.com",

    # PyPI API
    "pypi.org/pypi/",  # /pypi/<package>/json formatı
]


def is_api_endpoint(url: str) -> bool:
    """
    URL bilinen bir API endpoint'i mi?
    Eğer evet, robots.txt kontrolünden muaf tutulur.
    """
    if not url:
        return False

    url_lower = url.lower()
    for pattern in API_PATTERNS:
        if pattern in url_lower:
            return True

    # Reddit özel kontrolü: .json ile bitiyorsa API'dir
    if "reddit.com" in url_lower and url_lower.endswith(".json"):
        return True

    # PyPI özel: /pypi/<pkg>/json bir API'dir
    if "pypi.org/pypi/" in url_lower and url_lower.endswith("/json"):
        return True

    return False


# Site bazlı API alternatif önerileri (scraping reddedildiğinde gösterilir)
API_SUGGESTIONS = {
    "wikipedia.org": (
        "Wikipedia için resmi API kullanın:\n"
        "  https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts"
        "&exintro=true&explaintext=true&titles=YOUR_TOPIC\n"
        "Örnek: 'Python_(programming_language)' başlığını çekmek için 'titles=Python_(programming_language)'"
    ),
    "reddit.com": (
        "Reddit için JSON endpoint kullanın:\n"
        "  https://www.reddit.com/r/SUBREDDIT/.json\n"
        "  https://www.reddit.com/r/SUBREDDIT/hot.json?limit=10"
    ),
    "stackoverflow.com": (
        "Stack Exchange API kullanın:\n"
        "  https://api.stackexchange.com/2.3/questions?site=stackoverflow&order=desc&sort=activity"
    ),
    "stackexchange.com": (
        "Stack Exchange API: https://api.stackexchange.com/2.3/"
    ),
    "github.com": (
        "GitHub API kullanın:\n"
        "  https://api.github.com/repos/OWNER/REPO\n"
        "  https://api.github.com/repos/OWNER/REPO/issues"
    ),
    "arxiv.org": (
        "ArXiv API kullanın:\n"
        "  http://export.arxiv.org/api/query?search_query=all:KEYWORDS&max_results=10"
    ),
}


def suggest_api_for(url: str) -> str | None:
    """
    Verilen URL için API alternatifi var mı?
    Return: öneri string'i ya da None
    """
    if not url:
        return None

    url_lower = url.lower()
    for site, suggestion in API_SUGGESTIONS.items():
        if site in url_lower:
            return suggestion

    return None
