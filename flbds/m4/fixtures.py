"""flbds/m4/fixtures.py
Hand-Built Biological Mechanism Fixtures for Benchmark Dev Cases (FLBDS v9 §4.3, §6.3).

IMPORTANT AUDIT REQUIREMENT:
Source cards for the 4 dev organisms do NOT exist in the pilot silver card set.
These cards are hand-crafted benchmark fixtures and are labeled FIXTURE throughout.
They MUST NOT be referred to as 'extracted'.
"""

from typing import Dict, Any, Tuple
from flbds.schema.enums import DirectionEnum, TimeModeEnum
from flbds.schema.sapphire import (
    Part,
    Organ,
    ResourceInput,
    PhysicalEffect,
    Phenomenon,
    StateChange,
    Action,
)
from flbds.m4.sapphire_graph import SapphireGraph


def build_dev_m1_fixture() -> Tuple[Dict[str, Any], SapphireGraph]:
    meta = {
        "card_id": "MC-BIO-DEV-M1-FIXTURE",
        "organism": "Loxodonta africana (African Elephant)",
        "name": "Elephant Mud-Wallowing Evaporative Storage",
        "tier": "FIXTURE",
        "provenance": "HAND_BUILT_FIXTURE_NOT_EXTRACTED",
        "consumable_inputs": ["liquid_water"],
        "target_direction": DirectionEnum.STORE_AND_RELEASE,
        "time_mode": TimeModeEnum.CYCLIC_DIURNAL,
        "regime_max_length_m": 0.05,
        "effects": ["latent_heat_of_vaporization"],
    }
    g = SapphireGraph(
        graph_id="GRAPH-DEV-M1-FIXTURE",
        description="Porous mud layer retains water which evaporates under solar irradiation absorbing latent heat.",
        parts={"part_01": Part(description="Cracked epidermis and porous mud coating")},
        organs={"organ_01": Organ(description="Micro-crevice capillary retention network")},
        inputs={"input_01": ResourceInput(input_type="material", name="liquid_water")},
        effects={"effect_01": PhysicalEffect(canonical_name="latent_heat_of_vaporization", governing_equation="Q = m * h_fg")},
        phenomena={"phenom_01": Phenomenon(description="Water vaporization from mud layer under daytime heat load")},
        state_changes={"state_01": StateChange(state_variable="thermal_energy", from_value="baseline", to_value="stabilised")},
        actions={"action_01": Action(verb="regulate", object="body_temperature", description="Buffer core body temperature under diurnal solar irradiation")},
    )
    g.add_edge("part_01", "organ_01", "creates")
    g.add_edge("organ_01", "effect_01", "co_activates")
    g.add_edge("input_01", "effect_01", "co_activates")
    g.add_edge("effect_01", "phenom_01", "creates")
    g.add_edge("phenom_01", "state_01", "creates")
    g.add_edge("state_01", "action_01", "interpreted_as")
    return meta, g


def build_dev_m2_fixture() -> Tuple[Dict[str, Any], SapphireGraph]:
    meta = {
        "card_id": "MC-BIO-DEV-M2-FIXTURE",
        "organism": "Aptenodytes forsteri (Emperor Penguin)",
        "name": "Avian Appendicular Countercurrent Retia",
        "tier": "FIXTURE",
        "provenance": "HAND_BUILT_FIXTURE_NOT_EXTRACTED",
        "consumable_inputs": [],
        "target_direction": DirectionEnum.TRANSPORT_DIRECTIONAL,
        "time_mode": TimeModeEnum.STEADY,
        "regime_max_length_m": 0.10,
        "effects": ["countercurrent_convective_heat_exchange"],
    }
    g = SapphireGraph(
        graph_id="GRAPH-DEV-M2-FIXTURE",
        description="Countercurrent blood vessel bundle transfers heat from warm arterial blood to cold venous return blood.",
        parts={"part_01": Part(description="Arterial and venous vascular networks in extremity")},
        organs={"organ_01": Organ(description="Closely opposed countercurrent microvascular plexus (rete mirabile)")},
        inputs={"input_01": ResourceInput(input_type="energy", name="arterial_thermal_energy")},
        effects={"effect_01": PhysicalEffect(canonical_name="countercurrent_convective_heat_exchange", governing_equation="q = epsilon * C_min * (T_hot - T_cold)")},
        phenomena={"phenom_01": Phenomenon(description="Inter-vessel conductive-convective heat transfer across thin vascular walls")},
        state_changes={"state_01": StateChange(state_variable="blood_temperature", from_value="warm", to_value="conserved")},
        actions={"action_01": Action(verb="transport", object="thermal_energy", description="Recover extremity heat and prevent core hypothermia")},
    )
    g.add_edge("part_01", "organ_01", "creates")
    g.add_edge("organ_01", "effect_01", "co_activates")
    g.add_edge("input_01", "effect_01", "co_activates")
    g.add_edge("effect_01", "phenom_01", "creates")
    g.add_edge("phenom_01", "state_01", "creates")
    g.add_edge("state_01", "action_01", "interpreted_as")
    return meta, g


def build_dev_m3_fixture() -> Tuple[Dict[str, Any], SapphireGraph]:
    meta = {
        "card_id": "MC-BIO-DEV-M3-FIXTURE",
        "organism": "Cataglyphis bombycina (Saharan Silver Ant)",
        "name": "Saharan Silver Ant Passive Radiative Rejection",
        "tier": "FIXTURE",
        "provenance": "HAND_BUILT_FIXTURE_NOT_EXTRACTED",
        "consumable_inputs": [],
        "target_direction": DirectionEnum.DECREASE,
        "time_mode": TimeModeEnum.STEADY,
        "regime_max_length_m": 0.02,
        "effects": ["selective_thermal_radiation_and_solar_reflection"],
    }
    g = SapphireGraph(
        graph_id="GRAPH-DEV-M3-FIXTURE",
        description="Triangular cross-section hairs provide high solar reflectance and high mid-infrared emissivity to outer space.",
        parts={"part_01": Part(description="Dense layer of dorsal cuticular hairs")},
        organs={"organ_01": Organ(description="Triangular micro-faceted hair cross-section geometry")},
        inputs={"input_01": ResourceInput(input_type="energy", name="ambient_solar_irradiance")},
        effects={"effect_01": PhysicalEffect(canonical_name="selective_thermal_radiation_and_solar_reflection", governing_equation="P_net = P_rad - P_atm - P_solar")},
        phenomena={"phenom_01": Phenomenon(description="Total internal reflection of solar wavelengths and emissive cooling through 8-13 um atmospheric window")},
        state_changes={"state_01": StateChange(state_variable="cuticle_temperature", from_value="sub_ambient", to_value="depressed")},
        actions={"action_01": Action(verb="dissipate", object="thermal_energy", description="Maintain body temperature below critical thermal maximum in desert")},
    )
    g.add_edge("part_01", "organ_01", "creates")
    g.add_edge("organ_01", "effect_01", "co_activates")
    g.add_edge("input_01", "effect_01", "co_activates")
    g.add_edge("effect_01", "phenom_01", "creates")
    g.add_edge("phenom_01", "state_01", "creates")
    g.add_edge("state_01", "action_01", "interpreted_as")
    return meta, g


def build_dev_m4_fixture() -> Tuple[Dict[str, Any], SapphireGraph]:
    meta = {
        "card_id": "MC-BIO-DEV-M4-FIXTURE",
        "organism": "Aphelocheirus aestivalis (Aquatic Plastron Bug)",
        "name": "Aphelocheirus Aestivalis Hydrophobic Plastron Gill",
        "tier": "FIXTURE",
        "provenance": "HAND_BUILT_FIXTURE_NOT_EXTRACTED",
        "consumable_inputs": [],
        "target_direction": DirectionEnum.TRANSPORT_DIRECTIONAL,
        "time_mode": TimeModeEnum.STEADY,
        "regime_max_length_m": 0.005,
        "effects": ["knudsen_fickian_gas_diffusion"],
    }
    g = SapphireGraph(
        graph_id="GRAPH-DEV-M4-FIXTURE",
        description="Hydrophobic micro-hairs support a persistent air plastron film allowing underwater oxygen diffusion without flooding.",
        parts={"part_01": Part(description="Hydrophobic cuticular micro-hair array")},
        organs={"organ_01": Organ(description="Sub-micron pore clearance plastron gill membrane")},
        inputs={"input_01": ResourceInput(input_type="material", name="dissolved_oxygen")},
        effects={"effect_01": PhysicalEffect(canonical_name="knudsen_fickian_gas_diffusion", governing_equation="J = D_eff * delta_C / L")},
        phenomena={"phenom_01": Phenomenon(description="Diffusion of dissolved oxygen across stable water-gas interface into spiracles")},
        state_changes={"state_01": StateChange(state_variable="oxygen_concentration", from_value="ambient", to_value="replenished")},
        actions={"action_01": Action(verb="transport", object="dissolved_gas", description="Enable continuous underwater respiration at shallow depth")},
    )
    g.add_edge("part_01", "organ_01", "creates")
    g.add_edge("organ_01", "effect_01", "co_activates")
    g.add_edge("input_01", "effect_01", "co_activates")
    g.add_edge("effect_01", "phenom_01", "creates")
    g.add_edge("phenom_01", "state_01", "creates")
    g.add_edge("state_01", "action_01", "interpreted_as")
    return meta, g


DEV_FIXTURES = {
    "DEV-M1": build_dev_m1_fixture,
    "DEV-M2": build_dev_m2_fixture,
    "DEV-M3": build_dev_m3_fixture,
    "DEV-M4": build_dev_m4_fixture,
}
