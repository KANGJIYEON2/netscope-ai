
from collections import Counter

from src.analysis.rule_engine import RuleEngine, default_rules, aggregate
from src.analysis.validation.test_cases import TEST_CASES


def run_distribution_check(verbose: bool = False):
    engine = RuleEngine(default_rules())
    counter = Counter()

    mismatches = []

    for case in TEST_CASES:
        matches = engine.run(case["logs"])
        result = aggregate(matches)

        level = result["confidence_level"]
        counter[level] += 1

        expected_level = case["expected_confidence_level"]
        if level != expected_level:
            mismatches.append({
                "id": case["id"],
                "expected": expected_level,
                "actual": level,
                "rules": result["matched_rules"],
            })

        if verbose:
            print(f"[{case['id']}] {case['description']}")
            print("  confidence:", result["confidence"], level)
            print("  rules:", result["matched_rules"])
            print()

    print("\n=== Confidence Distribution ===")
    for level in ["LOW", "MEDIUM", "HIGH"]:
        print(f"{level:6}: {counter[level]}")

    if mismatches:
        print("\n=== MISMATCH CASES ===")
        for m in mismatches:
            print(
                f"{m['id']} | expected={m['expected']} actual={m['actual']} rules={m['rules']}"
            )
    else:
        print("\nAll test cases matched expected confidence levels.")


if __name__ == "__main__":
    run_distribution_check(verbose=False)
