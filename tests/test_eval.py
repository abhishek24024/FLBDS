from flbds.eval.benchmark import BenchmarkRunner

def test_benchmark_runner_all_families_pass():
    runner = BenchmarkRunner()
    report = runner.run_all()
    assert report.total_families == 5
    assert report.passed_families == 5
    assert report.overall_pass
    assert len(report.results) == 5
    for res in report.results:
        assert res.passed, f"Benchmark failed: {res.family_name}"
