# pytest-snap

A simple snapshot testing library implemented as a pytest plugin.

`pytest-snap` allows you to easily create and compare text-based snapshots of test data by writing `assert snap(".json", content)` where content is a string. The library handles file creation on first run and comparison on subsequent runs.

## Why another snapshot testing library?

There are many great snapshot testing libraries out there, like [syrupy](https://github.com/syrupy-project/syrupy), [pytest-snapshot](https://github.com/joseph-roitman/pytest-snapshot) or [pytest-insta](https://github.com/vberlier/pytest-insta).

This one is for you if:

* You want to snapshot your data as txt. **You** want to control the serialization of your data to text.
* You like the simple workflow of this library (see section "Quick Start" in this README)

And optionally:
* You are producing numerical data and want to compare it only to some significant digits. Check out the section "Optional feature: Rounding floating point numbers" in this README.

## Installation

Install `pytest-snap` using pip:

```bash
pip install pytest-snap
```

Or using uv:

```bash
uv add --dev pytest-snap
```

## Quick Start

1. Add the `snap` fixture as an argument to your test functions:

```python
def test_api_response(snap):
    response_data = {"user": "john", "status": "active"}
    response_json = json.dumps(response_data, indent=2)
    # This will create a snapshot file on first run
    assert snap(".json", response_json)


def test_multiple_formats(snap):
    # You can create multiple snapshots from one test function
    assert snap(".json", json.dumps({"message": "Hello"}))       # _0.json
    assert snap(".json", json.dumps({"message": "Hello again"})) # _1.json
    assert snap(".html", "<div><h1>Hello World</h1></div>")      # _2.html
```


2. Run your tests:

```bash
pytest
```

On the first run, `pytest-snap` will create snapshot files in a `__snapshots__` directory next to your test files:

```
tests/
├── test_example.py
└── __snapshots__/
    ├── test_example__test_api_response_0.json
    └── test_example__test_html_output_0.html
```

You should commit these snapshot files to your version control system (e.g. git).

3. On subsequent `pytest`runs, `pytest-snap` compares your test output against the stored snapshots and fails if they don't match, showing you a clear diff. So whenever you refactor your code, you can run the snapshot tests and as long as the tests pass, you can be confident that your code changes are safe.

4. Sometimes your code change is no refactor. You know that you want to change your code in a way which changes the snapshot files. Change your code, and then run pytest with the `--snap-update` flag to update the snapshots. Use your version control system to see how the snapshots have changed (e.g. git difftool).

```bash
pytest --snap-update
```


## File Organization

`pytest-snap` organizes snapshot files in a predictable structure:

```
your_project/
├── tests/
    ├── test_api.py
    ├── test_utils.py
    └── __snapshots__/
        ├── test_api__test_user_endpoint_0.json
        ├── test_api__test_error_handling_0.json
        ├── test_utils__test_format_data_0.txt
        └── test_utils__test_format_data_1.html
```

The naming convention is: `{test_file_name}__{test_function_name}_{call_index}{extension}`

## Error Messages and Debugging

When a snapshot doesn't match, `pytest-snap` provides a clear error message:

```
Snapshot mismatch for unit_test__test_very_long_0.txt
Snapshot file: /home/username/cool-project/tests/__snapshots__/unit_test__test_very_long_0.txt

In line 211 there is a mismatch between the snapshot and the current result:
expected: 'I like python very much'
current:  'I like python very much indeed'
Subsequent lines may also differ but will not be checked.

To update this snapshot, run: pytest --snap-update
============================================================== short test summary info ===============================================================
FAILED tests/unit_test.py::test_very_long - Failed: Snapshot mismatch for unit_test__test_very_long_0.txt
```

## Type hints
You can use a type hint for the `snap` fixture if you want to:

```python
from pytest_snap import SnapshotFixture

def test_api_response(snap : SnapshotFixture):
    assert snap(".json", json.dumps({"message": "Hello"}))
```


## Optional feature: Rounding floating point numbers
The `snap` fixture has an optional argument `digits` which allows you to round all floats within your snapshot string to `digits` significant digits.

```python
def test_number(snap):
    assert snap(".txt", "pi=3.14159!", digits=3)
    # will result in snapshot file with content "pi=3.14!"
```

Note that identifying which parts of a string are actually floats is inherently ambiguous.
The current implementation may work reasonably well for many cases, particularly json dumps, but should be used with caution.
It attempts to preserve timestamps, dates, IP addresses, SemVer and URLs, though edge cases may not be handled correctly.


## Development

* Make sure you have `uv` installed.
* To run tests: `uv run pytest`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
