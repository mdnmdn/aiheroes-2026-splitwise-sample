#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Read many files in one call, with a size budget. Made for agents.

Usage: digest.py [options] TARGET [TARGET ...]

A TARGET is a file or a folder (read recursively). Add a line range after a colon to limit
that target only:

    notes.md:10-40      lines 10 to 40
    notes.md:-20        lines 1 to 20
    notes.md:100-       line 100 to the end
    notes.md:5          line 5 only
    notes.md:1-10,50-60 two ranges
    _docs:1-15          the first 15 lines of each file in _docs

--lines gives the default range for each target without its own range. The same file given
twice gets the union of its ranges. "[...]" marks skipped lines between two printed parts.

Examples:
    digest.py --summary _docs                   size of each file, no content
    digest.py --headings _docs                  outline: the headings with line numbers
    digest.py --grep 'currency' -C 2 _docs      matching lines with 2 lines of context
    digest.py --lines 1-15 _docs                peek: the head of each file
    digest.py --compact --no-frontmatter _docs  read all, fewer tokens
    digest.py -n _docs/backlog.md:20-60 AGENTS.md
"""

import argparse
import fnmatch
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache",
             ".ruff_cache", "dist", "build", ".obsidian", ".idea", ".vscode"}
RANGE_RE = re.compile(r"^(\d*-\d*|\d+)(,(\d*-\d*|\d+))*$")
SIZE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([kmg]?)b?\s*$", re.I)
MULTI_SPACE_RE = re.compile(r"(?<=\S)[ \t]{2,}")
TABLE_PAD_RE = re.compile(r" *\| *")
TABLE_RULE_RE = re.compile(r"^\s*\|?(\s*:?-{3,}:?\s*\|)+\s*:?-*:?\s*\|?\s*$")
MD_HEADING_RE = re.compile(r"^#{1,6}\s")
PY_HEADING_RE = re.compile(r"^\s*(async\s+def|def|class)\s+\w")
GAP = "[...]"

Ranges = list[tuple[int, int | None]] | None


class Fail(Exception):
    pass


def parse_size(text: str) -> int:
    m = SIZE_RE.match(text)
    if not m:
        raise argparse.ArgumentTypeError(f"bad size {text!r}: use 4000, 20k, 1.5m")
    return int(float(m[1]) * {"": 1, "k": 1024, "m": 1024**2, "g": 1024**3}[m[2].lower()])


def parse_ranges(text: str) -> list[tuple[int, int | None]]:
    if not RANGE_RE.match(text):
        raise Fail(f"bad range {text!r}: use 10-40, -20, 100-, 5 or 1-10,50-60")
    out = []
    for part in text.split(","):
        a, b = part.split("-", 1) if "-" in part else (part, part)
        lo, hi = int(a) if a else 1, int(b) if b else None
        if lo < 1 or (hi is not None and hi < lo):
            raise Fail(f"bad range {part!r} in {text!r}: lines start at 1 and the end is not before the start")
        out.append((lo, hi))
    return out


def split_target(arg: str) -> tuple[Path, Ranges]:
    if Path(arg).exists() or ":" not in arg:
        return Path(arg), None
    path, spec = arg.rsplit(":", 1)
    if not Path(path).exists():
        raise Fail(f"not found: {path}")
    return Path(path), parse_ranges(spec)


def is_text(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return b"\0" not in f.read(4096)
    except OSError:
        return False


def walk(root: Path, include: list[str], exclude: list[str], hidden: bool) -> list[Path]:
    if root.is_file():
        return [root]
    files = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).parts
        if any(part in SKIP_DIRS or (not hidden and part.startswith(".")) for part in rel):
            continue
        if not p.is_file():
            continue
        if include and not any(fnmatch.fnmatch(p.name, g) for g in include):
            continue
        if any(fnmatch.fnmatch(p.name, g) or fnmatch.fnmatch(str(p), g) for g in exclude):
            continue
        if is_text(p):
            files.append(p)
    return files


def strip_frontmatter(lines: list[str]) -> int:
    """Return the number of leading lines that form a YAML frontmatter block."""
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return i + 1
    return 0


def table_rule(body: str) -> str:
    cells = body.strip().strip("|").split("|")
    out = []
    for c in cells:
        c = c.strip()
        out.append((":" if c.startswith(":") else "") + "---" + (":" if c.endswith(":") and len(c) > 1 else ""))
    return "|" + "|".join(out) + "|"


def compact(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Trim trailing space, collapse inner runs of space, squeeze tables and blank runs.

    Leading indentation stays: it carries meaning in code, YAML and nested lists.
    Code fences keep their content as is, blank lines included.
    """
    out: list[tuple[int, str]] = []
    in_fence = False
    for n, line in lines:
        line = line.rstrip()
        fence = line.lstrip().startswith(("```", "~~~"))
        if fence:
            in_fence = not in_fence
        elif not in_fence:
            indent = line[: len(line) - len(line.lstrip())]
            body = MULTI_SPACE_RE.sub(" ", line[len(indent):])
            if body.startswith("|"):
                body = table_rule(body) if TABLE_RULE_RE.match(body) else TABLE_PAD_RE.sub("|", body)
            line = indent + body
            if not line and out and not out[-1][1]:
                continue
        out.append((n, line))
    while out and not out[0][1]:
        out.pop(0)
    while out and not out[-1][1]:
        out.pop()
    return out


def headings(raw: list[str], path: Path) -> set[int]:
    rule = PY_HEADING_RE if path.suffix == ".py" else MD_HEADING_RE
    keep, in_fence = set(), False
    for n, line in enumerate(raw, 1):
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
        elif not in_fence and rule.match(line):
            keep.add(n)
    return keep


def grep(raw: list[str], pattern: re.Pattern, context: int) -> set[int]:
    keep = set()
    for n, line in enumerate(raw, 1):
        if pattern.search(line):
            keep.update(range(max(1, n - context), min(len(raw), n + context) + 1))
    return keep


def select(raw: list[str], ranges: Ranges, skip: int, only: set[int] | None) -> list[int]:
    """The line numbers to show, in order, before compaction."""
    keep = set(range(skip + 1, len(raw) + 1))
    if ranges:
        wanted = set()
        for a, b in ranges:
            wanted.update(range(a, min(b if b is not None else len(raw), len(raw)) + 1))
        keep &= wanted
    if only is not None:
        keep &= only
    return sorted(keep)


def segments(numbers: list[int]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for n in numbers:
        if out and n == out[-1][1] + 1:
            out[-1] = (out[-1][0], n)
        else:
            out.append((n, n))
    return out


def fmt_spans(spans: list[tuple[int, int]]) -> str:
    return ",".join(f"{a}-{b}" if a != b else str(a) for a, b in spans)


def kb(n: int) -> str:
    return f"{n / 1024:.1f} KB"


def show(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base))
    except ValueError:
        return str(path)


def summary(files: list[Path], base: Path) -> None:
    rows = []
    for p in files:
        data = p.read_bytes()
        rows.append((show(p, base), data.count(b"\n") + (not data.endswith(b"\n") and bool(data)), len(data)))
    width = max((len(r[0]) for r in rows), default=4)
    print(f"{'file'.ljust(width)}  {'lines':>6}  {'size':>9}  {'~tokens':>8}")
    for name, lines, size in rows:
        print(f"{name.ljust(width)}  {lines:>6}  {kb(size):>9}  {size // 4:>8}")
    total_l, total_b = sum(r[1] for r in rows), sum(r[2] for r in rows)
    print(f"{'total: ' + str(len(rows)) + ' files':<{width}}  {total_l:>6}  {kb(total_b):>9}  {total_b // 4:>8}")


def merge(old: Ranges, new: Ranges) -> Ranges:
    """Union of two range lists. None means the whole file."""
    if old is None or new is None:
        return None
    return old + new


def collect(args, default_ranges: Ranges) -> tuple[dict[Path, tuple[Path, Ranges]], list[str]]:
    jobs: dict[Path, tuple[Path, Ranges]] = {}
    notes = []
    for arg in args.targets:
        path, ranges = split_target(arg)
        if not path.exists():
            raise Fail(f"not found: {arg}")
        if path.is_file() and not is_text(path):
            notes.append(f"skipped binary file: {arg}")
            continue
        for f in walk(path, args.include, args.exclude, args.hidden):
            key = f.resolve()
            r = ranges or default_ranges
            jobs[key] = (f, merge(jobs[key][1], r)) if key in jobs else (f, r)
    return jobs, notes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 epilog=__doc__.split("\n", 2)[2],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="+", metavar="TARGET", help="file or folder, optional :RANGE")
    ap.add_argument("-s", "--summary", action="store_true", help="list files with lines, size and ~tokens; no content")
    ap.add_argument("-H", "--headings", action="store_true",
                    help="outline: markdown headings and Python def/class lines, numbered")
    ap.add_argument("-g", "--grep", metavar="REGEX", help="only lines that match REGEX (numbered). Files without a match are listed at the end")
    ap.add_argument("-C", "--context", type=int, default=0, metavar="N", help="with --grep: N lines before and after each match")
    ap.add_argument("-I", "--ignore-case", action="store_true", help="with --grep: ignore case")
    ap.add_argument("-l", "--lines", metavar="RANGE", help="default line range for targets without their own")
    ap.add_argument("-c", "--compact", action="store_true",
                    help="trim spaces, squeeze tables, collapse blank-line runs (code fences stay as is)")
    ap.add_argument("--no-blank", action="store_true", help="drop every blank line")
    ap.add_argument("--no-frontmatter", action="store_true", help="drop a leading YAML frontmatter block")
    ap.add_argument("-n", "--line-numbers", action="store_true", help="prefix each line with its number")
    ap.add_argument("--max-size", type=parse_size, default=parse_size("100k"),
                    help="total output budget (default 100k). Files past it are listed, not printed")
    ap.add_argument("--max-file-size", type=parse_size, default=parse_size("20k"),
                    help="budget per file (default 20k). A longer file is cut, with the range of the rest")
    ap.add_argument("-i", "--include", action="append", default=[], metavar="GLOB",
                    help="in folders, keep only names matching GLOB (repeatable), e.g. '*.md'")
    ap.add_argument("-x", "--exclude", action="append", default=[], metavar="GLOB",
                    help="skip names or paths matching GLOB (repeatable)")
    ap.add_argument("--hidden", action="store_true", help="include dotfiles and dot-folders")
    args = ap.parse_intermixed_args()

    try:
        default_ranges = parse_ranges(args.lines) if args.lines else None
        pattern = re.compile(args.grep, re.I if args.ignore_case else 0) if args.grep else None
        jobs, notes = collect(args, default_ranges)
    except (Fail, re.error) as e:
        print(f"digest: {e}", file=sys.stderr)
        return 2
    base = Path.cwd().resolve()
    numbered = args.line_numbers or args.headings or pattern is not None

    if args.summary:
        summary([f for f, _ in jobs.values()], base)
        for note in notes:
            print(f"[{note}]")
        return 0

    used, skipped, no_match = 0, [], []
    for path, ranges in jobs.values():
        if used >= args.max_size:
            skipped.append(path)
            continue
        raw = path.read_text(encoding="utf-8", errors="replace").splitlines()
        name = show(path, base)
        only = None
        if args.headings:
            only = headings(raw, path)
        if pattern is not None:
            only = grep(raw, pattern, max(0, args.context)) if only is None else only & grep(raw, pattern, 0)
        chosen = select(raw, ranges, strip_frontmatter(raw) if args.no_frontmatter else 0, only)
        if only is not None and not chosen:
            no_match.append(name)
            continue

        spans = segments(chosen)
        seg_of = {n: i for i, (a, b) in enumerate(spans) for n in range(a, b + 1)}
        lines = [(n, raw[n - 1]) for n in chosen]
        if args.compact:
            lines = compact(lines)
        if args.no_blank:
            lines = [(n, s) for n, s in lines if s.strip()]

        budget = min(args.max_file_size, args.max_size - used)
        body, size, cut_at, printed = [], 0, None, []
        width = len(str(len(raw)))
        prev_seg = None
        for n, s in lines:
            seg = seg_of[n]
            out = [GAP] if prev_seg is not None and seg != prev_seg else []
            out.append(f"{n:>{width}}: {s}" if numbered else s)
            cost = sum(len(t.encode()) + 1 for t in out)
            if size + cost > budget and body:
                cut_at = n
                break
            body.extend(out)
            size += cost
            prev_seg = seg
            if printed and seg_of[printed[-1][1]] == seg:
                printed[-1] = (printed[-1][0], n)
            else:
                printed.append((n, n))

        if not raw:
            span = "empty file"
        elif not chosen:
            asked = fmt_spans([(a, b if b is not None else len(raw)) for a, b in ranges or []])
            span = f"no lines selected: asked {asked or 'frontmatter only'}, file has {len(raw)} lines"
        elif only is not None:
            span = f"{sum(1 for _, t in lines if t)} lines selected of {len(raw)}"
        else:
            span = f"lines {fmt_spans(printed)} of {len(raw)}"
        print(f"==> {name} ({span}, {kb(path.stat().st_size)}) <==")
        if body:
            print("\n".join(body))
        if cut_at is not None:
            k = seg_of[cut_at]
            rest = [(cut_at, spans[k][1])] + spans[k + 1:]
            print(f"[cut: budget reached. Rest: {name}:{fmt_spans(rest)}]")
        print()
        used += size

    if no_match:
        print(f"[no match in {len(no_match)} file(s): {', '.join(no_match)}]")
    if skipped:
        print(f"[max-size reached: {len(skipped)} file(s) not printed]")
        for p in skipped:
            print(f"  {show(p, base)}")
    for note in notes:
        print(f"[{note}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
