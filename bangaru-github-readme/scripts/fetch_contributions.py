#!/usr/bin/env python3
"""Fetch the public contribution calendar and write data/contributions.json.

No token needed: this reads the same public HTML fragment the profile page uses.
Set GH_PROFILE_USER to use another account. Pass a saved HTML file as argv[1] to
parse offline.
"""
import datetime
import json
import os
import re
import sys
import urllib.request

USER = os.environ.get("GH_PROFILE_USER", "bangarukondabollapally")
URL = f"https://github.com/users/{USER}/contributions"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "contributions.json")


def load_html():
    if len(sys.argv) > 1:
        return open(sys.argv[1], encoding="utf-8").read()
    req = urllib.request.Request(URL, headers={"User-Agent": "profile-readme-bot/1.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")


def parse(html):
    tips = {}
    for m in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        txt = m.group(2).strip()
        n = re.match(r"(\d+)", txt)
        tips[m.group(1)] = int(n.group(1)) if n else 0
    days = []
    for m in re.finditer(r"<td[^>]*>", html):
        tag = m.group(0)
        date = re.search(r'data-date="([\d-]+)"', tag)
        if not date:
            continue
        cid = re.search(r'id="([^"]+)"', tag)
        lvl = re.search(r'data-level="(\d)"', tag)
        days.append({
            "date": date.group(1),
            "count": tips.get(cid.group(1), 0) if cid else 0,
            "level": int(lvl.group(1)) if lvl else 0,
        })
    days.sort(key=lambda d: d["date"])
    return days


def stats(days):
    today = datetime.date.today().isoformat()
    days = [d for d in days if d["date"] <= today]
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    i = len(days) - 1
    if i >= 0 and days[i]["count"] == 0:
        i -= 1  # today isn't over yet
    cur = 0
    while i >= 0 and days[i]["count"] > 0:
        cur += 1
        i -= 1
    months = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    best = max(days, key=lambda d: d["count"]) if days else {"count": 0, "date": ""}
    return {
        "total": sum(d["count"] for d in days),
        "active_days": sum(1 for d in days if d["count"] > 0),
        "span_days": len(days),
        "current_streak": cur,
        "longest_streak": longest,
        "best_day": best["count"],
        "months": months,
    }


if __name__ == "__main__":
    days = parse(load_html())
    if not days:
        sys.exit("no calendar cells found; GitHub markup may have changed")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"user": USER, "days": days, **stats(days)}, f)
    print(f"wrote data/contributions.json ({len(days)} days)")
