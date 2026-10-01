import json
import os
import re
import urllib.error
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

MODELS = [
    os.environ.get("GEMINI_MODEL", "").strip(),
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
]
MODELS = [m for m in MODELS if m]

payload = json.dumps({
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"maxOutputTokens": 8192},
}).encode()

text = None
errors = []

for model in MODELS:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": os.environ["GEMINI_API_KEY"],
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.load(r)
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
        if text:
            print("Model used:", model)
            break
        errors.append(f"{model}: empty response")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        errors.append(f"{model}: HTTP {e.code} {body}")
        if e.code in (401, 403):
            break
    except Exception as e:
        errors.append(f"{model}: {type(e).__name__} {e}")

if not text:
    raise SystemExit("All models failed:\n" + "\n".join(errors))

text = re.sub(r"^```[a-z]*\n|\n```$", "", text).strip()

try:
    slug, html = text.split("\n---\n", 1)
except ValueError:
    raise SystemExit(f"Bad output format, skipping. Got: {text[:300]!r}")

slug, html = slug.strip(), html.strip()
html = re.sub(r"^```[a-z]*\n|\n```$", "", html).strip()

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
