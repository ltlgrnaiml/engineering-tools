#!/usr/bin/env python3
"""Fast parallel documentation scraper using Patchright (stealth Playwright).

Bypasses Cloudflare and bot detection. Properly preserves inline code formatting.

Usage:
    python scripts/scrape_docs.py https://docs.x.ai/docs/overview
    python scripts/scrape_docs.py -f docs/scraped/urls.txt -o docs/scraped/xai -w 5
"""

import argparse
import asyncio
import random
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

from patchright.async_api import async_playwright


def html_to_markdown(html: str, base_url: str = "") -> str:
    """Convert HTML to markdown with proper inline code handling."""
    from bs4 import BeautifulSoup, NavigableString
    soup = BeautifulSoup(html, "html.parser")

    for el in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        el.decompose()

    main = soup.find("main") or soup.find("article") or soup.find("body") or soup

    def extract_text(element) -> str:
        """Extract text preserving inline `code` with backticks."""
        parts = []
        for child in element.children:
            if isinstance(child, NavigableString):
                text = str(child)
                text = re.sub(r'\s+', ' ', text)
                parts.append(text)
            elif child.name == "code":
                parts.append(f"`{child.get_text()}`")
            elif child.name == "a":
                href = child.get("href", "")
                text = child.get_text(strip=True)
                if href and text:
                    if base_url and not href.startswith(("http://", "https://")):
                        href = urljoin(base_url, href)
                    parts.append(f"[{text}]({href})")
                else:
                    parts.append(text)
            elif child.name in ["strong", "b"]:
                parts.append(f"**{child.get_text(strip=True)}**")
            elif child.name in ["em", "i"]:
                parts.append(f"*{child.get_text(strip=True)}*")
            elif child.name == "br":
                parts.append("\n")
            elif child.name in ["span", "div"]:
                parts.append(extract_text(child))
            else:
                parts.append(child.get_text())
        return "".join(parts).strip()

    lines = []
    for el in main.find_all(["h1","h2","h3","h4","h5","h6","p","pre","ul","ol","table","blockquote"]):
        if el.name.startswith("h"):
            lines.append(f"\n{'#'*int(el.name[1])} {extract_text(el)}\n")
        elif el.name == "p":
            text = extract_text(el)
            if text:
                lines.append(f"\n{text}\n")
        elif el.name == "pre":
            code_el = el.find("code")
            lang = ""
            if code_el:
                for cls in code_el.get("class", []):
                    if cls.startswith("language-"):
                        lang = cls[9:]
                        break
                code = code_el.get_text()
            else:
                code = el.get_text()
            code = '\n'.join(line.rstrip() for line in code.split('\n')).strip('\n')
            lines.append(f"\n```{lang}\n{code}\n```\n")
        elif el.name in ["ul", "ol"]:
            for i, li in enumerate(el.find_all("li", recursive=False)):
                prefix = f"{i+1}." if el.name == "ol" else "-"
                lines.append(f"{prefix} {extract_text(li)}")
        elif el.name == "table":
            for idx, row in enumerate(el.find_all("tr")):
                cells = [extract_text(c) for c in row.find_all(["th", "td"])]
                if cells:
                    lines.append("| " + " | ".join(cells) + " |")
                    if idx == 0:
                        lines.append("| " + " | ".join(["---"] * len(cells)) + " |")
        elif el.name == "blockquote":
            lines.append(f"\n> {extract_text(el)}\n")

    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


async def scrape_one(browser, url, output_dir, idx, sem):
    """Scrape single URL."""
    async with sem:
        ctx = None
        try:
            ctx = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            )
            page = await ctx.new_page()
            await asyncio.sleep(random.uniform(0.2, 0.8))

            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(0.3)

            content = await page.content()
            if "challenge-running" in content:
                await asyncio.sleep(6)
                content = await page.content()

            md = html_to_markdown(content, url)
            name = urlparse(url).path.strip("/").replace("/", "_") or "index"
            out = output_dir / f"{name}.md"
            out.write_text(f"# Source: {url}\n\n---\n\n{md}", encoding="utf-8")
            print(f"  [{idx:02d}] ✓ {name}.md")
            return True
        except Exception as e:
            print(f"  [{idx:02d}] ✗ {url}: {e}")
            return False
        finally:
            if ctx:
                await ctx.close()


async def main_async(urls, output_dir, workers=5):
    """Parallel scraper."""
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Scraping {len(urls)} URLs with {workers} parallel workers...\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        sem = asyncio.Semaphore(workers)
        tasks = [scrape_one(browser, url, output_dir, i+1, sem) for i, url in enumerate(urls)]
        results = await asyncio.gather(*tasks)
        await browser.close()

    ok = sum(results)
    print(f"\n{'='*50}\nComplete: {ok}/{len(urls)} success")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", nargs="?")
    parser.add_argument("-f", "--urls-file")
    parser.add_argument("-o", "--output-dir", default="docs/scraped")
    parser.add_argument("-w", "--workers", type=int, default=5)
    args = parser.parse_args()

    if args.urls_file:
        urls = [l.strip() for l in Path(args.urls_file).read_text().splitlines() if l.strip() and not l.startswith("#")]
    elif args.url:
        urls = [args.url]
    else:
        parser.print_help()
        sys.exit(1)

    asyncio.run(main_async(urls, Path(args.output_dir), args.workers))


if __name__ == "__main__":
    main()
