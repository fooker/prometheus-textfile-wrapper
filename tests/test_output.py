import os
import sys
import tempfile

import pytest

from click.testing import CliRunner

from prometheus_script_wrapper import main


@pytest.fixture
def temp_output_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = f.name

    yield path

    # Clean up after the test
    if os.path.exists(path):
        os.unlink(path)


def test_success(temp_output_file):
    runner = CliRunner()
    result = runner.invoke(main, ["--prefix", "test", "--output", temp_output_file, "--", "echo", "hello"])

    # Verify the wrapper executed successfully
    assert result.exit_code == 0

    # Check that the metrics file exists and contains the expected metrics
    assert os.path.exists(temp_output_file)
    with open(temp_output_file, "r") as f:
        content = f.read()
        assert "test_exit_code 0" in content
        assert "test_runtime_seconds" in content
        assert "test_success_timestamp_seconds" in content


def test_failure(temp_output_file):
    runner = CliRunner()
    result = runner.invoke(main, ["--prefix", "test", "--output", temp_output_file, "--", "false"])

    # Verify the wrapper executed successfully
    assert result.exit_code == 1

    # Check that the metrics file exists and contains the expected metrics
    assert os.path.exists(temp_output_file)
    with open(temp_output_file, "r") as f:
        content = f.read()
        assert "test_exit_code 1" in content
        assert "test_runtime_seconds" in content
        assert "test_success_timestamp_seconds" not in content  # Should not be present for failures


def test_custom_metrics(temp_output_file):
    runner = CliRunner()
    result = runner.invoke(main, ["--prefix", "test", "--output", temp_output_file, "--", "./example.sh", "testarg"])

    # Verify the wrapper executed successfully
    assert result.exit_code == 3

    # Check that the metrics file exists and contains both standard and custom metrics
    assert os.path.exists(temp_output_file)

    with open(temp_output_file, "r") as f:
        content = f.read()

        print(content, file=sys.stderr)

        assert "test_exit_code 3" in content
        assert "test_runtime_seconds 3" in content
        assert 'test_script_test_count{foo="bar",testkey="testarg"} 42' in content


def test_extra_labels(temp_output_file):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--prefix", "test", "--output", temp_output_file, "--label", "x", "one", "--label", "y", "two", "--", "./example.sh", "testarg"],
    )

    # Verify the wrapper executed successfully
    assert result.exit_code == 3

    # Check that the metrics file exists and contains both standard and custom metrics
    assert os.path.exists(temp_output_file)

    with open(temp_output_file, "r") as f:
        content = f.read()
        assert 'test_exit_code{x="one",y="two"} 3' in content
        assert 'test_runtime_seconds{x="one",y="two"}' in content
        assert 'test_script_test_count{foo="bar",testkey="testarg",x="one",y="two"} 42' in content
