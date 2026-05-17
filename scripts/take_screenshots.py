"""Take terminal screenshots using Playwright for blog posts."""

import html
import re
import subprocess
import tempfile
from pathlib import Path

SCREENSHOTS_DIR = Path(__file__).parent.parent / "assets" / "images" / "screenshots"

TERMINAL_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
  body {{
    margin: 0;
    padding: 0;
    background: #0d1117;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 20px;
  }}
  .terminal {{
    font-family: 'JetBrains Mono', 'Fira Code', 'Menlo', monospace;
    font-size: 14px;
    line-height: 1.6;
    color: #e0e0e0;
    background: #1a1a2e;
    padding: 0;
    border-radius: 12px;
    width: 820px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    overflow: hidden;
  }}
  .titlebar {{
    background: #2d2d44;
    padding: 10px 16px;
    display: flex;
    gap: 8px;
    align-items: center;
  }}
  .dot {{
    width: 12px; height: 12px;
    border-radius: 50%;
    display: inline-block;
  }}
  .dot-red {{ background: #ff5f57; }}
  .dot-yellow {{ background: #febc2e; }}
  .dot-green {{ background: #28c840; }}
  .title-text {{
    color: #8b949e;
    font-size: 12px;
    margin-left: 8px;
  }}
  .terminal-body {{
    padding: 16px 20px;
    white-space: pre-wrap;
    word-wrap: break-word;
  }}
  .prompt {{ color: #d97757; font-weight: 700; }}
  .command {{ color: #a9dc76; }}
  .output {{ color: #c9d1d9; }}
  .comment {{ color: #6a737d; }}
  .highlight {{ color: #79c0ff; }}
  .error {{ color: #f85149; }}
</style>
</head>
<body>
  <div class="terminal">
    <div class="titlebar">
      <span class="dot dot-red"></span>
      <span class="dot dot-yellow"></span>
      <span class="dot dot-green"></span>
      <span class="title-text">{title}</span>
    </div>
    <div class="terminal-body">{content}</div>
  </div>
</body>
</html>"""


def _render_segment(prompt: str, command: str, output: str) -> str:
    """Render a single command segment as styled HTML."""
    parts = []
    parts.append(f'<span class="prompt">{html.escape(prompt)}</span><span class="command">{html.escape(command)}</span>')
    if output:
        parts.append(f'\n<span class="output">{html.escape(output)}</span>')
    return "".join(parts)


def capture_cli_screenshot(
    name: str,
    commands: list[str],
    title: str = "Terminal",
    work_dir: str | None = None,
) -> str:
    """Execute commands and capture styled terminal output as a screenshot.

    Returns the relative path to the saved PNG (from project root).
    """
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    segments = []
    for cmd in commands:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                cwd=work_dir, timeout=30,
            )
            output = result.stdout
            if result.stderr:
                output += result.stderr
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            output = f"# Command failed: {e}"

        segments.append(_render_segment("$ ", cmd, output.rstrip()))

    content = "\n".join(segments)
    html_str = TERMINAL_HTML_TEMPLATE.format(title=html.escape(title), content=content)

    # Write HTML to temp file
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
        f.write(html_str)
        html_path = f.name

    img_path = SCREENSHOTS_DIR / f"{name}.png"

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(
                viewport={"width": 880, "height": 600},
                device_scale_factor=2,
            )
            page.goto(f"file://{html_path}")
            page.locator(".terminal").screenshot(path=str(img_path))
            browser.close()
    except ImportError:
        # Playwright not available - save HTML for manual screenshot
        fallback = SCREENSHOTS_DIR / f"{name}.html"
        fallback.write_text(html_str)
        print(f"Playwright not available. HTML saved to {fallback}")
        return f"assets/images/screenshots/{name}.html"
    finally:
        Path(html_path).unlink(missing_ok=True)

    return f"assets/images/screenshots/{name}.png"


def parse_screenshot_markers(content: str) -> list[dict]:
    """Extract screenshot placeholders from blog content.

    Format: <!-- SCREENSHOT: descriptive-name -->
    """
    pattern = re.compile(r"<!--\s*SCREENSHOT:\s*(.+?)\s*-->", re.IGNORECASE)
    markers = []
    for m in pattern.finditer(content):
        markers.append({
            "full_match": m.group(0),
            "name": m.group(1).strip(),
        })
    return markers


def replace_screenshot_markers(content: str, screenshots: dict[str, str]) -> str:
    """Replace screenshot markers with actual image references.

    screenshots: dict mapping marker name -> image path
    """
    def replacer(m):
        name = m.group(1).strip()
        if name in screenshots:
            path = screenshots[name]
            alt = name.replace("-", " ").replace("_", " ").title()
            return f"\n\n![{alt}]({path})\n\n"
        return m.group(0)

    return re.sub(
        r"<!--\s*SCREENSHOT:\s*(.+?)\s*-->",
        replacer, content, flags=re.IGNORECASE,
    )


# Default screenshot scenarios per topic
DEFAULT_SCENARIOS = {
    "quickstart": [
        {"name": "quickstart-docker", "commands": ["echo 'docker compose up -d'"], "title": "Docker Quickstart"},
        {"name": "quickstart-dry-run", "commands": ["echo 'freqtrade trade --config config.json --strategy SampleStrategy --dry-run'"], "title": "Dry Run Mode"},
    ],
    "installation": [
        {"name": "installation-docker", "commands": ["echo 'docker pull freqtradeorg/freqtrade:stable'"], "title": "Docker Pull"},
        {"name": "installation-pip", "commands": ["echo 'pip install freqtrade'"], "title": "Pip Install"},
    ],
    "configuration": [
        {"name": "config-example", "commands": ["echo 'freqtrade new-config --config config.json'"], "title": "Create Config"},
        {"name": "config-keys", "commands": ["echo 'freqtrade show-config'"], "title": "Show Config"},
    ],
    "strategy-quickstart": [
        {"name": "strategy-create", "commands": ["echo 'freqtrade new-strategy --strategy MyStrategy'"], "title": "Create Strategy"},
        {"name": "strategy-list", "commands": ["echo 'freqtrade list-strategies'"], "title": "List Strategies"},
    ],
    "strategy-customization": [
        {"name": "strategy-populate", "commands": ["echo 'def populate_entry_trend(self, dataframe, metadata):'"], "title": "Entry Trend"},
        {"name": "strategy-indicators", "commands": ["echo 'dataframe[\"rsi\"] = ta.RSI(dataframe, timeperiod=14)'"], "title": "Technical Indicators"},
    ],
    "strategy-callbacks": [
        {"name": "callbacks-custom-stake", "commands": ["echo 'def custom_stake_amount(self, pair, ...):'"], "title": "Custom Stake"},
        {"name": "callbacks-custom-exit", "commands": ["echo 'def custom_exit(self, pair, trade, ...):'"], "title": "Custom Exit"},
    ],
    "stoploss": [
        {"name": "stoploss-config", "commands": ["echo 'stoploss = -0.10'"], "title": "Stoploss Config"},
        {"name": "stoploss-trailing", "commands": ["echo 'trailing_stop = True'"], "title": "Trailing Stop"},
    ],
    "plugins": [
        {"name": "plugins-protection", "commands": ["echo 'protection_handler: StoplossGuard'"], "title": "Protection Plugin"},
    ],
    "bot-operation": [
        {"name": "bot-start", "commands": ["echo 'freqtrade trade --config config.json --strategy MyStrategy'"], "title": "Start Bot"},
        {"name": "bot-status", "commands": ["echo 'freqtrade status'"], "title": "Bot Status"},
    ],
    "telegram-control": [
        {"name": "telegram-start", "commands": ["echo '/start'"], "title": "Telegram Start"},
        {"name": "telegram-status", "commands": ["echo '/status'"], "title": "Telegram Status"},
    ],
    "frequi": [
        {"name": "frequi-open", "commands": ["echo 'http://localhost:8080'"], "title": "FreqUI Dashboard"},
    ],
    "rest-api": [
        {"name": "api-status", "commands": ["echo 'curl http://localhost:8080/api/v1/status'"], "title": "API Status"},
        {"name": "api-profit", "commands": ["echo 'curl http://localhost:8080/api/v1/profit'"], "title": "API Profit"},
    ],
    "data-downloading": [
        {"name": "data-download", "commands": ["echo 'freqtrade download-data --exchange binance --pairs BTC/USDT'"], "title": "Download Data"},
    ],
    "backtesting": [
        {"name": "backtesting-run", "commands": ["echo 'freqtrade backtesting --config config.json --strategy MyStrategy'"], "title": "Run Backtest"},
        {"name": "backtesting-results", "commands": ["echo 'freqtrade backtesting-show'"], "title": "Backtest Results"},
    ],
    "hyperopt": [
        {"name": "hyperopt-run", "commands": ["echo 'freqtrade hyperopt --config config.json --hyperopt-loss SharpeHyperOptLoss'"], "title": "Run Hyperopt"},
        {"name": "hyperopt-results", "commands": ["echo 'freqtrade hyperopt-show --best'"], "title": "Best Results"},
    ],
    "short-leverage": [
        {"name": "leverage-config", "commands": ["echo 'trading_mode: futures'"], "title": "Futures Config"},
    ],
    "plotting": [
        {"name": "plot-profit", "commands": ["echo 'freqtrade plot-profit --config config.json --strategy MyStrategy'"], "title": "Plot Profit"},
    ],
    "exchange-specific": [
        {"name": "exchange-list", "commands": ["echo 'freqtrade list-exchanges'"], "title": "List Exchanges"},
    ],
    "freqai-intro": [
        {"name": "freqai-enable", "commands": ["echo 'freqai: { enabled: true }'"], "title": "Enable FreqAI"},
    ],
    "freqai-configuration": [
        {"name": "freqai-config", "commands": ["echo 'freqai: { feature_parameters: { ... } }'"], "title": "FreqAI Config"},
    ],
    "producer-consumer": [
        {"name": "producer-config", "commands": ["echo 'mode: producer'"], "title": "Producer Mode"},
    ],
    "utility-commands": [
        {"name": "utils-trades", "commands": ["echo 'freqtrade show-trades --db tradesv3.sqlite'"], "title": "Show Trades"},
    ],
    "advanced-strategy": [
        {"name": "advanced-order", "commands": ["echo 'order_types: { entry: limit }'"], "title": "Order Types"},
    ],
    "faq": [
        {"name": "faq-common", "commands": ["echo 'freqtrade --help'"], "title": "Common FAQ"},
    ],
    "updating-migration": [
        {"name": "updating-docker", "commands": ["echo 'docker pull freqtradeorg/freqtrade:stable'"], "title": "Update Docker"},
    ],
}


def capture_topic_screenshots(topic: str, markers: list[dict] | None = None) -> dict[str, str]:
    """Capture screenshots for a topic. Returns dict of marker name -> image path."""
    screenshots = {}

    # Use markers from content if available, otherwise use default scenarios
    if markers:
        for marker in markers:
            name = marker["name"]
            # Try to find a matching default scenario
            scenarios = DEFAULT_SCENARIOS.get(topic, [])
            matched = next((s for s in scenarios if s["name"] == name), None)
            if matched:
                path = capture_cli_screenshot(
                    name=matched["name"],
                    commands=matched["commands"],
                    title=matched.get("title", "Terminal"),
                )
            else:
                # Generic screenshot with just the name
                path = capture_cli_screenshot(
                    name=name,
                    commands=[f"echo 'Screenshot: {name}'"],
                    title=name.replace("-", " ").title(),
                )
            screenshots[name] = path
    else:
        # Use default scenarios for the topic
        scenarios = DEFAULT_SCENARIOS.get(topic, [])
        for scenario in scenarios:
            path = capture_cli_screenshot(
                name=scenario["name"],
                commands=scenario["commands"],
                title=scenario.get("title", "Terminal"),
            )
            screenshots[scenario["name"]] = path

    return screenshots


if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "quickstart"
    result = capture_topic_screenshots(topic)
    for name, path in result.items():
        print(f"  {name}: {path}")
