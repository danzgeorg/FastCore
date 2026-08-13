# How we work in this repo

Read this once before the first ticket. It is short on purpose.

## The loop, every ticket

1. Take the top ticket from "This week" on the board. One at a time.
2. Move it to "In Progress".
3. Branch off `main`:
   `git switch main && git pull && git switch -c warmup-1-read-csv`
4. Work. Commit as you go, small commits, short message saying what changed:
   `add reject counting`, not `fixes` or `update`.
5. Push: `git push -u origin warmup-1-read-csv`
6. Open a pull request and fill in the template. All of it.
7. Move the ticket to "Testing".
8. Dad reviews in writing. Answer every comment, push the fixes to the same
   branch, the pull request updates itself.
9. Once approved: merge, delete the branch. Writing `Closes #2` in the pull
   request means the ticket closes on its own.

## Rules

- Nothing goes straight to `main`. Every change arrives through a pull request,
  including one-line fixes.
- One ticket in progress at a time.
- Never commit data or secrets. No `users.json`, no uploaded files, no keys, no
  `.env`. Unsure? Ask before you push, not after.
- Every workday ends with a pushed commit and the three-line log entry:
  shipped, learned, blocked.
- Stuck for more than 45 minutes: write the question down, park it, bring it to
  standup. No rabbit holes.

## Branch names

`warmup-<number>-<two or three words>`, lowercase, dashes instead of spaces.
The number is the warm-up number, not the issue number.

Examples: `warmup-1-read-csv`, `warmup-4-login-json`.

## Where the code goes

| Folder | Ticket |
|---|---|
| `warmup/01_data_structures/` | Warm-up 1, issue #2 |
| `warmup/02_language_features/` | Warm-up 2, issue #3 |
| `warmup/03_webapp/` | Warm-up 3 to 7, issues #4 to #8. One app that grows. |
| `warmup-data/` | Test files. Read them, do not change them. |

Tickets 3 to 7 all build the same app. Each one is a pull request that changes
the same folder, exactly like a real project where you add a feature a week.

## About review

Comments are about the code, never about you. Expect a lot of them early on,
that is normal and it is the point.

If a comment is not clear, ask. "I do not understand this comment" is a good
reply and a normal thing to say at work. Guessing what a reviewer meant and
changing the wrong thing is what wastes a day.
