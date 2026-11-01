"""Tests for FLBDS Pydantic v2 schemas: MechanismCard, ProblemCard, RoleBinding, VerificationReport."""

import json
import pytest
from pydantic import ValidationError

from flbds.schema import (
    Action,
    AssertionResult,
    Constraint,
    Contradiction,
    Context,
    EnvironmentSpec,
    EvidenceSpan,
    MechanismCard,
    Organ,
    Part,
    Phenomenon,
    PhysicsCheck,
    PhysicalEffect,
    ProblemCard,
    Quantity,
    RequiredFunction,
    ResourceInput,
    RoleBinding,
    StateChange,
    Subject,
    SystemSpec,
    TimePattern,
    VerificationReport,
)


class TestEvidenceSpan:
    def test_valid_evidence_span(self):
        span = EvidenceSpan(
            source_doc_id="PMC123456",
            text_span="The mud layer delays skin temperature rise by 2 hours.",
            char_start=120,
            char_end=176,
            figure_roi="Fig 3B",
            citation="Author et al. 2020, J Therm Biol",
        )
        assert span.char_start == 120
        assert span.char_end == 176
        assert span.source_doc_id == "PMC123456"

    def test_invalid_offsets_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            EvidenceSpan(
                source_doc_id="PMC123456",
                text_span="Invalid offset text",
                char_start=200,
                char_end=150,  # char_end < char_start
            )
        assert "char_end" in str(exc_info.value)


class TestQuantity:
    def test_valid_pint_units(self):
        q1 = Quantity(name="thermal_diffusivity", value=1e-7, unit="m^2 / s", regime_of_validity="at 30 degC")
        q2 = Quantity(name="latent_heat", value=2.4e6, unit="J / kg")
        q3 = Quantity(name="areal_mass", value=28.8, unit="kg / m^2")
        q4 = Quantity(name="thermal_conductivity", value=0.6, unit="W / (m * K)")

        assert q1.value == 1e-7
        assert q2.unit == "J / kg"
        assert q3.value == 28.8
        assert q4.name == "thermal_conductivity"

    def test_invalid_unit_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            Quantity(name="bad_quantity", value=100.0, unit="completely_fake_unit_xyz_123")
        assert "Unparseable or invalid unit string" in str(exc_info.value)


@pytest.fixture
def valid_bio_card_data():
    return {
        "card_id": "MC-BIO-0001",
        "domain": "bio",
        "subject": {
            "name": "Loxodonta africana",
            "identifier": "NCBI:txid9813",
        },
        "context": {
            "environment": "African savanna, high diurnal solar load",
            "scale": "macro (tonnes)",
            "regime": "sensible storage + latent evaporative boundary",
        },
        "action": {
            "verb": "regulate",
            "object": "body_temperature",
            "description": "Maintains core temperature within safe operating bounds under high solar insolation",
        },
        "state_change": {
            "state_variable": "skin_temperature",
            "from_value": "42 degC peak skin temp",
            "to_value": "35 degC evaporatively cooled",
            "magnitude": {
                "name": "temperature_drop",
                "value": 7.0,
                "unit": "delta_degC",
            },
        },
        "phenomenon": {
            "description": "Evaporation of retained water from mud crust absorbing latent heat of vaporization",
        },
        "effect": {
            "canonical_name": "latent_heat_of_vaporization",
            "governing_equation": "Q_evap = m_water * h_fg",
            "relevant_variables": ["latent_heat", "evaporation_rate", "surface_area"],
        },
        "inputs": [
            {
                "input_type": "material",
                "name": "liquid_water",
                "rate_or_quantity": {
                    "name": "water_mass",
                    "value": 50.0,
                    "unit": "kg",
                },
            },
            {
                "input_type": "energy",
                "name": "solar_radiation",
            },
        ],
        "organ": {
            "description": "Micro-channelled crevice skin morphology enhancing capillary fluid retention",
        },
        "part": {
            "description": "Epidermis, mud crust matrix, and body core thermal buffer",
        },
        "quantities": [
            {
                "name": "latent_heat",
                "value": 2.4e6,
                "unit": "J / kg",
            },
            {
                "name": "retention_time",
                "value": 26.0,
                "unit": "hour",
                "regime_of_validity": "in skin crevices vs flat surface",
            },
        ],
        "constraints_and_resources": ["requires periodic re-wetting with liquid water"],
        "evidence": [
            {
                "source_doc_id": "PMC_BIO_SAMPLE_001",
                "text_span": "Retention of mud in skin crevices delays dehydration for up to 26 hours.",
                "char_start": 450,
                "char_end": 526,
                "citation": "Physiol Zool 1987",
            }
        ],
        "license": "CC BY 4.0",
        "confidence": 0.92,
        "tier": "silver",
        "unsupported_fields": [],
    }


class TestMechanismCard:

    def test_valid_bio_card(self, valid_bio_card_data):
        card = MechanismCard(**valid_bio_card_data)
        assert card.card_id == "MC-BIO-0001"
        assert card.domain == "bio"
        assert card.tier == "silver"
        assert len(card.inputs) == 2
        assert card.action.verb == "regulate"

    def test_invalid_domain_raises(self, valid_bio_card_data):
        valid_bio_card_data["domain"] = "medical"  # invalid domain
        with pytest.raises(ValidationError):
            MechanismCard(**valid_bio_card_data)

    def test_gold_tier_without_evidence_raises(self, valid_bio_card_data):
        valid_bio_card_data["tier"] = "gold"
        valid_bio_card_data["evidence"] = []
        with pytest.raises(ValidationError) as exc_info:
            MechanismCard(**valid_bio_card_data)
        assert "Gold tier cards must include supporting evidence" in str(exc_info.value)

    def test_empty_license_raises(self, valid_bio_card_data):
        valid_bio_card_data["license"] = ""
        with pytest.raises(ValidationError):
            MechanismCard(**valid_bio_card_data)

    def test_unsupported_fields_tracking(self, valid_bio_card_data):
        valid_bio_card_data["organ"] = None
        valid_bio_card_data["unsupported_fields"] = ["organ"]
        card = MechanismCard(**valid_bio_card_data)
        assert card.organ is None
        assert "organ" in card.unsupported_fields


class TestProblemCard:
    def test_valid_problem_card(self):
        card = ProblemCard(
            problem_id="PROB-WALL-001",
            system=SystemSpec(
                name="Desert shelter thermal storage wall panel",
                components=["exterior facade", "thermal buffer core", "interior comfort surface"],
                scale="building facade (approx 20 m^2)",
            ),
            environment=EnvironmentSpec(
                climate="Hot arid desert, large diurnal temperature swing",
                temperature_range=(12.0, 45.0),
                radiation="Intense daytime direct solar; clear nocturnal radiative sky",
                fluids_available=["ambient dry air"],
                energy_available=["solar insolation", "night radiative cooling"],
                resources_absent=["liquid water", "grid electricity"],
            ),
            required_function=RequiredFunction(
                action="store",
                target_object="thermal_energy",
                state_variable="wall_heat_flux",
                target_change="absorb heat by day and release heat into interior at night",
            ),
            time_pattern=TimePattern(
                cycle_type="diurnal",
                period_hours=24.0,
                phases=["charging_8h_day", "discharging_12h_night"],
            ),
            constraints=[
                Constraint(variable="water_consumption", bound="== 0 kg/cycle", hard_or_soft="hard"),
                Constraint(variable="mass_per_area", bound="<= 40 kg/m^2", hard_or_soft="soft"),
            ],
            contradictions=[
                Contradiction(
                    improving_parameter="heat_storage_capacity",
                    worsening_parameter="structural_mass",
                    triz_parameters=["Thermal capacity vs Mass of stationary object"],
                )
            ],
            evidence=["Design brief: off-grid desert shelter climate control specifications"],
            confidence=0.98,
        )
        assert card.problem_id == "PROB-WALL-001"
        assert card.environment.resources_absent == ["liquid water", "grid electricity"]
        assert len(card.constraints) == 2


class TestRoleBinding:
    def test_valid_role_bindings(self):
        # T1: Loop closing
        rb_t1 = RoleBinding(
            binding_id="RB-001",
            source_role="Input: liquid water (open evaporative loss)",
            target_role="Working fluid in sealed regeneration loop",
            relation="transformed",
            operator="T1",
            reason="Liquid water is absent in desert target environment; open flow must be sealed into closed loop.",
            proof_obligations=["mass_closure_cycle", "leakage_loss_budget"],
        )
        assert rb_t1.operator == "T1"
        assert len(rb_t1.proof_obligations) == 2

        # T2: Flow inversion
        rb_t2 = RoleBinding(
            binding_id="RB-002",
            source_role="StateChange: reject heat to ambient",
            target_role="StateChange: store heat from ambient during day",
            relation="transformed",
            operator="T2",
            reason="Target requires daytime heat absorption rather than continuous heat rejection.",
            proof_obligations=["energy_balance_sign_check"],
        )
        assert rb_t2.operator == "T2"

        # T3: Temporal phase shift
        rb_t3 = RoleBinding(
            binding_id="RB-003",
            source_role="Timing: unbuffered steady daytime rejection",
            target_role="Timing: 24h diurnal cycle with 8h charge and 12h discharge",
            relation="transformed",
            operator="T3",
            reason="Target has anti-phase diurnal cycle requiring temporal thermal capacitance.",
            proof_obligations=["cycle_closure", "phase_lag_conduction"],
        )
        assert rb_t3.operator == "T3"

        # T4: Mechanism substitution
        rb_t4 = RoleBinding(
            binding_id="RB-004",
            source_role="Effect: liquid water vaporization",
            target_role="Effect: solid-liquid phase change or sorption storage",
            relation="substituted",
            operator="T4",
            reason="Open liquid evaporation is infeasible without water supply; substitute with solid-liquid PCM.",
            proof_obligations=["pcm_enthalpy_sizing", "sensible_vs_latent_ratio"],
        )
        assert rb_t4.operator == "T4"


class TestVerificationReport:
    def test_valid_passed_report(self):
        check = PhysicsCheck(
            template_name="latent_heat_storage_sizing",
            inputs={"heat_flux_W_m2": 200.0, "charge_hours": 8.0, "latent_heat_kJ_kg": 200.0},
            results={"energy_stored_MJ_m2": 5.76, "required_mass_kg_m2": 28.8, "thickness_mm": 36.0},
            assertions=[
                AssertionResult(
                    assertion_name="energy_closure",
                    passed=True,
                    message="Total energy absorbed equals latent enthalpy change (5.76 MJ/m^2).",
                ),
                AssertionResult(
                    assertion_name="mass_limit",
                    passed=True,
                    message="Required mass 28.8 kg/m^2 satisfies <= 40 kg/m^2 soft constraint.",
                ),
            ],
            verdict="pass",
        )
        report = VerificationReport(
            concept_id="CONCEPT-WALL-PCM-01",
            checks=[check],
            feasible_set={"thickness_m": (0.03, 0.045), "mass_kg_m2": (24.0, 36.0)},
            unmodelled_effects=[],
            overall_verdict="pass",
        )
        assert report.overall_verdict == "pass"
        assert len(report.checks) == 1

    def test_overall_verdict_cannot_pass_if_check_fails(self):
        failed_check = PhysicsCheck(
            template_name="mass_conservation",
            inputs={"inflow_kg": 10.0, "outflow_kg": 5.0},
            results={"deficit_kg": 5.0},
            assertions=[
                AssertionResult(
                    assertion_name="mass_closure",
                    passed=False,
                    message="Mass imbalance detected: 5.0 kg unaccounted for.",
                )
            ],
            verdict="fail",
        )
        with pytest.raises(ValidationError) as exc_info:
            VerificationReport(
                concept_id="CONCEPT-FAIL-01",
                checks=[failed_check],
                feasible_set={},
                unmodelled_effects=[],
                overall_verdict="pass",  # Invalid: check failed
            )
        assert "Overall verdict cannot be 'pass' when one or more individual checks fail" in str(exc_info.value)

    def test_overall_verdict_cannot_pass_with_unmodelled_effects(self):
        check = PhysicsCheck(
            template_name="conduction_1d",
            inputs={},
            results={},
            assertions=[
                AssertionResult(assertion_name="conduction_check", passed=True, message="Conduction ok")
            ],
            verdict="pass",
        )
        with pytest.raises(ValidationError) as exc_info:
            VerificationReport(
                concept_id="CONCEPT-UNMODELLED-01",
                checks=[check],
                feasible_set={},
                unmodelled_effects=["complex_multiphase_flow_in_porous_matrix"],
                overall_verdict="pass",  # Invalid: cannot claim pass with unmodelled effects
            )
        assert "Overall verdict cannot be 'pass' when there are unmodelled effects" in str(exc_info.value)


class TestSerializationRoundtrip:
    def test_json_roundtrip_mechanism_card(self):
        card = MechanismCard(
            card_id="MC-ENG-0010",
            domain="eng",
            subject=Subject(name="Heat Pipe Heat Exchanger", identifier="CPC:F28D15/02"),
            context=Context(environment="Industrial waste heat recovery", scale="1-5 m", regime="two-phase capillary"),
            action=Action(verb="transfer", object="thermal_energy", description="Transfers heat with minimal Delta T"),
            state_change=StateChange(state_variable="working_fluid_phase", from_value="liquid", to_value="vapor"),
            phenomenon=Phenomenon(description="Evaporation at evaporator followed by capillary pumping in wick"),
            effect=PhysicalEffect(canonical_name="latent_heat_and_capillary_pumping"),
            inputs=[ResourceInput(input_type="energy", name="waste_heat_source")],
            quantities=[
                Quantity(name="effective_thermal_conductivity", value=50000.0, unit="W / (m * K)"),
                Quantity(name="operating_temperature", value=150.0, unit="degC"),
            ],
            evidence=[
                EvidenceSpan(
                    source_doc_id="US_PATENT_9876543",
                    text_span="The heat pipe demonstrates an effective thermal conductivity exceeding 50,000 W/m-K.",
                    char_start=1020,
                    char_end=1115,
                    citation="US Patent 9,876,543 B2",
                )
            ],
            license="US Patent Public Domain",
            confidence=0.95,
            tier="silver",
            unsupported_fields=[],
        )

        json_str = card.model_dump_json()
        data = json.loads(json_str)
        assert data["card_id"] == "MC-ENG-0010"
        assert data["domain"] == "eng"

        reconstructed = MechanismCard.model_validate_json(json_str)
        assert reconstructed.card_id == card.card_id
        assert reconstructed.quantities[0].value == 50000.0
        assert reconstructed.quantities[0].unit == "W / (m * K)"
        assert reconstructed.evidence[0].source_doc_id == "US_PATENT_9876543"


class TestV9SchemaAdditions:
    def test_enums_and_poiseuille_numbers(self):
        from flbds.schema import (
            BoundaryTypeEnum,
            DirectionEnum,
            DuctCrossSectionEnum,
            HazardEnum,
            ResourceEnum,
            TemplateEnum,
            TimeModeEnum,
        )

        assert ResourceEnum.LIQUID_WATER.value == "liquid_water"
        assert HazardEnum.DUST_FOULING.value == "dust_fouling"
        assert DirectionEnum.STORE_AND_RELEASE.value == "store-and-release"
        assert BoundaryTypeEnum.BC_FLUX.value == "BC_FLUX"
        assert BoundaryTypeEnum.BC_TEMP.value == "BC_TEMP"
        assert DuctCrossSectionEnum.CIRCULAR.poiseuille_number == 64.0
        assert DuctCrossSectionEnum.PARALLEL_PLATES.poiseuille_number == 96.0
        assert TemplateEnum.TPL_02.value == "TPL_02"

    def test_problem_card_no_template_leakage(self):
        from flbds.schema import (
            BoundaryTypeEnum,
            EnvironmentSpec,
            HardConstraints,
            HazardEnum,
            ProblemCard,
            RequiredFunction,
            ResourceEnum,
            SystemSpec,
            TimeModeEnum,
            TimePattern,
        )

        # Valid card with typed constraints and no template names
        card = ProblemCard(
            problem_id="PROB-V9-001",
            system=SystemSpec(name="Passive thermal envelope", scale="macro"),
            environment=EnvironmentSpec(
                climate="Desert",
                resources_absent=[ResourceEnum.LIQUID_WATER],
                hazards=[HazardEnum.HIGH_HUMIDITY],
            ),
            required_function=RequiredFunction(
                action="buffer",
                target_object="thermal_flux",
                state_variable="wall_temperature",
                target_change="absorb heat by day",
                boundary_type=BoundaryTypeEnum.BC_FLUX,
                flux_or_load=200.0,
            ),
            time_pattern=TimePattern(cycle_type="diurnal", time_mode=TimeModeEnum.CYCLIC_DIURNAL),
            hard_constraints=HardConstraints(
                max_thickness_m=0.05,
                max_mass_kg_m2=45.0,
                max_surface_superheat_K=10.0,
            ),
        )
        assert card.hard_constraints.max_thickness_m == 0.05

        # Template leakage raises ValidationError
        with pytest.raises(ValidationError) as exc:
            ProblemCard(
                problem_id="PROB-BAD",
                system=SystemSpec(name="Bad System"),
                environment=EnvironmentSpec(climate="Desert"),
                required_function=RequiredFunction(
                    action="cool",
                    target_object="air",
                    state_variable="T",
                    target_change="use TPL_02 for latent cooling",  # Leaks template name!
                ),
                time_pattern=TimePattern(cycle_type="steady"),
            )
        assert "Template leakage detected" in str(exc.value)

    def test_ground_truth_eval_acceptable_templates_list(self):
        from flbds.schema import GroundTruthEval, TemplateEnum

        eval_spec = GroundTruthEval(
            case_id="DEV-M1-S2",
            source_card_id="MC-BIO-ELEPHANT",
            cluster="DEV-M1",
            split=2,
            expected_conflicts=["resource", "direction", "timing", "effect"],
            expected_operators=["T1", "T2", "T3", "T4", "T5"],
            acceptable_templates=[TemplateEnum.TPL_02, TemplateEnum.TPL_04],
            reference_design_file="ref_dev_m1_s2.json",
        )
        assert len(eval_spec.acceptable_templates) == 2
        assert TemplateEnum.TPL_02 in eval_spec.acceptable_templates

    def test_role_binding_node_ids_citation(self):
        from flbds.schema import RoleBinding

        rb = RoleBinding(
            source_node="organ_crevice_matrix",
            target_node="porous_aluminum_foam",
            relation="transformed",
            operator="T5",
            justification="Rescales effective thermal conductivity to keep Fo in range",
            source_card_node_ids=["MC-BIO-0001:organ", "MC-BIO-0001:effect"],
        )
        assert rb.operator == "T5"
        assert len(rb.source_card_node_ids) == 2

    def test_discriminated_union_template_parameters(self):
        from pydantic import TypeAdapter
        from flbds.schema import TPL01Params, TPL02Params, TemplateEnum, TemplateParameters

        adapter = TypeAdapter(TemplateParameters)

        # Deserialize TPL-02
        raw_tpl02 = {
            "template_id": "TPL_02",
            "thickness_m": 0.04,
            "pcm_density_kg_m3": 820.0,
            "pcm_latent_heat_J_kg": 210000.0,
            "matrix_volume_fraction": 0.12,
            "matrix_density_kg_m3": 2700.0,
            "k_eff_W_mK": 2.8,
            "melting_temp_degC": 28.0,
            "superheat_limit_K": 10.0,
            "heat_flux_W_m2": 200.0,
            "charge_hours": 8.0,
            "required_energy_J_m2": 5.76e6,
        }
        parsed_02 = adapter.validate_python(raw_tpl02)
        assert isinstance(parsed_02, TPL02Params)
        assert parsed_02.template_id == TemplateEnum.TPL_02
        assert parsed_02.k_eff_W_mK == 2.8

        # Deserialize TPL-01
        raw_tpl01 = {
            "template_id": "TPL_01",
            "thickness_m": 0.2,
            "density_kg_m3": 2400.0,
            "specific_heat_J_kgK": 1000.0,
            "thermal_conductivity_W_mK": 1.5,
            "required_energy_J_m2": 2.0e6,
            "period_hours": 24.0,
        }
        parsed_01 = adapter.validate_python(raw_tpl01)
        assert isinstance(parsed_01, TPL01Params)
        assert parsed_01.density_kg_m3 == 2400.0

    def test_mechanism_card_v9_additions(self, valid_bio_card_data):
        from flbds.schema import AbstractionLadder, MechanismCard

        valid_bio_card_data["abstraction_ladder"] = AbstractionLadder(
            L0_specimen="African elephant wallowing in mud",
            L1_mechanism="Porous mud retains water; evaporation absorbs latent heat; body mass buffers swing",
            L2_causal_chain="SAPPhIRE causal graph with mud crust and capillary retention",
            L3_solution_neutral_principle="Porous matrix holds working fluid; phase change absorbs heat; thermal mass damps cycle",
            L4_function="Keep body below temperature limit under diurnal heat load",
        ).model_dump()
        valid_bio_card_data["figure_regions"] = ["Fig 2A [100, 200, 400, 500]"]
        valid_bio_card_data["human_verified"] = False
        valid_bio_card_data["extraction_agreement"] = 0.85
        valid_bio_card_data["purpose_embedding"] = [0.1, 0.2, 0.3]
        valid_bio_card_data["mechanism_embedding"] = [0.4, 0.5, 0.6]
        valid_bio_card_data["effect_embedding"] = [0.7, 0.8, 0.9]

        card = MechanismCard(**valid_bio_card_data)
        assert card.abstraction_ladder.L0_specimen == "African elephant wallowing in mud"
        assert card.extraction_agreement == 0.85
        assert card.figure_regions == ["Fig 2A [100, 200, 400, 500]"]
        assert len(card.purpose_embedding) == 3
