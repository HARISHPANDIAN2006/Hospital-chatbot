import csv
from pathlib import Path
from collections import defaultdict


def csv_to_labtests_markdown(csv_path: Path, md_path: Path):
    """
    Convert lab_tests.csv into RAG-optimized Markdown.
    """

    categories = defaultdict(list)

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            categories[row["category"]].append(row)

    lines = []
    lines.append("# Hospital Laboratory Test Directory\n")
    lines.append(
        "This document contains a comprehensive list of laboratory and diagnostic tests "
        "available at the hospital, including preparation requirements, costs, and clinical relevance.\n"
    )

    for category, tests in categories.items():
        lines.append(f"\n## {category} Tests\n")

        for test in tests:
            lines.extend([
                f"### {test['test_name']}",
                f"- **Category:** {test['category']}",
                f"- **Normal Range:** {test['normal_range']}",
                f"- **Unit:** {test['unit']}",
                f"- **Fasting Required:** {test['fasting_required']}",
                f"- **Sample Type:** {test['sample_type']}",
                f"- **Report Time:** {test['report_time']}",
                f"- **Cost:** ₹{test['cost_inr']}",
                f"- **Clinical Significance:** {test['clinical_significance']}",
                f"- **Notes:** {test['notes']}",
                ""
            ])

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"✅ Converted {csv_path.name} → {md_path.name}")



csv_to_labtests_markdown(
    Path("data/raw_docs/lab_tests.csv"),
    Path("data/raw_docs/lab_tests.md")
)
