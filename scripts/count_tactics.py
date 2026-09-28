#!/usr/bin/env python3
"""Count literal occurrences of common tactic names in selected Lean files."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TACTIC_NAMES = sorted(
    {
        "abel",
        "abel_nf",
        "ac_rfl",
        "aesop",
        "aesop?",
        "all_goals",
        "any_goals",
        "apply",
        "apply?",
        "apply_fun",
        "apply_rules",
        "assumption",
        "assumption_mod_cast",
        "backward",
        "by_cases",
        "by_contra",
        "case",
        "cases",
        "casesm",
        "change",
        "choose",
        "clear",
        "clear_dependent",
        "clear_value",
        "congr",
        "congrm",
        "contradiction",
        "constructor",
        "convert",
        "decide",
        "done",
        "dsimp",
        "exact",
        "exact?",
        "exact_mod_cast",
        "exists",
        "ext",
        "ext1",
        "ext_1",
        "fail_if_success",
        "field",
        "field_simp",
        "filter_upwards",
        "first",
        "focus",
        "fun_prop",
        "funext",
        "generalize",
        "gcongr",
        "guard_hyp",
        "guard_target",
        "have",
        "haveI",
        "induction",
        "infer_instance",
        "intro",
        "intros",
        "library_search",
        "linarith",
        "linear_combination",
        "measurability",
        "native_decide",
        "norm_cast",
        "norm_num",
        "norm_num1",
        "nlinarith",
        "nth_rewrite",
        "nth_rewrite_lhs",
        "nth_rewrite_rhs",
        "obtain",
        "omega",
        "on_goal",
        "positivity",
        "polyrith",
        "push_cast",
        "push_neg",
        "qify",
        "rcases",
        "rfl",
        "refine",
        "repeat",
        "revert",
        "rintro",
        "ring",
        "ring_nf",
        "rotate_left",
        "rotate_right",
        "rwa",
        "rw",
        "set",
        "simp",
        "simp?",
        "simp_all",
        "simpa",
        "skip",
        "solve",
        "solve_by_elim",
        "specialize",
        "split",
        "subst",
        "subst_vars",
        "suffices",
        "swap",
        "symm",
        "tauto",
        "trace_state",
        "trans",
        "trivial",
        "try",
        "unfold",
        "use",
        "wlog",
        "zify",
    },
    key=len,
    reverse=True,
)
TACTIC_PATTERN = re.compile(
    r"(?<![\w'.])(?:" + "|".join(re.escape(name) for name in TACTIC_NAMES) + r")(?![\w'.?])"
)


def remove_comments_and_strings(source: str) -> str:
    """Remove comments and string contents using fast delimiter searches."""
    output: list[str] = []
    copied_through = 0
    length = len(source)
    while True:
        candidates = [(source.find(marker, copied_through), marker) for marker in ("--", "/-", '"')]
        candidates = [(position, marker) for position, marker in candidates if position >= 0]
        if not candidates:
            break
        position, marker = min(candidates, key=lambda item: item[0])
        output.append(source[copied_through:position])

        if marker == "--":
            end = source.find("\n", position)
            if end < 0:
                end = length
            output.append(" ")
            if end < length:
                output.append("\n")
                end += 1
            copied_through = end
            continue

        if marker == "/-":
            index = position + 2
            depth = 1
            while index < length and depth:
                opening = source.find("/-", index)
                closing = source.find("-/", index)
                if closing < 0:
                    index = length
                elif 0 <= opening < closing:
                    depth += 1
                    index = opening + 2
                else:
                    depth -= 1
                    index = closing + 2
            output.append(" ")
            output.append("\n" * source.count("\n", position, index))
            copied_through = index
            continue

        index = position + 1
        while index < length:
            quote = source.find('"', index)
            escape = source.find("\\", index)
            if quote < 0:
                index = length
                break
            if 0 <= escape < quote:
                index = escape + 2
            else:
                index = quote + 1
                break
        output.append(" ")
        output.append("\n" * source.count("\n", position, min(index, length)))
        copied_through = index

    output.append(source[copied_through:])
    return "".join(output)


def selected_files(source_root: Path, include: list[str]):
    for entry in include:
        target = source_root / entry
        if target.is_file() and target.suffix == ".lean":
            yield target
        elif target.is_dir():
            yield from target.rglob("*.lean")
        else:
            raise FileNotFoundError(f"Included Lean path does not exist: {target}")


def count_source(source_root: Path, include: list[str]) -> tuple[Counter[str], int]:
    counts: Counter[str] = Counter()
    file_count = 0
    files = sorted(set(selected_files(source_root, include)))
    for path in files:
        code = remove_comments_and_strings(path.read_text(encoding="utf-8"))
        counts.update(TACTIC_PATTERN.findall(code))
        file_count += 1
    return counts, file_count


def parse_source_args(items: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for item in items:
        if "=" not in item:
            raise argparse.ArgumentTypeError("source directories must use NAME=PATH")
        name, path = item.split("=", 1)
        result[name] = Path(path).expanduser().resolve()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        action="append",
        required=True,
        metavar="ID=PATH",
        help="source checkout path; repeat once for each entry in sources.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "site" / "data.json",
        help="where to write the generated JSON",
    )
    args = parser.parse_args()
    source_paths = parse_source_args(args.source)
    source_config = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))

    results = []
    for source in source_config["sources"]:
        source_id = source["id"]
        if source_id not in source_paths:
            raise SystemExit(f"Missing --source {source_id}=PATH")
        counts, file_count = count_source(source_paths[source_id], source["include"])
        results.append(
            {
                **source,
                "files_scanned": file_count,
                "total_tactic_mentions": sum(counts.values()),
                "tactics": dict(sorted(counts.items())),
            }
        )

    data = {
        "method": (
            "Counts literal occurrences of the listed tactic spellings in selected .lean files. "
            "Line comments, nested block comments, and string contents are ignored. "
            "This is a simple text count: it does not expand macros, count runtime tactic executions, "
            "or include spellings outside the script's tactic-name list."
        ),
        "sources": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for source in results:
        print(
            f"{source['name']}: {source['total_tactic_mentions']:,} tactic-name mentions "
            f"across {source['files_scanned']:,} files"
        )
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
