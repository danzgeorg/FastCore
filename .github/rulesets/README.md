# Branch rulesets

`main-ruleset.json` protects the `main` branch. Once applied, every change to
`main` must go through a pull request with one approving review from someone
other than the author, the `ruff` and `mypy` checks must pass before merging,
and force-pushes and branch deletion are blocked. There are no bypass actors,
so the rules apply to repository admins as well.

Applying the ruleset requires admin access on the repository. Either import
it through the web interface under Settings > Rules > Rulesets > New ruleset >
Import a ruleset by uploading this file, or create it with the GitHub CLI:

    gh api -X POST repos/danzgeorg/FastCore/rulesets \
      --input .github/rulesets/main-ruleset.json

Changes to the ruleset should be edited here first and re-applied, so this
file stays the source of truth for how `main` is protected.
