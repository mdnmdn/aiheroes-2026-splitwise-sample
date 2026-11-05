#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml", "rich"]
# ///
"""Documentation maintenance for _docs/: lint, index, new, stamp, verify, drift and more.

Run it through mise: `mise run docs-lint`, `mise run docs-index`, `mise run docs-new feature <slug>`, ...
Reference: `_docs/_meta/tools.md`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import yaml
from rich.console import Console
from rich.markup import escape
from rich.table import Table

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "_docs"
HOME = DOCS / "Home.md"
REVIEW_LOG = DOCS / "_meta" / "review-log.md"

# Source roots (relative to REPO). Empty while the project is in ideation: fill when the stack
# is chosen, for example ("src",). Code-symbol checks and the code-map tree switch on with it.
SOURCE_ROOTS: tuple[str, ...] = ()
SOURCE_SUFFIXES: set[str] = set()  # for example {".ts", ".py"}
IGNORED_DIRS = {".git", "node_modules", ".venv", "__pycache__", "refs", "tmp", "_data"}

# Not documents: raw input is preserved verbatim, so it carries no frontmatter.
DOC_EXCLUDE_DIRS = ("inbox",)

REQUIRED_FIELDS = ("id", "title", "kind", "status", "summary", "read_when", "updated", "verified")
ALLOWED_STATUS = ("current", "draft", "superseded")
KIND_FOLDER = {
    "product": "product",
    "feature": "features",
    "tech": "tech",
    "infra": "infra",
    "meta": "_meta",
    "wip": "wip",
}
KIND_PREFIX = {
    "product": "prod-",
    "feature": "feat-",
    "tech": "tech-",
    "infra": "infra-",
    "meta": "meta-",
    "wip": "wip-",
}
# Root documents: id -> kind. They sit in `_docs/` itself, outside the kind folders.
ROOT_EXCEPTIONS = {"index": "meta", "backlog": "product"}

LENGTH_TARGET = (150, 400)
LENGTH_CEILING = 500
LENGTH_FLOOR_WARN = 80
FENCE_DENSITY_MAX = 0.15
FENCE_LINES_MAX = 20

# Read by lookup, not read through: no length band, no fence caps.
L4_EXEMPT_IDS = {
    "index",
    "backlog",
    "prod-glossary",
    "meta-feedback",
    "meta-review-log",
    "meta-asd-ste-100",
}
LINK_REPEAT_EXEMPT_IDS = {"index", "backlog"}

# A backticked token is a claim about a file only when it starts with one of these.
# `refs/`, `tmp/` and `_data/` are never claims.
REPO_PATH_PREFIXES = ("_tools/", "_design/", "_docs/", *(r.rstrip("/") + "/" for r in SOURCE_ROOTS))
EXTERNAL_PATH_MARKERS = ("refs/", "tmp/", "_data/")

BANNED_PHRASES = (
    "now",
    "already",
    "no longer",
    "used to",
    "previously",
    "currently",
    "not yet",
    "will be",
    "has been added",
    "was changed",
)
TIMELESSNESS_EXEMPT_DIRS = ("wip", "inbox", "_meta")
# The ledgers name documents that may since have been deleted.
DOC_HISTORY_DIRS = ("_meta",)

WIP_STALE_DAYS = 30
INBOX_STALE_DAYS = 14
FRESHNESS_TOLERANCE_DAYS = 2
MAX_LINK_REPEATS = 3
MAX_INBOUND_EDGES = 5
CYCLE_DAYS = {"monthly": 30, "quarterly": 91, "yearly": 365}

FENCE_RE = re.compile(r"^(`{3,}|~{3,})(.*)$")
LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
FILE_SPAN_RE = re.compile(r"^[\w./-]+\.(?:toml|md|json|yaml|yml|py|sh|css|html|js|ts|tsx|png|sql)$")
SYMBOL_SPAN_RE = re.compile(r"^([A-Za-z_][\w]*)\(\)$")
IDENTIFIER_RE = re.compile(r"[A-Za-z_][\w]*")
MARKER_RE = "<!-- generated:{kind} {name} -->"

console = Console()


# ---------------------------------------------------------------- shared core


@dataclass
class Fence:
    start: int
    lines: int
    info: str


@dataclass
class Doc:
    path: Path
    rel: str
    meta: dict
    lines: list[str]
    prose: list[tuple[int, str]]
    fences: list[Fence]
    headings: list[tuple[int, int, str]]
    links: list[tuple[int, str]]
    file_spans: list[tuple[int, str]]
    symbol_spans: list[tuple[int, str]]
    meta_error: str | None = None

    @property
    def id(self) -> str | None:
        value = self.meta.get("id")
        return str(value) if value else None

    @property
    def folder(self) -> str:
        parts = Path(self.rel).relative_to("_docs").parts
        return parts[0] if len(parts) > 1 else ""

    @property
    def title(self) -> str:
        if self.meta.get("title"):
            return str(self.meta["title"])
        for _, level, text in self.headings:
            if level == 1:
                return text
        return self.path.name

    @property
    def total_lines(self) -> int:
        return len(self.lines)

    @property
    def fence_lines(self) -> int:
        return sum(f.lines for f in self.fences)

    def _list(self, key: str) -> list[str]:
        raw = self.meta.get(key) or []
        return [str(a) for a in raw] if isinstance(raw, list) else [str(raw)]

    @property
    def anchors(self) -> list[str]:
        return self._list("source_anchors")

    @property
    def depends_on(self) -> list[str]:
        return self._list("depends_on")


def split_frontmatter(lines: list[str]) -> tuple[dict, int, str | None]:
    if not lines or lines[0].rstrip() != "---":
        return {}, 0, "no frontmatter block"
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            try:
                meta = yaml.safe_load("\n".join(lines[1:i])) or {}
            except (yaml.YAMLError, ValueError) as exc:
                return (
                    {},
                    i + 1,
                    f"frontmatter YAML does not parse: {exc}. Fix the syntax or the date.",
                )
            if not isinstance(meta, dict):
                return {}, i + 1, "frontmatter is not a mapping"
            return meta, i + 1, None
    return {}, 0, "frontmatter block is never closed"


def scan_structure(lines: list[str], skip_to: int) -> tuple[list[tuple[int, str]], list[Fence]]:
    """Split a document into prose lines and fenced blocks, tracking fence state line by line."""
    prose: list[tuple[int, str]] = []
    fences: list[Fence] = []
    open_marker: tuple[str, int] | None = None
    start = count = 0
    info = ""
    for lineno, raw in enumerate(lines, start=1):
        if lineno <= skip_to:
            continue
        match = FENCE_RE.match(raw.lstrip())
        if open_marker is None:
            if match:
                open_marker = (match.group(1)[0], len(match.group(1)))
                start, count, info = lineno, 0, match.group(2).strip()
            else:
                prose.append((lineno, raw))
            continue
        char, width = open_marker
        if (
            match
            and match.group(1)[0] == char
            and len(match.group(1)) >= width
            and not match.group(2).strip()
        ):
            fences.append(Fence(start, count, info))
            open_marker = None
        else:
            count += 1
    if open_marker is not None:
        fences.append(Fence(start, count, info))
    return prose, fences


def load_doc(path: Path) -> Doc:
    lines = path.read_text(encoding="utf-8").splitlines()
    meta, fm_end, meta_error = split_frontmatter(lines)
    prose, fences = scan_structure(lines, fm_end)
    headings, links, file_spans, symbol_spans = [], [], [], []
    for lineno, raw in prose:
        heading = HEADING_RE.match(raw)
        if heading:
            headings.append((lineno, len(heading.group(1)), heading.group(2).strip()))
        blanked = CODE_SPAN_RE.sub(lambda m: " " * len(m.group(0)), raw)
        links += [(lineno, t) for _, t in LINK_RE.findall(blanked)]
        for span in CODE_SPAN_RE.findall(raw):
            span = span.strip()
            if FILE_SPAN_RE.match(span):
                file_spans.append((lineno, span))
            symbol = SYMBOL_SPAN_RE.match(span)
            if symbol:
                symbol_spans.append((lineno, symbol.group(1)))
    return Doc(
        path,
        path.relative_to(REPO).as_posix(),
        meta,
        lines,
        prose,
        fences,
        headings,
        links,
        file_spans,
        symbol_spans,
        meta_error,
    )


def load_docs() -> list[Doc]:
    paths = sorted(
        p
        for p in DOCS.rglob("*.md")
        if not any(d in IGNORED_DIRS for d in p.relative_to(REPO).parts)
        and p.relative_to(DOCS).parts[0] not in DOC_EXCLUDE_DIRS
    )
    return [load_doc(p) for p in paths]


def walk_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        p
        for p in root.rglob("*")
        if not any(d in IGNORED_DIRS for d in p.relative_to(root).parts) and p.is_file()
    )


def source_files() -> list[str]:
    return sorted(
        p.relative_to(REPO).as_posix()
        for root in SOURCE_ROOTS
        for p in walk_files(REPO / root)
        if p.suffix in SOURCE_SUFFIXES
    )


_symbols: set[str] | None = None


def symbol_index() -> set[str]:
    global _symbols
    if _symbols is None:
        _symbols = set()
        for rel in source_files():
            text = (REPO / rel).read_text(encoding="utf-8", errors="ignore")
            _symbols.update(IDENTIFIER_RE.findall(text))
    return _symbols


def is_repo_path_claim(ref: str) -> bool:
    if any(marker in ref for marker in EXTERNAL_PATH_MARKERS):
        return False
    return ref.startswith(REPO_PATH_PREFIXES)


def resolve_doc_reference(ref: str) -> bool:
    """A bare `something.md` names a document: resolve it at the root or anywhere in `_docs/`."""
    tail = ref.lstrip("./")
    while tail.startswith("../"):
        tail = tail.removeprefix("../")
    if (REPO / tail).exists():
        return True
    return any(p.as_posix().endswith(f"/{tail}") for p in DOCS.rglob("*.md"))


def git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=False
        )
    except OSError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def as_date(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def file_date(path: Path | str) -> date | None:
    """Last commit date; the mtime where git has nothing to say (git absent or file untracked)."""
    path = REPO / path
    rel = path.relative_to(REPO).as_posix()
    out = git("log", "-1", "--format=%cI", "--", rel)
    if out:
        return datetime.fromisoformat(out).date()
    if path.exists():
        return datetime.fromtimestamp(path.stat().st_mtime).date()
    return None


def file_age_days(path: Path) -> int:
    d = file_date(path)
    return (date.today() - d).days if d else 0


def select_docs(docs: list[Doc], paths: list[str]) -> list[Doc]:
    if not paths:
        return docs
    wanted = {str((Path.cwd() / p).resolve()) for p in paths}
    return [d for d in docs if str(d.path.resolve()) in wanted]


# ---------------------------------------------------------------------- lint


@dataclass
class Finding:
    check: str
    doc: str
    message: str
    line: int | None = None
    severity: str = "fail"
    markup: str | None = None


@dataclass
class LintReport:
    findings: list[Finding] = field(default_factory=list)

    def add(self, *args, **kwargs) -> None:
        self.findings.append(Finding(*args, **kwargs))

    @property
    def failures(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "fail"]


def check_l1(docs: list[Doc], report: LintReport) -> None:
    seen: dict[str, str] = {}
    known = {d.id for d in docs if d.id}
    for doc in docs:
        if doc.meta_error:
            report.add("L1", doc.rel, doc.meta_error)
            continue
        if not doc.id:
            report.add("L1", doc.rel, "frontmatter has no `id`")
            continue
        if doc.id in seen:
            report.add("L1", doc.rel, f"`id: {doc.id}` is already used by {seen[doc.id]}")
        else:
            seen[doc.id] = doc.rel
        check_frontmatter_fields(doc, report)
        for dep in doc.depends_on:
            if dep not in known:
                report.add("L1", doc.rel, f"`depends_on: {dep}` resolves to no known document")
    check_cycles(docs, report)


def check_frontmatter_fields(doc: Doc, report: LintReport) -> None:
    for key in REQUIRED_FIELDS:
        if doc.meta.get(key) in (None, ""):
            report.add("L1", doc.rel, f"frontmatter has no `{key}`: the field is required. Add it.")
    status = doc.meta.get("status")
    if status and status not in ALLOWED_STATUS:
        report.add(
            "L1",
            doc.rel,
            f"`status: {status}` is not valid: use one of {', '.join(ALLOWED_STATUS)}.",
        )
    for key in ("updated", "verified"):
        value = doc.meta.get(key)
        if value in (None, ""):
            continue
        # YAML turns an unquoted 2026-11-05 into a date: accept that and a plain ISO string only.
        ok = isinstance(value, date) and not isinstance(value, datetime)
        if isinstance(value, str):
            ok = bool(re.fullmatch(r"\d{4}-\d\d-\d\d", value)) and as_date(value) is not None
        if not ok:
            report.add("L1", doc.rel, f"`{key}: {value}` is not an ISO date: use YYYY-MM-DD.")
    kind = doc.meta.get("kind")
    if kind and kind not in KIND_FOLDER:
        report.add(
            "L1", doc.rel, f"`kind: {kind}` is not valid: use one of {', '.join(KIND_FOLDER)}."
        )
    elif kind:
        expected = KIND_FOLDER[kind]
        is_root_exception = (
            doc.id in ROOT_EXCEPTIONS and not doc.folder and ROOT_EXCEPTIONS[doc.id] == kind
        )
        if doc.folder != expected and not is_root_exception:
            report.add(
                "L1",
                doc.rel,
                f"`kind: {kind}` does not match the folder `{doc.folder or '_docs'}`: "
                f"move the file to `{expected}/` or fix `kind`.",
            )
        prefix = KIND_PREFIX[kind]
        if doc.id and not doc.id.startswith(prefix) and doc.id not in ROOT_EXCEPTIONS:
            report.add(
                "L1",
                doc.rel,
                f"`id: {doc.id}` does not start with `{prefix}`: "
                f"the prefix must match `kind: {kind}`. Rename the id.",
            )


def check_cycles(docs: list[Doc], report: LintReport) -> None:
    by_id = {d.id: d for d in docs if d.id}
    state: dict[str, int] = {}  # 1 on the current path, 2 done
    reported: set[frozenset[str]] = set()

    def visit(node: str, path: list[str]) -> None:
        state[node] = 1
        path.append(node)
        for dep in by_id[node].depends_on:
            if dep not in by_id:
                continue
            if state.get(dep) == 1:
                cycle = path[path.index(dep) :]
                key = frozenset(cycle)
                if key not in reported:
                    reported.add(key)
                    report.add(
                        "L1",
                        by_id[dep].rel,
                        f"`depends_on` cycle: {' -> '.join(cycle + [dep])}. Remove one edge.",
                    )
            elif dep not in state:
                visit(dep, path)
        path.pop()
        state[node] = 2

    for node in sorted(by_id):
        if node not in state:
            visit(node, [])


_slug_cache: dict[Path, set[str]] = {}


def heading_slugs(path: Path) -> set[str]:
    """GitHub-style heading anchors of a markdown file: lowercase, no punctuation, hyphens, -N for repeats."""
    if path not in _slug_cache:
        lines = path.read_text(encoding="utf-8").splitlines()
        _, fm_end, _ = split_frontmatter(lines)
        prose, _ = scan_structure(lines, fm_end)
        slugs: set[str] = set()
        counts: dict[str, int] = {}
        for _, raw in prose:
            match = HEADING_RE.match(raw)
            if not match:
                continue
            text = re.sub(
                r"[`*_]", "", re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", match.group(2).strip())
            )
            slug = re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")
            n = counts.get(slug, 0)
            counts[slug] = n + 1
            slugs.add(slug if n == 0 else f"{slug}-{n}")
        _slug_cache[path] = slugs
    return _slug_cache[path]


def check_l2(docs: list[Doc], report: LintReport) -> None:
    for doc in docs:
        here = doc.path.parent
        for anchor in doc.anchors:
            if not (REPO / anchor).exists():
                report.add("L2", doc.rel, f"`source_anchors` names a missing file: {anchor}")
        seen: set[str] = set()
        for lineno, ref in doc.file_spans:
            if ref in seen:
                continue
            seen.add(ref)
            if is_repo_path_claim(ref):
                if not (REPO / ref).exists():
                    report.add("L2", doc.rel, f"referenced file does not exist: `{ref}`", lineno)
            elif (
                ref.endswith(".md")
                and doc.folder not in DOC_HISTORY_DIRS
                and not any(m in ref for m in EXTERNAL_PATH_MARKERS)
                and not resolve_doc_reference(ref)
            ):
                report.add("L2", doc.rel, f"referenced document does not exist: `{ref}`", lineno)
        if SOURCE_ROOTS:
            seen = set()
            for lineno, name in doc.symbol_spans:
                if name not in seen and name not in symbol_index():
                    report.add("L2", doc.rel, f"symbol not found in the tree: `{name}()`", lineno)
                seen.add(name)
        seen = set()
        for lineno, target in doc.links:
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            clean, _, fragment = target.partition("#")
            if target in seen:
                continue
            seen.add(target)
            dest = (here / clean).resolve() if clean else doc.path
            if not dest.exists():
                report.add("L2", doc.rel, f"link target does not resolve: `{target}`", lineno)
            elif fragment and dest.suffix == ".md" and fragment.lower() not in heading_slugs(dest):
                report.add(
                    "L2",
                    doc.rel,
                    f"link anchor not found in {dest.name}: `{target}`. Fix the anchor.",
                    lineno,
                    severity="warn",
                )


def check_l4(docs: list[Doc], report: LintReport) -> None:
    for doc in docs:
        total = doc.total_lines
        if doc.id in L4_EXEMPT_IDS:
            continue
        if total > LENGTH_CEILING:
            report.add("L4", doc.rel, f"{total} lines, over the {LENGTH_CEILING}-line ceiling")
        elif total > LENGTH_TARGET[1]:
            report.add(
                "L4",
                doc.rel,
                f"{total} lines, over the {LENGTH_TARGET[1]}-line target",
                severity="warn",
            )
        if total < LENGTH_FLOOR_WARN:
            report.add(
                "L4",
                doc.rel,
                f"{total} lines, under {LENGTH_FLOOR_WARN}: fold it into its parent?",
                severity="warn",
            )
        if total and doc.fence_lines / total > FENCE_DENSITY_MAX:
            report.add(
                "L4",
                doc.rel,
                f"fenced code is {100 * doc.fence_lines / total:.0f}% of the document "
                f"({doc.fence_lines}/{total} lines), over {FENCE_DENSITY_MAX:.0%}",
            )
        for fence in doc.fences:
            if fence.lines > FENCE_LINES_MAX:
                label = f" ({fence.info})" if fence.info else ""
                report.add(
                    "L4",
                    doc.rel,
                    f"fence{label} is {fence.lines} lines, over {FENCE_LINES_MAX}",
                    fence.start,
                )


_BANNED = [
    (p, re.compile(r"\b" + r"\s+".join(re.escape(w) for w in p.split()) + r"\b", re.I))
    for p in BANNED_PHRASES
]


def check_l5(docs: list[Doc], report: LintReport) -> None:
    for doc in docs:
        if doc.meta.get("status") != "current" or doc.folder in TIMELESSNESS_EXEMPT_DIRS:
            continue
        for lineno, raw in doc.prose:
            text = CODE_SPAN_RE.sub(lambda m: " " * len(m.group(0)), raw)
            for phrase, pattern in _BANNED:
                match = pattern.search(text)
                if not match:
                    continue
                s, e = match.span()
                marked = (
                    escape(raw[:s].strip())
                    + f" [bold red]{escape(raw[s:e])}[/bold red] "
                    + escape(raw[e:].strip())
                )
                report.add(
                    "L5", doc.rel, f'banned phrasing "{phrase}"', lineno, markup=marked.strip()
                )


def check_todo(docs: list[Doc], report: LintReport) -> None:
    """Warn on a `TODO` in prose or in frontmatter of a document that is not a draft."""
    for doc in docs:
        if doc.meta_error or doc.meta.get("status") == "draft":
            continue
        for lineno, raw in doc.prose:
            text = CODE_SPAN_RE.sub(lambda m: " " * len(m.group(0)), raw)
            if re.search(r"\bTODO\b", text):
                report.add(
                    "L5",
                    doc.rel,
                    "`TODO` in a document that is not a draft: finish it or set `status: draft`.",
                    lineno,
                    severity="warn",
                )
        for key, value in doc.meta.items():
            if re.search(r"\bTODO\b", str(value)):
                report.add(
                    "L5",
                    doc.rel,
                    f"`TODO` in frontmatter field `{key}` of a document that is "
                    "not a draft: finish it or set `status: draft`.",
                    severity="warn",
                )


def check_l7(docs: list[Doc], report: LintReport, all_docs: list[Doc]) -> None:
    linked: set[str] = set()
    home = next((d for d in all_docs if d.path == HOME), None)
    if home:
        for _, target in home.links:
            clean = target.split("#", 1)[0]
            if clean.endswith(".md"):
                linked.add(str((HOME.parent / clean).resolve()))
    for doc in docs:
        if doc.path == HOME:
            continue
        if doc.folder != "wip" and str(doc.path.resolve()) not in linked:
            report.add("L7", doc.rel, "orphan: not linked from `Home.md`")
        if doc.folder == "wip":
            updated = as_date(doc.meta.get("updated"))
            if updated is None:
                report.add("L7", doc.rel, "`wip/` document has no usable `updated` date")
            elif (age := (date.today() - updated).days) > WIP_STALE_DAYS:
                report.add("L7", doc.rel, f"`wip/` document last updated {age} days ago")
    for path in walk_files(DOCS / "inbox"):
        if path.name != ".gitkeep" and (age := file_age_days(path)) > INBOX_STALE_DAYS:
            report.add(
                "L7", path.relative_to(REPO).as_posix(), f"`inbox/` file is {age} days old: file it"
            )


def check_l9(docs: list[Doc], report: LintReport) -> None:
    for doc in docs:
        if doc.id in LINK_REPEAT_EXEMPT_IDS:
            continue
        counts: dict[str, int] = {}
        for _, target in doc.links:
            key = target.split("#", 1)[0] or target
            counts[key] = counts.get(key, 0) + 1
        for target, count in sorted(counts.items()):
            if count > MAX_LINK_REPEATS:
                report.add(
                    "L9", doc.rel, f"link `{target}` appears {count} times (max {MAX_LINK_REPEATS})"
                )


def check_l10(report: LintReport) -> None:
    for path, rel in ((REPO / "AGENTS.md", "AGENTS.md"), (HOME, "_docs/Home.md")):
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if "_meta/authoring.md" not in text:
            report.add("L10", rel, "does not mention `_meta/authoring.md`")


def stale_docs(docs: list[Doc], tolerance: int) -> list[tuple[Doc, date, date]]:
    """Documents whose file date outruns `updated` by more than `tolerance` days."""
    out = []
    for doc in docs:
        updated, filed = as_date(doc.meta.get("updated")), file_date(doc.path)
        if updated and filed and (filed - updated).days > tolerance:
            out.append((doc, updated, filed))
    return out


def check_l11(docs: list[Doc], report: LintReport) -> None:
    for doc, updated, filed in stale_docs(docs, FRESHNESS_TOLERANCE_DAYS):
        report.add(
            "L11",
            doc.rel,
            f"file dated {filed}, `updated` is {updated}: stamp or re-read",
            severity="warn",
        )


def run_lint(paths: list[str], as_json: bool) -> int:
    missing = [p for p in paths if not (Path.cwd() / p).exists()]
    if missing:
        console.print(
            f"[red]path does not exist: {escape(', '.join(missing))}[/red]. "
            "Give the path of a document in `_docs/`."
        )
        return 2
    docs = load_docs()
    if not docs:
        console.print(
            f"[red]lint scanned 0 documents[/red]: no `.md` file found under {escape(str(DOCS))}. "
            "Check the repository path."
        )
        return 1
    report = LintReport()
    check_l10(report)
    check_l1(docs, report)
    selected = select_docs(docs, paths)
    if paths and not selected:
        console.print(
            "[red]no document matched the given paths[/red]: the paths are not documents "
            "of the library. Give a `.md` file in `_docs/`."
        )
        return 2
    for check in (check_l2, check_l4, check_l5, check_todo, check_l9, check_l11):
        check(selected, report)
    check_l7(selected, report, docs)

    if as_json:
        print(
            json.dumps(
                {
                    "failures": len(report.failures),
                    "findings": [vars(f) | {"markup": None} for f in report.findings],
                },
                indent=2,
            )
        )
        return 1 if report.failures else 0

    l10 = [f for f in report.findings if f.check == "L10"]
    if l10:
        console.rule("[bold red]L10: the update duty is not discoverable")
        for f in l10:
            console.print(f"  [red]{escape(f.doc)}[/red]: {escape(f.message)}")
        console.print()
    else:
        console.print("[green]L10 ok[/green]: the update duty is discoverable\n")

    by_doc: dict[str, list[Finding]] = {}
    for f in report.findings:
        if f.check != "L10":
            by_doc.setdefault(f.doc, []).append(f)
    for doc in sorted(by_doc):
        console.rule(f"[bold]{escape(doc)}", align="left")
        for f in sorted(by_doc[doc], key=lambda f: (int(f.check[1:]), f.line or 0)):
            colour = "red" if f.severity == "fail" else "yellow"
            where = f":{f.line}" if f.line else ""
            console.print(
                f"  [{colour}]{f.check}[/{colour}] {escape(doc)}{where}: {escape(f.message)}"
            )
            if f.markup:
                console.print(f"        {f.markup}", highlight=False)
        console.print()

    counts: dict[str, list[int]] = {}
    for f in report.findings:
        counts.setdefault(f.check, [0, 0])[0 if f.severity == "fail" else 1] += 1
    table = Table(title="Summary", title_justify="left")
    for col in ("Check", "Failures", "Warnings"):
        table.add_column(col, justify="left" if col == "Check" else "right")
    for check in sorted(counts, key=lambda c: int(c[1:])):
        table.add_row(check, str(counts[check][0]), str(counts[check][1]))
    table.add_section()
    table.add_row(
        "total", str(sum(c[0] for c in counts.values())), str(sum(c[1] for c in counts.values()))
    )
    console.print(table)
    console.print(f"{len(docs)} documents scanned")
    return 1 if report.failures else 0


# --------------------------------------------------------------------- index

GROUPS = (
    ("product", "Product"),
    ("features", "Features"),
    ("tech", "Tech"),
    ("infra", "Infra"),
)
GROUP_BY_KIND = {"product": "product", "feature": "features", "tech": "tech", "infra": "infra"}


def read_marker(text: str, name: str) -> tuple[int, int] | None:
    begin = MARKER_RE.format(kind="begin", name=name)
    end = MARKER_RE.format(kind="end", name=name)
    i, j = text.find(begin), text.find(end)
    if i < 0 or j < 0 or j < i:
        return None
    return i + len(begin), j


def replace_marker(text: str, name: str, body: str) -> str | None:
    span = read_marker(text, name)
    if span is None:
        return None
    return text[: span[0]] + "\n\n" + body.strip() + "\n\n" + text[span[1] :]


def doc_group(doc: Doc) -> str:
    """Folder of the document; root documents (`backlog`) file under Product."""
    return doc.folder or GROUP_BY_KIND.get(str(doc.meta.get("kind") or ""), "product")


def link_from(base: Path, target: Path) -> str:
    out = os.path.relpath(target, base.parent)
    return out if out.startswith(".") else f"./{out}"


def render_catalogue(docs: list[Doc]) -> str:
    """Product, Features, Tech, Infra. `_meta/`, `wip/` and `Home.md` stay out: Home links them by hand."""
    out: list[str] = []
    for folder, heading in GROUPS:
        group = [d for d in docs if d.path != HOME and doc_group(d) == folder]
        if not group:
            continue
        out += [f"### {heading}\n", "| Document | What it is | Verified |", "|---|---|---|"]
        for doc in sorted(group, key=lambda d: d.rel):
            summary = str(doc.meta.get("summary") or "").strip().replace("\n", " ") or "-"
            verified = as_date(doc.meta.get("verified"))
            out.append(
                f"| [{doc.title}]({link_from(HOME, doc.path)}) | {summary} | "
                f"{verified.isoformat() if verified else '-'} |"
            )
        out.append("")
    return "\n".join(out)


TREE_LINE_RE = re.compile(r"^((?:(?:│   |    ))*)(├── |└── )(.+)$")


def parse_tree(block: str) -> tuple[dict[str, str], dict[str, int]]:
    """Read the existing tree for its hand-written notes and entry order, so no diff appears."""
    notes: dict[str, str] = {}
    order: dict[str, int] = {}
    stack: list[str] = []
    for raw in block.splitlines():
        line = raw.rstrip()
        if not line or line.startswith("```"):
            continue
        match = TREE_LINE_RE.match(line)
        if match:
            depth, rest = len(match.group(1)) // 4, match.group(3)
        elif re.match(r"^[\w./-]+/?\s*$", line):
            depth, rest = -1, line
        else:
            continue
        parts = re.split(r"\s{2,}", rest.strip(), maxsplit=1)
        stack = stack[: depth + 1]
        while len(stack) < depth + 1:
            stack.append("")
        stack.append(parts[0].rstrip("/"))
        key = "/".join(p for p in stack if p)
        order.setdefault(key, len(order))
        if len(parts) > 1:
            notes[key] = parts[1].strip()
    return notes, order


def render_tree(existing: str) -> str:
    notes, order = parse_tree(existing)
    children: dict[str, list[tuple[str, bool]]] = {}
    for root in SOURCE_ROOTS:
        base = REPO / root
        for path in sorted(base.rglob("*")) if base.exists() else []:
            if any(d in IGNORED_DIRS for d in path.relative_to(base).parts):
                continue
            rel = path.relative_to(REPO).as_posix()
            children.setdefault(str(Path(rel).parent), []).append((rel, path.is_dir()))
    rows: list[tuple[str, str]] = []

    def walk(parent: str, prefix: str) -> None:
        entries = sorted(
            children.get(parent, []), key=lambda e: (order.get(e[0], len(order)), not e[1], e[0])
        )
        for i, (rel, is_dir) in enumerate(entries):
            last = i == len(entries) - 1
            rows.append(
                (
                    prefix
                    + ("└── " if last else "├── ")
                    + Path(rel).name
                    + ("/" if is_dir else ""),
                    notes.get(rel, ""),
                )
            )
            if is_dir:
                walk(rel, prefix + ("    " if last else "│   "))

    for root in SOURCE_ROOTS:
        if (REPO / root).exists():
            if rows:
                rows.append(("", ""))
            rows.append((f"{root}/", notes.get(root, "")))
            walk(root, "")
    width = max((len(label) for label, note in rows if note), default=0) + 2
    body = ["```"] + [
        f"{label.ljust(width)}{note}".rstrip() if note else label for label, note in rows
    ]
    return "\n".join(body + ["```"])


def run_index(check_only: bool) -> int:
    docs = load_docs()
    plan: list[tuple[Path, str, str]] = []
    if HOME.exists():
        plan.append((HOME, "catalogue", render_catalogue(docs)))
    code_map = DOCS / "tech" / "code-map.md"
    if SOURCE_ROOTS and code_map.exists():
        current = code_map.read_text(encoding="utf-8")
        span = read_marker(current, "tree")
        plan.append((code_map, "tree", render_tree(current[span[0] : span[1]] if span else "")))
    if not plan:
        console.print("[yellow]nothing to generate[/yellow]: no Home.md, no code map")
        return 0

    changed = False
    for path in dict.fromkeys(p for p, _, _ in plan):
        text = updated = path.read_text(encoding="utf-8")
        rel = path.relative_to(REPO).as_posix()
        for target, name, body in plan:
            if target != path:
                continue
            result = replace_marker(updated, name, body)
            if result is None:
                console.print(f"[yellow]skipped[/yellow] {rel}: no `{name}` markers")
            else:
                updated = result
        if updated == text:
            console.print(f"[green]unchanged[/green] {rel}")
            continue
        changed = True
        console.print(
            f"[cyan]{'would rewrite' if check_only else 'rewrote'}[/cyan] {rel} "
            f"({len(text.splitlines())} -> {len(updated.splitlines())} lines)"
        )
        if not check_only:
            path.write_text(updated, encoding="utf-8")
    if check_only and changed:
        console.print("[red]generated blocks are out of date[/red]")
        return 1
    return 0


# ------------------------------------------------------------------ new

SKELETONS = {
    "product": ("product", "prod", ["Purpose", "Scope", "Non-goals", "Related docs"]),
    "feature": ("features", "feat", ["Purpose", "Behaviour", "Assumptions", "Related docs"]),
    "tech": ("tech", "tech", ["What it is", "Rules", "Rationale", "Related docs"]),
    "infra": ("infra", "infra", ["What it is", "Rules", "Rationale", "Related docs"]),
    "meta": ("_meta", "meta", ["Purpose", "Procedure", "Related docs"]),
    "wip": ("wip", "wip", ["Goal", "Notes", "Related docs"]),
}


def run_new(kind: str, slug: str) -> int:
    if kind not in SKELETONS:
        console.print(f"[red]unknown kind `{kind}`[/red]; use one of {', '.join(SKELETONS)}")
        return 2
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        console.print("[red]slug must be lowercase words joined by hyphens[/red]")
        return 2
    folder, prefix, sections = SKELETONS[kind]
    path = DOCS / folder / f"{slug}.md"
    if path.exists():
        console.print(f"[red]refusing to overwrite[/red] {path.relative_to(REPO)}")
        return 1
    today = date.today().isoformat()
    title = slug.replace("-", " ").capitalize()
    front = [
        "---",
        f"id: {prefix}-{slug}",
        f"title: {title}",
        f"kind: {kind}",
        "status: draft",
        "summary: TODO one line, the catalogue entry in Home.md",
        "read_when: TODO the task, not the subject",
        f"updated: {today}",
        f"verified: {today}",
    ]
    if kind in ("tech", "infra", "feature"):
        front.append("source_anchors: []")
    front += [
        "depends_on: [prod-overview]" if kind != "product" else "depends_on: []",
        "review_cycle: quarterly",
        "---",
        "",
        f"# {title}",
        "",
    ]
    for section in sections:
        front += [f"## {section}", "", "TODO", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(front), encoding="utf-8")
    console.print(f"[green]created[/green] {path.relative_to(REPO)}")
    console.print(
        "Still to do by hand: set `status: current`, add the document to the reading paths "
        "in `_docs/Home.md`, then run `mise run docs-index`."
    )
    return 0


# ----------------------------------------------------- date maintenance


def set_frontmatter_line(path: Path, key: str, value: str) -> bool:
    """Rewrite one `key:` line inside the frontmatter block, and nothing else."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    if not lines or lines[0].rstrip() != "---":
        return False
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return False
        if re.match(rf"{key}:", lines[i]):
            new = re.sub(rf"^({key}:\s*)\S+", rf"\g<1>{value}", lines[i])
            if new == lines[i]:
                return False
            lines[i] = new
            path.write_text("".join(lines), encoding="utf-8")
            return True
    return False


def run_changed(days: int) -> int:
    rows = stale_docs(load_docs(), days)
    table = Table(
        title=f"L11: file date outruns `updated` by more than {days} days", title_justify="left"
    )
    for col in ("Document", "updated", "File dated"):
        table.add_column(col)
    for doc, updated, filed in sorted(rows, key=lambda r: r[2]):
        table.add_row(doc.rel, updated.isoformat(), filed.isoformat())
    console.print(table if rows else "[green]every `updated` date is current[/green]")
    return 0


def run_stamp(dry: bool, snapshot: list[tuple[Doc, date, date]] | None = None) -> int:
    rows = snapshot if snapshot is not None else stale_docs(load_docs(), FRESHNESS_TOLERANCE_DAYS)
    for doc, updated, filed in rows:
        verb = "would stamp" if dry else "stamped"
        if not dry and not set_frontmatter_line(doc.path, "updated", filed.isoformat()):
            verb = "[red]could not stamp[/red]"
        console.print(f"{verb} {doc.rel}: updated {updated} -> {filed}")
        if filed > (as_date(doc.meta.get("verified")) or date.min):
            console.print(
                "  [yellow]updated is ahead of verified: read it, then `docs-verify`[/yellow]"
            )
    if not rows:
        console.print("[green]nothing to stamp[/green]")
    return 0


def run_verify(paths: list[str]) -> int:
    if not paths:
        console.print("[red]verify needs explicit paths[/red]: `mise run docs-verify <paths>`")
        return 2
    selected = select_docs(load_docs(), paths)
    if not selected:
        console.print("[red]no document matched the given paths[/red]")
        return 1
    today = date.today().isoformat()
    for doc in selected:
        ok = set_frontmatter_line(doc.path, "verified", today)
        console.print(f"{'verified' if ok else 'unchanged'} {doc.rel}")
    return 0


def run_review() -> int:
    rows = []
    for doc in load_docs():
        if doc.folder in ("wip",):
            continue
        verified = as_date(doc.meta.get("verified"))
        cycle = str(doc.meta.get("review_cycle") or "quarterly")
        limit = CYCLE_DAYS.get(cycle, CYCLE_DAYS["quarterly"])
        age = (date.today() - verified).days if verified else None
        if age is None or age > limit:
            rows.append((doc, cycle, verified, age))
    table = Table(title="Review queue: review_cycle elapsed since `verified`", title_justify="left")
    for col in ("Document", "Cycle", "Verified", "Age (days)"):
        table.add_column(col)
    for doc, cycle, verified, age in sorted(rows, key=lambda r: r[2] or date.min):
        table.add_row(doc.rel, cycle, verified.isoformat() if verified else "-", str(age or "-"))
    console.print(table if rows else "[green]no document is due for review[/green]")
    return 0


def run_sync() -> int:
    snapshot = stale_docs(load_docs(), FRESHNESS_TOLERANCE_DAYS)  # before the index write
    run_index(False)
    return run_stamp(False, snapshot)


# --------------------------------------------------------------------- drift


def run_drift() -> int:
    docs = [d for d in load_docs() if d.anchors]
    rows = []
    for doc in docs:
        verified = as_date(doc.meta.get("verified"))
        moved = [(a, f) for a in doc.anchors if (f := file_date(a)) and verified and f > verified]
        if moved:
            rows.append((doc, verified, sorted(moved, key=lambda m: m[1], reverse=True)))
    rows.sort(key=lambda r: r[1] or date.min)
    table = Table(title="L3 drift queue: most stale first", title_justify="left")
    for col in ("Document", "Verified", "Anchored files that moved after it"):
        table.add_column(col)
    for doc, verified, moved in rows:
        table.add_row(
            doc.rel,
            verified.isoformat() if verified else "-",
            "\n".join(f"{a} ({d.isoformat()})" for a, d in moved),
        )
    console.print(
        table
        if rows
        else "[green]no anchored file has moved since its document was verified[/green]"
    )
    console.print("[yellow]This detects the possibility of drift only.[/yellow]")
    console.print(f"{len(rows)} of {len(docs)} anchored documents queued")
    return 0


def run_touched(paths: list[str]) -> int:
    if not paths:
        paths = [p for p in git("diff", "--name-only", "HEAD").splitlines() if p]
        if not paths:  # no git: files modified within the tolerance window
            cutoff = date.today().toordinal() - FRESHNESS_TOLERANCE_DAYS
            paths = [
                p.relative_to(REPO).as_posix()
                for p in walk_files(REPO)
                if datetime.fromtimestamp(p.stat().st_mtime).date().toordinal() >= cutoff
            ]
        paths = [p for p in paths if not p.startswith("_docs/")]
    if not paths:
        console.print("[yellow]no changed files[/yellow]")
        return 0
    docs = load_docs()
    normalized = []
    for p in paths:
        candidate = Path(p) if Path(p).is_absolute() else Path.cwd() / p
        try:
            normalized.append(candidate.resolve().relative_to(REPO).as_posix())
        except ValueError:
            normalized.append(p)
    table = Table(title="Documents to verify", title_justify="left")
    table.add_column("Changed file")
    table.add_column("Anchored by")
    unanchored = []
    for rel in sorted(set(normalized)):
        if any(part.startswith(".") and part not in (".", "..") for part in Path(rel).parts):
            continue
        owners = sorted(d.rel for d in docs if rel in d.anchors)
        if owners:
            table.add_row(rel, "\n".join(owners))
        else:
            unanchored.append(rel)
    if table.row_count:
        console.print(table)
        console.print(
            "Verify each of these in the same change, then `mise run docs-verify <paths>`."
        )
    if unanchored:
        console.print("\n[yellow]Anchored by no document[/yellow]:")
        for rel in unanchored:
            console.print(f"  {rel}")
    return 0


# ------------------------------------------------------- stats, inbox, log


def run_stats() -> int:
    docs = load_docs()
    table = Table(title="Library", title_justify="left")
    table.add_column("Folder")
    table.add_column("Documents", justify="right")
    table.add_column("Lines", justify="right")
    by_folder: dict[str, list[Doc]] = {}
    for d in docs:
        by_folder.setdefault(d.folder or "(root)", []).append(d)
    for folder in sorted(by_folder):
        table.add_row(
            folder, str(len(by_folder[folder])), str(sum(d.total_lines for d in by_folder[folder]))
        )
    console.print(table)

    status: dict[str, int] = {}
    for d in docs:
        status[str(d.meta.get("status"))] = status.get(str(d.meta.get("status")), 0) + 1
    console.print("status: " + ", ".join(f"{k} {v}" for k, v in sorted(status.items())))
    lo, hi = LENGTH_TARGET
    console.print(
        f"length: fold {sum(d.total_lines < LENGTH_FLOOR_WARN for d in docs)} (<{LENGTH_FLOOR_WARN}), "
        f"in band {sum(lo <= d.total_lines <= hi for d in docs)} ({lo}-{hi}), "
        f"over target {sum(hi < d.total_lines <= LENGTH_CEILING for d in docs)}, "
        f"over ceiling {sum(d.total_lines > LENGTH_CEILING for d in docs)}"
    )
    bearing = [d for d in docs if d.folder in ("tech", "infra", "features")]
    console.print(
        f"no source_anchors: {sum(not d.anchors for d in bearing)} of {len(bearing)} "
        "tech, infra and feature documents"
    )
    verified = [
        (as_date(d.meta.get("verified")), d) for d in docs if as_date(d.meta.get("verified"))
    ]
    if verified:
        oldest, doc = min(verified, key=lambda v: v[0])
        console.print(f"oldest verification: {oldest} ({doc.rel})")
    inbox = [p for p in walk_files(DOCS / "inbox") if p.name != ".gitkeep"]
    console.print(f"inbox: {len(inbox)} files")
    last = last_log_row()
    console.print(f"last logged pass: {last[0]} ({last[1]})" if last else "last logged pass: none")
    return 0


def run_inbox() -> int:
    files = [p for p in walk_files(DOCS / "inbox") if p.name != ".gitkeep"]
    if not files:
        console.print("[green]inbox is empty[/green]")
        return 0
    corpus = "\n".join(d.path.read_text(encoding="utf-8") for d in load_docs())
    table = Table(title="Inbox: the filing queue", title_justify="left")
    for col in ("File", "Age (days)", "Size (bytes)", "Anchored", "Action"):
        table.add_column(col, justify="right" if col in ("Age (days)", "Size (bytes)") else "left")
    for p in files:
        rel = p.relative_to(REPO).as_posix()
        age = file_age_days(p)
        flag = "[red]file it[/red]" if age > INBOX_STALE_DAYS else ""
        anchored = "yes" if (rel in corpus or p.name in corpus) else "no"
        table.add_row(rel, str(age), str(p.stat().st_size), anchored, flag)
    console.print(table)
    return 0


def last_log_row() -> tuple[str, str] | None:
    if not REVIEW_LOG.exists():
        return None
    rows = [
        [c.strip() for c in line.strip().strip("|").split("|")]
        for line in REVIEW_LOG.read_text(encoding="utf-8").splitlines()
        if re.match(r"^\|\s*\d{4}-\d\d-\d\d", line)
    ]
    return (rows[-1][0], rows[-1][1]) if rows and len(rows[-1]) > 1 else None


def run_log(scope: str, checks: str, counts: str, notes: str) -> int:
    if not REVIEW_LOG.exists():
        console.print("[red]_docs/_meta/review-log.md does not exist[/red]")
        return 1
    if not scope:
        console.print("[red]log needs --scope[/red] (and usually --checks, --counts, --notes)")
        return 2
    cells = [date.today().isoformat(), scope, checks or "-", counts or "-", notes or "-"]
    row = "| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |"
    lines = REVIEW_LOG.read_text(encoding="utf-8").split("\n")
    table_rows = [i for i, line in enumerate(lines) if line.startswith("|")]
    if not table_rows:
        console.print(
            "[red]review-log.md has no table[/red]: the log row has no place. Restore the table."
        )
        return 1
    lines.insert(table_rows[-1] + 1, row)
    REVIEW_LOG.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]appended[/green] {row}")
    return 0


# --------------------------------------------------------------------- graph


def run_graph() -> int:
    docs = [d for d in load_docs() if d.id]
    by_id = {d.id: d for d in docs}
    outbound = {d.id: [dep for dep in d.depends_on if dep in by_id] for d in docs}
    inbound: dict[str, list[str]] = {d.id: [] for d in docs}
    for src, deps in outbound.items():
        for dep in deps:
            inbound[dep].append(src)

    console.print("[bold]depends_on graph[/bold]\n")

    def render(node: str, depth: int, seen: tuple[str, ...]) -> None:
        console.print(
            "  " * depth + ("└─ " if depth else "") + f"{node} [dim]{escape(by_id[node].rel)}[/dim]"
        )
        if node in seen:
            console.print("  " * (depth + 1) + "[red]... cycle[/red]")
            return
        for dep in sorted(outbound[node]):
            render(dep, depth + 1, seen + (node,))

    for root in sorted(d.id for d in docs if not inbound[d.id] and outbound[d.id]):
        render(root, 0, ())
        console.print()
    isolated = sorted(d.id for d in docs if not inbound[d.id] and not outbound[d.id])
    hubs = [(i, len(v)) for i, v in inbound.items() if len(v) > MAX_INBOUND_EDGES]
    if isolated:
        console.print("[yellow]Isolated[/yellow]: no inbound or outbound edge:")
        for node in isolated:
            console.print(f"  {node} [dim]{escape(by_id[node].rel)}[/dim]")
    if hubs:
        console.print(
            f"\n[yellow]Over-connected[/yellow]: more than {MAX_INBOUND_EDGES} inbound edges:"
        )
        for node, count in sorted(hubs, key=lambda h: -h[1]):
            console.print(f"  {node}: {count} inbound")
    if not isolated and not hubs:
        console.print("[green]no isolated or over-connected documents[/green]")
    return 0


# ----------------------------------------------------------------------- cli

ACTIONS = [
    "lint",
    "index",
    "index-check",
    "new",
    "touched",
    "stats",
    "changed",
    "drift",
    "review",
    "stamp",
    "stamp-check",
    "verify",
    "log",
    "inbox",
    "graph",
    "sync",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=ACTIONS)
    parser.add_argument(
        "args", nargs="*", help="paths, `<kind> <slug>` for new, or days for changed"
    )
    parser.add_argument("--json", action="store_true", help="lint: machine-readable output")
    parser.add_argument("--scope", default="", help="log: what the pass covered")
    parser.add_argument("--checks", default="", help="log: checks run")
    parser.add_argument("--counts", default="", help="log: counts")
    parser.add_argument("--notes", default="", help="log: notes")
    a = parser.parse_args()

    if not DOCS.exists():
        console.print(f"[red]no _docs/ directory at {DOCS}[/red]")
        return 2
    match a.action:
        case "lint":
            return run_lint(a.args, a.json)
        case "index":
            return run_index(False)
        case "index-check":
            return run_index(True)
        case "new":
            if len(a.args) != 2:
                console.print("[red]usage: new <kind> <slug>[/red]")
                return 2
            return run_new(a.args[0], a.args[1])
        case "touched":
            return run_touched(a.args)
        case "stats":
            return run_stats()
        case "changed":
            return run_changed(int(a.args[0]) if a.args else FRESHNESS_TOLERANCE_DAYS)
        case "drift":
            return run_drift()
        case "review":
            return run_review()
        case "stamp":
            return run_stamp(False)
        case "stamp-check":
            return run_stamp(True)
        case "verify":
            return run_verify(a.args)
        case "log":
            return run_log(a.scope, a.checks, a.counts, a.notes)
        case "inbox":
            return run_inbox()
        case "graph":
            return run_graph()
        case "sync":
            return run_sync()
    return 2


if __name__ == "__main__":
    sys.exit(main())
