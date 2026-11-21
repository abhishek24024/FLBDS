# V11 engineering problem library (23 problems)

Each problem has numeric operating conditions/requirements (`env`) and the physics cards that could plausibly solve it. Mode B lets the model pick one of these; Mode A supplies one.

## P-THM-01 — Passive roof skin for a desert telecom cabinet

- **Domain:** thermal
- **Statement:** Keep an outdoor telecom/battery cabinet roof from loading heat into the enclosure under full sun without power: limit heat leaking inward and either reject or buffer the daytime solar load.
- **Plausible physics cards:** THM_RADIATIVE_COOLING, THM_PCM_STORAGE
- **Source:** ETSI EN 300 019-1-4 (outdoor equipment climatic class); Raman et al. 2014 Nature
- **Requirements / conditions:**
  - `solar_irradiance_W_m2` = 900
  - `T_ambient_degC` = 42
  - `T_sky_degC` = 20
  - `T_inner_degC` = 32
  - `h_conv_W_m2K` = 8
  - `max_inner_leakage_W_m2` = 40
  - `required_net_cooling_W_m2` = 20
  - `thickness_max_m` = 0.05
  - `mass_cap_kg_m2` = 20
  - `heat_flux_W_m2` = 150
  - `charge_hours` = 6
  - `required_energy_J_m2` = 3.078e+06
  - `superheat_limit_K` = 10

## P-THM-02 — Off-grid vaccine store roof panel

- **Domain:** thermal
- **Statement:** A solar-direct-drive vaccine store in a hot climate needs a roof panel that keeps its internal heat gain small through the day with no electrical cooling budget for the roof.
- **Plausible physics cards:** THM_RADIATIVE_COOLING, THM_PCM_STORAGE
- **Source:** WHO PQS E003 (refrigerators/freezers for vaccine storage) performance specification
- **Requirements / conditions:**
  - `solar_irradiance_W_m2` = 1000
  - `T_ambient_degC` = 38
  - `T_sky_degC` = 13
  - `T_inner_degC` = 30
  - `h_conv_W_m2K` = 6
  - `max_inner_leakage_W_m2` = 25
  - `required_net_cooling_W_m2` = 30
  - `thickness_max_m` = 0.06
  - `mass_cap_kg_m2` = 10
  - `heat_flux_W_m2` = 120
  - `charge_hours` = 8
  - `required_energy_J_m2` = 3.1104e+06
  - `superheat_limit_K` = 8

## P-THM-03 — Lightweight roof/wall liner for a humid-tropics relief shelter

- **Domain:** thermal
- **Statement:** Damp the afternoon heat load through a lightweight shelter envelope in a hot, humid (hazy-sky) climate, with tight mass and thickness limits for transport.
- **Plausible physics cards:** THM_PCM_STORAGE, THM_RADIATIVE_COOLING
- **Source:** UNHCR Shelter Design Catalogue (2016); Mehling & Cabeza 2008 (PCM building envelopes)
- **Requirements / conditions:**
  - `solar_irradiance_W_m2` = 750
  - `T_ambient_degC` = 34
  - `T_sky_degC` = 26
  - `T_inner_degC` = 30
  - `h_conv_W_m2K` = 10
  - `max_inner_leakage_W_m2` = 50
  - `required_net_cooling_W_m2` = 40
  - `thickness_max_m` = 0.04
  - `mass_cap_kg_m2` = 30
  - `heat_flux_W_m2` = 180
  - `charge_hours` = 5
  - `required_energy_J_m2` = 3.078e+06
  - `superheat_limit_K` = 12

## P-THM-04 — Data-centre liquid-loop heat recuperator

- **Domain:** thermal
- **Statement:** Recover heat from a warm rack-cooling water loop into a cold make-up water stream within a compact length and a pump pressure budget.
- **Plausible physics cards:** THM_COUNTERCURRENT_HX
- **Source:** ASHRAE TC 9.9 Liquid Cooling Guidelines for Datacom Equipment Centers (W32/W45 classes)
- **Requirements / conditions:**
  - `required_duty_W` = 2000
  - `T_cold_in_degC` = 18
  - `T_hot_in_degC` = 45
  - `max_pressure_drop_Pa` = 1000
  - `length_cap_m` = 1

## P-THM-05 — Avionics coolant heat-recovery core

- **Domain:** thermal
- **Statement:** Transfer heat between two liquid coolant loops of an avionics bay with a short exchanger and low pressure drop.
- **Plausible physics cards:** THM_COUNTERCURRENT_HX
- **Source:** SAE AIR1277 (cooling of airborne electronic equipment); Shah & Sekulic 2003
- **Requirements / conditions:**
  - `required_duty_W` = 800
  - `T_cold_in_degC` = 15
  - `T_hot_in_degC` = 40
  - `max_pressure_drop_Pa` = 400
  - `length_cap_m` = 0.6

## P-STR-01 — Floor panel for a delivery drone payload bay

- **Domain:** structures
- **Statement:** A drone payload-bay floor must carry a parcel point load stiffly while adding as little mass as possible and staying thin.
- **Plausible physics cards:** STR_SANDWICH_HONEYCOMB, STR_LATTICE_TRUSS
- **Source:** ASTM C393 / D7250 sandwich beam flexure; drone airframe practice (CFRP sandwich floors)
- **Requirements / conditions:**
  - `span_m` = 0.4
  - `width_m` = 0.2
  - `design_load_N` = 300
  - `stiffness_min_N_m` = 200000
  - `areal_mass_cap_kg_m2` = 2.5
  - `thickness_cap_m` = 0.015
  - `face_modulus_Pa` = 6e+10
  - `face_strength_Pa` = 6e+08
  - `face_density_kg_m3` = 1550
  - `min_foil_thickness_m` = 2.5e-05
  - `min_strut_diameter_m` = 0.0003

## P-STR-02 — Satellite equipment mounting panel

- **Domain:** structures
- **Statement:** A spacecraft equipment panel must be stiff and strong under launch-equivalent point loads with a strict areal-mass budget.
- **Plausible physics cards:** STR_SANDWICH_HONEYCOMB, STR_LATTICE_TRUSS
- **Source:** ECSS-E-HB-32-24A Buckling of structures handbook; NASA SP-8007; Hexcel HexWeb design guide
- **Requirements / conditions:**
  - `span_m` = 1
  - `width_m` = 0.5
  - `design_load_N` = 2000
  - `stiffness_min_N_m` = 500000
  - `areal_mass_cap_kg_m2` = 4
  - `thickness_cap_m` = 0.04
  - `face_modulus_Pa` = 7.2e+10
  - `face_strength_Pa` = 3.2e+08
  - `face_density_kg_m3` = 2780
  - `min_foil_thickness_m` = 2.5e-05
  - `min_strut_diameter_m` = 0.0003

## P-STR-03 — Aircraft cabin floor panel

- **Domain:** structures
- **Statement:** A passenger-cabin floor panel must survive concentrated heel loads and meet deflection limits at minimum weight within a ~10 mm build height.
- **Plausible physics cards:** STR_SANDWICH_HONEYCOMB, STR_LATTICE_TRUSS
- **Source:** Airbus AITM / Boeing BMS 4-20 floor panel specs (heel load, flexure); ASTM C393
- **Requirements / conditions:**
  - `span_m` = 0.5
  - `width_m` = 0.3
  - `design_load_N` = 4000
  - `stiffness_min_N_m` = 400000
  - `areal_mass_cap_kg_m2` = 4
  - `thickness_cap_m` = 0.0127
  - `face_modulus_Pa` = 6e+10
  - `face_strength_Pa` = 6e+08
  - `face_density_kg_m3` = 1550
  - `min_foil_thickness_m` = 2.5e-05
  - `min_strut_diameter_m` = 0.0003

## P-FLD-01 — Skin-friction reduction film for a long-haul airliner fuselage

- **Domain:** fluids
- **Statement:** Reduce turbulent skin-friction drag on a cruising airliner fuselage with a passive film that can be manufactured by micro-replication.
- **Plausible physics cards:** FLD_RIBLET_DRAG
- **Source:** Lufthansa Technik/BASF AeroSHARK riblet film (2022); Bechert et al. 1997
- **Requirements / conditions:**
  - `flow_velocity_m_s` = 250
  - `kinematic_viscosity_m2_s` = 3.5e-05
  - `reference_length_m` = 20
  - `target_drag_reduction_pct` = 2
  - `min_feature_m` = 3e-05

## P-FLD-02 — Hull drag reduction for a container ship

- **Domain:** fluids
- **Statement:** Lower frictional resistance of a container-ship hull at service speed with a passive surface treatment.
- **Plausible physics cards:** FLD_RIBLET_DRAG
- **Source:** IMO EEXI/CII energy-efficiency regulations; Dean & Bhushan 2010 review
- **Requirements / conditions:**
  - `flow_velocity_m_s` = 10
  - `kinematic_viscosity_m2_s` = 1.05e-06
  - `reference_length_m` = 50
  - `target_drag_reduction_pct` = 3
  - `min_feature_m` = 2e-05

## P-FLD-03 — Wind-turbine blade surface drag reduction

- **Domain:** fluids
- **Statement:** Reduce skin-friction drag on the outer span of a wind-turbine blade to raise aerodynamic efficiency.
- **Plausible physics cards:** FLD_RIBLET_DRAG
- **Source:** IEC 61400-1 design conditions; Sareen et al. 2014 Wind Energy (riblet tests on DU 96-W-180)
- **Requirements / conditions:**
  - `flow_velocity_m_s` = 70
  - `kinematic_viscosity_m2_s` = 1.5e-05
  - `reference_length_m` = 1.5
  - `target_drag_reduction_pct` = 4
  - `min_feature_m` = 3e-05

## P-ADH-01 — Glass-facade climbing inspection robot pads

- **Domain:** adhesion
- **Statement:** A small inspection robot must hold onto smooth glass facades without suction or power using reusable dry pads and low engagement force.
- **Plausible physics cards:** ADH_FIBRILLAR
- **Source:** Menon & Sitti 2006; Stickybot (Kim et al. 2008 IEEE T-RO)
- **Requirements / conditions:**
  - `required_adhesion_pressure_Pa` = 20000
  - `work_of_adhesion_J_m2` = 0.05
  - `max_preload_pressure_Pa` = 5000
  - `surface_roughness_amplitude_m` = 5e-08
  - `min_feature_m` = 2e-06

## P-ADH-02 — Residue-free gripper for wafers and display glass

- **Domain:** adhesion
- **Statement:** Pick and place silicon wafers / display glass in a cleanroom without vacuum and without leaving residue, releasing by peeling.
- **Plausible physics cards:** ADH_FIBRILLAR
- **Source:** SEMI E15 / cleanroom handling; Song et al. 2017 (gecko-inspired micro-transfer printing)
- **Requirements / conditions:**
  - `required_adhesion_pressure_Pa` = 5000
  - `work_of_adhesion_J_m2` = 0.05
  - `max_preload_pressure_Pa` = 10000
  - `surface_roughness_amplitude_m` = 1e-08
  - `min_feature_m` = 1e-06

## P-ADH-03 — Grasping pads for spacecraft servicing

- **Domain:** adhesion
- **Statement:** Grip painted/composite spacecraft surfaces in vacuum (no suction, no tape residue) with very low preload to avoid pushing the target away.
- **Plausible physics cards:** ADH_FIBRILLAR
- **Source:** Jiang et al. 2017 Science Robotics (gecko gripper for space, NASA JPL)
- **Requirements / conditions:**
  - `required_adhesion_pressure_Pa` = 2000
  - `work_of_adhesion_J_m2` = 0.03
  - `max_preload_pressure_Pa` = 2000
  - `surface_roughness_amplitude_m` = 2e-06
  - `min_feature_m` = 1e-05

## P-WET-01 — Self-cleaning cover glass for desert PV modules

- **Domain:** wetting
- **Statement:** Make PV cover-glass shed rain and dew droplets (carrying dust) instead of wetting, and stay non-wetting under raindrop impact.
- **Plausible physics cards:** WET_SUPERHYDROPHOBIC
- **Source:** IEC 61215 (PV module qualification); Nayshevsky et al. 2019 IEEE J. Photovolt. (anti-soiling)
- **Requirements / conditions:**
  - `target_apparent_angle_deg` = 150
  - `droplet_impact_speed_m_s` = 6.5
  - `droplet_diameter_m` = 0.002
  - `hydrostatic_head_m` = 0
  - `min_feature_m` = 5e-07
  - `min_solid_fraction` = 0.05

## P-WET-02 — Rain-shedding antenna radome

- **Domain:** wetting
- **Statement:** Prevent a water film forming on a 5G/radar radome in rain (water films attenuate the signal).
- **Plausible physics cards:** WET_SUPERHYDROPHOBIC
- **Source:** ITU-R P.838 rain attenuation; Anderson 1975 IEEE T-AP (radome wet-loss)
- **Requirements / conditions:**
  - `target_apparent_angle_deg` = 145
  - `droplet_impact_speed_m_s` = 4
  - `droplet_diameter_m` = 0.0015
  - `hydrostatic_head_m` = 0
  - `min_feature_m` = 2e-06
  - `min_solid_fraction` = 0.1

## P-OPT-01 — Pigment-free green security film

- **Domain:** optics
- **Statement:** A thin, dye-free film for banknote/brand security must reflect a saturated green colour.
- **Plausible physics cards:** OPT_BRAGG_STRUCTURAL_COLOR
- **Source:** ISO 12931 (anti-counterfeiting authentication); 3M/Teijin multilayer polymer films
- **Requirements / conditions:**
  - `target_wavelength_m` = 5.3e-07
  - `wavelength_tolerance_m` = 1e-08
  - `min_peak_reflectance` = 0.6
  - `max_total_thickness_m` = 2e-06
  - `max_bandwidth_m` = 1.2e-07
  - `min_layer_thickness_m` = 3e-08
  - `incident_index` = 1
  - `substrate_index` = 1.65

## P-OPT-02 — Fade-proof blue structural-colour coating

- **Domain:** optics
- **Statement:** A coating for outdoor products must show a bright blue that never fades (no pigment) and remain thin.
- **Plausible physics cards:** OPT_BRAGG_STRUCTURAL_COLOR
- **Source:** Kinoshita & Yoshioka 2005 review; Teijin MORPHOTEX fibre (product category)
- **Requirements / conditions:**
  - `target_wavelength_m` = 4.7e-07
  - `wavelength_tolerance_m` = 1e-08
  - `min_peak_reflectance` = 0.5
  - `max_total_thickness_m` = 3e-06
  - `max_bandwidth_m` = 8e-08
  - `min_layer_thickness_m` = 3e-08
  - `incident_index` = 1
  - `substrate_index` = 1.5

## P-OPT-03 — Near-infrared heat-mirror window film

- **Domain:** optics
- **Statement:** A transparent window film must reflect near-infrared solar radiation around 1 um to cut solar heat gain.
- **Plausible physics cards:** OPT_BRAGG_STRUCTURAL_COLOR
- **Source:** ISO 9050 (glazing solar factor); 3M Prestige multilayer window film (product category)
- **Requirements / conditions:**
  - `target_wavelength_m` = 1e-06
  - `wavelength_tolerance_m` = 5e-08
  - `min_peak_reflectance` = 0.9
  - `max_total_thickness_m` = 5e-06
  - `max_bandwidth_m` = 4e-07
  - `min_layer_thickness_m` = 3e-08
  - `incident_index` = 1
  - `substrate_index` = 1.5

## P-MT-01 — Passive oxygen window for an underwater sensor

- **Domain:** mass_transfer
- **Statement:** A submerged instrument housing needs passive gas exchange through a membrane that never floods at its deployment depth.
- **Plausible physics cards:** MT_PLASTRON_MEMBRANE
- **Source:** Flynn & Bush 2008 JFM; ocean-observing sensor housings (product category)
- **Requirements / conditions:**
  - `required_flux_mol_m2_s` = 0.005
  - `min_pore_diameter_m` = 3e-08
  - `hydrostatic_head_m` = 10
  - `delta_concentration_mol_m3` = 5

## P-MT-02 — Bubble-free aquaculture membrane aerator

- **Domain:** mass_transfer
- **Statement:** Supply oxygen into a fish tank across a gas-permeable hydrophobic membrane without bubbling or water breakthrough.
- **Plausible physics cards:** MT_PLASTRON_MEMBRANE
- **Source:** Ahmed & Semmens 1992 J. Membr. Sci. (bubbleless membrane aeration)
- **Requirements / conditions:**
  - `required_flux_mol_m2_s` = 0.01
  - `min_pore_diameter_m` = 2e-08
  - `hydrostatic_head_m` = 3
  - `delta_concentration_mol_m3` = 6

## P-MT-03 — Fog-water collector for a mountain village

- **Domain:** mass_transfer
- **Statement:** Collect drinking water from advective fog for a village with a wind-rated frame of limited size and anchor capacity.
- **Plausible physics cards:** MT_FOG_HARVEST_MESH
- **Source:** Dar Si Hmad / CloudFisher fog collectors (Morocco); Schemenauer & Cereceda 1994
- **Requirements / conditions:**
  - `wind_speed_m_s` = 5
  - `liquid_water_content_kg_m3` = 0.0003
  - `droplet_diameter_m` = 1e-05
  - `fog_hours_per_day` = 8
  - `drainage_efficiency` = 0.7
  - `target_yield_L_day` = 350
  - `max_mesh_area_m2` = 100
  - `design_wind_speed_m_s` = 33
  - `max_wind_load_N` = 60000
  - `min_feature_m` = 5e-05

## P-MT-04 — Fog irrigation for a coastal desert farm

- **Domain:** mass_transfer
- **Statement:** Irrigate a small coastal-desert plot from fog with a modest collector and a light frame.
- **Plausible physics cards:** MT_FOG_HARVEST_MESH
- **Source:** Atacama camanchaca fog-collection projects (Cereceda et al. 2008 Atmos. Res.)
- **Requirements / conditions:**
  - `wind_speed_m_s` = 4
  - `liquid_water_content_kg_m3` = 0.0002
  - `droplet_diameter_m` = 1.2e-05
  - `fog_hours_per_day` = 6
  - `drainage_efficiency` = 0.6
  - `target_yield_L_day` = 120
  - `max_mesh_area_m2` = 60
  - `design_wind_speed_m_s` = 25
  - `max_wind_load_N` = 40000
  - `min_feature_m` = 5e-05
