import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pytest


@pytest.fixture(scope="session")
def uv_snapshot_env():
    """
    Sets up a temporary project with uv, builds and installs snap.

    This fixture is session-scoped, so it runs only once for the entire
    test session. It creates a temporary directory, initializes a Python project
    with `uv`, builds the `snap` package from the project root, and installs
    it into the temporary environment.

    It yields the path to the temporary directory, which can then be used
    by tests to run pytest in that environment.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # The snap project root is the parent directory of the 'tests' directory
        snap_path = Path(__file__).parent.parent.resolve()

        # Initialize a new python project in the temporary directory
        subprocess.run(["uv", "init", "--lib"], cwd=tmp_path, check=True)

        # Install pytest and pytest-json-report in the new environment
        subprocess.run(
            ["uv", "add", "pytest", "pytest-json-report"], cwd=tmpdir, check=True
        )

        # Build the snap package
        subprocess.run(["uv", "build"], cwd=snap_path, check=True)

        # Find the built wheel file
        dist_dir = snap_path / "dist"
        try:
            wheel = next(dist_dir.glob("*.whl"))
        except StopIteration:
            pytest.fail(
                "No wheel file found in the 'dist' directory. "
                "Please build the project first."
            )

        # Install the snap wheel into the temporary environment
        subprocess.run(["uv", "add", str(wheel)], cwd=tmpdir, check=True)

        # Create a 'tests' subdirectory for test files
        (tmp_path / "tests").mkdir()

        # use yield instead of return to make sure that tmp dir is removed after tests
        yield tmp_path


@dataclass
class PytestResult:
    outcomes: list[Literal["passed", "failed", "skipped"]]
    snapshots: dict[str, str]  # filename => content


def run_with_uv(
    uv_snapshot_env: Path,
    code_versions: list[str],
    snap_update_flag: bool = False,
) -> list[PytestResult]:
    """
    Run snapshot test for each code version and return test results.

    First code_version[0] is written to test_dummy.py.
    Then we run pytest (with snap) and record the test result.
    Then we change the code to code_version[1], run pytest again and record the test
    result. We do this for all code_versions
    """

    tmp = uv_snapshot_env

    tests = tmp / "tests"
    test_file = uv_snapshot_env / "tests" / "test_dummy.py"

    # remove existing snapshot files from previous tests to get a clean environment
    snapshot_path = tests / "__snapshots__"
    if snapshot_path.exists():
        shutil.rmtree(snapshot_path)

    results: list[PytestResult] = []
    for i, code in enumerate(code_versions, start=1):
        test_file.write_text(code)
        outname = f"report_{i}.json"
        outpath = tmp / outname

        args = [
            "uv",
            "run",
            "pytest",
            "--json-report",
            f"--json-report-file={outname}",
            "-q",
        ]
        if snap_update_flag:
            args.insert(3, "--snap-update")

        subprocess.run(args, cwd=tmp, text=True, capture_output=True, check=False)

        pytest_json = json.loads(outpath.read_text())
        outcomes = [x["outcome"] for x in pytest_json["tests"]]

        # collect snapshot files if present
        snapdir = tests / "__snapshots__"
        snapshots: dict[str, str] = {}
        if snapdir.exists():
            for f in snapdir.iterdir():
                snapshots[f.name] = f.read_text()

        results.append(PytestResult(outcomes=outcomes, snapshots=snapshots))

    return results


def sample_code(msg: str) -> str:
    return f"""
def test_html_output(snap):
    html_content = "<div><h1>{msg}</h1></div>"
    assert snap(".html", html_content)
"""


def test_if_snapshot_does_not_exist(uv_snapshot_env: Path):
    msg = "Hello world"
    results = run_with_uv(uv_snapshot_env, [sample_code(msg)])
    snapshots = results[0].snapshots
    assert results[0].outcomes[0] == "passed"
    assert (
        snapshots["test_dummy__test_html_output_0.html"] == f"<div><h1>{msg}</h1></div>"
    )


def test_if_snapshot_exists_and_does_not_change(uv_snapshot_env: Path):
    # first run creates snapshot, second run asserts on it
    msg = "Hello world"

    results = run_with_uv(uv_snapshot_env, [sample_code(msg), sample_code(msg)])
    assert results[0].outcomes[0] == "passed"
    assert results[1].outcomes[0] == "passed"


def test_if_snapshot_exists_and_does_change(uv_snapshot_env: Path):
    # first run creates snapshot, second run asserts on it
    # but since the content changes, the second run should fail
    msg1 = "Hello world"
    msg2 = "Hello world!!!!"
    results = run_with_uv(uv_snapshot_env, [sample_code(msg1), sample_code(msg2)])
    assert results[0].outcomes[0] == "passed"
    assert results[1].outcomes[0] == "failed"


def test_if_snapshot_exists_and_does_change_but_we_use_snap_update(
    uv_snapshot_env: Path,
):
    # if we pass the snap-update flag, tests should always pass

    msg1 = "Hello world"
    msg2 = "Hello world!!!!"
    results = run_with_uv(
        uv_snapshot_env, [sample_code(msg1), sample_code(msg2)], snap_update_flag=True
    )
    assert results[0].outcomes[0] == "passed"
    assert (
        results[0].snapshots["test_dummy__test_html_output_0.html"]
        == f"<div><h1>{msg1}</h1></div>"
    )
    assert results[1].outcomes[0] == "passed"
    assert (
        results[1].snapshots["test_dummy__test_html_output_0.html"]
        == f"<div><h1>{msg2}</h1></div>"
    )


def test_two_files_in_one_test(uv_snapshot_env: Path):
    code_with_two_snapshots = """
def test_dummy(snap):
    import json
    cont1 = "Hello world!"
    cont2 = "Hello world again!"
    cont3 = json.dumps({"a":2})
    assert snap(".txt", cont1)
    assert snap(".txt", cont2)
    assert snap(".json", cont3)
    """
    results = run_with_uv(uv_snapshot_env, [code_with_two_snapshots])
    assert results[0].outcomes[0] == "passed"
    assert results[0].snapshots["test_dummy__test_dummy_0.txt"] == "Hello world!"
    assert results[0].snapshots["test_dummy__test_dummy_1.txt"] == "Hello world again!"
    assert results[0].snapshots["test_dummy__test_dummy_2.json"] == json.dumps({"a": 2})


def test_test_file_with_two_test(uv_snapshot_env: Path):
    code_with_two_tests = """
def test_number_one(snap):
    assert snap(".txt", "Hello world from number one!")

def test_number_two(snap):
    assert snap(".txt", "Hello world from number two!")
    """
    results = run_with_uv(uv_snapshot_env, [code_with_two_tests])
    assert results[0].outcomes[0] == "passed"
    assert results[0].outcomes[1] == "passed"
    assert (
        results[0].snapshots["test_dummy__test_number_one_0.txt"]
        == "Hello world from number one!"
    )
    assert (
        results[0].snapshots["test_dummy__test_number_two_0.txt"]
        == "Hello world from number two!"
    )


def test_with_rounding(uv_snapshot_env: Path):
    code_which_produces_snapshot_with_floats = """
def test_number(snap):
    assert snap(".txt", "pi=3.14159!", digits=3)
    """
    results = run_with_uv(
        uv_snapshot_env, 2 * [code_which_produces_snapshot_with_floats]
    )
    assert results[0].outcomes[0] == "passed"
    assert results[1].outcomes[0] == "passed"
    assert results[0].snapshots["test_dummy__test_number_0.txt"] == "pi=3.14!"
