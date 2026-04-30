#!/usr/bin/env python3
"""username-osint — search a username across 100+ platforms."""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

try:
    import aiohttp
    from tqdm.asyncio import tqdm_asyncio
except ImportError as e:
    print(f"[!] Missing: {e}\n    pip install aiohttp tqdm")
    sys.exit(1)

log = logging.getLogger("username-osint")

C = {
    "red": "\033[91m", "green": "\033[92m", "yellow": "\033[93m",
    "cyan": "\033[96m", "magenta": "\033[95m", "bold": "\033[1m", "reset": "\033[0m"
}

PLATFORMS = [
    # Dev & Code
    {"name": "GitHub",         "url": "https://github.com/{}", "check": "type=\"profile\""},
    {"name": "GitLab",         "url": "https://gitlab.com/{}", "status_only": True},
    {"name": "Replit",         "url": "https://replit.com/@{}", "status_only": True},
    {"name": "Codepen",        "url": "https://codepen.io/{}", "status_only": True},
    {"name": "JSFiddle",       "url": "https://jsfiddle.net/user/{}/", "status_only": True},
    {"name": "Npm",            "url": "https://www.npmjs.com/~{}", "check": "~{}"},
    {"name": "PyPI",           "url": "https://pypi.org/user/{}/", "status_only": True},
    {"name": "HuggingFace",    "url": "https://huggingface.co/{}", "status_only": True},
    {"name": "DockerHub",      "url": "https://hub.docker.com/u/{}", "status_only": True},
    {"name": "Kaggle",         "url": "https://www.kaggle.com/{}", "status_only": True},
    {"name": "Dev.to",         "url": "https://dev.to/{}", "status_only": True},
    {"name": "Hashnode",       "url": "https://hashnode.com/@{}", "check": "@{}"},
    {"name": "Medium",         "url": "https://medium.com/@{}", "check": "@{}"},
    {"name": "CodeChef",       "url": "https://www.codechef.com/users/{}", "status_only": True},
    {"name": "AtCoder",        "url": "https://atcoder.jp/users/{}", "status_only": True},
    {"name": "Codeforces",     "url": "https://codeforces.com/profile/{}", "check": "profile/{}"},
    {"name": "Exercism",       "url": "https://exercism.org/profiles/{}", "status_only": True},
    {"name": "Codewars",       "url": "https://www.codewars.com/users/{}", "status_only": True},
    {"name": "HackerRank",     "url": "https://www.hackerrank.com/{}", "status_only": True},
    {"name": "TopCoder",       "url": "https://www.topcoder.com/members/{}", "status_only": True},
    {"name": "LeetCode",       "url": "https://leetcode.com/{}/", "status_only": True},
    {"name": "HackerEarth",    "url": "https://www.hackerearth.com/@{}", "status_only": True},
    # Security / CTF
    {"name": "HackTheBox",     "url": "https://app.hackthebox.com/users/profile/{}", "check": "{}"},
    {"name": "TryHackMe",      "url": "https://tryhackme.com/p/{}", "check": "{}"},
    {"name": "root-me",        "url": "https://www.root-me.org/{}", "status_only": True},
    # Social
    {"name": "Twitter/X",      "url": "https://twitter.com/{}", "check": "@{}"},
    {"name": "Instagram",      "url": "https://www.instagram.com/{}/", "check": "\"username\":\"{}\""},
    {"name": "TikTok",         "url": "https://www.tiktok.com/@{}", "check": "\"uniqueId\":\"{}\""},
    {"name": "Reddit",         "url": "https://www.reddit.com/user/{}", "check": "has no posts yet", "invert": True},
    {"name": "Threads",        "url": "https://www.threads.net/@{}", "status_only": True},
    {"name": "Bluesky",        "url": "https://bsky.app/profile/{}", "status_only": True},
    {"name": "Mastodon",       "url": "https://mastodon.social/@{}", "status_only": True},
    {"name": "Infosec.Exchange","url": "https://infosec.exchange/@{}", "status_only": True},
    {"name": "VK",             "url": "https://vk.com/{}", "status_only": True},
    {"name": "Tumblr",         "url": "https://{}.tumblr.com", "check": "There's nothing here", "invert": True},
    {"name": "Pinterest",      "url": "https://www.pinterest.com/{}/", "status_only": True},
    {"name": "Snapchat",       "url": "https://www.snapchat.com/add/{}", "check": "\"username\":\"{}\""},
    {"name": "Telegram",       "url": "https://t.me/{}", "check": "tg://resolve?domain={}"},
    # Streaming / Gaming
    {"name": "Twitch",         "url": "https://www.twitch.tv/{}", "check": "\"login\":\"{}\""},
    {"name": "YouTube",        "url": "https://www.youtube.com/@{}", "check": "\"@{}\""},
    {"name": "Steam",          "url": "https://steamcommunity.com/id/{}", "check": "The specified profile could not be found", "invert": True},
    {"name": "NameMC",         "url": "https://namemc.com/profile/{}", "status_only": True},
    {"name": "Faceit",         "url": "https://www.faceit.com/en/players/{}", "status_only": True},
    # Music
    {"name": "SoundCloud",     "url": "https://soundcloud.com/{}", "check": "{}"},
    {"name": "Spotify",        "url": "https://open.spotify.com/user/{}", "check": "user/{}"},
    {"name": "LastFm",         "url": "https://www.last.fm/user/{}", "status_only": True},
    {"name": "Mixcloud",       "url": "https://www.mixcloud.com/{}/", "status_only": True},
    {"name": "Bandcamp",       "url": "https://bandcamp.com/{}", "status_only": True},
    # Creative / Art
    {"name": "ArtStation",     "url": "https://www.artstation.com/{}", "status_only": True},
    {"name": "DeviantArt",     "url": "https://www.deviantart.com/{}", "status_only": True},
    {"name": "Behance",        "url": "https://www.behance.net/{}", "status_only": True},
    {"name": "Dribbble",       "url": "https://dribbble.com/{}", "status_only": True},
    {"name": "Flickr",         "url": "https://www.flickr.com/people/{}", "status_only": True},
    {"name": "Wattpad",        "url": "https://www.wattpad.com/user/{}", "status_only": True},
    {"name": "Vimeo",          "url": "https://vimeo.com/{}", "status_only": True},
    {"name": "Dailymotion",    "url": "https://www.dailymotion.com/{}", "status_only": True},
    {"name": "Unsplash",       "url": "https://unsplash.com/@{}", "status_only": True},
    {"name": "500px",          "url": "https://500px.com/p/{}", "status_only": True},
    # Community / Q&A
    {"name": "HackerNews",     "url": "https://news.ycombinator.com/user?id={}", "check": "user?id={}"},
    {"name": "ProductHunt",    "url": "https://www.producthunt.com/@{}", "status_only": True},
    {"name": "Quora",          "url": "https://www.quora.com/profile/{}", "status_only": True},
    {"name": "Gravatar",       "url": "https://en.gravatar.com/{}", "status_only": True},
    {"name": "About.me",       "url": "https://about.me/{}", "status_only": True},
    {"name": "Keybase",        "url": "https://keybase.io/{}", "check": "\"username\":\"{}\""},
    {"name": "Disqus",         "url": "https://disqus.com/by/{}/", "status_only": True},
    {"name": "Flipboard",      "url": "https://flipboard.com/@{}", "status_only": True},
    # Support / Funding
    {"name": "Patreon",        "url": "https://www.patreon.com/{}", "status_only": True},
    {"name": "Ko-fi",          "url": "https://ko-fi.com/{}", "status_only": True},
    {"name": "Fiverr",         "url": "https://www.fiverr.com/{}", "status_only": True},
    {"name": "Wellfound",      "url": "https://wellfound.com/u/{}", "status_only": True},
    # Blog / Publishing
    {"name": "Substack",       "url": "https://{}.substack.com", "check": "doesn't exist", "invert": True},
    {"name": "WordPress.com",  "url": "https://{}.wordpress.com", "check": "doesn't exist", "invert": True},
    # Misc
    {"name": "Pastebin",       "url": "https://pastebin.com/u/{}", "check": "Not Found", "invert": True},
    {"name": "Linktree",       "url": "https://linktr.ee/{}", "status_only": True},
    {"name": "Strava",         "url": "https://www.strava.com/athletes/{}", "status_only": True},
    {"name": "Goodreads",      "url": "https://www.goodreads.com/{}", "status_only": True},
    {"name": "Chess.com",      "url": "https://www.chess.com/member/{}", "check": "member/{}"},
    {"name": "Lichess",        "url": "https://lichess.org/@/{}", "check": "@/{}"},
    {"name": "Letterboxd",     "url": "https://letterboxd.com/{}/", "status_only": True},
    {"name": "Trakt.tv",       "url": "https://trakt.tv/users/{}", "status_only": True},
    {"name": "Duolingo",       "url": "https://www.duolingo.com/profile/{}", "check": "profile/{}"},
    {"name": "Imgur",          "url": "https://imgur.com/user/{}", "status_only": True},
    {"name": "Giphy",          "url": "https://giphy.com/{}", "status_only": True},
    {"name": "Livejournal",    "url": "https://www.livejournal.com/profile?user={}", "check": "user={}"},
]


def setup_logging(verbose: bool):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )


def colored_result(found: bool) -> str:
    return f"{C['green']}✅ Found{C['reset']}" if found else f"{C['red']}❌ Not Found{C['reset']}"


async def check_platform(
    session: aiohttp.ClientSession,
    platform: dict,
    username: str,
    semaphore: asyncio.Semaphore,
) -> dict:
    async with semaphore:
        url   = platform["url"].format(username)
        invert = platform.get("invert", False)
        check  = platform.get("check", "").format(username).lower() if platform.get("check") else ""

        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
                allow_redirects=True,
            ) as resp:
                status = resp.status
                body   = (await resp.text(encoding="utf-8", errors="ignore")).lower()

                if status == 404:
                    found = False
                elif platform.get("status_only"):
                    found = (status == 200)
                elif status == 200:
                    if check in body:
                        found = not invert
                    else:
                        found = invert
                else:
                    return {"platform": platform["name"], "url": url, "status": "unknown", "found": None}

                log.debug("%s → HTTP %d → found=%s", platform["name"], status, found)
                return {"platform": platform["name"], "url": url if found else None, "status": "ok", "found": found}

        except asyncio.TimeoutError:
            return {"platform": platform["name"], "url": None, "status": "timeout", "found": None}
        except Exception as e:
            log.debug("%s error: %s", platform["name"], e)
            return {"platform": platform["name"], "url": None, "status": "error", "found": None}


async def run(username: str) -> list[dict]:
    semaphore = asyncio.Semaphore(15)
    async with aiohttp.ClientSession() as session:
        tasks = [check_platform(session, p, username, semaphore) for p in PLATFORMS]
        results = await tqdm_asyncio.gather(*tasks, desc="Scanning", ncols=70)
    return list(results)


def print_results(username: str, results: list[dict]):
    found   = [r for r in results if r["found"] is True]
    missing = [r for r in results if r["found"] is False]
    unknown = [r for r in results if r["found"] is None]

    print(f"\n{C['cyan']}{'='*60}{C['reset']}")
    print(f"  Username: {C['bold']}{username}{C['reset']}")
    print(f"{C['cyan']}{'='*60}{C['reset']}")

    print(f"\n{C['green']}Found on {len(found)} platforms:{C['reset']}")
    for r in found:
        print(f"  ✅ {r['platform']:<20} {r['url']}")

    if unknown:
        print(f"\n{C['yellow']}Unknown/Error ({len(unknown)}):{C['reset']}")
        for r in unknown:
            print(f"  ⚠  {r['platform']:<20} ({r['status']})")

    print(f"\n{C['cyan']}Summary: {C['green']}{len(found)} found{C['reset']} | "
          f"{C['red']}{len(missing)} not found{C['reset']} | "
          f"{C['yellow']}{len(unknown)} unknown{C['reset']}")
    print(f"{C['cyan']}{'='*60}{C['reset']}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="username-osint",
        description="Search a username across 100+ platforms.",
        epilog="Examples:\n  python username-osint.py johndoe\n  python username-osint.py johndoe -o results.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("username",        help="Username to search")
    p.add_argument("-o", "--output",  metavar="FILE", help="Save JSON report")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.verbose)

    username = args.username.strip().lstrip("@")
    print(f"{C['cyan']}=== USERNAME OSINT — searching: {username} ==={C['reset']}")

    results = asyncio.run(run(username))
    print_results(username, results)

    if args.output:
        report = {
            "username":  username,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results":   results,
        }
        tmp = args.output + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        os.replace(tmp, args.output)
        print(f"{C['green']}[+] Report saved: {args.output}{C['reset']}")


if __name__ == "__main__":
    main()
