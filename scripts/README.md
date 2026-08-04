# scripts/

Utility scripts for the Edify repository.

## lint-mermaid.py

Validates every Mermaid diagram block in `docs/` (or a specified directory) by
extracting fenced `​```​mermaid ... `​```​` blocks and running each through
`mmdc` (Mermaid CLI). Also runs structural checks for known-problematic patterns
that some strict renderers (VS Code preview, Obsidian) reject:

  1. `Note over X: ...` statements nested inside `alt` / `else` / `loop` / `par`
     / `opt` / `critical` / `break` / `rect` blocks (not portable)
  2. Undeclared participant references in `sequenceDiagram` blocks
     (any X in `Y->>X:` or `X-->>Y:` where X was never declared)
  3. Any parse error reported by `mmdc`

### Requirements

- Python 3.8+
- `mmdc` (Mermaid CLI): `npm install -g @mermaid-js/mermaid-cli`

### Usage

```bash
# Lint all docs/ (default)
python3 scripts/lint-mermaid.py

# Lint a specific subtree
python3 scripts/lint-mermaid.py docs/features

# Show help
python3 scripts/lint-mermaid.py --help
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0    | All Mermaid blocks parse correctly |
| 1    | One or more Mermaid blocks failed to parse |
| 2    | `mmdc` is not installed |
| 3    | Invalid arguments |

### When to run

- Before committing any documentation change that touches `.md` files with
  Mermaid blocks.
- In CI (the script is invokable from any CI system without depending on
  `.github/`).
- After editing a Mermaid diagram to verify it renders in strict parsers
  (VS Code, Obsidian) in addition to GitHub.

### Output

The script reports:
- Per-file, per-block failures with line numbers
- The exact `mmdc` error message (truncated to 10 lines per failure)
- Structural warnings (Note-in-block, undeclared participant)
- A summary at the end: files scanned, blocks checked, failures count
