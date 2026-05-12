"""
Web Fetcher v6.10 — Liste odaklı düzleştirme (Flatten).

Bu modül, web sayfalarından veya API'lerden gelen verileri çeker.
Özellikle Reddit veya GitHub gibi JSON dönen yapılarda veriyi anlamlı şekilde temizler.
"""
import json
from urllib.parse import urlparse
from typing import Optional, Any

# Güvenlik ve limit kontrol modülleri (Projenin ilgili yollarında olduğu varsayılır)
from tools.web.domain_whitelist import is_allowed as is_domain_allowed
from tools.web.rate_limiter import check_and_record
from tools.web.robots_checker import is_allowed as is_robots_allowed
from tools.web.injection_filter import sanitize


DEFAULT_TIMEOUT = 15
MAX_RESPONSE_SIZE = 3500
USER_AGENT = "CelebiAgent/1.0 (otonom araştırma botu)"


# Liste içindeki her öğe için öncelikli gösterilecek alanlar
LIST_ITEM_KEY_FIELDS = [
    "title", "name", "full_name", "summary", "description",
    "version", "url", "permalink", "author", "subreddit",
    "score", "ups", "stargazers_count",
]


# Genel önemli alan adları (liste dışı, üst seviye veriler için)
PRIORITY_FIELD_NAMES = {
    "name", "full_name", "description", "language", "topics",
    "stargazers_count", "forks_count", "forks", "watchers_count", "watchers",
    "open_issues_count", "subscribers_count", "size",
    "default_branch", "homepage",
    "version", "summary", "author", "author_email", "license",
    "requires_python", "keywords", "home_page",
    "title", "extract", "pageid",
    "subreddit", "ups", "score", "num_comments", "permalink",
    "abstract", "published", "updated",
    "id", "url", "created_at", "updated_at", "type", "kind",
}


def _truncate(text: str, limit: int = MAX_RESPONSE_SIZE) -> str:
    """Metni belirlenen sınıra göre keser."""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n\n... [KESİLDİ, {len(text) - limit} karakter daha var]"


def _try_httpx(url: str, timeout: int) -> Optional[tuple[int, str, str]]:
    """httpx kütüphanesini kullanarak veri çekmeyi dener."""
    try:
        import httpx
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT}
        ) as client:
            response = client.get(url)
            return (
                response.status_code,
                response.headers.get("content-type", "unknown"),
                response.text,
            )
    except Exception:
        return None


def _try_requests(url: str, timeout: int) -> Optional[tuple[int, str, str]]:
    """requests kütüphanesini kullanarak veri çekmeyi dener."""
    try:
        import requests
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": USER_AGENT}
        )
        return (
            response.status_code,
            response.headers.get("content-type", "unknown"),
            response.text,
        )
    except Exception:
        return None


def _find_main_list(data: Any, path: str = "") -> tuple[str, list]:
    """
    JSON içerisinde ana veri listesini bulur (Reddit: children, GitHub: items vb.).
    """
    if isinstance(data, list) and len(data) > 1 and isinstance(data[0], dict):
        return path, data

    if isinstance(data, dict):
        # Yaygın kullanılan liste anahtar kelimeleri
        for preferred in ["children", "items", "results", "entries", "feed", "hits"]:
            if preferred in data and isinstance(data[preferred], list):
                if len(data[preferred]) > 0 and isinstance(data[preferred][0], dict):
                    child_path = f"{path}.{preferred}" if path else preferred
                    return child_path, data[preferred]

        # 'data' katmanı altındaki listeleri kontrol et (Reddit yapısı)
        if "data" in data and isinstance(data["data"], dict):
            child_path = f"{path}.data" if path else "data"
            found = _find_main_list(data["data"], child_path)
            if found[1]:
                return found

    return "", []


def _extract_item_summary(item: dict) -> str:
    """Bir liste öğesindeki önemli alanları özetler."""
    if not isinstance(item, dict):
        return str(item)[:120]

    # Nested 'data' kontrolü
    nested = item.get("data") if isinstance(item.get("data"), dict) else None
    source = nested if nested else item

    parts = []
    for key in LIST_ITEM_KEY_FIELDS:
        if key in source:
            value = source[key]
            value_str = str(value)
            if len(value_str) > 150:
                value_str = value_str[:150] + "..."
            parts.append(f"{key}={value_str}")
            if len(parts) >= 2:  # Her öğe için en fazla 2 alan
                break

    return " | ".join(parts) if parts else str(source)[:120]


def _flatten_top_level(data: Any, prefix: str = "", max_depth: int = 3, depth: int = 0,
                       skip_paths: set = None) -> list[tuple[str, str]]:
    """Sözlük yapısını düzleştirir ancak ana listeyi atlar."""
    items = []
    if depth >= max_depth or skip_paths is None:
        skip_paths = skip_paths or set()

    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix}.{key}" if prefix else key

            if new_prefix in skip_paths:
                continue

            if isinstance(value, list):
                items.append((new_prefix, f"[{len(value)} öğeli liste]"))
            elif isinstance(value, dict):
                if depth + 1 < max_depth:
                    items.extend(_flatten_top_level(value, new_prefix, max_depth, depth + 1, skip_paths))
                else:
                    items.append((new_prefix, "[iç içe obje]"))
            else:
                value_str = str(value)
                if len(value_str) > 200:
                    value_str = value_str[:200] + "..."
                items.append((new_prefix, value_str))
    return items


def _is_priority(key: str) -> bool:
    """Alanın öncelikli olup olmadığını kontrol eder."""
    last_segment = key.split(".")[-1].split("[")[0]
    return last_segment in PRIORITY_FIELD_NAMES


def _format_json_response(body: str) -> str:
    """JSON yanıtını liste farkındalığıyla formatlar."""
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return body

    parts = []

    # 1. Ana listeyi tespit et
    list_path, main_list = _find_main_list(data)

    if main_list and len(main_list) >= 2:
        parts.append(f"🎯 '{list_path}' İÇERİSİNDEKİ LİSTE ({len(main_list)} öğe):")
        for i, item in enumerate(main_list[:10]):
            summary = _extract_item_summary(item)
            parts.append(f"  [{i}] {summary}")
        if len(main_list) > 10:
            parts.append(f"  ... ({len(main_list) - 10} öğe daha var)")
        parts.append("")

    # 2. Üst seviye alanlar
    skip = {list_path} if list_path else set()
    top_items = _flatten_top_level(data, skip_paths=skip)

    if top_items:
        priority = [(k, v) for k, v in top_items if _is_priority(k)]
        other = [(k, v) for k, v in top_items if not _is_priority(k)]

        if priority:
            parts.append("📋 ÖNEMLİ ALANLAR:")
            for key, value in priority[:15]:
                parts.append(f"  {key} = {value}")
            parts.append("")

        if other:
            parts.append("📦 Diğer alanlar:")
            for key, value in other[:8]:
                display_value = value if len(str(value)) < 100 else str(value)[:100] + "..."
                parts.append(f"  {key} = {display_value}")
            if len(other) > 8:
                parts.append(f"  ... ({len(other) - 8} tane daha)")

    return "\n".join(parts)


def web_fetch(url: str, extract_text: bool = False) -> str:
    """Web içeriğini çekmek için ana fonksiyon."""
    if not url or not isinstance(url, str):
        return "HATA: URL boş veya geçersiz."

    allowed, reason = is_domain_allowed(url)
    if not allowed:
        return f"🛡️ GÜVENLİK ENGELİ (ALAN ADI): {reason}"

    try:
        host = urlparse(url).hostname
    except Exception as e:
        return f"HATA: URL ayrıştırılamadı: {e}"

    can_proceed, reason = check_and_record(host)
    if not can_proceed:
        return f"🛡️ HIZ LİMİTİ: {reason}"

    can_fetch, reason = is_robots_allowed(url)
    if not can_fetch:
        return f"🛡️ ROBOTS.TXT: {reason}"

    result = _try_httpx(url, DEFAULT_TIMEOUT)
    engine_used = "httpx"
    if result is None:
        result = _try_requests(url, DEFAULT_TIMEOUT)
        engine_used = "requests"

    if result is None:
        return f"HATA: Bağlantı sağlanamadı. URL: {url}"

    status, content_type, body = result

    if status >= 400:
        return f"HATA: HTTP {status} ({engine_used})\nURL: {url}\nİçerik: {body[:300]}"

    is_json = "json" in content_type.lower()
    if is_json:
        body = _format_json_response(body)

    if extract_text and "html" in content_type.lower():
        body = _extract_text_from_html(body)

    truncated = _truncate(body)
    sanitized, findings = sanitize(truncated)

    header = (
        f"URL: {url}\n"
        f"Durum: {status} ({engine_used})\n"
        f"İçerik Türü: {content_type}\n"
    )

    if findings:
        high = sum(1 for f in findings if f.severity == "high")
        med = sum(1 for f in findings if f.severity == "medium")
        header += f"Enjeksiyon Taraması: {high} yüksek, {med} orta risk bulundu\n"

    return header + "\n" + sanitized


def _extract_text_from_html(html: str) -> str:
    """HTML içeriğinden sadece metinleri ayıklar."""
    import re
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    # HTML varlıklarını temizle
    replacements = {
        "&amp;": "&", "&lt;": "<", "&gt;": ">",
        "&quot;": '"', "&#39;": "'", "&nbsp;": " "
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text