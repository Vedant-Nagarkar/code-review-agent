from graph.graph import review_graph
from eval.golden_dataset import GOLDEN_DATASET

SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2}


def check_expectations(sample_name, expect, feedbacks, final_report):
    failures = []

    for category in ["security", "performance", "style", "test_coverage"]:
        key = f"{category}_has_findings"
        if key in expect:
            category_feedbacks = [fb for fb in feedbacks if fb.agent_name == category]
            has_findings = any(fb.findings for fb in category_feedbacks)
            if has_findings != expect[key]:
                failures.append(
                    f"{key}: expected {expect[key]}, got {has_findings}"
                )

        min_sev_key = f"min_{category}_severity"
        if min_sev_key in expect:
            category_feedbacks = [fb for fb in feedbacks if fb.agent_name == category]
            if category_feedbacks:
                actual_max_sev = max(
                    (SEVERITY_RANK.get(fb.severity, 0) for fb in category_feedbacks),
                    default=0
                )
                expected_min_sev = SEVERITY_RANK.get(expect[min_sev_key], 0)
                if actual_max_sev < expected_min_sev:
                    failures.append(
                        f"{min_sev_key}: expected at least {expect[min_sev_key]}, "
                        f"got max severity rank {actual_max_sev}"
                    )

    return failures


def run_evaluation():
    results = []

    for sample in GOLDEN_DATASET:
        print(f"Running: {sample['name']}...")
        result = review_graph.invoke({
            "code": sample["code"],
            "language": "python",
            "filename": f"{sample['name']}.py"
        })

        feedbacks = result.get("feedbacks", [])
        final_report = result.get("final_report", {})

        failures = check_expectations(sample["name"], sample["expect"], feedbacks, final_report)

        results.append({
            "name": sample["name"],
            "passed": len(failures) == 0,
            "failures": failures
        })

    print("\n" + "=" * 50)
    print("EVAL RESULTS")
    print("=" * 50)

    passed_count = sum(1 for r in results if r["passed"])
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['name']}")
        for f in r["failures"]:
            print(f"       - {f}")

    print(f"\n{passed_count}/{len(results)} samples passed")


if __name__ == "__main__":
    run_evaluation()