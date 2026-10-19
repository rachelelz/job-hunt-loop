#!/usr/bin/env python3
"""Poll company job boards and print the new postings that match your keywords.

Supports the vendors that expose a public JSON feed:
Greenhouse, Lever (US and EU hosts), Ashby, Recruitee and Workable.

Usage:
    python3 scripts/poll_boards.py --config ~/job-hunt/watchlist.json --state ~/job-hunt/seen.json
    python3 scripts/poll_boards.py --config ~/job-hunt/watchlist.json --state ~/job-hunt/seen.json --days 7
    python3 scripts/poll_boards.py --config ... --state ... --all        # ignore keyword filters
    python3 scripts/poll_boards.py --config ... --state ... --json       # machine-readable
    python3 scripts/poll_boards.py --config ... --state ... --no-save    # look without marking anything as seen

Without --state nothing is remembered between runs and every match prints as new.

Matching: title must contain a title_keyword as a whole word and none of title_exclude;
location must contain a location_keyword as a whole word. A posting the vendor marks remote
with an empty location passes the location filter when "remote" is in location_keywords.
Undated postings are always included in the --days window.

Standard library only. Python 3.8+.
"""

import argparse
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

USER_AGENT = "job-hunt-loop/1.0 (+https://github.com/rachelelz/job-hunt-loop)"
TIMEOUT = 25
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")


# --------------------------------------------------------------------------- fetch

def fetch_json(url, retries=1):
    """GET a URL and parse JSON. Follows redirects (Recruitee needs that). One retry on 429/5xx or network error."""
    last_exc = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                raise ValueError("response is not JSON (probably an HTML page; no API at this address)")
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries:
                last_exc = exc
                time.sleep(2 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError as exc:
            if attempt < retries:
                last_exc = exc
                time.sleep(2 * (attempt + 1))
                continue
            raise
    raise last_exc  # pragma: no cover


def valid_slug(slug, vendor):
    if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug) or ".." in slug:
        return False
    if vendor == "recruitee" and "." in slug:
        return False  # Recruitee puts the slug in the hostname
    return True


def parse_date(value):
    """Best-effort parse of the many date shapes vendors use. Returns aware datetime or None."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 1e11 else value  # Lever uses milliseconds since epoch
        try:
            return datetime.fromtimestamp(seconds, tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            return None
    text = str(value).strip()
    text = text.replace(" UTC", "+00:00").replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


# --------------------------------------------------------------------------- vendors
# Each fetcher returns a list of normalized postings:
# {"id", "title", "location", "remote", "url", "published", "extra"}

def fetch_greenhouse(slug):
    data = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
    out = []
    for job in data.get("jobs", []):
        loc = (job.get("location") or {}).get("name") or ""
        out.append({
            "id": str(job.get("id")),
            "title": (job.get("title") or "").strip(),
            "location": loc.strip(),
            "remote": True if "remote" in loc.lower() else None,
            "url": job.get("absolute_url") or "",
            "published": job.get("first_published") or job.get("updated_at"),
            "extra": "",
        })
    return out


def _fetch_lever(slug, host):
    data = fetch_json(f"https://{host}/v0/postings/{slug}?mode=json")
    if not isinstance(data, list):
        raise ValueError("Lever returned a non-list; the board may not exist")
    out = []
    for job in data:
        cats = job.get("categories") or {}
        locs = cats.get("allLocations") or ([cats.get("location")] if cats.get("location") else [])
        wp = job.get("workplaceType")
        out.append({
            "id": str(job.get("id")),
            "title": (job.get("text") or "").strip(),
            "location": " / ".join(l.strip() for l in locs if l),
            "remote": True if wp == "remote" else (False if wp in ("hybrid", "onsite", "on-site") else None),
            "url": job.get("hostedUrl") or job.get("applyUrl") or "",
            "published": job.get("createdAt"),
            "extra": " · ".join(x for x in [cats.get("commitment"), wp] if x),
        })
    return out


def fetch_lever(slug):
    return _fetch_lever(slug, "api.lever.co")


def fetch_lever_eu(slug):
    return _fetch_lever(slug, "api.eu.lever.co")


def fetch_ashby(slug):
    data = fetch_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true")
    out = []
    for job in data.get("jobs", []):
        if job.get("isListed") is False:
            continue
        locs = [job.get("location") or ""] + [s.get("location") or "" for s in job.get("secondaryLocations") or []]
        wp = job.get("workplaceType")
        # Ashby sets isRemote on hybrid jobs too; workplaceType is the honest field when present
        remote = (wp == "Remote") if wp else job.get("isRemote")
        comp = ""
        c = job.get("compensation") or {}
        if isinstance(c, dict):
            comp = c.get("compensationTierSummary") or c.get("scrapeableCompensationSalarySummary") or ""
        out.append({
            "id": str(job.get("id")),
            "title": (job.get("title") or "").strip(),
            "location": " / ".join(l.strip() for l in locs if l),
            "remote": remote,
            "url": job.get("jobUrl") or job.get("applyUrl") or "",
            "published": job.get("publishedAt"),
            "extra": " · ".join(x for x in [job.get("employmentType"), wp, comp] if x),
        })
    return out


def _recruitee_salary(sal):
    if not isinstance(sal, dict):
        return ""
    lo, hi = sal.get("min"), sal.get("max")
    if not lo and not hi:
        return ""
    cur = sal.get("currency") or ""
    per = sal.get("period") or ""
    rng = f"{lo}-{hi}" if lo and hi else str(lo or hi)
    return f"{cur} {rng}{'/' + per if per else ''}".strip()


def fetch_recruitee(slug):
    data = fetch_json(f"https://{slug}.recruitee.com/api/offers/")
    out = []
    for job in data.get("offers", []):
        if job.get("status") not in (None, "published"):
            continue
        out.append({
            "id": str(job.get("id")),
            "title": (job.get("title") or "").strip(),
            "location": (job.get("location") or "").strip(),
            "remote": job.get("remote"),
            "url": job.get("careers_url") or "",
            "published": job.get("published_at") or job.get("created_at"),
            "extra": " · ".join(x for x in [job.get("employment_type_code"), _recruitee_salary(job.get("salary"))] if x),
        })
    return out


def fetch_workable(slug):
    data = fetch_json(f"https://apply.workable.com/api/v1/widget/accounts/{slug}")
    by_code = {}
    order = []
    for job in data.get("jobs", []):
        code = job.get("shortcode")
        if not code:
            continue
        loc = ", ".join(x for x in [job.get("city"), job.get("country")] if x)
        if code in by_code:
            p = by_code[code]
            if loc and loc not in p["_locs"]:
                p["_locs"].append(loc)
            p["remote"] = bool(p["remote"]) or bool(job.get("telecommuting"))
            continue
        by_code[code] = {
            "id": str(code),
            "title": (job.get("title") or "").strip(),
            "_locs": [loc] if loc else [],
            "remote": job.get("telecommuting"),
            "url": job.get("url") or job.get("shortlink") or "",
            "published": job.get("published_on") or job.get("created_at"),
            "extra": job.get("employment_type") or "",
        }
        order.append(code)
    out = []
    for code in order:
        p = by_code[code]
        p["location"] = " / ".join(p.pop("_locs"))
        out.append(p)
    return out


VENDORS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "lever-eu": fetch_lever_eu,
    "ashby": fetch_ashby,
    "recruitee": fetch_recruitee,
    "workable": fetch_workable,
}


# --------------------------------------------------------------------------- filtering

def _word_in(keyword, text):
    return re.search(r"(?<![A-Za-z0-9])" + re.escape(keyword) + r"(?![A-Za-z0-9])", text) is not None


def keyword_list(cfg, key):
    value = cfg.get(key) or []
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        sys.exit(f"watchlist: '{key}' must be a list of strings")
    return [v.strip().lower() for v in value if v.strip()]


def matches(posting, include, exclude, locations):
    title = posting["title"].lower()
    loc = posting["location"].lower()
    if include and not any(_word_in(k, title) for k in include):
        return False
    if any(_word_in(k, title) for k in exclude):
        return False
    if locations:
        if loc:
            return any(_word_in(k, loc) for k in locations)
        # no location text: pass if the vendor says remote and the user accepts remote
        return posting.get("remote") is True and any(k in ("remote", "anywhere") for k in locations)
    return True


# --------------------------------------------------------------------------- state

def load_state(path):
    if not path:
        return {"seen": {}, "zero_runs": {}}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
    except FileNotFoundError:
        state = {}
    except json.JSONDecodeError as exc:
        sys.exit(f"State file {path} is not valid JSON: {exc}")
    if not isinstance(state, dict):
        sys.exit(f"State file {path} must hold a JSON object")
    state.setdefault("seen", {})
    state.setdefault("zero_runs", {})
    if not isinstance(state["seen"], dict) or not isinstance(state["zero_runs"], dict):
        sys.exit("State 'seen' and 'zero_runs' must be JSON objects")
    for entry in state["zero_runs"].values():
        if (not isinstance(entry, dict) or type(entry.get("count", 0)) is not int
                or entry.get("count", 0) < 0):
            sys.exit("State zero-run entries must be objects with nonnegative integer counts")
    return state


def save_state(path, state):
    if not path:
        return
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    # Unique private temp file prevents collisions and predictable-temp symlink writes.
    fd, tmp = tempfile.mkstemp(prefix=".job-hunt-state-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=1, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


# --------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, help="path to watchlist.json")
    ap.add_argument("--state", default=None, help="path to the state file that remembers what you were shown (recommended)")
    ap.add_argument("--days", type=int, default=None, help="only postings published within the last N days (undated postings always pass)")
    ap.add_argument("--all", action="store_true", help="ignore title/location keyword filters")
    ap.add_argument("--show-seen", action="store_true", help="also print postings already in the state file")
    ap.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    ap.add_argument("--no-save", action="store_true", help="do not write the state file")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any board failed (default: only when all failed)")
    args = ap.parse_args()

    if args.days is not None and args.days < 1:
        sys.exit("--days must be 1 or more")
    if not args.state:
        print("note: no --state given, so nothing is remembered between runs and every match prints as new", file=sys.stderr)

    try:
        with open(args.config, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
    except FileNotFoundError:
        sys.exit(f"Config not found: {args.config}")
    except json.JSONDecodeError as exc:
        sys.exit(f"Config {args.config} is not valid JSON: {exc}")
    if not isinstance(cfg, dict):
        sys.exit("watchlist.json must hold a JSON object")

    boards = cfg.get("boards") or []
    if not isinstance(boards, list) or not boards:
        sys.exit("watchlist.json has no 'boards' entries")
    include = keyword_list(cfg, "title_keywords")
    exclude = keyword_list(cfg, "title_exclude")
    locations = keyword_list(cfg, "location_keywords")

    state = load_state(args.state)
    today = datetime.now(timezone.utc).date().isoformat()
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days) if args.days else None

    results, errors, quiet = [], [], []
    totals = {"boards": 0, "failed": 0, "postings": 0, "matched": 0, "new": 0}
    active_keys = set()

    for board in boards:
        if not isinstance(board, dict):
            errors.append(f"board entry is not an object: {board!r}")
            continue
        vendor = str(board.get("vendor") or "").lower()
        slug = board.get("slug")
        company = board.get("company") or slug or "?"
        if vendor not in VENDORS:
            errors.append(f"{company}: vendor must be one of {sorted(VENDORS)}")
            continue
        if not valid_slug(slug, vendor):
            errors.append(f"{company}: slug {slug!r} is not valid (letters, digits, dot, dash, underscore; no dots for recruitee)")
            continue
        key = f"{vendor}:{slug}"
        active_keys.add(key)
        totals["boards"] += 1

        def bump_zero(reason):
            entry = state["zero_runs"].get(key)
            if not isinstance(entry, dict):
                entry = {"count": 0, "last": None}
            if entry.get("last") != today:  # count once per day
                entry["count"] = entry.get("count", 0) + 1
                entry["last"] = today
            entry["reason"] = reason
            entry["company"] = company
            state["zero_runs"][key] = entry

        try:
            postings = VENDORS[vendor](slug)
        except urllib.error.HTTPError as exc:
            totals["failed"] += 1
            bump_zero(f"HTTP {exc.code}")
            hint = " (404 usually means no board at this slug; try scripts/probe_board.py)" if exc.code == 404 else ""
            errors.append(f"{company} ({key}): HTTP {exc.code}{hint}")
            continue
        except urllib.error.URLError as exc:
            totals["failed"] += 1
            bump_zero("network error")
            errors.append(f"{company} ({key}): network error: {exc.reason}")
            continue
        except Exception as exc:
            totals["failed"] += 1
            bump_zero(type(exc).__name__)
            errors.append(f"{company} ({key}): {type(exc).__name__}: {exc}")
            continue

        totals["postings"] += len(postings)
        if not postings:
            bump_zero("empty list")
            if vendor.startswith("lever"):
                errors.append(f"{company} ({key}): empty list. Lever keeps an empty husk after a company moves vendors; probe the others before pruning")
        else:
            state["zero_runs"].pop(key, None)

        matched_here = 0
        for p in postings:
            if not args.all and not matches(p, include, exclude, locations):
                continue
            pub = parse_date(p.get("published"))
            if cutoff and pub and pub < cutoff:
                continue
            matched_here += 1
            totals["matched"] += 1
            seen_key = f"{key}:{p['id']}"
            is_new = seen_key not in state["seen"]
            if is_new:
                totals["new"] += 1
                state["seen"][seen_key] = today
            if not is_new and not args.show_seen:
                continue
            results.append({
                "company": company, "vendor": vendor, "new": is_new, "state_key": seen_key,
                "title": p["title"], "location": p["location"], "remote": p.get("remote"),
                "published": pub.date().isoformat() if pub else None,
                "url": p["url"], "extra": p.get("extra") or "", "note": board.get("note") or "",
            })
        if postings and matched_here == 0:
            quiet.append(f"{company} ({len(postings)} postings, none matched)")

    # drop counters for boards no longer in the config; warn at 3
    for k in list(state["zero_runs"]):
        if k not in active_keys:
            state["zero_runs"].pop(k)
    zero_warnings = []
    for k, entry in state["zero_runs"].items():
        if isinstance(entry, dict) and entry.get("count", 0) >= 3:
            zero_warnings.append(f"{entry.get('company', k)} ({k}): {entry['count']} days with {entry.get('reason', 'nothing')}. "
                                 f"Run scripts/probe_board.py before pruning; companies move vendors.")

    results.sort(key=lambda x: (x["company"].lower(), x["published"] or ""), reverse=False)
    results.sort(key=lambda x: x["published"] or "", reverse=True)
    results.sort(key=lambda x: x["company"].lower())

    # print first, save after, so a print failure never loses postings
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if args.json:
        print(json.dumps({"totals": totals, "results": results, "quiet": quiet, "errors": errors,
                          "zero_warnings": zero_warnings}, indent=1, ensure_ascii=False))
    else:
        print(f"# Watchlist poll, {today}\n")
        window = f" within {args.days} days" if args.days else ""
        print(f"Boards polled: {totals['boards']} ({totals['failed']} failed) · postings seen: {totals['postings']} · "
              f"matched filters{window}: {totals['matched']} · new since last run: {totals['new']}")
        if not results:
            print("\nNo new matching postings.")
        current = None
        for r in results:
            if r["company"] != current:
                current = r["company"]
                note = f" ({r['note']})" if r["note"] else ""
                print(f"\n## {current}{note}")
            tag = "" if r["new"] else " (seen before)"
            remote = " · remote" if r["remote"] is True else ""
            extra = f" · {r['extra']}" if r["extra"] else ""
            pub = f" · posted {r['published']}" if r["published"] else ""
            print(f"- **{r['title'] or '(untitled)'}** · {r['location'] or 'location not stated'}{remote}{extra}{pub}{tag}")
            if r["url"]:
                print(f"  {r['url']}")
        if quiet:
            print("\nBoards that answered with no matches: " + " · ".join(quiet))
        if zero_warnings:
            print("\n## Boards to check")
            for w in zero_warnings:
                print(f"- {w}")
        if errors:
            print("\n## Errors")
            for e in errors:
                print(f"- {e}")
        print()
    sys.stdout.flush()

    if not args.no_save:
        try:
            save_state(args.state, state)
        except OSError as exc:
            print(f"could not write state file {args.state}: {exc}", file=sys.stderr)
            sys.exit(1)

    if not totals["boards"]:
        print("no valid boards configured", file=sys.stderr)
        sys.exit(1)
    if totals["failed"] == totals["boards"]:
        print("every board failed", file=sys.stderr)
        sys.exit(1)
    if args.strict and errors:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
