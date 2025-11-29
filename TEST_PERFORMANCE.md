# Test Performance Statistics

This document provides detailed performance statistics for the caldav-server-tester test suite.

## Quick Summary

| Test Category | Count | Total Time | Avg Time/Test | Memory Usage |
|--------------|-------|------------|---------------|--------------|
| **Fast Tests** (unit) | 54 | ~1.2s | <5ms | ~76 MB |
| **Slow Tests** (mocked server) | 14 | ~70s | ~5s | ~77 MB |
| **Total** | 68 | ~71s | ~1s | ~77 MB |

## Running Tests

### Fast Tests Only (Recommended for Development)
```bash
# Run only fast unit tests
pytest -m "not slow"

# With verbose output
pytest -m "not slow" -v

# With duration statistics
pytest -m "not slow" --durations=10
```

**Performance:** 54 tests in ~1.2 seconds

### All Tests (Including Slow Mocked Server Tests)
```bash
# Run all tests
pytest

# With detailed timing
pytest --durations=20
```

**Performance:** 68 tests in ~71 seconds

### Slow Tests Only
```bash
pytest -m "slow"
```

**Performance:** 14 tests in ~70 seconds

## Detailed Test Timing

### Fast Unit Tests (< 5ms each)

All 54 fast unit tests complete in under 5 milliseconds each:

- **test_ai_check_base.py**: 18 tests for Check base class
  - set_feature method: 8 tests
  - feature_checked method: 3 tests
  - run_check dependency resolution: 7 tests

- **test_ai_checker.py**: 24 tests for ServerQuirkChecker
  - Initialization: 7 tests
  - Properties: 2 tests
  - Methods (check_one, report, cleanup): 15 tests

- **test_ai_filters.py**: 12 tests for _filter_2000 function
  - Date range filtering
  - Edge cases and boundary conditions

### Slow Mocked Server Tests

These tests run actual check logic with mocked server responses:

| Test | Duration | Category |
|------|----------|----------|
| `test_calendar_auto_creation_detected` | ~60s | CheckMakeDeleteCalendar |
| `test_calendar_creation_with_displayname` | ~10s | CheckMakeDeleteCalendar |
| Other mocked tests | <0.5s each | Various |

**Why these are slow:**
- They execute the full `_run_check()` logic
- Complex retry/fallback mechanisms
- Multiple calendar creation/deletion cycles
- Extensive feature detection logic

## Resource Usage

### CPU Usage
```
CPU: 99% (single-threaded)
Context switches: ~75 involuntary
Page faults: ~22,000 minor
```

### Memory Usage
```
Maximum resident set size: ~77 MB
Average memory footprint: Stable throughout execution
No memory leaks detected
```

### I/O
```
File system inputs: 0
File system outputs: 32 (test result files)
No network I/O (all tests are offline)
```

## Performance Tips

### For Development (Fast Feedback)
```bash
# Run only fast tests - get results in ~1 second
pytest -m "not slow" -x

# Run specific test file
pytest tests/test_ai_filters.py

# Run specific test
pytest tests/test_ai_filters.py::TestFilter2000::test_filter_includes_dtstart_at_start_boundary
```

### For CI/CD
```bash
# Run all tests with coverage
pytest --cov=caldav_server_tester --cov-report=html

# Run with JUnit XML output for CI
pytest --junitxml=test-results.xml

# Parallel execution (if pytest-xdist installed)
pytest -n auto
```

### Profiling Individual Tests
```bash
# Show detailed timing for all tests
pytest --durations=0 -vv

# Profile specific test with cProfile
python -m cProfile -o profile.stats -m pytest tests/test_ai_filters.py
python -c "import pstats; p=pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

## Performance Optimization

The test suite is optimized for:

1. **Fast Iteration**: Unit tests run in ~1 second for rapid development
2. **Comprehensive Coverage**: 71 total tests (54 fast + 14 slow + 3 skipped)
3. **Selective Execution**: Use markers to run appropriate test subset
4. **Low Memory**: < 80 MB memory footprint
5. **No Dependencies**: All tests run offline without external services

## Monitoring Performance Over Time

To track test performance over time:

```bash
# Generate timing report
pytest --durations=0 --tb=no > timing_report.txt

# Compare with previous run
diff timing_report_old.txt timing_report.txt
```

For continuous monitoring, consider integrating with CI to track:
- Total test execution time
- Individual slow test trends
- Memory usage patterns
- Test failure rates

## Troubleshooting Slow Tests

If tests are slower than expected:

1. **Check for slow markers**: Some tests are intentionally slow
   ```bash
   pytest --co -m slow  # List slow tests
   ```

2. **Profile specific test**:
   ```bash
   pytest tests/test_checks_with_mocks.py::TestCheckMakeDeleteCalendar::test_calendar_auto_creation_detected --durations=0 -vv
   ```

3. **Check system load**: Ensure system isn't under heavy load
   ```bash
   top  # Check CPU/memory availability
   ```

4. **Reduce test scope**: Run subset of tests
   ```bash
   pytest tests/test_ai_filters.py  # Just one file
   ```

## Generated Reports

- **Duration Report**: Use `pytest --durations=N` to see N slowest tests
- **Coverage Report**: Use `pytest --cov` for coverage analysis
- **JUnit XML**: Use `pytest --junitxml` for CI integration
- **HTML Report**: Use `pytest-html` plugin for visual reports

---

**Last Updated**: Generated from test run statistics
**Test Framework**: pytest 8.4.2
**Python Version**: 3.13.7
