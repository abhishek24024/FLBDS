from flbds.reasoning.buckingham import BuckinghamAuditor, parse_dimension, find_dimensionless_groups

def test_parse_dimension():
    assert parse_dimension("M L^-1 T^-2") == {"M": 1, "L": -1, "T": -2}
    assert parse_dimension("L T^-1") == {"L": 1, "T": -1}
    assert parse_dimension("") == {}

def test_buckingham_nullspace_groups():
    vars_fluid = [("rho", "M L^-3"), ("v", "L T^-1"), ("L", "L"), ("mu", "M L^-1 T^-1")]
    groups = find_dimensionless_groups(vars_fluid)
    assert len(groups) == 1

def test_scale_auditor_violation():
    auditor = BuckinghamAuditor()
    bio = {"h": 50.0, "L_c": 0.005, "k_s": 50.0}
    eng = {"h": 50.0, "L_c": 1.0, "k_s": 50.0}
    report = auditor.audit_effect("fourier_conduction", bio, eng, length_scale_ratio=200.0)
    assert report.has_violations
    assert report.v_scale_total > 0
    assert "Thermal trapping" in report.group_results[0].recommendation

def test_exergy_check():
    auditor = BuckinghamAuditor()
    valid, edot, ideality = auditor.audit_exergy(t0=300.0, sigma_gen=0.5, action_utility=10.0, exergy_cost=2.0)
    assert valid
    assert edot == 150.0
    assert ideality == 5.0
