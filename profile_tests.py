#!/usr/bin/env python
"""
Profile pytest tests to get detailed statistics on time and resource usage.

Usage:
    python profile_tests.py [--fast-only]
"""

import subprocess
import sys
import time


def run_pytest_with_timing(markers=None):
    """Run pytest and capture timing information"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--durations=0",
        "-v",
        "--tb=no",
        "--quiet"
    ]

    if markers:
        cmd.extend(["-m", markers])

    print(f"Running: {' '.join(cmd)}")
    print("=" * 80)

    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start

    return result, elapsed


def parse_durations(output):
    """Parse pytest duration output"""
    durations = []
    in_durations = False

    for line in output.split('\n'):
        if 'slowest' in line and 'durations' in line:
            in_durations = True
            continue

        if in_durations:
            if line.strip() and 's call' in line:
                parts = line.split()
                if len(parts) >= 3:
                    duration = parts[0].rstrip('s')
                    test_name = ' '.join(parts[2:])
                    try:
                        durations.append((float(duration), test_name))
                    except ValueError:
                        pass
            elif 'passed' in line or 'failed' in line:
                break

    return sorted(durations, reverse=True)


def format_duration(seconds):
    """Format duration in human-readable form"""
    if seconds < 0.001:
        return f"{seconds*1000000:.0f}µs"
    elif seconds < 1:
        return f"{seconds*1000:.1f}ms"
    else:
        return f"{seconds:.2f}s"


def print_statistics(durations, total_time, test_type="All"):
    """Print formatted statistics"""
    print(f"\n{'='*80}")
    print(f"{test_type} Tests Performance Statistics")
    print(f"{'='*80}")

    if not durations:
        print("No test durations found")
        return

    print(f"\nTotal execution time: {format_duration(total_time)}")
    print(f"Number of tests: {len(durations)}")

    if durations:
        avg_time = sum(d[0] for d in durations) / len(durations)
        print(f"Average test time: {format_duration(avg_time)}")
        print(f"Slowest test: {format_duration(durations[0][0])}")
        print(f"Fastest test: {format_duration(durations[-1][0])}")

    print(f"\n{'Test Name':<80} {'Duration':>12}")
    print("-" * 93)

    for duration, name in durations[:20]:  # Show top 20
        # Truncate long test names
        display_name = name if len(name) <= 80 else name[:77] + "..."
        print(f"{display_name:<80} {format_duration(duration):>12}")

    if len(durations) > 20:
        print(f"\n... and {len(durations) - 20} more tests")

    # Category breakdown
    categories = {}
    for duration, name in durations:
        if '::' in name:
            file_name = name.split('::')[0]
            categories[file_name] = categories.get(file_name, 0) + duration

    print(f"\n{'File':<60} {'Total Time':>12}")
    print("-" * 73)
    for file_name in sorted(categories.keys(), key=categories.get, reverse=True):
        print(f"{file_name:<60} {format_duration(categories[file_name]):>12}")


def main():
    fast_only = "--fast-only" in sys.argv

    if fast_only:
        print("Running FAST tests only (excluding 'slow' marker)")
        result, total_time = run_pytest_with_timing("not slow")
        test_type = "Fast"
    else:
        print("Running ALL tests")
        result, total_time = run_pytest_with_timing()
        test_type = "All"

    # Print pytest output
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr, file=sys.stderr)

    # Parse and display statistics
    durations = parse_durations(result.stdout)
    print_statistics(durations, total_time, test_type)

    # Summary
    print(f"\n{'='*80}")
    print(f"Summary: {len(durations)} tests completed in {format_duration(total_time)}")
    print(f"{'='*80}\n")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
