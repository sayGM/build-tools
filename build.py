import random
import shutil
from datetime import datetime, timezone
from pathlib import Path

templates = sorted(Path("templates").glob("*.html"))
tools = Path("tools")
tools.mkdir(exist_ok=True)

used = {p.name.split("_", 1)[1] for p in tools.iterdir() if p.is_dir()}
available = [t for t in templates if t.stem not in used]

if available:
    pick = random.choice(available)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dest = tools / f"{today}_{pick.stem}"
    if not any(p.name.startswith(today) for p in tools.iterdir()):
        dest.mkdir()
        shutil.copy(pick, dest / "index.html")
        print("Added", dest)
else:
    print("No unused templates left")

items = sorted((p for p in tools.iterdir() if p.is_dir()), reverse=True)
links = "\n".join(
    f'<li><span>{p.name.split("_")[0]}</span> '
    f'<a href="tools/{p.name}/">{p.name.split("_", 1)[1].replace("-", " ").title()}</a></li>'
    for p in items
)

html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daily Tools</title>
<style>
body{{font-family:system-ui,sans-serif;background:#0b1211;color:#cfe;max-width:600px;margin:40px auto;padding:0 16px}}
h1{{color:#14B8A6}} ul{{list-style:none;padding:0}} li{{padding:10px 0;border-bottom:1px solid #1c2b29}}
span{{color:#6b8; font-size:13px;margin-right:10px}} a{{color:#14B8A6;text-decoration:none}}
</style></head><body>
<h1>Daily Tools</h1><ul>{links}</ul>
</body></html>"""

Path("index.html").write_text(html, encoding="utf-8")
