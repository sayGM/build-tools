import json
import os
import re
import urllib.request
from pathlib import Path

existing = sorted(p.stem for p in Path("templates").glob("*.html"))

prompt = f"""Create ONE new small single-file HTML tool. HTML, CSS and JS inline only.
No external libraries, no network requests, no external fonts or images.
Style: dark background #0b1211, card #111c1a, accent teal #14B8A6, mobile friendly.
Topic: useful for web or Ethereum/crypto developers, or a general everyday utility.
It must be clearly different from these existing tools: {', '.join(existing) or 'none'}.
Output format: first line is only the slug (lowercase letters, numbers and hyphens, no underscores),
then a line containing only ---, then the full HTML starting with <!DOCTYPE html>.
Nothing else, no markdown fences."""

req = urllib.request.Request(
    "https://models.github.ai/inference/chat/completions",
    data=json.dumps({
        "model": "openai/gpt-4.1",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000,
    }).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
    },
)

with urllib.request.urlopen(req, timeout=120) as r:
    text = json.load(r)["choices"][0]["message"]["content"].strip()

text = re.sub(r"^```[a-z]*\n|\n```$", "", text).strip()

try:
    slug, html = text.split("\n---\n", 1)
except ValueError:
    raise SystemExit("Bad output format, skipping")

slug, html = slug.strip(), html.strip()

if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
    raise SystemExit(f"Invalid slug: {slug}")
if slug in existing:
    raise SystemExit("Slug already exists")
if not html.lower().startswith("<!doctype html"):
    raise SystemExit("Not a full HTML document")
if len(html) > 40000:
    raise SystemExit("File too large")
if re.search(r'<script[^>]+src=|<link[^>]+href=\s*["\']?https?:|fetch\(|XMLHttpRequest|WebSocket', html, re.I):
    raise SystemExit("External or network code found, rejected")

Path("templates").mkdir(exist_ok=True)
Path(f"templates/{slug}.html").write_text(html + "\n", encoding="utf-8")
print("Created", slug)
