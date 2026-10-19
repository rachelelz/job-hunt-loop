# Search criteria — [your name]

*The single source of truth for the job-hunt-loop. The loop reads this file first on every run and follows it on every judgment call. Last updated: [date].*

Fill in every bracket. Delete the lanes, gates and rubrics you do not need. A gate the loop cannot check against the text of a posting is not a gate; move it to section 1 as something to watch for.

## 1. Who I am, what I want, what I watch for

- Current or last title, years, the two or three things I am known for: [...]
- What I want next, one sentence: [...]
- Things that matter but are not gates (the loop notes these in every brief, under "Fit"): [e.g. how much autonomy, how many layers of approval, whether the team ships]

## 2. Lanes

A lane is one kind of role you would take. Most people have one or two. Each lane has its own search terms, its own gates on top of the hard gates, its own rubric, and its own section in the digest.

### Lane A — [name]
- Titles and role types: [...]
- Lane gates, each marked `receipt required` or `reject on contrary evidence`: [e.g. "the role is hands-on engineering, not people management (reject on contrary evidence)"]
- Rubric: [name of a rubric from section 5]
- Search terms, English: [...]
- Search terms, other language if relevant: [...]

### Lane B — [name]
- Titles and role types: [...]
- Lane gates: [...]
- Rubric: [...]
- Search terms, English: [...]
- Search terms, other language if relevant: [...]

## 3. Hard gates

Fail any one and the posting is rejected without scoring. Each gate is one of two kinds, and you choose which:

- `receipt required`: the posting, the company's own site, or the ATS record must state it. Not stated = open question: the role can be flagged with the question named, but does not become a packet on its own until it is answered (you can still say `packet` and have the questions put on the checklist).
- `reject on contrary evidence`: passes unless the posting says the opposite. Not stated = pass. Use this for things postings rarely mention (on-call, travel, visa sponsorship).

1. **Location:** [e.g. "remote within the EU, or an office within 30 minutes of <town>"] · kind: [receipt required]
2. **Hours and schedule:** [e.g. "a fixed on-site 9 to 6 fails" (reject on contrary evidence) or "flexible hours or async culture must be stated" (receipt required)] · kind: [...]
3. **Language:** [e.g. "working language English; <language>-required fails; <language>-preferred fails"] · kind: [reject on contrary evidence]
4. **Contract type:** [e.g. "permanent, or fixed-term with a stated path to permanent; interim and project-only fail"] · kind: [reject on contrary evidence]
5. **Travel:** [e.g. "up to 15%; more fails"] · kind: [reject on contrary evidence]
6. **Pay floor:** [e.g. "≥ 85k base"] · kind: [receipt required (band must be published; unposted = open question) · or reject on contrary evidence (fails only when a published band is below the floor; unposted pay is scored low in the rubric instead) · or "soft: tiebreaker only, never a gate"]
7. **Hiring entity and employment form (remote roles):** [e.g. "can employ me in <country> as an employee; contractor-only fails" or "contractor is fine"] · kind: [reject on contrary evidence]
8. **Time zone:** [e.g. "core overlap within ±2 hours of CET"] · kind: [reject on contrary evidence]
9. **Other dealbreakers:** [e.g. "no on-call; no sales quota; nothing at companies on the off-limits list"] · kind: [reject on contrary evidence]

**Exceptions:** [e.g. "a freelance role paying above <rate>/hour may skip gate 2 if the rate is stated in the posting"]

## 4. Must-haves

A stated must-have is an item under the posting's requirements / must-have / what-you-bring heading; nice-to-haves and "a plus" do not count. Each is compared against `proof-file.md`: ✓ proven, partial (nearby proof: adjacent tool, years within about 20%, same work at smaller scale), ✗ not proven. One ✗ makes the role a "close, but" line at most. Partials are allowed in a packet if the brief names the gap in the posting's words.

Caps (optional): [e.g. "a posting that requires people-management experience caps at 6.9 for me"]

## 5. Scoring

Only postings that pass every gate get scored. Each dimension is scored 0 to 10, multiplied by its weight, summed; weights total 100%. Anchors: 10 = the posting states it explicitly in my favor · 7 = strong signal, not explicit · 5 = not stated · 2 = the posting states the opposite.

Pick four to six dimensions that reflect what you would trade off. Pay is usually one of them; where you put it is your call.

### Rubric: [name, e.g. "main"] (used by lane [A])

| Dimension | Weight | 10 looks like | 5 looks like | 2 looks like |
|---|---|---|---|---|
| [e.g. Remote and hours flexibility] | [%] | [explicit async or flexible-hours language] | [nothing stated] | [fixed office presence] |
| [e.g. Role fit] | [%] | [my strongest proof points are the posting's must-haves] | [adjacent] | [a different job] |
| [e.g. Pay] | [%] | [band published at or above my target] | [unposted, estimate near target] | [below floor] |
| [e.g. Company] | [%] | [product and team I would choose] | [neutral] | [signals I distrust] |
| [e.g. Growth] | [%] | [...] | [...] | [...] |

### Rubric: [second name] (used by lane [B])

| Dimension | Weight | 10 looks like | 5 looks like | 2 looks like |
|---|---|---|---|---|
| | | | | |

### Thresholds

| Band | What happens |
|---|---|
| ≥ [7.0], every gate passed on evidence, no ✗, no open question | packet: brief + tailored CV + cover letter |
| > [5.0], no ✗ | "Flagged" line near the top of the digest, open questions named, even when pay is not posted |
| [4.0] to [6.9] | one digest line under its lane |
| below [4.0] or any gate failed | silent; counted |

A score that needs rounding up to cross a line stays below it. Zero packets is a good run.

## 6. Sources

- Watchlist: `watchlist.json`, polled first every run (the keywords in that file do the first title and location filter)
- Boards to search each run: [e.g. LinkedIn Jobs guest search, Welcome to the Jungle, WeWorkRemotely, RemoteOK, <boards for your country>]
- Locations to search: [e.g. "<city>", "remote <country>", "remote EU"]
- Lookback: [e.g. "7 days when the last digest is 3 or more days old, 3 days otherwise"]
- Minimum searches per run: [8]
- Always confirm a posting on the company's own site before scoring. Aggregators show dead jobs.

## 7. Standing rules

The first four cannot be edited away (the skill enforces them). Edit the rest.

- The loop never submits an application, never creates an account, never sends an email. I apply.
- Every claim in a CV or letter traces to `proof-file.md` or `cv-master.md`.
- Gates and must-haves are judged on what the posting states; nothing passes on "probably fine".
- Never nudge me to apply. One action at the top of the digest; I decide.
- **Off limits:** [people, companies, channels the loop may never contact or suggest as a referral path]
- **Interview availability:** [...]
- **Name on materials, exactly:** [...]
- **Never mention in materials:** [...]
- **Referrals:** [e.g. "I know people at <company>; for roles there draft a referral ask before the application"]
- **Earliest start date:** [...]
- **Verification emails:** when a gate is an open question that only the company can answer, the loop drafts a two-line email to `drafts/verification-<company>.md` for me to send; it never sends.

## 8. Packet rules

- Master CV: `cv-master.md`. Tailor from it; never add a fact that is not in it or in `proof-file.md`.
- Sample letters in my own register (the loop copies the register, never the text): [paths under `samples/`, or "none; use the register of my CV summary"]
- Letter: [paragraphs / word limit]. Language: [...]. Spelling: [US / UK].
- Writing defaults (edit to taste): plain verbs; sentences the length I actually write; one concrete detail only I could have written; name any partial must-have honestly; no "I am excited to apply"; no quoting the posting back as flattery; [any punctuation or phrasing rules of my own].
- CV filename: `[Firstname Lastname] CV.pdf`. The company name goes in the folder, not the file.
- Length: CV [2] pages, letter [1] page. Check the PDF before reporting a packet.
- Output: `packets/YYYY-MM-DD-<company-slug>/` inside my config folder. [Optional mirror folder for finished packets]

## 9. Notes and history

[Dated notes on changes to this file, so you and the loop can see why a rule exists.]
