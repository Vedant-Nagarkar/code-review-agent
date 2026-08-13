from graph.state import CodeReviewState
from agents.security import security_node
from agents.performance import performance_node
from agents.style import style_node
from agents.test_coverage import test_coverage_node
from eval.golden_dataset import GOLDEN_DATASET
import json
from datetime import datetime, timezone
from pathlib import Path

AGENT_FUNCTIONS = {
    "security": security_node,
    "performance": performance_node,
    "style": style_node,
    "test_coverage": test_coverage_node,
}


def run_category_eval(category, samples):
    agent_fn = AGENT_FUNCTIONS[category]
    tp = fp = tn = fn = 0
    details = []

    for sample in samples:
        state = CodeReviewState(
            code=sample["code"],
            language="python",
            filename=f"{sample['name']}.py",
            agents_to_run=[category]
        )
        result = agent_fn(state)
        feedbacks = result.get("feedbacks", [])
        actually_flagged = any(fb.findings for fb in feedbacks)
        expected = sample["expected_flag"]

        if expected and actually_flagged:
            tp += 1
            outcome = "TP"
        elif expected and not actually_flagged:
            fn += 1
            outcome = "FN"
        elif not expected and actually_flagged:
            fp += 1
            outcome = "FP"
        else:
            tn += 1
            outcome = "TN"

        details.append({"name": sample["name"], "expected": expected, "actual": actually_flagged, "outcome": outcome})

    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    f1 = (2 * precision * recall / (precision + recall)) if precision and recall and (precision + recall) > 0 else None
    false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else None

    return {
        "category": category,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": round(precision, 2) if precision is not None else None,
        "recall": round(recall, 2) if recall is not None else None,
        "f1": round(f1, 2) if f1 is not None else None,
        "false_positive_rate": round(false_positive_rate, 2) if false_positive_rate is not None else None,
        "details": details
    }


def run_evaluation():
    all_results = []
    for category, samples in GOLDEN_DATASET.items():
        print(f"Evaluating: {category} ({len(samples)} samples)...")
        result = run_category_eval(category, samples)
        all_results.append(result)

    print("\n" + "=" * 70)
    print("EVAL RESULTS — precision / recall / F1 / false-positive rate")
    print("=" * 70)

    total_tp = total_fp = total_tn = total_fn = 0
    for r in all_results:
        print(f"\n{r['category'].upper()}")
        print(f"  TP={r['tp']} FP={r['fp']} TN={r['tn']} FN={r['fn']}")
        print(f"  Precision: {r['precision']}  Recall: {r['recall']}  F1: {r['f1']}  FP rate: {r['false_positive_rate']}")
        for d in r["details"]:
            if d["outcome"] in ("FP", "FN"):
                print(f"    ! {d['outcome']}: {d['name']} (expected={d['expected']}, got={d['actual']})")
        total_tp += r["tp"]; total_fp += r["fp"]; total_tn += r["tn"]; total_fn += r["fn"]

    overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else None
    overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else None
    print(f"\nOVERALL — Precision: {round(overall_precision, 2)}  Recall: {round(overall_recall, 2)}")
    print(f"Total samples: {total_tp + total_fp + total_tn + total_fn}")

    Path("eval/results").mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    with open(f"eval/results/eval_{timestamp}.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to eval/results/eval_{timestamp}.json")


if __name__ == "__main__":
    run_evaluation()