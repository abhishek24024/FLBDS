from flbds.knowledge.physics import PhysicalLawsCatalog

def test_physics_catalog_loading():
    cat = PhysicalLawsCatalog()
    assert len(cat.all_laws()) >= 9
    assert len(cat.all_groups()) >= 4

def test_dimensionless_group_exponents_acceptance():
    cat = PhysicalLawsCatalog()
    # Acceptance criteria from docs/PHASES.md: length exponents (1, 1, 2, 1)
    assert cat.get_group("Re").length_exponent == 1
    assert cat.get_group("Bi").length_exponent == 1
    assert cat.get_group("Bo").length_exponent == 2
    assert cat.get_group("Pi_g").length_exponent == 1
