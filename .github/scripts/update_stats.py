import json, os, re, urllib.request
from datetime import datetime, timezone

TOKEN = os.environ["GH_TOKEN"]
INCLUDE_PRIVATE = os.environ.get("INCLUDE_PRIVATE", "false").lower() == "true"

def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)

user = api("/user")

repos, page = [], 1
while True:
    batch = api(f"/user/repos?affiliation=owner&per_page=100&page={page}")
    if not batch:
        break
    repos += batch
    page += 1

public = [r for r in repos if not r["private"]]
own_public = [r for r in public if not r["fork"]]
stars = sum(r["stargazers_count"] for r in own_public)
forks = sum(r["forks_count"] for r in own_public)

views = 0
for r in (repos if INCLUDE_PRIVATE else public):
    try:
        views += api(f"/repos/{r['full_name']}/traffic/views")["count"]
    except Exception:
        pass

today = datetime.now(timezone.utc).strftime("%d %b %Y")
block = (
    f"**{len(repos)}** repositories (incl. private) · **{stars}** stars · **{forks}** forks · "
    f"**{user['followers']}** followers · **{views}** views in the last 14 days\n\n"
)

with open("README.md", encoding="utf-8") as f:
    readme = f.read()

new = re.sub(
    r"(<!-- STATS:START -->).*?(<!-- STATS:END -->)",
    lambda m: f"{m.group(1)}\n{block}\n{m.group(2)}",
    readme,
    flags=re.S,
)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(new)
