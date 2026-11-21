"""V11 engineering problem library (contract: docs/v11/INTERFACES.md section 2).

Env values are SI and use the env_space names of every plausible card (superset dict).
Statements deliberately contain no biology and no card ids.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Problem:
    id: str
    domain: str
    title: str
    statement: str
    env: dict[str, float]
    plausible_cards: list[str]
    source: str


RAD, PCM, HX = "THM_RADIATIVE_COOLING", "THM_PCM_STORAGE", "THM_COUNTERCURRENT_HX"
HC, LAT = "STR_SANDWICH_HONEYCOMB", "STR_LATTICE_TRUSS"
RIB, ADH, SH = "FLD_RIBLET_DRAG", "ADH_FIBRILLAR", "WET_SUPERHYDROPHOBIC"
BRAGG, FOG, MEM = (
    "OPT_BRAGG_STRUCTURAL_COLOR",
    "MT_FOG_HARVEST_MESH",
    "MT_PLASTRON_MEMBRANE",
)


def _roof(
    g: float,
    t_amb: float,
    sky_dep: float,
    t_in: float,
    h: float,
    leak: float,
    net: float,
    th: float,
    mass: float,
) -> dict[str, float]:
    return {
        "solar_irradiance_W_m2": g,
        "T_ambient_degC": t_amb,
        "T_sky_degC": t_amb - sky_dep,
        "T_inner_degC": t_in,
        "h_conv_W_m2K": h,
        "max_inner_leakage_W_m2": leak,
        "required_net_cooling_W_m2": net,
        "thickness_max_m": th,
        "mass_cap_kg_m2": mass,
    }


def _pcm(q: float, hours: float, frac: float, superheat: float) -> dict[str, float]:
    return {
        "heat_flux_W_m2": q,
        "charge_hours": hours,
        "required_energy_J_m2": q * hours * 3600.0 * frac,
        "superheat_limit_K": superheat,
    }


def _panel(
    span: float,
    width: float,
    load: float,
    k: float,
    mass: float,
    th: float,
    face: str,
    foil: float,
    strut: float,
) -> dict[str, float]:
    faces = {
        "cfrp": (60.0e9, 600.0e6, 1550.0),
        "al2024": (72.0e9, 320.0e6, 2780.0),
        "gfrp": (25.0e9, 350.0e6, 1900.0),
    }
    e_f, s_f, r_f = faces[face]
    return {
        "span_m": span,
        "width_m": width,
        "design_load_N": load,
        "stiffness_min_N_m": k,
        "areal_mass_cap_kg_m2": mass,
        "thickness_cap_m": th,
        "face_modulus_Pa": e_f,
        "face_strength_Pa": s_f,
        "face_density_kg_m3": r_f,
        "min_foil_thickness_m": foil,
        "min_strut_diameter_m": strut,
    }


PROBLEMS: list[Problem] = [
    # ---------------- thermal ----------------
    Problem(
        "P-THM-01",
        "thermal",
        "Passive roof skin for a desert telecom cabinet",
        "Keep an outdoor telecom/battery cabinet roof from loading heat into the enclosure under full sun "
        "without power: limit heat leaking inward and either reject or buffer the daytime solar load.",
        {
            **_roof(900.0, 42.0, 22.0, 32.0, 8.0, 40.0, 20.0, 0.05, 20.0),
            **_pcm(150.0, 6.0, 0.95, 10.0),
        },
        [RAD, PCM],
        "ETSI EN 300 019-1-4 (outdoor equipment climatic class); Raman et al. 2014 Nature",
    ),
    Problem(
        "P-THM-02",
        "thermal",
        "Off-grid vaccine store roof panel",
        "A solar-direct-drive vaccine store in a hot climate needs a roof panel that keeps its internal "
        "heat gain small through the day with no electrical cooling budget for the roof.",
        {
            **_roof(1000.0, 38.0, 25.0, 30.0, 6.0, 25.0, 30.0, 0.06, 10.0),
            **_pcm(120.0, 8.0, 0.9, 8.0),
        },
        [RAD, PCM],
        "WHO PQS E003 (refrigerators/freezers for vaccine storage) performance specification",
    ),
    Problem(
        "P-THM-03",
        "thermal",
        "Lightweight roof/wall liner for a humid-tropics relief shelter",
        "Damp the afternoon heat load through a lightweight shelter envelope in a hot, humid (hazy-sky) climate, "
        "with tight mass and thickness limits for transport.",
        {
            **_roof(750.0, 34.0, 8.0, 30.0, 10.0, 50.0, 40.0, 0.04, 30.0),
            **_pcm(180.0, 5.0, 0.95, 12.0),
        },
        [PCM, RAD],
        "UNHCR Shelter Design Catalogue (2016); Mehling & Cabeza 2008 (PCM building envelopes)",
    ),
    Problem(
        "P-THM-04",
        "thermal",
        "Data-centre liquid-loop heat recuperator",
        "Recover heat from a warm rack-cooling water loop into a cold make-up water stream within a "
        "compact length and a pump pressure budget.",
        {
            "required_duty_W": 2000.0,
            "T_cold_in_degC": 18.0,
            "T_hot_in_degC": 45.0,
            "max_pressure_drop_Pa": 1000.0,
            "length_cap_m": 1.0,
        },
        [HX],
        "ASHRAE TC 9.9 Liquid Cooling Guidelines for Datacom Equipment Centers (W32/W45 classes)",
    ),
    Problem(
        "P-THM-05",
        "thermal",
        "Avionics coolant heat-recovery core",
        "Transfer heat between two liquid coolant loops of an avionics bay with a short exchanger and low "
        "pressure drop.",
        {
            "required_duty_W": 800.0,
            "T_cold_in_degC": 15.0,
            "T_hot_in_degC": 40.0,
            "max_pressure_drop_Pa": 400.0,
            "length_cap_m": 0.6,
        },
        [HX],
        "SAE AIR1277 (cooling of airborne electronic equipment); Shah & Sekulic 2003",
    ),
    # ---------------- structures ----------------
    Problem(
        "P-STR-01",
        "structures",
        "Floor panel for a delivery drone payload bay",
        "A drone payload-bay floor must carry a parcel point load stiffly while adding as little mass as "
        "possible and staying thin.",
        _panel(0.40, 0.20, 300.0, 2.0e5, 2.5, 0.015, "cfrp", 2.5e-5, 3.0e-4),
        [HC, LAT],
        "ASTM C393 / D7250 sandwich beam flexure; drone airframe practice (CFRP sandwich floors)",
    ),
    Problem(
        "P-STR-02",
        "structures",
        "Satellite equipment mounting panel",
        "A spacecraft equipment panel must be stiff and strong under launch-equivalent point loads with a "
        "strict areal-mass budget.",
        _panel(1.00, 0.50, 2000.0, 5.0e5, 4.0, 0.04, "al2024", 2.5e-5, 3.0e-4),
        [HC, LAT],
        "ECSS-E-HB-32-24A Buckling of structures handbook; NASA SP-8007; Hexcel HexWeb design guide",
    ),
    Problem(
        "P-STR-03",
        "structures",
        "Aircraft cabin floor panel",
        "A passenger-cabin floor panel must survive concentrated heel loads and meet deflection limits at "
        "minimum weight within a ~10 mm build height.",
        _panel(0.50, 0.30, 4000.0, 4.0e5, 4.0, 0.0127, "cfrp", 2.5e-5, 3.0e-4),
        [HC, LAT],
        "Airbus AITM / Boeing BMS 4-20 floor panel specs (heel load, flexure); ASTM C393",
    ),
    # ---------------- fluids ----------------
    Problem(
        "P-FLD-01",
        "fluids",
        "Skin-friction reduction film for a long-haul airliner fuselage",
        "Reduce turbulent skin-friction drag on a cruising airliner fuselage with a passive film that "
        "can be manufactured by micro-replication.",
        {
            "flow_velocity_m_s": 250.0,
            "kinematic_viscosity_m2_s": 3.5e-5,
            "reference_length_m": 20.0,
            "target_drag_reduction_pct": 2.0,
            "min_feature_m": 3.0e-5,
        },
        [RIB],
        "Lufthansa Technik/BASF AeroSHARK riblet film (2022); Bechert et al. 1997",
    ),
    Problem(
        "P-FLD-02",
        "fluids",
        "Hull drag reduction for a container ship",
        "Lower frictional resistance of a container-ship hull at service speed with a passive surface "
        "treatment.",
        {
            "flow_velocity_m_s": 10.0,
            "kinematic_viscosity_m2_s": 1.05e-6,
            "reference_length_m": 50.0,
            "target_drag_reduction_pct": 3.0,
            "min_feature_m": 2.0e-5,
        },
        [RIB],
        "IMO EEXI/CII energy-efficiency regulations; Dean & Bhushan 2010 review",
    ),
    Problem(
        "P-FLD-03",
        "fluids",
        "Wind-turbine blade surface drag reduction",
        "Reduce skin-friction drag on the outer span of a wind-turbine blade to raise aerodynamic "
        "efficiency.",
        {
            "flow_velocity_m_s": 70.0,
            "kinematic_viscosity_m2_s": 1.5e-5,
            "reference_length_m": 1.5,
            "target_drag_reduction_pct": 4.0,
            "min_feature_m": 3.0e-5,
        },
        [RIB],
        "IEC 61400-1 design conditions; Sareen et al. 2014 Wind Energy (riblet tests on DU 96-W-180)",
    ),
    # ---------------- adhesion ----------------
    Problem(
        "P-ADH-01",
        "adhesion",
        "Glass-facade climbing inspection robot pads",
        "A small inspection robot must hold onto smooth glass facades without suction or power using "
        "reusable dry pads and low engagement force.",
        {
            "required_adhesion_pressure_Pa": 2.0e4,
            "work_of_adhesion_J_m2": 0.05,
            "max_preload_pressure_Pa": 5.0e3,
            "surface_roughness_amplitude_m": 5.0e-8,
            "min_feature_m": 2.0e-6,
        },
        [ADH],
        "Menon & Sitti 2006; Stickybot (Kim et al. 2008 IEEE T-RO)",
    ),
    Problem(
        "P-ADH-02",
        "adhesion",
        "Residue-free gripper for wafers and display glass",
        "Pick and place silicon wafers / display glass in a cleanroom without vacuum and without leaving "
        "residue, releasing by peeling.",
        {
            "required_adhesion_pressure_Pa": 5.0e3,
            "work_of_adhesion_J_m2": 0.05,
            "max_preload_pressure_Pa": 1.0e4,
            "surface_roughness_amplitude_m": 1.0e-8,
            "min_feature_m": 1.0e-6,
        },
        [ADH],
        "SEMI E15 / cleanroom handling; Song et al. 2017 (gecko-inspired micro-transfer printing)",
    ),
    Problem(
        "P-ADH-03",
        "adhesion",
        "Grasping pads for spacecraft servicing",
        "Grip painted/composite spacecraft surfaces in vacuum (no suction, no tape residue) with very low "
        "preload to avoid pushing the target away.",
        {
            "required_adhesion_pressure_Pa": 2.0e3,
            "work_of_adhesion_J_m2": 0.03,
            "max_preload_pressure_Pa": 2.0e3,
            "surface_roughness_amplitude_m": 2.0e-6,
            "min_feature_m": 1.0e-5,
        },
        [ADH],
        "Jiang et al. 2017 Science Robotics (gecko gripper for space, NASA JPL)",
    ),
    # ---------------- wetting ----------------
    Problem(
        "P-WET-01",
        "wetting",
        "Self-cleaning cover glass for desert PV modules",
        "Make PV cover-glass shed rain and dew droplets (carrying dust) instead of wetting, and stay "
        "non-wetting under raindrop impact.",
        {
            "target_apparent_angle_deg": 150.0,
            "droplet_impact_speed_m_s": 6.5,
            "droplet_diameter_m": 2.0e-3,
            "hydrostatic_head_m": 0.0,
            "min_feature_m": 5.0e-7,
            "min_solid_fraction": 0.05,
        },
        [SH],
        "IEC 61215 (PV module qualification); Nayshevsky et al. 2019 IEEE J. Photovolt. (anti-soiling)",
    ),
    Problem(
        "P-WET-02",
        "wetting",
        "Rain-shedding antenna radome",
        "Prevent a water film forming on a 5G/radar radome in rain (water films attenuate the signal).",
        {
            "target_apparent_angle_deg": 145.0,
            "droplet_impact_speed_m_s": 4.0,
            "droplet_diameter_m": 1.5e-3,
            "hydrostatic_head_m": 0.0,
            "min_feature_m": 2.0e-6,
            "min_solid_fraction": 0.1,
        },
        [SH],
        "ITU-R P.838 rain attenuation; Anderson 1975 IEEE T-AP (radome wet-loss)",
    ),
    # ---------------- optics ----------------
    Problem(
        "P-OPT-01",
        "optics",
        "Pigment-free green security film",
        "A thin, dye-free film for banknote/brand security must reflect a saturated green colour.",
        {
            "target_wavelength_m": 5.3e-7,
            "wavelength_tolerance_m": 1.0e-8,
            "min_peak_reflectance": 0.6,
            "max_total_thickness_m": 2.0e-6,
            "max_bandwidth_m": 1.2e-7,
            "min_layer_thickness_m": 3.0e-8,
            "incident_index": 1.0,
            "substrate_index": 1.65,
        },
        [BRAGG],
        "ISO 12931 (anti-counterfeiting authentication); 3M/Teijin multilayer polymer films",
    ),
    Problem(
        "P-OPT-02",
        "optics",
        "Fade-proof blue structural-colour coating",
        "A coating for outdoor products must show a bright blue that never fades (no pigment) and remain thin.",
        {
            "target_wavelength_m": 4.7e-7,
            "wavelength_tolerance_m": 1.0e-8,
            "min_peak_reflectance": 0.5,
            "max_total_thickness_m": 3.0e-6,
            "max_bandwidth_m": 8.0e-8,
            "min_layer_thickness_m": 3.0e-8,
            "incident_index": 1.0,
            "substrate_index": 1.5,
        },
        [BRAGG],
        "Kinoshita & Yoshioka 2005 review; Teijin MORPHOTEX fibre (product category)",
    ),
    Problem(
        "P-OPT-03",
        "optics",
        "Near-infrared heat-mirror window film",
        "A transparent window film must reflect near-infrared solar radiation around 1 um to cut "
        "solar heat gain.",
        {
            "target_wavelength_m": 1.0e-6,
            "wavelength_tolerance_m": 5.0e-8,
            "min_peak_reflectance": 0.9,
            "max_total_thickness_m": 5.0e-6,
            "max_bandwidth_m": 4.0e-7,
            "min_layer_thickness_m": 3.0e-8,
            "incident_index": 1.0,
            "substrate_index": 1.5,
        },
        [BRAGG],
        "ISO 9050 (glazing solar factor); 3M Prestige multilayer window film (product category)",
    ),
    # ---------------- mass transfer ----------------
    Problem(
        "P-MT-01",
        "mass_transfer",
        "Passive oxygen window for an underwater sensor",
        "A submerged instrument housing needs passive gas exchange through a membrane that never floods "
        "at its deployment depth.",
        {
            "required_flux_mol_m2_s": 0.005,
            "min_pore_diameter_m": 3.0e-8,
            "hydrostatic_head_m": 10.0,
            "delta_concentration_mol_m3": 5.0,
        },
        [MEM],
        "Flynn & Bush 2008 JFM; ocean-observing sensor housings (product category)",
    ),
    Problem(
        "P-MT-02",
        "mass_transfer",
        "Bubble-free aquaculture membrane aerator",
        "Supply oxygen into a fish tank across a gas-permeable hydrophobic membrane without bubbling or "
        "water breakthrough.",
        {
            "required_flux_mol_m2_s": 0.01,
            "min_pore_diameter_m": 2.0e-8,
            "hydrostatic_head_m": 3.0,
            "delta_concentration_mol_m3": 6.0,
        },
        [MEM],
        "Ahmed & Semmens 1992 J. Membr. Sci. (bubbleless membrane aeration)",
    ),
    Problem(
        "P-MT-03",
        "mass_transfer",
        "Fog-water collector for a mountain village",
        "Collect drinking water from advective fog for a village with a wind-rated frame of limited "
        "size and anchor capacity.",
        {
            "wind_speed_m_s": 5.0,
            "liquid_water_content_kg_m3": 3.0e-4,
            "droplet_diameter_m": 1.0e-5,
            "fog_hours_per_day": 8.0,
            "drainage_efficiency": 0.7,
            "target_yield_L_day": 350.0,
            "max_mesh_area_m2": 100.0,
            "design_wind_speed_m_s": 33.0,
            "max_wind_load_N": 6.0e4,
            "min_feature_m": 5.0e-5,
        },
        [FOG],
        "Dar Si Hmad / CloudFisher fog collectors (Morocco); Schemenauer & Cereceda 1994",
    ),
    Problem(
        "P-MT-04",
        "mass_transfer",
        "Fog irrigation for a coastal desert farm",
        "Irrigate a small coastal-desert plot from fog with a modest collector and a light frame.",
        {
            "wind_speed_m_s": 4.0,
            "liquid_water_content_kg_m3": 2.0e-4,
            "droplet_diameter_m": 1.2e-5,
            "fog_hours_per_day": 6.0,
            "drainage_efficiency": 0.6,
            "target_yield_L_day": 120.0,
            "max_mesh_area_m2": 60.0,
            "design_wind_speed_m_s": 25.0,
            "max_wind_load_N": 4.0e4,
            "min_feature_m": 5.0e-5,
        },
        [FOG],
        "Atacama camanchaca fog-collection projects (Cereceda et al. 2008 Atmos. Res.)",
    ),
]

PROBLEMS_BY_ID: dict[str, Problem] = {p.id: p for p in PROBLEMS}
