# Lean tactic counts

A small comparison of tactic-name counts in three Lean codebases:

- mathlib: `Mathlib/`
- OpenAI's Navier–Stokes certificate: `NavierStokes/`
- Anthropic's Fermat's Last Theorem certificate: `Definitions/`, `P2M/`, and `Theorems/`

The counts are deliberately plain: the script counts literal occurrences of 200 tracked tactic spellings in the selected `.lean` files. The list covers common Mathlib spellings plus project-specific tactics found in the certificates. It ignores line comments, nested block comments, and string contents. It does not expand macros or count tactic executions, and spellings outside the list are not included. Treat the numbers as a simple source-text comparison, not an exhaustive inventory.

The repository URLs, exact revisions, Lean versions, and included paths are recorded in [`sources.json`](sources.json). The current counts are in [`site/data.json`](site/data.json).

## Regenerate the counts

Clone each source into a temporary directory and check out the revision listed in `sources.json`. Then run:

```sh
python3 scripts/count_tactics.py \
  --source mathlib=/path/to/mathlib4 \
  --source openai-navier-stokes=/path/to/NavierStokesAndEuler \
  --source anthropic-flt=/path/to/fermats-last-theorem
```

The script writes `site/data.json`. It only reads the configured source paths; the source repositories are not copied into this repository.

## View the chart

Serve the `site/` directory locally so the browser can load its JSON data:

```sh
python3 -m http.server 8000 --directory site
```

Then open <http://localhost:8000>.
