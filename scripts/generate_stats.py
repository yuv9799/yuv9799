#!/usr/bin/env python3
"""
Generate GitHub profile statistics SVGs.

Fetches real data from the GitHub API and generates three SVG cards
matching the TokyoNight dark/purple aesthetic:

  1. github-stats.svg  - GitHub Statistics
  2. top-langs.svg     - Top Languages
  3. streak-stats.svg  - Contribution Streak

Usage:
  GITHUB_TOKEN=<token> python scripts/generate_stats.py
"""

import html
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta

# --- Configuration ---
USERNAME = "yuv9799"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API_BASE = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"

# --- TokyoNight dark/purple color scheme ---
BG_START = "#0D0D1A"
BG_END = "#1A1A2E"
PRIMARY = "#7C3AED"
SECONDARY = "#6D28D9"
TEXT = "#C4B5FD"
ACCENT = "#4338CA"
WHITE = "#FFFFFF"
MUTED = "#8B8BA8"

# --- SVG layout constants ---
CARD_W = 400
CARD_H = 180
RADIUS = 10
PAD = 20
TITLE_Y = 32
ROW_Y = 52
ROW_H = 24
FONT = "Segoe UI, Arial, sans-serif"


def rest_get(path):
    """GET a GitHub REST endpoint and return parsed JSON."""
    req = urllib.request.Request(f"{API_BASE}{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-stats-generator")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def graphql(query, variables=None):
    """POST a GitHub GraphQL query and return the data payload."""
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(GRAPHQL_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "profile-stats-generator")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    if "errors" in data:
        raise RuntimeError(f"GraphQL error: {data['errors']}")
    return data["data"]


def fmt(n):
    """Format a number with commas."""
    return f"{n:,}"


def esc(s):
    """Escape a string for safe inclusion in SVG/XML."""
    return html.escape(str(s), quote=True)


def svg_header(w, h):
    """Return the SVG opening tags with a gradient background."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="GitHub statistics">\n'
        f'  <defs>\n'
        f'    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">\n'
        f'      <stop offset="0%" style="stop-color:{BG_START};stop-opacity:1"/>\n'
        f'      <stop offset="100%" style="stop-color:{BG_END};stop-opacity:1"/>\n'
        f'    </linearGradient>\n'
        f'  </defs>\n'
        f'  <rect width="{w}" height="{h}" rx="{RADIUS}" fill="url(#bg)" '
        f'stroke="{ACCENT}" stroke-width="1"/>\n'
    )


def svg_footer():
    """Return the SVG closing tag."""
    return "</svg>\n"


def card_title(title):
    """Return an SVG title text element."""
    return (
        f'  <text x="{PAD}" y="{TITLE_Y}" fill="{PRIMARY}" '
        f'font-family="{FONT}" font-size="16" font-weight="bold">'
        f"{esc(title)}</text>\n"
    )


def stat_row(y, icon, label, value):
    """Return an SVG row with an icon, label, and right-aligned value."""
    return (
        f'  <text x="{PAD}" y="{y}" fill="{TEXT}" font-family="{FONT}" '
        f'font-size="13">{esc(icon)} {esc(label)}</text>\n'
        f'  <text x="{CARD_W - PAD}" y="{y}" fill="{WHITE}" font-family="{FONT}" '
        f'font-size="13" font-weight="bold" text-anchor="end">{esc(value)}</text>\n'
    )


def generate_stats_svg(stats):
    """Generate the GitHub Statistics card."""
    lines = [svg_header(CARD_W, CARD_H), card_title("GitHub Statistics")]
    y = ROW_Y
    rows = [
        ("⭐", "Total Stars", fmt(stats["stars"])),
        ("📝", "Total Commits", fmt(stats["commits"])),
        ("🔀", "Total PRs", fmt(stats["prs"])),
        ("🐛", "Total Issues", fmt(stats["issues"])),
        ("👥", "Followers", fmt(stats["followers"])),
    ]
    for icon, label, value in rows:
        lines.append(stat_row(y, icon, label, value))
        y += ROW_H
    lines.append(svg_footer())
    return "".join(lines)


def generate_langs_svg(langs):
    """Generate the Top Languages card with proportional bars."""
    n = len(langs)
    h = max(CARD_H, ROW_Y + n * ROW_H + 10)
    lines = [svg_header(CARD_W, h), card_title("Top Languages")]
    y = ROW_Y
    max_count = max(langs.values()) if langs else 1
    for name, count in langs.items():
        pct = int(count / max_count * 100)
        bar_w = int((CARD_W - 2 * PAD - 60) * count / max_count)
        lines.append(
            f'  <text x="{PAD}" y="{y}" fill="{TEXT}" font-family="{FONT}" '
            f'font-size="12">{esc(name)}</text>\n'
        )
        lines.append(
            f'  <rect x="{PAD}" y="{y + 4}" width="{bar_w}" height="6" '
            f'rx="3" fill="{PRIMARY}"/>\n'
        )
        lines.append(
            f'  <text x="{CARD_W - PAD}" y="{y}" fill="{WHITE}" font-family="{FONT}" '
            f'font-size="12" text-anchor="end">{pct}%</text>\n'
        )
        y += ROW_H
    lines.append(svg_footer())
    return "".join(lines)


def generate_streak_svg(streak):
    """Generate the Contribution Streak card."""
    lines = [svg_header(CARD_W, CARD_H), card_title("Contribution Streak")]
    y = ROW_Y
    rows = [
        ("🔥", "Current Streak", f"{streak['current']} days"),
        ("🏆", "Longest Streak", f"{streak['longest']} days"),
        ("📊", "Total Contributions", fmt(streak["total"])),
    ]
    for icon, label, value in rows:
        lines.append(stat_row(y, icon, label, value))
        y += ROW_H
    lines.append(svg_footer())
    return "".join(lines)


def compute_streaks(weeks):
    """Compute current and longest streaks from contribution calendar weeks."""
    days = []
    for week in weeks:
        for day in week["contributionDays"]:
            days.append((day["date"], day["contributionCount"]))
    days.sort(key=lambda d: d[0])

    contrib_dates = {d[0] for d in days if d[1] > 0}

    # Longest streak
    longest = 0
    current_run = 0
    prev = None
    for date_str, count in days:
        if count > 0:
            if prev is not None:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
                p = datetime.strptime(prev, "%Y-%m-%d").date()
                if (d - p).days == 1:
                    current_run += 1
                else:
                    current_run = 1
            else:
                current_run = 1
            longest = max(longest, current_run)
        else:
            current_run = 0
        prev = date_str

    # Current streak (ending today or yesterday)
    today = datetime.utcnow().date()
    current = 0
    d = today
    if d.isoformat() not in contrib_dates:
        d = d - timedelta(days=1)
    while d.isoformat() in contrib_dates:
        current += 1
        d = d - timedelta(days=1)

    total = sum(count for _, count in days)
    return {"current": current, "longest": longest, "total": total}


def main():
    """Main entry point."""
    try:
        # Fetch user data
        user = rest_get(f"/users/{USERNAME}")
        repos = rest_get(f"/users/{USERNAME}/repos?per_page=100&sort=updated")

        # Aggregate repo stats
        stars = sum(r.get("stargazers_count", 0) for r in repos)
        lang_counts = {}
        for r in repos:
            lang = r.get("language")
            if lang:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1

        # Fetch contribution data via GraphQL
        query = """
        query($username: String!) {
          user(login: $username) {
            contributionsCollection {
              totalCommitContributions
              totalPullRequestContributions
              totalIssueContributions
              contributionCalendar {
                totalContributions
                weeks {
                  contributionDays {
                    contributionCount
                    date
                  }
                }
              }
            }
          }
        }
        """
        gql = graphql(query, {"username": USERNAME})
        contrib = gql["user"]["contributionsCollection"]

        stats = {
            "stars": stars,
            "commits": contrib["totalCommitContributions"],
            "prs": contrib["totalPullRequestContributions"],
            "issues": contrib["totalIssueContributions"],
            "followers": user.get("followers", 0),
        }

        streak = compute_streaks(contrib["contributionCalendar"]["weeks"])
        streak["total"] = contrib["contributionCalendar"]["totalContributions"]

        # Sort languages by count descending, take top 8
        top_langs = dict(
            sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        )

        # Generate SVGs into dist/stats/ so they can be deployed
        # alongside the snake SVGs to the output branch.
        os.makedirs("dist/stats", exist_ok=True)
        with open("dist/stats/github-stats.svg", "w", encoding="utf-8") as f:
            f.write(generate_stats_svg(stats))
        with open("dist/stats/top-langs.svg", "w", encoding="utf-8") as f:
            f.write(generate_langs_svg(top_langs))
        with open("dist/stats/streak-stats.svg", "w", encoding="utf-8") as f:
            f.write(generate_streak_svg(streak))

        print("✅ Generated stats SVGs successfully")
        print(
            f"   Stars: {stats['stars']}, Commits: {stats['commits']}, "
            f"PRs: {stats['prs']}, Issues: {stats['issues']}"
        )
        print(f"   Top languages: {list(top_langs.keys())}")
        print(
            f"   Streak: current={streak['current']}, "
            f"longest={streak['longest']}, total={streak['total']}"
        )

    except Exception as e:
        print(f"❌ Error generating stats: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()