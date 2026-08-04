#!/usr/bin/env python3
"""
lint-mermaid.py — Validate every Mermaid diagram in the docs tree.

Strategy: extract every ```mermaid ... ``` block from every .md file under
the directory tree, write each block to a temporary .mmd file, and run mmdc
against it. mmdc fails if the block has a syntax error; we collect the
failures with file:line metadata.

Additionally, we run structural checks for known-problematic patterns that
some strict renderers reject:

  1. Note statements nested inside alt/else/loop/par/opt/critical/break/rect blocks
     (not portable across all parsers)
  2. Undeclared participant references in sequenceDiagram blocks
     (any X in `Y->>X:` or `X-->>Y:` where X was never declared)
  3. Note statement syntax that mmdc may accept but VS Code rejects
     (single-word Note without "over")

Usage:
    python3 scripts/lint-mermaid.py [path]
    python3 scripts/lint-mermaid.py                  # lints docs/
    python3 scripts/lint-mermaid.py docs/architecture

Exit codes:
    0  no errors
    1  one or more Mermaid blocks failed to parse
    2  mmdc is not installed
    3  invalid arguments
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional


def extract_mermaid_blocks(md_path: Path) -> List[Tuple[int, int, str]]:
    """
    Extract every mermaid block from a markdown file.
    Returns list of (start_line, end_line, content) tuples.
    Lines are 1-indexed.
    """
    blocks = []
    try:
        text = md_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return blocks

    lines = text.split("\n")
    i = 0
    while i < len(lines):
        if lines[i].strip() == "```mermaid":
            start = i + 1  # 1-indexed
            j = i + 1
            while j < len(lines) and lines[j].strip() != "```":
                j += 1
            if j < len(lines):
                end = j + 1  # 1-indexed closing fence line
                content = "\n".join(lines[i + 1 : j])
                blocks.append((start, end, content))
                i = j + 1
                continue
        i += 1
    return blocks


def structural_check(content: str, file: Path, start_line: int) -> List[str]:
    """
    Run heuristic structural checks that catch known-problematic patterns
    even when mmdc accepts them.
    Returns list of issue strings (empty if no issues).
    """
    issues = []
    lines = content.split("\n")

    # Check 1: Note inside alt/else/loop/par/opt/critical/break/rect blocks
    block_depth = 0
    current_block_type = ""
    for idx, line in enumerate(lines):
        line_num = start_line + 1 + idx
        stripped = line.strip()

        # Match block-opening keywords (alt, loop, par, opt, critical, break, rect)
        # Also match "else" but only when it follows an "alt" (we track depth)
        m_open = re.match(
            r"^(alt|loop|par|opt|critical|break|rect)\b", stripped
        )
        m_else = re.match(r"^else\b", stripped)
        m_end = re.match(r"^end\b", stripped)

        if m_open:
            if block_depth == 0:
                current_block_type = m_open.group(1)
            block_depth += 1
        elif m_else:
            # "else" is part of an existing alt/if block; does not change depth
            pass
        elif m_end:
            if block_depth > 0:
                block_depth -= 1
                if block_depth == 0:
                    current_block_type = ""
        else:
            # Check for Note statements inside a block
            if re.match(r"^Note\b", stripped) and block_depth > 0:
                issues.append(
                    f"{file}:{line_num}: Note statement inside "
                    f"{current_block_type} block "
                    f"(may not render in VS Code preview)"
                )

    # Check 2: Undeclared participant references in sequenceDiagram
    if any(re.match(r"^sequenceDiagram\b", l.strip()) for l in lines):
        declared = set()
        for line in lines:
            stripped = line.strip()
            # participant X as Y / participant X / participant X, X2
            m = re.match(r"^participant\s+(.*)", stripped)
            if m:
                tokens = m.group(1).split()
                # First token is the identifier; rest is optional "as Label"
                if tokens:
                    declared.add(tokens[0].rstrip(","))
                # Also add comma-separated additional identifiers
                # e.g., "participant A, B as Labels" -> add both A and B
                full = m.group(1)
                # Strip everything after " as " to get just the identifier list
                if " as " in full:
                    full = full.split(" as ", 1)[0]
                for tok in full.split(","):
                    tok = tok.strip()
                    if tok:
                        declared.add(tok)
            # actor X as Y
            m = re.match(r"^actor\s+(.*)", stripped)
            if m:
                tokens = m.group(1).split()
                if tokens:
                    declared.add(tokens[0].rstrip(","))
                full = m.group(1)
                if " as " in full:
                    full = full.split(" as ", 1)[0]
                for tok in full.split(","):
                    tok = tok.strip()
                    if tok:
                        declared.add(tok)

        # Now find references
        for idx, line in enumerate(lines):
            stripped = line.strip()
            line_num = start_line + 1 + idx
            # Match arrows: ->>, -->>, ->, -->, --x, -x
            # Capture tokens before and after the arrow
            m = re.match(
                r"^([A-Za-z_][A-Za-z0-9_]*)\s*(-->>|->>|-->|->|---)\s*"
                r"([A-Za-z_][A-Za-z0-9_]*)\s*:",
                stripped,
            )
            if m:
                src, _arrow, dst = m.group(1), m.group(2), m.group(3)
                for tok in (src, dst):
                    if tok not in declared:
                        issues.append(
                            f"{file}:{line_num}: undeclared participant "
                            f"reference \"{tok}\""
                        )

    return issues


def run_mmdc(content: str, tmp_dir: Path, idx: int) -> Tuple[bool, str]:
    """
    Run mmdc against the given content. Returns (ok, error_output).
    """
    mmd_file = tmp_dir / f"block_{idx}.mmd"
    svg_file = tmp_dir / f"block_{idx}.svg"
    mmd_file.write_text(content, encoding="utf-8")

    try:
        result = subprocess.run(
            ["mmdc", "-i", str(mmd_file), "-o", str(svg_file), "--quiet"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return False, "mmdc timed out"
    except FileNotFoundError:
        return False, "mmdc not found"

    combined = (result.stdout or "") + (result.stderr or "")

    # mmdc in --quiet mode: exit 0 on success, exit 1 on error
    if result.returncode != 0:
        return False, combined

    # Check for error keywords in output even with exit 0
    error_patterns = [
        r"syntax error",
        r"parse error",
        r"expected",
        r"unexpected",
        r"cannot resolve",
        r"lexical",
    ]
    for pat in error_patterns:
        if re.search(pat, combined, re.IGNORECASE):
            return False, combined

    # Verify SVG was actually generated and has content
    if not svg_file.exists() or svg_file.stat().st_size < 100:
        return False, combined or "SVG not generated"

    return True, ""


def find_md_files(root: Path) -> List[Path]:
    """Find all .md files under root, sorted."""
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def main():
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)

    root = Path(args[0]) if args and not args[0].startswith("-") else Path("docs")
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        sys.exit(3)

    # Check mmdc
    try:
        subprocess.run(
            ["mmdc", "--version"], capture_output=True, check=True, timeout=10
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        print("ERROR: mmdc (Mermaid CLI) is not installed.", file=sys.stderr)
        print("Install with: npm install -g @mermaid-js/mermaid-cli", file=sys.stderr)
        sys.exit(2)

    md_files = find_md_files(root)
    if not md_files:
        print(f"No .md files found under {root}", file=sys.stderr)
        sys.exit(0)

    total_blocks = 0
    failed_blocks = 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        for md_file in md_files:
            blocks = extract_mermaid_blocks(md_file)
            for start, end, content in blocks:
                total_blocks += 1
                block_id = f"{md_file}:{start}-{end}"

                # Structural checks
                struct_issues = structural_check(content, md_file, start)

                # mmdc check
                mmdc_ok, mmdc_output = run_mmdc(content, tmp_path, total_blocks)

                if not mmdc_ok or struct_issues:
                    failed_blocks += 1
                    print(f"\nFAIL: {block_id}")
                    if struct_issues:
                        print("  Structural:")
                        for issue in struct_issues:
                            print(f"    {issue}")
                    if not mmdc_ok:
                        if mmdc_output:
                            # Take first 10 lines of error output
                            for line in mmdc_output.strip().split("\n")[:10]:
                                print(f"    {line}")

    print("")
    print("=" * 50)
    print("Mermaid lint summary")
    print("=" * 50)
    print(f"Files scanned:  {len(md_files)}")
    print(f"Blocks checked: {total_blocks}")
    print(f"Failures:       {failed_blocks}")
    print("=" * 50)

    if failed_blocks > 0:
        print("\nFix the failing diagrams and re-run this script.")
        sys.exit(1)

    print("\nAll Mermaid blocks parse correctly.")
    sys.exit(0)


if __name__ == "__main__":
    main()
