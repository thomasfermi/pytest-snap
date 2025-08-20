"""Pytest plugin for snapshot testing."""

from pathlib import Path

import pytest

from .round import round_floats_in_text


class SnapSession:
    """Manages snapshot state during a test session."""

    def __init__(self) -> None:
        self.update_snapshots = False
        self.snapshot_counters: dict[str, int] = {}
        self.current_test_file: str | None = None
        self.current_test_name: str | None = None

    def get_snapshot_path(self, extension: str) -> Path:
        """Generate the snapshot file path for the current test."""
        if not self.current_test_file or not self.current_test_name:
            raise RuntimeError("snap can only be used within test functions")

        test_file_stem = Path(self.current_test_file).stem
        test_key = f"{test_file_stem}__{self.current_test_name}"

        counter = self.snapshot_counters.get(test_key, 0)
        self.snapshot_counters[test_key] = counter + 1

        snapshot_name = f"{test_key}_{counter}{extension}"
        snapshot_dir = Path(self.current_test_file).parent / "__snapshots__"
        snapshot_dir.mkdir(exist_ok=True, parents=True)

        return snapshot_dir / snapshot_name

    def compare_or_create_snapshot(
        self, extension: str, content: str, digits: int | None = None
    ) -> bool:
        """Create or compare a snapshot with the given content.

        If `digits` is provided, round all floating-point numbers in the content to the
        specified number of decimal places.
        """
        if digits:
            content = round_floats_in_text(content, digits=digits)
        snapshot_path = self.get_snapshot_path(extension)

        if self.update_snapshots or not snapshot_path.exists():
            snapshot_path.write_text(content, encoding="utf-8")
            return True

        expected_content = snapshot_path.read_text(encoding="utf-8")
        if content == expected_content:
            return True

        diff_message = _first_diff(expected_content, content)

        error_msg = (
            f"Snapshot mismatch for {snapshot_path.name}\n"
            f"Snapshot file: {snapshot_path}\n\n"
            f"{diff_message}\n\n"
            f"To update this snapshot, run: pytest --snap-update"
        )

        pytest.fail(error_msg, pytrace=False)


# Global session instance
_session = SnapSession()


def snap_impl(extension: str, content: str, digits: int | None = None) -> bool:
    """Implementation of the snap function injected into test modules."""
    return _session.compare_or_create_snapshot(extension, content, digits)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add snap command line options."""
    parser.addoption(
        "--snap-update",
        action="store_true",
        default=False,
        help="Update all snapshots with current test output",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Configure the snap plugin."""
    _session.update_snapshots = config.getoption("--snap-update", default=False)


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Set up test context for snap."""
    _session.current_test_file = str(item.fspath)
    _session.current_test_name = item.name

    # Reset counter for this specific test
    test_file_stem = Path(item.fspath).stem
    test_key = f"{test_file_stem}__{item.name}"
    _session.snapshot_counters[test_key] = 0


@pytest.fixture
def snap(request):
    """
    Pytest fixture for snapshot testing.

    Allows tests to use `def test_xxx(snap):` and call snap(".ext", content).
    """
    return snap_impl


def _first_diff(expected: str, current: str) -> str:
    """Find the first line difference between two strings and return a diagnostic message."""
    expected_lines = expected.splitlines()
    current_lines = current.splitlines()

    max_lines = max(len(expected_lines), len(current_lines))

    for i in range(max_lines):
        expected_line = expected_lines[i] if i < len(expected_lines) else None
        current_line = current_lines[i] if i < len(current_lines) else None

        if expected_line is not None and current_line is not None:
            if expected_line != current_line:
                return (
                    f"In line {i + 1} there is a mismatch between the snapshot and the current result:\n"
                    f"expected: {expected_line!r}\n"
                    f"current:  {current_line!r}\n"
                    "Subsequent lines may also differ but will not be checked."
                )
        elif expected_line is not None and current_line is None:
            return (
                f"In line {i + 1} the current result is shorter than the snapshot:\n"
                f"expected: {expected_line!r}\n"
                f"current:  <end of content>"
            )
        elif expected_line is None and current_line is not None:
            return (
                f"In line {i + 1} the current result is longer than the snapshot:\n"
                f"expected: <end of content>\n"
                f"current:  {current_line!r}"
            )

    return "No differences found"
