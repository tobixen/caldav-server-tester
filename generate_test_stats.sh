#!/bin/bash
#
# Generate comprehensive test statistics including timing and resource usage
#
# Usage: ./generate_test_stats.sh [--fast-only]

set -e

OUTPUT_FILE="test_stats_$(date +%Y%m%d_%H%M%S).txt"

echo "Generating test statistics..."
echo "Output file: $OUTPUT_FILE"
echo ""

{
    echo "================================================================================"
    echo "Test Performance Report"
    echo "Generated: $(date)"
    echo "================================================================================"
    echo ""

    if [ "$1" == "--fast-only" ]; then
        echo "Running FAST tests only (excluding 'slow' marker)"
        echo ""

        echo "--- Test Execution with Timing ---"
        /usr/bin/time -v python -m pytest tests/ -m "not slow" --durations=0 -v --tb=no 2>&1

    else
        echo "Running ALL tests"
        echo ""

        echo "--- Fast Tests Only ---"
        echo ""
        /usr/bin/time -v python -m pytest tests/ -m "not slow" -q 2>&1

        echo ""
        echo "================================================================================"
        echo "--- All Tests (including slow mocked server tests) ---"
        echo ""
        /usr/bin/time -v python -m pytest tests/ --durations=20 -v --tb=no 2>&1
    fi

    echo ""
    echo "================================================================================"
    echo "Test Statistics Summary"
    echo "================================================================================"

    # Count tests by file
    echo ""
    echo "Tests by file:"
    find tests/ -name "test_*.py" -exec sh -c 'echo "  $(basename {}): $(grep -c "def test_" {} 2>/dev/null || echo 0) tests"' \;

    echo ""
    echo "Total test functions: $(find tests/ -name "test_*.py" -exec cat {} \; | grep -c "def test_")"

} | tee "$OUTPUT_FILE"

echo ""
echo "Report saved to: $OUTPUT_FILE"
echo ""
echo "Quick commands:"
echo "  View report: cat $OUTPUT_FILE"
echo "  View timing only: grep -A 30 'slowest.*duration' $OUTPUT_FILE"
echo "  View resource usage: grep -A 20 'Maximum resident' $OUTPUT_FILE"
