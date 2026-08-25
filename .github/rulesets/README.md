# Branch rulesets

`main-ruleset.json` protects the `main` branch. Once applied, every change to
`main` must go through a pull request with one approving review from someone
other than the author, and the `ruff` and `mypy` checks must pass before
merging. Force-pushes to `main` are blocked: a force-push (`git push --force`)
replaces commits that already exist on the remote with rewritten ones instead
of adding on top of them, so blocking it keeps the history of `main`
append-only. Deleting the `main` branch itself is also blocked. There are no
bypass actors, so the rules apply to repository admins as well.

Only `main` is covered. Every other branch behaves exactly as before:
contributors can create, rename, force-push and delete their own feature
branches freely, including deleting a mis-created branch or cleaning up a
branch after its pull request has been merged. Merging never deletes the
source branch by itself; that is always a separate step, and it stays allowed
for everything except `main`.

Applying the ruleset requires admin access on the repository. Either import
it through the web interface under Settings > Rules > Rulesets > New ruleset >
Import a ruleset by uploading this file, or create it with the GitHub CLI:

    gh api -X POST repos/danzgeorg/FastCore/rulesets \
      --input .github/rulesets/main-ruleset.json

Changes to the ruleset should be edited here first and re-applied, so this
file stays the source of truth for how `main` is protected.
