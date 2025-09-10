import os

from textwrap import dedent

from click.testing import CliRunner

from prometheus_script_wrapper import main


def test_success(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["--prefix", "test", "--output", tmp_path / "out.prom", "--", "true"])

    # Verify the wrapper executed successfully
    assert result.exit_code == 0

    # Check that the metrics file exists and contains the expected metrics
    assert os.path.exists(tmp_path / "out.prom")
    with (tmp_path / "out.prom").open("r") as f:
        content = f.read()
        assert "test_exit_code 0" in content
        assert "test_success 1" in content
        assert "test_runtime_seconds" in content
        assert "test_success_timestamp_seconds" in content


def test_failure(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["--prefix", "test", "--output", tmp_path / "out.prom", "--", "false"])

    # Verify the wrapper executed successfully
    assert result.exit_code == 1

    # Check that the metrics file exists and contains the expected metrics
    assert os.path.exists(tmp_path / "out.prom")
    with (tmp_path / "out.prom").open("r") as f:
        content = f.read()
        assert "test_exit_code 1" in content
        assert "test_success 0" in content
        assert "test_runtime_seconds" in content
        assert "test_success_timestamp_seconds" not in content  # Should not be present for failures


def test_exit_code(tmp_path):
    with (tmp_path / "script.sh").open("w") as f:
        f.write(
            dedent(
                r"""#!/usr/bin/env bash
                exit 42
            """
            )
        )

    runner = CliRunner()
    result = runner.invoke(main, ["--prefix", "test", "--output", tmp_path / "out.prom", "--", "bash", tmp_path / "script.sh"])

    # Verify the wrapper executed successfully
    assert result.exit_code == 42

    # Check that the metrics file exists and contains both standard and custom metrics
    assert os.path.exists(tmp_path / "out.prom")
    with (tmp_path / "out.prom").open("r") as f:
        content = f.read()
        assert "test_exit_code 42" in content
        assert "test_success 0" in content


def test_custom_metrics(tmp_path):
    with (tmp_path / "script.sh").open("w") as f:
        f.write(
            dedent(
                r"""#!/usr/bin/env bash
            
                echo "# HELP test_count_total This is a test metric\nwith description containing a newline" >&${PROM_METRICS_FD}
                echo "# TYPE test_count_total counter" >&${PROM_METRICS_FD}
                echo "test_count_total 42" >&${PROM_METRICS_FD}
                
                echo "# HELP test_gauge This is another test metric\nwith labels" >&${PROM_METRICS_FD}
                echo "# TYPE test_gauge gauge" >&${PROM_METRICS_FD}
                echo "test_gauge{mylabel=\"test\"} 23" >&${PROM_METRICS_FD}
            """
            )
        )

    runner = CliRunner()
    result = runner.invoke(main, ["--prefix", "test", "--output", tmp_path / "out.prom", "--", "bash", tmp_path / "script.sh"])

    # Verify the wrapper executed successfully
    assert result.exit_code == 0

    # Check that the metrics file exists and contains both standard and custom metrics
    assert os.path.exists(tmp_path / "out.prom")
    with (tmp_path / "out.prom").open("r") as f:
        content = f.read()
        assert "test_runtime_seconds" in content
        assert "test_script_test_count_total 42" in content
        assert 'test_script_test_gauge{mylabel="test"} 23' in content


def test_extra_labels(tmp_path):
    with (tmp_path / "script.sh").open("w") as f:
        f.write(
            dedent(
                r"""#!/usr/bin/env bash

                echo "# HELP test_count_total This is a test metric" >&${PROM_METRICS_FD}
                echo "# TYPE test_count_total counter" >&${PROM_METRICS_FD}
                echo "test_count_total 42" >&${PROM_METRICS_FD}
                            
                echo "# HELP test_gauge This is another test metric\nwith labels" >&${PROM_METRICS_FD}
                echo "# TYPE test_gauge gauge" >&${PROM_METRICS_FD}
                echo "test_gauge{mylabel=\"test\"} 23" >&${PROM_METRICS_FD}
            """
            )
        )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--prefix",
            "test",
            "--output",
            tmp_path / "out.prom",
            "--label",
            "x",
            "one",
            "--label",
            "y",
            "two",
            "--",
            "bash",
            tmp_path / "script.sh",
        ],
    )

    # Verify the wrapper executed successfully
    assert result.exit_code == 0

    # Check that the metrics file exists and contains both standard and custom metrics
    assert os.path.exists(tmp_path / "out.prom")
    with (tmp_path / "out.prom").open("r") as f:
        content = f.read()
        assert 'test_exit_code{x="one",y="two"}' in content
        assert 'test_success{x="one",y="two"}' in content
        assert 'test_runtime_seconds{x="one",y="two"}' in content
        assert 'test_script_test_count_total{x="one",y="two"} 42' in content
        assert 'test_script_test_gauge{mylabel="test",x="one",y="two"} 23' in content


def test_argument_passing(tmp_path):
    with (tmp_path / "script.sh").open("w") as f:
        f.write(
            dedent(
                r"""#!/usr/bin/env bash

                echo "# HELP test_count_total This is a test metric\nwith description containing a newline" >&${PROM_METRICS_FD}
                echo "# TYPE test_count_total counter" >&${PROM_METRICS_FD}
                echo "test_count_total{test=\"$2\"} $1" >&${PROM_METRICS_FD}
            """
            )
        )

    runner = CliRunner()
    result = runner.invoke(
        main, ["--prefix", "test", "--output", tmp_path / "out.prom", "--", "bash", tmp_path / "script.sh", "1337", "--extra"]
    )

    # Verify the wrapper executed successfully
    assert result.exit_code == 0

    # Check that the metrics file exists and contains both standard and custom metrics
    assert os.path.exists(tmp_path / "out.prom")
    with (tmp_path / "out.prom").open("r") as f:
        content = f.read()
        assert 'test_script_test_count_total{test="--extra"} 1337' in content
