#!/usr/bin/env python3
"""
NyayaPath — Evaluation Harness

Single-command automated evaluation runner that tests all 18 cases
from eval/cases.json against the NyayaPath graph.

Usage:
    python eval.py              # Run all cases
    python eval.py --dry-run    # Validate cases without running the graph
    python eval.py --case CASE-01  # Run a specific case

Output: Pass/fail summary table in the terminal.
"""

import json
import sys
import os
import argparse
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel


console = Console()

CASES_FILE = Path(__file__).parent / "eval" / "cases.json"


def load_cases() -> list[dict]:
    """Load evaluation cases from JSON."""
    with open(CASES_FILE) as f:
        return json.load(f)


def validate_case(case: dict) -> list[str]:
    """Validate a single case's schema. Returns list of issues."""
    issues = []
    required = ["id", "prompt", "expected_path", "must_contain", "must_not_contain"]
    for field in required:
        if field not in case:
            issues.append(f"Missing field: {field}")
    return issues


def check_assertions(output: str, case: dict) -> tuple[bool, list[str]]:
    """Check output against case assertions.

    Returns:
        Tuple of (all_passed, list_of_failure_reasons).
    """
    failures = []
    output_lower = output.lower()

    # Check must_contain
    for phrase in case.get("must_contain", []):
        if phrase.lower() not in output_lower:
            failures.append(f"Missing required phrase: '{phrase}'")

    # Check must_not_contain
    for phrase in case.get("must_not_contain", []):
        if phrase.lower() in output_lower:
            failures.append(f"Found prohibited phrase: '{phrase}'")

    return len(failures) == 0, failures


def run_case(case: dict, graph) -> dict:
    """Run a single evaluation case through the graph.

    Returns:
        Result dict with pass/fail, output, and failure details.
    """
    from src.graph.builder import get_initial_state

    case_id = case["id"]
    console.print(f"  ⏳ Running {case_id}: {case.get('description', '')[:50]}...")

    try:
        initial_state = get_initial_state(
            user_story=case["prompt"],
            disclaimer_accepted=True,
        )

        result = graph.invoke(initial_state)
        output = result.get("final_guidance", "")
        is_crisis = result.get("is_crisis", False)
        is_harmful = result.get("is_harmful", False)

        # Determine actual path
        if is_crisis:
            actual_path = "crisis"
        elif is_harmful:
            actual_path = "refusal"
        else:
            actual_path = "guidance"

        # Check path match
        expected_path = case["expected_path"]
        path_match = actual_path == expected_path

        # Check string assertions
        assertions_pass, failures = check_assertions(output, case)

        all_pass = path_match and assertions_pass

        if not path_match:
            failures.insert(0, f"Path mismatch: expected={expected_path}, actual={actual_path}")

        return {
            "id": case_id,
            "passed": all_pass,
            "expected_path": expected_path,
            "actual_path": actual_path,
            "failures": failures,
            "output_preview": output[:200],
        }

    except Exception as exc:
        return {
            "id": case_id,
            "passed": False,
            "expected_path": case["expected_path"],
            "actual_path": "error",
            "failures": [f"Exception: {str(exc)}"],
            "output_preview": "",
        }


def print_results(results: list[dict]):
    """Print a formatted results table with category-wise breakdown."""
    table = Table(title="NyayaPath Evaluation Results", show_lines=True)
    table.add_column("Case", style="cyan", no_wrap=True)
    table.add_column("Category", style="magenta")
    table.add_column("Description", style="white", max_width=40)
    table.add_column("Expected", style="dim")
    table.add_column("Actual", style="dim")
    table.add_column("Result", justify="center")
    table.add_column("Issues", style="yellow", max_width=50)

    cases = load_cases()
    case_map = {c["id"]: c for c in cases}

    category_stats: dict[str, dict[str, int]] = {}

    for r in results:
        case = case_map.get(r["id"], {})
        bucket = case.get("bucket", "general")

        if bucket not in category_stats:
            category_stats[bucket] = {"passed": 0, "total": 0}
        category_stats[bucket]["total"] += 1
        if r["passed"]:
            category_stats[bucket]["passed"] += 1

        result_str = "✅ PASS" if r["passed"] else "❌ FAIL"
        result_style = "green" if r["passed"] else "red"
        issues_str = "; ".join(r["failures"][:3]) if r["failures"] else ""

        table.add_row(
            r["id"],
            bucket,
            case.get("description", "")[:40],
            r["expected_path"],
            r["actual_path"],
            f"[{result_style}]{result_str}[/{result_style}]",
            issues_str,
        )

    console.print(table)

    # Category Breakdown Table
    cat_table = Table(title="Category Breakdown", show_lines=True)
    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Passed", justify="center")
    cat_table.add_column("Total", justify="center")
    cat_table.add_column("Pass Rate", justify="center")

    for cat, stats in sorted(category_stats.items()):
        p = stats["passed"]
        t = stats["total"]
        rate = (p / t * 100) if t > 0 else 0
        style = "green" if p == t else ("yellow" if p > 0 else "red")
        cat_table.add_row(
            cat,
            f"[{style}]{p}[/{style}]",
            str(t),
            f"[{style}]{rate:.1f}%[/{style}]",
        )

    console.print(cat_table)

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    summary_style = "green" if failed == 0 else "red"
    console.print(
        Panel(
            f"[bold {summary_style}]{passed}/{total} passed, {failed} failed ({passed/total*100:.1f}% overall pass rate)[/bold {summary_style}]",
            title="Summary",
            border_style=summary_style,
        )
    )


def main():
    parser = argparse.ArgumentParser(description="NyayaPath Evaluation Harness")
    parser.add_argument("--dry-run", action="store_true", help="Validate cases without running")
    parser.add_argument("--case", type=str, help="Run a specific case by ID")
    parser.add_argument("--category", type=str, help="Filter cases by bucket/category name")
    args = parser.parse_args()

    console.print(Panel("⚖️ NyayaPath Evaluation Harness", style="bold cyan"))

    # Load cases
    cases = load_cases()
    console.print(f"Loaded {len(cases)} evaluation cases\n")

    # Validate
    for case in cases:
        issues = validate_case(case)
        if issues:
            console.print(f"  ⚠️  {case.get('id', '?')}: {issues}")

    if args.dry_run:
        console.print("\n[green]✅ Dry run complete — all cases valid[/green]")
        return 0

    # Filter if specific case requested
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
        if not cases:
            console.print(f"[red]Case {args.case} not found[/red]")
            return 1

    # Filter if category requested
    if args.category:
        target = args.category.lower()
        cases = [c for c in cases if target in c.get("bucket", "").lower()]
        if not cases:
            console.print(f"[red]No cases found for category: {args.category}[/red]")
            return 1
        console.print(f"[cyan]Filtered to {len(cases)} cases in category '{args.category}'[/cyan]")

    # Build graph
    console.print("\n🔧 Building NyayaPath graph...")
    from src.graph.builder import build_graph
    graph = build_graph()
    console.print("[green]Graph compiled successfully[/green]\n")

    # Run cases
    console.print("🧪 Running evaluation cases:\n")
    results = []
    for case in cases:
        result = run_case(case, graph)
        status = "✅" if result["passed"] else "❌"
        console.print(f"  {status} {result['id']}")
        results.append(result)

    # Print results
    console.print()
    print_results(results)

    # Exit code
    failed = sum(1 for r in results if not r["passed"])
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
