from flbds.knowledge.triz import TrizKnowledge

def test_triz_spine_loading():
    triz = TrizKnowledge()
    assert len(triz.all_parameters()) == 39
    assert len(triz.all_principles()) == 40
    assert len(triz.separations()) >= 4

def test_principles_lookup_acceptance():
    triz = TrizKnowledge()
    # Acceptance criteria from docs/PHASES.md
    principles = triz.principles_for(14, 21)
    assert principles == [10, 26, 28, 35]

def test_lexical_parameter_matcher():
    triz = TrizKnowledge()
    matches = triz.match_parameter("aerodynamic drag reduction speed")
    assert len(matches) > 0
    top_param, score = matches[0]
    assert top_param.id in (9, 21, 29) # Speed, Power, Manufacturing precision
