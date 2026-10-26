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


class TestMechanismCard:
    @pytest.fixture
    def valid_bio_card_data(self):
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
