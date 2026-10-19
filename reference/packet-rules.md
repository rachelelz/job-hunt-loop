# Packet rules: how to build a CV and cover letter that are true and sound like the applicant

A packet is a draft for the applicant to review and tweak. It is never sent by the loop.

## Order of work

1. `jd.txt`, then `brief.md` from `templates/brief.template.md`: facts, gates, score, the must-haves table. If the table shows a ✗ on a stated must-have, stop: this is a "close, but" line, not a packet, unless the applicant asked for it anyway.
2. Tailored CV from `cv-master.md`.
3. `cover-letter.md` from `proof-file.md` and the sample letters named in the criteria file, then `cover-letter.html`, `Cover letter.pdf`, and `Cover letter.txt` (the body as plain text, for application forms with a text field).
4. Render both to PDF with `bash "$SKILL_DIR/scripts/render_pdf.sh" <file.html> "<name>.pdf" <max pages>` (2 for the CV, 1 for the letter), check page count and breaks.
5. Claims audit, written into the brief.
6. `referral-ask.md`, only when the criteria file names a referral rule for this company.

## The CV

- Start from the master. Reorder so the posting's must-haves appear in the summary and the first bullets. Trim what the posting does not care about. Do not add.
- Every number comes from `proof-file.md` or the master, used the way the proof file's "OK to use as" column allows: `CV + letter`, `CV only`, `letter, softened as "..."`, `interview only`, `not yet`. A number marked `CV only` never appears in the letter; one marked `not yet` appears nowhere.
- Keep the applicant's own sentences where they exist. Rewriting a true bullet into smoother prose is how facts drift; if you must shorten, cut words, do not replace them.
- Tools: list only the ones the applicant can actually use, from the proof file. If the posting names a tool they do not have, leave it out and put the gap in the brief.
- Two pages. A job heading never splits from its bullets (the template's `break-inside: avoid-page` handles most of this; check the preview images anyway).
- Filename is the applicant's plain name, `Firstname Lastname CV.pdf`. The company name goes in the folder, never in the file. Recruiters save dozens of files called `CV_CompanyName.pdf`; a plain name is the one they can find again.

## The cover letter

Read the applicant's sample letters first and copy the register, never the text: sentence length, how formal, how much humor, how they open and close. Then:

- **Paragraph 1:** the one line in the posting that is a true description of their recent work, and the proof. Never open with "I am excited to apply for" or a restatement of the job title.
- **Paragraph 2:** the must-haves they meet, with the numbers the proof file allows in prose.
- **Paragraph 3:** one detail only this applicant could have written (a real scene, a specific thing they built, a number with a story behind it) and an honest line on any must-have they only partly meet. Honesty about a gap reads as confidence; a hidden gap gets found in the first interview.
- **Paragraph 4:** why this company and this role, concretely (something from the posting or the company's own site that is checkable), and the start date from the criteria file.

Writing rules:

- Plain verbs. Say what they did: "ran", "built", "launched", "wrote". Not "spearheaded", "leveraged", "drove".
- Long flowing sentences are fine when that is how the applicant writes. Short clipped fragments stacked for effect are not.
- Defaults the criteria file (section 8) can change: no "it's not X, it's Y" flips, no "Here's the thing", no rule-of-three lists for rhythm, no closing line that restates the letter, one or two em-dashes at most.
- No posting phrases quoted back as flattery ("your mission to empower..."). Quote the posting only to name a must-have you are answering.
- Spelling as the criteria file says (US or UK). Numbers as digits with units (€65k, 12 markets, 2 pages).
- Under one page in the template. Four paragraphs, usually under 400 words.

The master test before you save it: if any other applicant could have signed this letter, rewrite paragraph 3 until they could not.

## The claims audit

In the brief, list every number and every named achievement in both documents with the file and row it came from. A claim with no row is removed, not softened. Mark anything the applicant must confirm before sending (for example "did you personally run the tracking setup, or did your team?") as an open checklist item.

## The honesty line

The loop writes what the applicant can prove. It does not round 1.8x up to 2x, does not turn "part of the team that" into "led", does not list a tool they watched someone else use. The applicant can choose to be bolder when they review. The loop cannot choose for them.
