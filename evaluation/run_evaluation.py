import json
from pathlib import Path
from collections import defaultdict

from app.agent import SupportAgent
from app.session import Session


ROOT = Path(__file__).resolve().parent.parent

VISIBLE_CASES = ROOT / "evaluation" / "visible-cases.json"
ORIGINAL_CASES = ROOT / "evaluation" / "original-cases.json"


def load_cases(path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["cases"]


def contains_all(
    text,
    values,
):
    text_lower = text.lower()

    return all(
        value.lower() in text_lower
        for value in values
    )


def contains_none(
    text,
    values,
):
    text_lower = text.lower()

    return all(
        value.lower() not in text_lower
        for value in values
    )


def evaluate_case(
    case,
    agent,
):
    session = Session(
        session_id=f"evaluation-{case['id']}"
    )

    responses = []

    for message in case["messages"]:

        response = agent.handle(
            session,
            message["content"],
        )

        responses.append(response)

    final_response = responses[-1]

    # Combine all assistant responses because some
    # multi-turn expectations may refer to earlier turns.
    full_text = "\n".join(
        response.answer
        for response in responses
    )

    expect = case.get(
        "expect",
        {},
    )

    must_include = expect.get(
        "must_include",
        [],
    )

    must_not_include = expect.get(
        "must_not_include",
        [],
    )

    include_pass = contains_all(
        full_text,
        must_include,
    )

    exclude_pass = contains_none(
        full_text,
        must_not_include,
    )

    passed = (
        include_pass
        and exclude_pass
    )

    return {
        "id": case["id"],
        "category": case.get(
            "category",
            "uncategorized",
        ),
        "passed": passed,
        "must_include_pass": include_pass,
        "must_not_include_pass": exclude_pass,
        "tool_used": any(
            response.tool_used
            for response in responses
        ),
        "handoff": any(
            response.handoff
            for response in responses
        ),
        "sources": [
            source
            for response in responses
            for source in response.sources
        ],
        "answer": final_response.answer,
    }


def print_results(results):

    print()
    print("=" * 70)
    print("ASTER & ROW EVALUATION")
    print("=" * 70)
    print()

    for result in results:

        status = (
            "PASS"
            if result["passed"]
            else "FAIL"
        )

        print(
            f"[{status}] "
            f"{result['id']} "
            f"({result['category']})"
        )

        if result["tool_used"]:
            print("  tool: used")

        if result["handoff"]:
            print("  handoff: yes")

        if result["sources"]:
            print("  sources:")

            for source in result["sources"]:
                print(
                    f"    - {source}"
                )

        # Show detailed information for failures.
        if not result["passed"]:

            print(
                "  include check:",
                result["must_include_pass"],
            )

            print(
                "  exclusion check:",
                result["must_not_include_pass"],
            )

            print("  ACTUAL ANSWER:")
            print(
                f"    {result['answer']}"
            )

        print()


def print_summary(results):

    total = len(results)

    passed = sum(
        result["passed"]
        for result in results
    )

    print("=" * 70)
    print(
        f"TOTAL: {passed}/{total} passed"
    )
    print("=" * 70)

    categories = defaultdict(
        list
    )

    for result in results:
        categories[
            result["category"]
        ].append(result)

    print()
    print("CATEGORY RESULTS")
    print()

    for category, category_results in sorted(
        categories.items()
    ):

        category_passed = sum(
            result["passed"]
            for result in category_results
        )

        print(
            f"{category}: "
            f"{category_passed}/"
            f"{len(category_results)}"
        )


def main():

    visible_cases = load_cases(
        VISIBLE_CASES
    )

    original_cases = load_cases(
        ORIGINAL_CASES
    )

    cases = (
        visible_cases
        + original_cases
    )

    agent = SupportAgent()

    results = []

    for case in cases:

        result = evaluate_case(
            case,
            agent,
        )

        results.append(result)

    print_results(results)

    print_summary(results)

    failed = [
        result
        for result in results
        if not result["passed"]
    ]

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()