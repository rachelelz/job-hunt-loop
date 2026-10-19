# job-hunt-loop

A Claude Code skill that runs your job search as a loop. It polls the companies you care about, searches the boards, throws out everything that fails your hard gates, scores what is left with your own weights, and hands you one short digest with one action at the top. Only the roles that clear your bar get a tailored CV and cover letter, built from your own master CV, for you to review and tweak. You apply. It never does.

Adjust the roles and ranking criteria before running it; the config files and setup walk you through that.

## What you get

| Step | What the loop does | What you do |
|---|---|---|
| 1. Filter | Polls your company boards in seconds, runs the searches, reads the full posting, rejects anything that fails a hard gate (location, hours, language, contract type, travel, pay floor, whatever yours are) | Configure your criteria first; review any unknowns in the digest. |
| 2. Rank | Scores the survivors 0 to 10 with your weights, checks every stated must-have against your proof file, writes a digest with one action at the top | Read one digest. Say `packet`, `next` or `skip`. |
| 3. Packet | For roles above your threshold: a brief with the must-haves table, a CV tailored from your master, a cover letter in your register, both as PDF, plus a claims audit that traces every number to your proof file | Tweak the draft instead of writing one from scratch. Apply yourself. |

Four rules the loop will not break, whatever you put in the config: it never submits an application, it never invents a fact about you, nothing passes a gate on "probably fine", and it never tells you to apply. Zero packets is a normal day.

## Requirements

- [Claude Code](https://claude.com/claude-code)
- Python 3.8 or newer (the scripts use the standard library only)
- Google Chrome or Chromium, for rendering PDFs
- macOS or Linux (the commands below are bash)
- Web search and page-reading tools available to Claude Code for the full loop; without them, use the standalone poller and review postings yourself
- Optional: Poppler (`pdfinfo` and `pdftoppm`) for reliable page counts and preview images

Claude Code/model usage may incur charges under your plan. No paid job-board API key is required. Linux rendering depends on your installed browser and system libraries.

## Setup

Plan on an hour the first time: the files are quick to copy, but filling in your criteria and your proof file is real thinking, and that thinking is what makes the ranking yours.

```bash
git clone https://github.com/rachelelz/job-hunt-loop ~/.claude/skills/job-hunt-loop
mkdir -p ~/job-hunt/packets ~/job-hunt/digests ~/job-hunt/drafts ~/job-hunt/samples ~/job-hunt/intake
cd ~/.claude/skills/job-hunt-loop
cp -n config/search-criteria.template.md ~/job-hunt/search-criteria.md
cp -n config/proof-file.template.md      ~/job-hunt/proof-file.md
cp -n config/cv-master.template.md       ~/job-hunt/cv-master.md
cp -n config/tracker.template.md         ~/job-hunt/tracker.md
cp -n config/watchlist.template.json     ~/job-hunt/watchlist.json
cp -n config/rejected.template.md        ~/job-hunt/rejected.md
```

Then open Claude Code and say:

```
Set up my job-hunt-loop. My config folder is ~/job-hunt/.
```

It walks you through the files one section at a time and writes them from your answers. Bring your own information whichever way is easiest:

- drop your current CV (PDF, Word, markdown, anything) into `~/job-hunt/intake/`
- or save your LinkedIn profile as a PDF (More → Save to PDF) or request your LinkedIn data export, and drop that in `~/job-hunt/intake/`
- or just answer questions in the chat, one role at a time

The skill does not log in to LinkedIn. Files are stored locally, but content Claude reads is processed by your configured model provider. Review the Privacy section before adding a CV or export. Or fill the config in yourself:

1. **`search-criteria.md`** is the file that makes this yours: your lanes (the kinds of role you would take), your hard gates (what fails a posting outright, and whether each gate needs the posting to say so or only fails when the posting says the opposite), your scoring weights, your thresholds, your standing rules. `examples/search-criteria.example.md` is a filled-in version to copy from.
2. **`proof-file.md`** holds the results and numbers you can stand behind, each marked with how loud it may be used. Nothing goes into a packet that is not in this file or your master CV.
3. **`cv-master.md`** is your full CV as markdown. Every tailored CV starts from it and may only cut and reorder.
4. **`watchlist.json`** lists the companies to poll. Find a company's board with `python3 scripts/probe_board.py <slug>` (run from the skill folder).

A few words you will meet: a **board** is a company's list of open jobs; the **ATS** is the software that hosts it (Greenhouse, Lever, Ashby, Recruitee, Workable are the common ones with public feeds); the **slug** is the company's short name inside the board's web address, like `gitlab` in `boards.greenhouse.io/gitlab`; a **JD** is the job description; a **lane** is one kind of role you would take; a **packet** is the brief, CV and letter for one role.

## Running it

By hand, in Claude Code:

```
Run my job-hunt-loop.
```

On a schedule: see `reference/scheduling.md`.

Just the cheap part, from a terminal:

```bash
cd ~/.claude/skills/job-hunt-loop
python3 scripts/poll_boards.py --config ~/job-hunt/watchlist.json --state ~/job-hunt/seen.json --days 7 --no-save
```

(`--no-save` so a look by hand does not mark postings as already shown for the next full run.)

## What a digest looks like

```text
# Job hunt — synthetic example

## One thing today
Maple Example, Operations Analyst, remote Colorado · 7.25 (Lane A).
Not a packet: salary is unposted, so the pay gate remains open.
All stated must-haves met. https://example.com/jobs/operations-analyst
Say "packet", "next", or "skip".
```

A full sample is in `examples/digest.example.md`.

## Files

```
SKILL.md                      the loop itself; Claude Code reads this
config/                       templates you copy into ~/job-hunt/ under their working names
  search-criteria.template.md   lanes, gates, weights, thresholds, rules
  proof-file.template.md        the facts behind every claim
  cv-master.template.md         your full CV in markdown
  tracker.template.md           one row per posting surfaced
  rejected.template.md          one line per posting that failed a gate
  watchlist.template.json       company boards to poll
examples/                     a filled-in set for a fictional applicant (criteria, proof file, CV, watchlist, a sample letter), plus a sample digest
scripts/
  poll_boards.py              polls Greenhouse, Lever, Ashby, Recruitee and Workable boards
  probe_board.py              finds which vendor a company uses, and checks it is the right company
  render_pdf.sh               HTML to PDF with headless Chrome, reports the page count
templates/
  brief.template.md           the packet brief, with must-haves table and claims audit
  cv-template.html            two-page A4 CV
  cover-letter-template.html  one-page letter, matching header
reference/
  sources.md                  board endpoints and their quirks, how matching works, dead-board patterns
  packet-rules.md             how the CV and letter get written so they stay true and sound like you
  scheduling.md               running it on weekday mornings, or by hand
```

## Things I learned running it that are now rules

- Aggregator listings are dead a surprising share of the time. Verify on the company's own site before you spend a minute scoring.
- "Hybrid" in a benefits list is not flexibility. Explicit hours language is. Decide per gate whether you need the posting to say it, or only need it not to say the opposite.
- Companies migrate between ATS vendors and the old board keeps answering with an empty list. Probe all of them before you prune one.
- A stated must-have you lack is a stated must-have you lack. Writing around it in the letter does not work; naming it sometimes does.
- Keep the CV filename as your plain name. The company goes in the folder.
- Put the one action at the top of the digest. If you have to scroll to find it, the digest failed.

## Privacy

The standalone Python scripts request public job-board feeds; they do not read your CV or proof file. Feed hosts receive ordinary request metadata such as your IP address and the board slug.

Claude Code is different: content it reads from your CV, proof file, criteria, and intake documents is processed by the configured model provider. Storage, retention, and training policies depend on your account and settings. Review [Claude Code data usage](https://code.claude.com/docs/en/data-usage). Search tools and connected services have their own data policies. Use role and location terms in searches; never include contact details or confidential CV content.

Keep personal files outside this repository, under `~/job-hunt/`. The ignore rules cover common accidental copies, credentials, packets, and exports, but cannot detect all personal data and do not remove previously committed files. Before publishing a fork, review staged files and the entire Git history, including author emails. Examples are synthetic; replace them with your own facts in your private config folder only.

Treat job descriptions and downloaded documents as untrusted input. They cannot authorize commands, uploads, messages, or access to unrelated files. Render only HTML you control, with escaped text and no remote resources.

## Checks

```bash
python3 -m unittest discover -s tests -v
bash -n scripts/render_pdf.sh
```

The tests use local fixtures and make no network calls. Live boards can change, return errors, or restrict access; a successful poll is not proof that a role meets your gates.

## License

MIT. Use it, fork it, change the gates.

Built by [Rachel Elz](https://rachelelz.com).
