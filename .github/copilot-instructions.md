# Copilot Instructions (Submodule: sck-core-db)

## Plan → Approval → Execute (Mandatory)
Follow the root repository workflow: present a numbered plan for any non-trivial action and wait for approval before executing. Trivial explanatory answers may proceed without plan. Explicit user override to "skip plan" is honored; otherwise, wait.

- Tech: Python package (DB helpers).
- Precedence: Local first; then root at `../../.github/...`.
- Conventions: Follow `../sck-core-ui/docs/backend-code-style.md` for shared patterns.

## Google Docstring Requirements
**MANDATORY**: All docstrings must use Google-style format for Sphinx documentation generation:
- Use Google-style docstrings with proper Args/Returns/Example sections
- Napoleon extension will convert Google format to RST for Sphinx processing
- Avoid direct RST syntax (`::`, `:param:`, etc.) in docstrings - use Google format instead
- Example sections should use `>>>` for doctests or simple code examples
- This ensures proper IDE interpretation while maintaining clean Sphinx documentation

## Contradiction Detection
- Validate against backend patterns and root precedence.
- On conflict, warn + options + example.
- Example: "Suggesting unbounded scans conflicts with performance guidance; require pagination/indices and limits."

## Standalone clone note
If cloned standalone, see:
- UI/backend conventions: https://github.com/eitssg/simple-cloud-kit/tree/develop/sck-core-ui/docs
- Root Copilot guidance: https://github.com/eitssg/simple-cloud-kit/blob/develop/.github/copilot-instructions.md
 
