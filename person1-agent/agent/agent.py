
import json
from pathlib import Path

from test_generator import TestGenerator


# ==========================================================
# CONFIGURATION
# ==========================================================

ROUND6_TEST_COUNT = 30
COVERAGE_BEFORE_ROUND7 = 59.40

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIRECTORY = PROJECT_ROOT / "tests"
RESULTS_DIRECTORY = PROJECT_ROOT / "results"

TESTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)


# ==========================================================
# FILE PATHS
# ==========================================================

ROUND_FILES = {
    1: TESTS_DIRECTORY / "agent_initial_tests.json",
    2: TESTS_DIRECTORY / "agent_targeted_tests.json",
    3: TESTS_DIRECTORY / "agent_round3_tests.json",
    4: TESTS_DIRECTORY / "agent_round4_tests.json",
    5: TESTS_DIRECTORY / "agent_round5_tests.json",
    6: TESTS_DIRECTORY / "agent_round6_tests.json",
    7: TESTS_DIRECTORY / "agent_round7_tests.json",
}

ROUND6_FEEDBACK_FILE = (
    RESULTS_DIRECTORY / "coverage_feedback_round6.txt"
)

USAGE_FILE = RESULTS_DIRECTORY / "agent_usage.json"


# ==========================================================
# FILE HELPERS
# ==========================================================

def save_tests(tests, output_file):
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump({"tests": tests}, file, indent=4)


def load_tests(input_file):
    with open(input_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {input_file}")

    tests = data.get("tests")

    if not isinstance(tests, list):
        raise ValueError(f"Missing tests list: {input_file}")

    return tests


def read_feedback(feedback_file):
    if not feedback_file.exists():
        return None

    return feedback_file.read_text(encoding="utf-8").strip() or None


# ==========================================================
# API USAGE
# ==========================================================

def load_usage():
    if not USAGE_FILE.exists():
        return []

    try:
        with open(USAGE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, list) else []

    except (json.JSONDecodeError, OSError):
        return []


def save_usage(usage_records):
    with open(USAGE_FILE, "w", encoding="utf-8") as file:
        json.dump(usage_records, file, indent=4)


# ==========================================================
# TEST HELPERS
# ==========================================================

def assign_round_ids(tests, prefix):
    for index, test in enumerate(tests, start=1):
        test["id"] = f"{prefix}{index:03d}"

    return tests


def show_tests(tests):
    for test in tests:
        print(test.get("id"), "-", test.get("command"))
        print("  Category:", test.get("category"))
        print("  Reason:", test.get("reason"))
        print()


def validate_commands(tests):
    problems = []

    for test in tests:
        test_id = test.get("id")
        command = test.get("command", "")

        if not isinstance(command, str):
            problems.append({
                "id": test_id,
                "problem": "Command is not a string"
            })
            continue

        if command.count("grep.exe") != 1:
            problems.append({
                "id": test_id,
                "problem": "Expected exactly one grep.exe execution"
            })

        for forbidden in [";", "&&", "||"]:
            if forbidden in command:
                problems.append({
                    "id": test_id,
                    "problem": f"Command contains {forbidden}"
                })

    return problems


# ==========================================================
# ROUND 6 - LOAD EXISTING OR GENERATE IF MISSING
# ==========================================================

def generate_round6(usage_records):

    print("\n======================================")
    print("ROUND 6")
    print("======================================\n")

    round6_file = ROUND_FILES[6]

    # Existing tests take priority.
    # No Claude API call is needed.

    if round6_file.exists():
        tests = load_tests(round6_file)

        print("Existing Round 6 tests found.")
        print("Claude will NOT be called again.")
        print("Loaded", len(tests), "Round 6 tests.")

        return tests

    # Only generate if Round 6 file is absent.

    feedback = read_feedback(ROUND6_FEEDBACK_FILE)

    if not feedback:
        print("ERROR: Round 6 feedback is missing.")
        print(ROUND6_FEEDBACK_FILE)
        return None

    print("Round 6 tests are missing.")
    print("Claude generation would be required.")

    try:
        generator = TestGenerator()
    except ValueError as error:
        print("Cannot initialize Claude:", error)
        print("Restore your API key before generating tests.")
        return None

    tests, usage = generator.generate_tests(
        number_of_tests=ROUND6_TEST_COUNT,
        coverage_feedback=feedback
    )

    if tests is None:
        print("ERROR: Round 6 generation failed.")
        return None

    tests = assign_round_ids(tests, "R6-")

    problems = validate_commands(tests)

    if problems:
        print("WARNING: Commands require review.")
        for problem in problems:
            print(problem)

    save_tests(tests, round6_file)

    usage_records.append({
        "round": 6,
        "type": "coverage_guided_generation",
        "coverage_before_round": 56.42,
        "requested_tests": ROUND6_TEST_COUNT,
        "generated_tests": len(tests),
        **(usage or {})
    })

    save_usage(usage_records)

    return tests


# ==========================================================
# ROUND 7 - LOAD TARGETED TESTS
# ==========================================================

def load_round7():

    print("\n======================================")
    print("ROUND 7 - TARGETED BRANCH TESTS")
    print("======================================\n")

    round7_file = ROUND_FILES[7]

    if not round7_file.exists():
        print("ERROR: Round 7 file not found.")
        print(round7_file)
        return None

    try:
        tests = load_tests(round7_file)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print("ERROR loading Round 7:", error)
        return None

    print("Coverage before Round 7: 59.40%")
    print("Round 7 tests loaded:", len(tests))

    if len(tests) != 165:
        print("WARNING: Expected 165 Round 7 tests.")

    problems = validate_commands(tests)

    if problems:
        print("\nCommands requiring review:")

        for problem in problems:
            print(
                problem.get("id"),
                "-",
                problem.get("problem")
            )
    else:
        print("Basic command validation passed.")

    print("\nNo Claude API call was made.")
    print("Previous test files are unchanged.")

    return tests


# ==========================================================
# MAIN
# ==========================================================

def main():

    print("======================================")
    print("GREP COVERAGE-GUIDED AI TEST AGENT")
    print("======================================\n")

    usage_records = load_usage()

    print("Existing experiment history:\n")

    expected_counts = {
        1: 10,
        2: 10,
        3: 10,
        4: 10,
        5: 30,
        6: 30,
        7: 165,
    }

    # Verify previous rounds without overwriting them.

    previous_total = 0

    for round_number in range(1, 6):

        test_file = ROUND_FILES[round_number]

        if not test_file.exists():
            print(f"ERROR: Round {round_number} missing.")
            print(test_file)
            return

        try:
            tests = load_tests(test_file)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"ERROR reading Round {round_number}:", error)
            return

        previous_total += len(tests)

        print(
            f"Round {round_number}: "
            f"{len(tests)} existing tests found."
        )

        if len(tests) != expected_counts[round_number]:
            print("WARNING: Unexpected test count.")

    # ======================================================
    # COVERAGE HISTORY
    # ======================================================

    print("\n======================================")
    print("COVERAGE HISTORY")
    print("======================================\n")

    print("Claude-only baseline: 39.55%")
    print("Round 1: 34.16%")
    print("Round 2: 35.73%")
    print("Round 3: 37.79%")
    print("Round 4: 44.59%")
    print("Round 5: 56.42%")
    print("Round 6: 59.40%")

    print("\nCurrent verified coverage: 59.40%")
    print("Target coverage: 100%")

    # ======================================================
    # ROUND 6
    # ======================================================

    round6_tests = generate_round6(usage_records)

    if round6_tests is None:
        return

    previous_total += len(round6_tests)

    # ======================================================
    # ROUND 7
    # ======================================================

    round7_tests = load_round7()

    if round7_tests is None:
        return

    # ======================================================
    # FINAL SUMMARY
    # ======================================================

    print("\n======================================")
    print("ROUND 7 GENERATION/LOADING COMPLETE")
    print("======================================\n")

    print("Coverage before Round 7: 59.40%")
    print("Target coverage: 100%")
    print("Round 7 new tests:", len(round7_tests))

    print("\nCumulative test counts:\n")

    for round_number in range(1, 8):

        test_file = ROUND_FILES[round_number]
        tests = load_tests(test_file)

        print(f"Round {round_number}: {len(tests)}")

    cumulative_total = previous_total + len(round7_tests)

    print("\nTOTAL:", cumulative_total, "agent-generated tests")

    print("\nRound 7 tests saved at:")
    print(ROUND_FILES[7])

    print("\nAPI usage file:")
    print(USAGE_FILE)

    print("\nNEXT STEP:")
    print("Send agent_round7_tests.json to Person 2.")
    print("Person 2 should reset coverage counters and")
    print("execute Rounds 1 through 7 cumulatively.")

    print("\nDo NOT measure Round 7 alone.")
    
    
    # ======================================================
    # ROUND 7 - LOAD EXISTING TARGETED TESTS
    # ======================================================

    print("\n======================================")
    print("ROUND 7 - TARGETED BRANCH TESTS")
    print("======================================\n")

    round7_file = TESTS_DIRECTORY / "agent_round7_tests.json"

    if not round7_file.exists():
        print("ERROR: Round 7 JSON file is missing.")
        print(round7_file)
        return

    round7_tests = load_tests(round7_file)

    print("Coverage before Round 7: 59.40%")
    print("Round 7 tests:", len(round7_tests))

    problems = validate_commands(round7_tests)

    if problems:
        print("Commands requiring review:")
        for problem in problems:
            print(problem)
    else:
        print("Basic command validation passed.")

    print("\nPrevious tests: 100")
    print("New Round 7 tests:", len(round7_tests))
    print("Cumulative total:", 100 + len(round7_tests))

    print("\nSend agent_round7_tests.json to Person 2.")
    print("Run Rounds 1-7 cumulatively to measure coverage.")

    print("Coverage improvement is not verified yet.")


# ==========================================================
# START PROGRAM
# ==========================================================

if __name__ == "__main__":
    main()
