# username-osint

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Platforms](https://img.shields.io/badge/Platforms-50+-orange?style=for-the-badge)

## Overview

Search a username across 50+ platforms using async HTTP requests. Covers social media, dev platforms, gaming, creative, and more.

## Why this project

Username enumeration is a core OSINT technique for building a target profile. This tool demonstrates async Python, HTTP fingerprinting, and structured OSINT methodology.

## Platforms Covered

GitHub, GitLab, Twitter/X, Instagram, TikTok, Reddit, YouTube, Twitch, Steam, Pinterest, SoundCloud, Spotify, Medium, Dev.to, HackerNews, Keybase, HackTheBox, TryHackMe, Replit, Pastebin, Flickr, Vimeo, Behance, Dribbble, Fiverr, Codepen, npm, PyPI, DockerHub, Kaggle, Leetcode, Codeforces, Duolingo, Chess.com, Lichess, Telegram, Linktree, Letterboxd, and more.

## Setup

```bash
git clone https://github.com/TaoTheReaper/username-osint
cd username-osint
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python3 username-osint.py johndoe
python3 username-osint.py johndoe -o results.json
python3 username-osint.py --help
```

## Lessons Learned

- HTTP 404 is reliable; HTTP 200 needs body content check to avoid false positives
- Many platforms block bots — rotating user agents helps but isn't foolproof
- Username != identity; always corroborate findings from multiple sources
