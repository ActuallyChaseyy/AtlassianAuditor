# Contributing to AtlassianAuditor

Contributions are welcome. Please follow the guidelines below to keep the codebase consistent.

## Workflow

1. Fork the repository and create a branch from `main`:
   ```bash
   git checkout -b your-branch-name
   ```
2. Make your changes.
3. Open a pull request against `main` with a clear description of what the change does and why.

## What to contribute

- **New checks** - the most common contribution. See the [Adding new checks](README.md#adding-new-checks) section of the README for the exact pattern to follow.
- **New data handlers** - if a check requires data not yet collected (e.g. Confluence spaces, permissions), add a handler under `src/handlers/` and wire it into `Auditor.py`.
- **Report improvements** - changes to `src/report/generator.py` that improve readability or usability of the HTML output.
- **Bug fixes** - incorrect check logic, pagination issues, API compatibility.

## Guidelines

- **One concern per PR.** A new check, a bug fix, and a report change should be separate PRs.
- **No new dependencies** without a good reason. The project intentionally keeps its dependency footprint small (`requests`, `python-dotenv`).
- **Keep check functions focused.** Each `_check_*` function should test exactly one condition and return findings via `_finding()`. See existing checks for the pattern.
- **Document your code.** Add a docstring to every function describing what it does, its parameters, and what it returns. Inline comments explaining the reasoning behind non-obvious logic are strongly encouraged - err on the side of over-commenting rather than under.

## AI-assisted contributions

Using AI tools during development is fine, but PRs where the contribution was written entirely by AI without meaningful human authorship will not be accepted. You should be able to explain every part of what you're submitting - why the logic works, why the approach was chosen, and what edge cases were considered.

If AI tooling meaningfully assisted your contribution, briefly note how in the PR description. This isn't a requirement to disclose every autocomplete suggestion, but rather to be transparent when a significant portion of the code or design came from a model.

The goal is to ensure that contributors understand and stand behind what they're submitting.

## Running locally

```bash
cd src
cp .env.example .env  # fill in your credentials
python Auditor.py
```

See the [Setup](README.md#setup) section of the README for credential details.
