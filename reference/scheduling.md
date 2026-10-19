# Running the loop on a schedule

The loop works run by hand ("Run my job-hunt-loop" in Claude Code). It works better on a schedule, because the value is in catching a posting within a day or two and in never having to remember to look. Everything is local: the config, the CV, the state file and the scripts all live on your machine, so whatever runs the schedule has to run there too, with the machine awake.

## Option A: Claude Code scheduled task

Scheduling options depend on the Claude Code version and interface. CLI [scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks) run inside an active session and are not a permanent background scheduler. Confirm the task's persistence, expiration, and timezone in your installed interface.

For a local session, ask to run the skill on your preferred days with this prompt:

```text
Run the job-hunt-loop skill. Config folder: ~/job-hunt/.
Write the digest to ~/job-hunt/digests/ and tell me the One thing today line.
```

Use a lookback that covers the gap between runs. For an unattended persistent schedule of just the poller, use Option B. Do not move private config into a cloud scheduler without reviewing its data handling.

## Option B: cron for the poller only

If you want only the cheap part (the watchlist poll) to run automatically and do the judgment work yourself, give the cron job its own state file and output folder so it does not interfere with full loop runs:

```cron
# Monday looks back a week, Tue-Thu three days. Use full paths: cron's PATH is short.
30 8 * * 1    cd $HOME/.claude/skills/job-hunt-loop && /usr/bin/python3 scripts/poll_boards.py --config $HOME/job-hunt/watchlist.json --state $HOME/job-hunt/polls/seen.json --days 7 > $HOME/job-hunt/polls/$(date +\%F).md 2>&1
30 8 * * 2-4  cd $HOME/.claude/skills/job-hunt-loop && /usr/bin/python3 scripts/poll_boards.py --config $HOME/job-hunt/watchlist.json --state $HOME/job-hunt/polls/seen.json --days 3 > $HOME/job-hunt/polls/$(date +\%F).md 2>&1
```

Create `~/job-hunt/polls/` first, and check `which python3` for the right interpreter path. Then open the newest file in `~/job-hunt/polls/` with Claude Code and say "gate and score these against my criteria".

## Option C: by hand

```
Run my job-hunt-loop.
Run my job-hunt-loop with lookback 14.
```

Then `packet`, `next`, `skip`, `applied <company> <date>` as described in SKILL.md under Commands.

## Keeping it honest over time

- Reread `search-criteria.md` every few weeks. Your gates move as your situation moves (a new schedule, a pay floor you are willing to lower, a lane you want to add). Date the change in section 9 so the loop can tell why a rule exists.
- When a packet gets rejected or a role turns out different from the posting, write one line in the tracker about why. Patterns show up after ten rows.
- Zero packets for a month is information: either the market is thin for your lanes, or your gates are tighter than your real constraints. Decide which on purpose.
