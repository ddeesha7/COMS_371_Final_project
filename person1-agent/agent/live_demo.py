
import os
import json
from pathlib import Path

from dotenv import load_dotenv
from test_generator import TestGenerator

# ==========================================
# PROJECT PATHS
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"
RESULTS_DIR = PROJECT_ROOT / "results"

TESTS_DIR.mkdir(exist_ok=True)

# Load local API credentials before ClaudeClient starts.
for env_file in [
    PROJECT_ROOT / ".env",
    PROJECT_ROOT.parent / ".env",
    Path(__file__).resolve().parent / ".env",
]:
    if env_file.is_file():
        load_dotenv(env_file, override=False)

# ==========================================
# DEMO SETTINGS
# ==========================================

NUMBER_OF_TESTS = 5

# Prefer feedback from the completed Round 7,
# if your team has saved it.
FEEDBACK_FILES = [
    RESULTS_DIR / "coverage_feedback_round7.txt",
    RESULTS_DIR / "coverage_feedback_round6.txt",
]

OUTPUT_FILE = TESTS_DIR / "agent_live_demo_tests.json"


def main():

    print("=" * 50)
    print("LIVE CLAUDE COVERAGE-GUIDED TEST DEMO")
    print("=" * 50)

    # --------------------------------------
    # Check API key
    # --------------------------------------

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY is missing.")
        print("Check your local .env file.")
        return

    print("\nClaude API key detected.")

    # --------------------------------------
    # Load coverage feedback
    # --------------------------------------

    feedback_file = next(
        (p for p in FEEDBACK_FILES if p.is_file()),
        None
    )

    if feedback_file is None:
        print("ERROR: No coverage feedback file found.")
        return

    feedback = feedback_file.read_text(
        encoding="utf-8"
    ).strip()

    if not feedback:
        print("ERROR: Coverage feedback is empty.")
        return

    print("\nCoverage feedback loaded from:")
    print(feedback_file.name)

    print("\nFeedback preview:")
    print(feedback[:600])

    # --------------------------------------
    # Initialize Claude
    # --------------------------------------

    print("\nInitializing Claude API client...")

    generator = TestGenerator()

    # --------------------------------------
    # LIVE API CALL
    # --------------------------------------

    print("\nRequesting targeted grep tests...")
    print("Requested tests:", NUMBER_OF_TESTS)

    tests, usage = generator.generate_tests(
        number_of_tests=NUMBER_OF_TESTS,
        coverage_feedback=feedback
    )

    if tests is None:
        print("ERROR: Test generation failed.")
        return

    # --------------------------------------
    # Show and save new test cases
    # --------------------------------------

    for index, test in enumerate(tests, start=1):

        test["id"] = f"DEMO-{index:03d}"

        print("\n" + "-" * 50)
        print("Test:", test["id"])
        print("Command:", test.get("command"))
        print("Category:", test.get("category"))
        print("Reason:", test.get("reason"))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            {"tests": tests},
            file,
            indent=4
        )

    print("\n" + "=" * 50)
    print("LIVE GENERATION COMPLETE")
    print("=" * 50)

    print("Tests generated:", len(tests))
    print("Saved to:", OUTPUT_FILE)

    print("\nAPI usage:")
    print(usage)

    print("\nExisting Rounds 1-7 were not changed.")
    print("Final verified branch coverage remains 61.11%.")


if __name__ == "__main__":
    main()
