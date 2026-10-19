# Sources: where postings come from, and the quirks of each

Order of trust: a company's own ATS feed > the company's careers page > an aggregator. Score only from the full posting text on the company's own site. Aggregators show dead jobs, recruiter duplicates and stale pay.

## 1. Company ATS feeds (polled by `scripts/poll_boards.py`)

| Vendor | Endpoint | Notes |
|---|---|---|
| Greenhouse | `https://boards-api.greenhouse.io/v1/boards/<slug>/jobs` | `jobs[].title`, `location.name`, `absolute_url`, `first_published`. Add `?content=true` for full descriptions. |
| Lever | `https://api.lever.co/v0/postings/<slug>?mode=json` (EU-hosted accounts: `api.eu.lever.co`, vendor `lever-eu`) | A list. `text` is the title; `categories.allLocations`; `hostedUrl`; `createdAt` in milliseconds; `workplaceType` (remote / hybrid / onsite). An empty list is often a husk left after the company moved vendors. |
| Ashby | `https://api.ashbyhq.com/posting-api/job-board/<slug>?includeCompensation=true` | `jobs[]` with `isListed`, `location`, `secondaryLocations`, `jobUrl`, `publishedAt`, `workplaceType` (Remote / Hybrid / OnSite) and `compensation` when the company publishes bands. `isRemote` is also set on hybrid jobs, so the poller reads `workplaceType` first. Slugs can contain a dot (`mistral.ai`). |
| Recruitee | `https://<slug>.recruitee.com/api/offers/` | Redirects (302), so follow redirects. `offers[]` with `location`, `careers_url`, `published_at`, `remote`, `employment_type_code` (e.g. `fulltime_fixed_term`, useful for the contract gate), `salary` (usually empty). |
| Workable | `https://apply.workable.com/api/v1/widget/accounts/<slug>` | One record per city for the same job; the poller merges by `shortcode`. `telecommuting` is the remote flag. The top-level `name` field says which company the board belongs to, which matters because a slug like `linear` can be an unrelated company. |

Not pollable, check in a browser: SmartRecruiters (its public search returns `200 {"totalFound":0}` for any slug, including nonsense, so a 200 proves nothing), HiBob (401 on the API), Workday (JS, per-tenant), Personio, Join, Softgarden (common in Germany; XML or HTML feeds, no stable public JSON), most in-house ATSes.

### How the poller matches

- Title must contain a `title_keyword` as a whole word (so `ai` does not match `retail`, and `intern` does not match `internal`), and none of `title_exclude`.
- Location must contain a `location_keyword` as a whole word. A posting with an empty location that the vendor marks remote passes when `remote` is in `location_keywords`.
- `remote` as a location keyword also matches `Remote, United States`. To get "remote in Europe only", list the countries or regions you accept instead and let `remote` do less work.
- `--days N` keeps postings published within N days; undated postings always pass.
- Everything shown is recorded in the state file by `vendor:slug:id`, so a company that changes its slug re-announces its postings once.

### Finding a company's slug

Open the careers page and read the apply link. `jobs.lever.co/<slug>`, `boards.greenhouse.io/<slug>` or `job-boards.greenhouse.io/<slug>`, `jobs.ashbyhq.com/<slug>`, `<slug>.recruitee.com`, `apply.workable.com/<slug>`. Then confirm with:

```bash
cd ~/.claude/skills/job-hunt-loop && python3 scripts/probe_board.py <slug>
```

It prints, for every vendor that answers, how many postings and what the board calls itself, so you can tell `linear` the software company (Ashby, 29 postings) from `linear` the agency (Workable, 0 postings). Slugs that bit us: `automatticcareers` (not `automattic`), `mistral.ai` (with the dot), `doitintl` (not `doit`), `soda-data-nv` (not `soda`).

### Dead-board patterns

- **Migration husk.** Company moved from Lever to Ashby (or Greenhouse to Ashby); the old endpoint still answers 200 with `[]` or a stale list. Probe all vendors before pruning.
- **Rebrand.** The slug changes with the company name (`paires` to `pairs`, `travelperk` to `perk`). Every vendor 404s on the old slug. Check the careers page.
- **In-house move.** Larger companies move to their own ATS; the Greenhouse board goes empty but stays up. Add the careers page to `careers_pages` instead.
- **Phantom 200.** SmartRecruiters and some custom search APIs return a valid-looking empty result for any input. Never count those as a verified board.
- **Redirect read as dead.** Recruitee 302s. A client that does not follow redirects sees nothing.
- **Same slug, other company.** Workable and Ashby both host a `linear`. Read the identity line the prober prints.

Rule: the poller counts, per board, consecutive days that returned an error, a 404, or an empty list, and warns at 3. A board with postings but no matches is healthy and is listed under "Boards that answered with no matches". When a warning appears: probe, then fix the entry, move it to `careers_pages`, or remove it, and say which in the digest.

## 2. LinkedIn Jobs

LinkedIn is where most European roles post first. It serves a logged-out search page that returns a list of job cards:

```
https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=<KW>&location=<LOC>&f_TPR=r604800&start=0
```

- `f_TPR`: `r` followed by seconds, so `r86400` (24h), `r259200` (3 days), `r604800` (7 days), `r2592000` (30 days); for N days use `r<N×86400>`
- `f_WT=2` remote only · `distance=10` plus a town for a radius search
- paginate with `start=0,10,25,...`
- each card has a title, company, location and a link whose numeric id opens the full description at `https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/<ID>`

Caveats: this is an undocumented endpoint that worked in October 2026 and can change or disappear without notice. Read LinkedIn's User Agreement before you use it, and use it the way a person browsing would: the handful of searches your criteria file lists, not a crawl. Treat every result as a lead to verify on the company's own site, never as the posting of record. Recruiter agencies re-post the same seat under their own name; dedupe by company and title.

## 3. Other boards worth a query each run

- Indeed and Glassdoor block plain fetches; search them through a web search engine (`site:indeed.nl <title> <town>`) and open results in the browser.
- Google Jobs: search `<title> jobs <town>` and open the jobs panel.
- Welcome to the Jungle / Otta, Flexa (flexibility-first, Europe).
- WeWorkRemotely, RemoteOK, Remotive (remote; mostly US pay, check the time-zone and hiring-entity lines).
- Local boards for your country. Netherlands: Intermediair, Nationale Vacaturebank, werkenvoor.nl (public sector). Germany: StepStone, Xing Jobs, Arbeitsagentur. UK: Reed, Totaljobs, CWJobs. Add yours to criteria section 6.
- Aggregator-recruiters such as Jobgether list partner companies' remote roles without naming the company; say "via <aggregator>" in the digest line.

## 4. What to read in a posting (the extraction list)

For every posting in lane and in area, read the full description and pull out, as stated, with `not stated` where it is missing:

language requirement · office days and remote policy (exact wording) · hours, part-time option, core hours, time zone · pay or band · travel % · contract type and employee vs contractor · hiring entity and whether it can employ in your country · years of experience and every item under requirements / must-haves (nice-to-haves separately) · posting date · where it is live (company URL beats aggregator URL)

"Hybrid" in a benefits list is not a flexibility receipt. "Flexible working hours" is. "We trust you to manage your own time" is. A fixed-term code on the ATS with no "path to permanent" language is an open question unless the criteria file says otherwise.
