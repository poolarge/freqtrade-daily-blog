"""Fetch and parse Freqtrade documentation from the official site."""

import re
import requests
from pathlib import Path

BASE_URL = "https://www.freqtrade.io/en/stable"
CACHE_DIR = Path(__file__).parent.parent / "state"

TOPIC_URLS = {
    "quickstart": f"{BASE_URL}/docker_quickstart/",
    "installation": f"{BASE_URL}/installation/",
    "configuration": f"{BASE_URL}/configuration/",
    "strategy-quickstart": f"{BASE_URL}/strategy-quickstart/",
    "strategy-customization": f"{BASE_URL}/strategy-customization/",
    "strategy-callbacks": f"{BASE_URL}/strategy-callbacks/",
    "stoploss": f"{BASE_URL}/stoploss/",
    "plugins": f"{BASE_URL}/plugins/",
    "bot-operation": f"{BASE_URL}/bot-operation/",
    "telegram-control": f"{BASE_URL}/telegram-usage/",
    "frequi": f"{BASE_URL}/frequi/",
    "rest-api": f"{BASE_URL}/rest-api/",
    "data-downloading": f"{BASE_URL}/data-downloading/",
    "backtesting": f"{BASE_URL}/backtesting/",
    "hyperopt": f"{BASE_URL}/hyperopt/",
    "short-leverage": f"{BASE_URL}/leverage/",
    "plotting": f"{BASE_URL}/plotting/",
    "exchange-specific": f"{BASE_URL}/exchanges/",
    "freqai-intro": f"{BASE_URL}/freqai/",
    "freqai-configuration": f"{BASE_URL}/freqai-configuration/",
    "producer-consumer": f"{BASE_URL}/producer-consumer/",
    "utility-commands": f"{BASE_URL}/utils/",
    "advanced-strategy": f"{BASE_URL}/strategy-customization/",
    "faq": f"{BASE_URL}/faq/",
    "updating-migration": f"{BASE_URL}/updating/",
}

# Fallback URLs for topics that redirect or have different paths
TOPIC_FALLBACK_URLS = {
    "freqai-configuration": f"{BASE_URL}/freqai/",
}


def _html_to_markdown(html: str) -> str:
    """Simple HTML to markdown conversion for documentation pages."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(["nav", "footer", "script", "style", "header"]):
        tag.decompose()

    main = soup.find("article") or soup.find("div", class_="md-content") or soup.find("main") or soup

    lines = []
    for el in main.descendants:
        if el.name == "h1":
            lines.append(f"\n# {el.get_text(strip=True)}\n")
        elif el.name == "h2":
            lines.append(f"\n## {el.get_text(strip=True)}\n")
        elif el.name == "h3":
            lines.append(f"\n### {el.get_text(strip=True)}\n")
        elif el.name == "h4":
            lines.append(f"\n#### {el.get_text(strip=True)}\n")
        elif el.name == "p":
            text = el.get_text(strip=True)
            if text:
                lines.append(f"\n{text}\n")
        elif el.name == "pre":
            code = el.get_text()
            lang = ""
            if el.find("code"):
                classes = el.find("code").get("class", [])
                for c in classes:
                    if c.startswith("language-") or c.startswith("highlight-"):
                        lang = c.split("-")[-1]
                        break
            lines.append(f"\n```{lang}\n{code.strip()}\n```\n")
        elif el.name == "code" and el.parent.name != "pre":
            lines.append(f"`{el.get_text()}`")
        elif el.name == "li":
            text = el.get_text(strip=True)
            if text:
                lines.append(f"- {text}")
        elif el.name == "table":
            for row in el.find_all("tr"):
                cells = [td.get_text(strip=True) for td in row.find_all(["th", "td"])]
                if row.find("th"):
                    lines.append("| " + " | ".join(cells) + " |")
                    lines.append("| " + " | ".join(["---"] * len(cells)) + " |")
                else:
                    lines.append("| " + " | ".join(cells) + " |")

    content = "\n".join(lines)
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


def _extract_code_examples(markdown: str) -> list[dict]:
    """Extract code blocks from markdown."""
    pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
    examples = []
    for m in pattern.finditer(markdown):
        examples.append({
            "language": m.group(1) or "text",
            "code": m.group(2).strip(),
        })
    return examples


def fetch_topic(topic_slug: str) -> dict:
    """Fetch a single Freqtrade documentation topic."""
    url = TOPIC_URLS.get(topic_slug)
    if not url:
        raise ValueError(f"Unknown topic: {topic_slug}")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"doc_{topic_slug}.md"

    if cache_file.exists():
        import time
        age = time.time() - cache_file.stat().st_mtime
        if age < 86400:
            raw_md = cache_file.read_text()
            return {
                "topic": topic_slug,
                "title": raw_md.split("\n")[0].lstrip("# ").strip(),
                "source_url": url,
                "raw_markdown": raw_md,
                "code_examples": _extract_code_examples(raw_md),
            }

    # Try primary URL, fall back to alternative if 404
    urls_to_try = [url]
    fallback = TOPIC_FALLBACK_URLS.get(topic_slug)
    if fallback:
        urls_to_try.append(fallback)

    raw_md = None
    for try_url in urls_to_try:
        print(f"  Fetching {try_url}...")
        try:
            resp = requests.get(try_url, timeout=60)
            resp.raise_for_status()
            raw_md = _html_to_markdown(resp.text)
            break
        except requests.HTTPError:
            continue

    if raw_md is None:
        raise ValueError(f"Failed to fetch topic '{topic_slug}' from any URL")

    cache_file.write_text(raw_md)

    return {
        "topic": topic_slug,
        "title": raw_md.split("\n")[0].lstrip("# ").strip(),
        "source_url": url,
        "raw_markdown": raw_md,
        "code_examples": _extract_code_examples(raw_md),
    }


if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "quickstart"
    data = fetch_topic(topic)
    print(f"Title: {data['title']}")
    print(f"Source: {data['source_url']}")
    print(f"Code examples: {len(data['code_examples'])}")
    print(f"Content length: {len(data['raw_markdown'])} chars")
    print("---")
    print(data["raw_markdown"][:2000])