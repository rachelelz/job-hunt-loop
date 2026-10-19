#!/usr/bin/env python3
"""Find out which applicant-tracking system a company uses, and whether its public feed works.

Tries Greenhouse, Lever (US and EU), Ashby, Recruitee and Workable for each slug you give it,
reports what each returned, and prints a ready-to-paste watchlist entry for every board that
has postings, with the company name the board itself reports so you can tell it is the right one.

Usage:
    python3 scripts/probe_board.py gitlab
    python3 scripts/probe_board.py mistral.ai tonyschocolonely soda-data-nv

Tips:
- Slugs are usually the company name in lowercase with no spaces, but not always.
  Open the company's careers page and look at the apply link: jobs.lever.co/<slug>,
  boards.greenhouse.io/<slug> or job-boards.greenhouse.io/<slug>, jobs.ashbyhq.com/<slug>,
  <slug>.recruitee.com, apply.workable.com/<slug>. Some slugs have a dot (mistral.ai) or a
  suffix (automatticcareers), which is why a guessed slug can miss a board that exists.
- A Lever board that returns an empty list is often a husk left after the company moved to
  another vendor. A 200 with zero postings is not proof of a quiet board.
- A 200 under a slug can belong to a different company with the same name. Read the
  "reports itself as" line before you trust it.

Standard library only. Python 3.8+.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "job-hunt-loop/1.0 (+https://github.com/rachelelz/job-hunt-loop)"
TIMEOUT = 20
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")


def identity_greenhouse(d):
    jobs = d.get("jobs", [])
    return len(jobs), (jobs[0].get("company_name") if jobs else None), (jobs[0].get("title") if jobs else None)


def identity_lever(d):
    if not isinstance(d, list):
        return -1, None, None
    first = d[0] if d else {}
    host = urllib.parse.urlsplit(first.get("hostedUrl") or "").path.strip("/").split("/")[0] if first else None
    return len(d), host, first.get("text") if first else None


def identity_ashby(d):
    jobs = d.get("jobs", [])
    first = jobs[0] if jobs else {}
    host = urllib.parse.urlsplit(first.get("jobUrl") or "").path.strip("/").split("/")[0] if first else None
    return len(jobs), host, first.get("title") if first else None


def identity_recruitee(d):
    offers = d.get("offers", [])
    first = offers[0] if offers else {}
    return len(offers), first.get("company_name") if first else None, first.get("title") if first else None


def identity_workable(d):
    jobs = d.get("jobs", [])
    codes = {j.get("shortcode") for j in jobs if j.get("shortcode")}
    return len(codes), d.get("name"), (jobs[0].get("title") if jobs else None)


PROBES = [
    ("greenhouse", "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", identity_greenhouse),
    ("lever", "https://api.lever.co/v0/postings/{slug}?mode=json", identity_lever),
    ("lever-eu", "https://api.eu.lever.co/v0/postings/{slug}?mode=json", identity_lever),
    ("ashby", "https://api.ashbyhq.com/posting-api/job-board/{slug}", identity_ashby),
    ("recruitee", "https://{slug}.recruitee.com/api/offers/", identity_recruitee),
    ("workable", "https://apply.workable.com/api/v1/widget/accounts/{slug}", identity_workable),
]


def probe(vendor, url, identify):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        return {"vendor": vendor, "text": f"HTTP {exc.code}", "count": None, "conclusive": exc.code == 404}
    except urllib.error.URLError as exc:
        reason = str(exc.reason)
        dns = "nodename nor servname" in reason or "Name or service not known" in reason or "getaddrinfo" in reason
        return {"vendor": vendor, "text": f"no such host ({reason})" if dns else f"network error ({reason})",
                "count": None, "conclusive": dns}
    except Exception as exc:
        return {"vendor": vendor, "text": f"{type(exc).__name__}: {exc}", "count": None, "conclusive": False}
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return {"vendor": vendor, "text": f"HTTP {status}, not JSON (an HTML page; no API here)", "count": None, "conclusive": True}
    try:
        count, name, first_title = identify(data)
    except Exception:
        count, name, first_title = -1, None, None
    if count < 0:
        return {"vendor": vendor, "text": f"HTTP {status}, unexpected shape", "count": None, "conclusive": False}
    return {"vendor": vendor, "text": f"HTTP {status}, {count} postings", "count": count,
            "name": name, "first_title": first_title, "conclusive": True}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slugs", nargs="+", help="one or more slugs to try")
    args = ap.parse_args()

    invalid = False
    for slug in args.slugs:
        print(f"\n# {slug}")
        if not SLUG_RE.fullmatch(slug) or ".." in slug:
            invalid = True
            print("- not a valid slug (letters, digits, dot, dash, underscore only)")
            continue
        hits, inconclusive = [], False
        for vendor, pattern, identify in PROBES:
            if vendor == "recruitee" and "." in slug:
                print(f"- {vendor:<10} skipped (Recruitee slugs cannot contain a dot)")
                continue
            r = probe(vendor, pattern.format(slug=urllib.parse.quote(slug, safe=".") if vendor != "recruitee" else slug), identify)
            flag = ""
            if r["count"] == 0 and vendor.startswith("lever"):
                flag = "  <- empty husk? the company may have moved vendors"
            elif r["count"] == 0:
                flag = "  <- a board exists under this slug but has no postings; it may belong to another company"
            line = f"- {r['vendor']:<10} {r['text']}{flag}"
            if r.get("count"):
                who = r.get("name") or "(name not in feed)"
                line += f"\n             reports itself as: {who} · first posting: {r.get('first_title')}"
            print(line)
            if not r.get("conclusive", True):
                inconclusive = True
            if r.get("count"):
                hits.append(r)

        if hits:
            print("\nPaste into the \"boards\" list in watchlist.json (set \"company\" to the display name you want):")
            for r in hits:
                print(json.dumps({"company": r.get("name") or slug, "vendor": r["vendor"], "slug": slug, "note": ""}))
            if len(hits) > 1:
                print("More than one vendor has postings: the company may be mid-migration, or two different companies share the slug. Open both before choosing.")
        elif inconclusive:
            print("\nInconclusive: at least one vendor returned something other than a clean 404 or 200 (network error, rate limit, TLS). Try again later.")
        else:
            print("\nNo public feed found under this slug. Check the apply links on the company's careers page for the real slug, "
                  "or add the page to 'careers_pages' in watchlist.json and check it in a browser.")

    if invalid:
        sys.exit(1)


if __name__ == "__main__":
    main()
