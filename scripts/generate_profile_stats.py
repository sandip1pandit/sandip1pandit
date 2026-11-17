#!/usr/bin/env python3
"""Generate self-hosted GitHub profile statistics SVG cards."""
import json
import os
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from xml.sax.saxutils import escape

USER = os.environ.get("GITHUB_USERNAME", "sandip1pandit")
API = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "profile-stats-generator"}

def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def svg_card(title, rows, width=495):
    # Fit the SVG height to the number of rows so labels never get clipped.
    height = max(190, 76 + (len(rows) - 1) * 29 + 42)
    lines = []
    y = 76
    for label, value in rows:
        lines.append(
            f'<text x="28" y="{y}" class="label">{escape(str(label))}</text>'
            f'<text x="{width-28}" y="{y}" text-anchor="end" class="value">{escape(str(value))}</text>'
        )
        y += 29
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
  <defs>
    <style>
      .card{{fill:#ffffff;stroke:#d0d7de;stroke-width:1.2}}
      .title{{font:600 18px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;fill:#0969da}}
      .label{{font:14px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;fill:#57606a}}
      .value{{font:600 14px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;fill:#1f2328}}
      @media(prefers-color-scheme:dark){{
        .card{{fill:#0d1117;stroke:#30363d}}
        .title{{fill:#58a6ff}}
        .label{{fill:#8b949e}}
        .value{{fill:#e6edf3}}
      }}
    </style>
  </defs>
  <rect class="card" x="1" y="1" width="{width-2}" height="{height-2}" rx="10"/>
  <text class="title" x="28" y="39">{escape(title)}</text>
  {''.join(lines)}
  <text x="{width-28}" y="{height-12}" text-anchor="end" style="font:10px sans-serif;fill:#8b949e">Updated {datetime.now(timezone.utc).strftime('%Y-%m-%d')}</text>
</svg>'''

def main():
    user = get_json(f"{API}/users/{USER}")
    repos = get_json(f"{API}/users/{USER}/repos?per_page=100&type=owner")
    public_repos = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in public_repos)
    forks = sum(r.get("forks_count", 0) for r in public_repos)
    languages = Counter()
    for repo in public_repos:
        if repo.get("languages_url"):
            try:
                languages.update(get_json(repo["languages_url"]))
            except Exception as exc:
                print(f"Skipping language data for {repo['name']}: {exc}")
    total_bytes = sum(languages.values()) or 1
    top_languages = languages.most_common(6)
    stats_rows = [
        ("Public repositories", user.get("public_repos", 0)),
        ("Followers", user.get("followers", 0)),
        ("Following", user.get("following", 0)),
        ("Total stars earned", stars),
        ("Total forks", forks),
    ]
    lang_rows = [(name, f"{count / total_bytes * 100:.1f}%") for name, count in top_languages]
    if not lang_rows:
        lang_rows = [("No language data yet", "—")]
    os.makedirs("profile", exist_ok=True)
    with open("profile/stats.svg", "w", encoding="utf-8") as f:
        f.write(svg_card("GitHub Statistics", stats_rows))
    with open("profile/top-langs.svg", "w", encoding="utf-8") as f:
        f.write(svg_card("Most Used Languages", lang_rows))
    print("Generated profile/stats.svg and profile/top-langs.svg")

if __name__ == "__main__":
    main()
