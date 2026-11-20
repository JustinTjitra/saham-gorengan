"""Consistency checks between tasks/BOARD.md and the chunk specs in tasks/."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

TASKS = Path(__file__).resolve().parent.parent / "tasks"
BOARD = TASKS / "BOARD.md"
HEADER = ["id", "title", "phase", "model", "deps", "status", "commit"]
STATUSES = {"todo", "doing", "done", "blocked"}
MODELS = {"haiku", "sonnet"}


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_board(path: Path) -> list[dict[str, str]]:
    """Rows of the first markdown table whose header is the board header."""
    rows: list[dict[str, str]] = []
    in_table = False
    for line in path.read_text().splitlines():
        s = line.strip()
        if not in_table:
            if s.startswith("|") and _cells(s) == HEADER:
                in_table = True
            continue
        if not s.startswith("|"):
            break
        cells = _cells(s)
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        cells += [""] * (len(HEADER) - len(cells))
        rows.append(dict(zip(HEADER, cells)))
    return rows


def parse_spec_header(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text().splitlines()[:10]:
        m = re.match(r"^- \*\*(\w+):\*\*\s*(.*?)\s*$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def parse_deps(value: str) -> set[str]:
    value = value.strip()
    if value in ("", "none"):
        return set()
    return {d.strip() for d in value.split(",") if d.strip()}


def find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    """DFS; returns a cycle as a list of ids, or None."""
    WHITE, GREY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}
    stack: list[str] = []

    def visit(n: str) -> list[str] | None:
        color[n] = GREY
        stack.append(n)
        for d in sorted(graph.get(n, ())):
            if d not in graph:
                continue
            if color[d] == GREY:
                return stack[stack.index(d):] + [d]
            if color[d] == WHITE:
                found = visit(d)
                if found:
                    return found
        stack.pop()
        color[n] = BLACK
        return None

    for n in sorted(graph):
        if color[n] == WHITE:
            found = visit(n)
            if found:
                return found
    return None


@pytest.fixture(scope="module")
def rows() -> list[dict[str, str]]:
    r = parse_board(BOARD)
    assert r, "no rows parsed from tasks/BOARD.md"
    return r


def test_ids_unique(rows):
    seen: set[str] = set()
    dups = sorted({r["id"] for r in rows if r["id"] in seen or seen.add(r["id"])})
    assert not dups, f"duplicate ids on board: {dups}"


def test_every_row_has_spec(rows):
    missing = [r["id"] for r in rows if not (TASKS / f"{r['id']}.md").is_file()]
    assert not missing, f"board rows without tasks/<id>.md: {missing}"


def test_every_spec_has_row(rows):
    ids = {r["id"] for r in rows}
    specs = {p.stem for p in TASKS.glob("*.md")} - {"BOARD", "TEMPLATE"}
    missing = sorted(specs - ids)
    assert not missing, f"specs not on the board: {missing}"


def test_status_and_model_values(rows):
    for r in rows:
        assert r["status"] in STATUSES, f"{r['id']}: bad status {r['status']!r}"
        assert r["model"] in MODELS, f"{r['id']}: bad model {r['model']!r}"


def test_deps_exist_and_acyclic(rows):
    ids = {r["id"] for r in rows}
    graph = {r["id"]: parse_deps(r["deps"]) for r in rows}
    for i, deps in graph.items():
        unknown = sorted(deps - ids)
        assert not unknown, f"{i}: deps not on board: {unknown}"
    cycle = find_cycle(graph)
    assert cycle is None, f"dependency cycle: {' -> '.join(cycle or [])}"


def test_commit_cells_are_hex_or_empty(rows):
    # A chunk's own commit cannot contain its hash, so `done` rows may be empty
    # until the run's log commit fills them in (docs/LOOP.md step 8).
    for r in rows:
        assert r["commit"] == "" or re.fullmatch(r"[0-9a-f]{7,40}", r["commit"]), (
            f"{r['id']}: commit {r['commit']!r} is not a hex sha"
        )
        if r["commit"]:
            assert r["status"] == "done", f"{r['id']}: has a commit but status {r['status']!r}"


def test_spec_header_matches_board(rows):
    for r in rows:
        spec = TASKS / f"{r['id']}.md"
        if not spec.is_file():
            continue  # reported by test_every_row_has_spec
        h = parse_spec_header(spec)
        assert h.get("Model") == r["model"], (
            f"{r['id']}: spec Model {h.get('Model')!r} != board {r['model']!r}"
        )
        assert parse_deps(h.get("Deps", "")) == parse_deps(r["deps"]), (
            f"{r['id']}: spec Deps {h.get('Deps')!r} != board {r['deps']!r}"
        )


def test_parser_detects_cycle_in_broken_table(tmp_path):
    board = tmp_path / "BOARD.md"
    board.write_text(
        "intro text\n\n"
        "| id | title | phase | model | deps | status | commit |\n"
        "|---|---|---|---|---|---|---|\n"
        "| A-1 | a | P0 | sonnet | B-1 | todo | |\n"
        "| B-1 | b | P0 | haiku | C-1, A-1 | todo | |\n"
        "| C-1 | c | P0 | haiku | none | todo | |\n\n"
        "trailing text\n"
    )
    parsed = parse_board(board)
    assert [r["id"] for r in parsed] == ["A-1", "B-1", "C-1"]
    graph = {r["id"]: parse_deps(r["deps"]) for r in parsed}
    cycle = find_cycle(graph)
    assert cycle is not None and set(cycle) == {"A-1", "B-1"}
    assert find_cycle({"X": set(), "Y": {"X"}}) is None
