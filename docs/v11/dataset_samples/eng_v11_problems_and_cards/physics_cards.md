# V11 physics cards (11 closed-form, cited models)

A card takes a design (numbers within bounds) and a problem's operating conditions, and returns pass/fail for each constraint with margins and regime-validity notes. The optimiser and the LLM both work within these bounds.

## THM_PCM_STORAGE — Phase-change thermal buffer layer (latent heat storage, melt point 28 degC)

- **Domain:** thermal
- **Principle:** A layer of thickness d of PCM (+ optional conductive matrix) absorbs a constant flux q for t hours. Latent capacity rho_eff*L_eff*d >= required energy q*t; melt-front depth x = q t/(rho L); closed-form surface superheat dT = q x / k_eff (quasi-steady Stefan/Neumann limit) <= limit; areal mass rho_eff*d <= cap. Validity: effective Fourier number Fo = alpha t / d^2 in [0.8, 135] (lumped and solver-validity window).
- **Biological exemplars:** honeybee nest thermoregulation (wax/honey thermal mass; analogy is thermal buffering, not true PCM), termite mound thermal mass (sensible, not latent; weak analogy), camel diurnal heat storage in body mass (sensible heat buffering)
- **Design fields (bounds):**
  - `thickness_m` [0.003 … 0.08]
  - `k_eff_W_mK` [0.15 … 15]
  - `matrix_volume_fraction` [0 … 0.3]
  - `matrix_density_kg_m3` [1.5e+03 … 9e+03]
  - `matrix_specific_heat_J_kgK` [380 … 1e+03]
  - `pcm_density_kg_m3` [750 … 1.7e+03]
  - `pcm_latent_heat_J_kg` [1.2e+05 … 2.6e+05]
  - `pcm_specific_heat_J_kgK` [1.4e+03 … 3e+03]
- **Operating-condition inputs:** `heat_flux_W_m2`, `charge_hours`, `required_energy_J_m2`, `thickness_max_m`, `mass_cap_kg_m2`, `superheat_limit_K`
- **References:**
  - Mehling H., Cabeza L.F. (2008) Heat and Cold Storage with PCM, Springer.
  - Alexiades V., Solomon A.D. (1993) Mathematical Modeling of Melting and Freezing Processes.
  - flbds.physics.tpl02_pcm (screen_tpl02, compute_composite_properties); flbds.v10.families.PCMFamily.

## THM_COUNTERCURRENT_HX — Counter-current liquid-liquid heat exchanger (epsilon-NTU)

- **Domain:** thermal
- **Principle:** Counter-flow effectiveness eps = (1-exp(-NTU(1-Cr)))/(1-Cr exp(-NTU(1-Cr))), NTU = UA/C_min; duty Q = eps C_min (T_h,in - T_c,in) >= required; duct pressure drop dP = f (L/D) rho v^2/2 (Poiseuille/Blasius) <= cap; length <= cap. Axial wall conduction degradation reported (Kroeger) as derived.
- **Biological exemplars:** bird leg rete mirabile (counter-current heat retention), camel nasal turbinates, tuna/lamnid shark red-muscle retia, dolphin flipper arteriovenous bundles
- **Design fields (bounds):**
  - `m_dot_hot_kg_s` [0.002 … 0.5]
  - `m_dot_cold_kg_s` [0.002 … 0.5]
  - `overall_U_W_m2K` [50 … 5e+03]
  - `heat_transfer_area_m2` [0.01 … 5]
  - `length_m` [0.05 … 2]
  - `hydraulic_diameter_m` [0.0005 … 0.05]
  - `wall_conductivity_W_mK` [0.2 … 400]
  - `wall_cross_section_m2` [1e-06 … 0.001]
- **Operating-condition inputs:** `required_duty_W`, `T_cold_in_degC`, `T_hot_in_degC`, `max_pressure_drop_Pa`, `length_cap_m`
- **References:**
  - Incropera F.P., DeWitt D.P. et al. Fundamentals of Heat and Mass Transfer, ch. 11 (eps-NTU).
  - Kroeger P.G. (1967) Performance deterioration in high effectiveness heat exchangers due to axial conduction.
  - Scholander P.F. (1957) The wonderful net, Sci. Am. 196:96-107 (biological counter-current exchange).
  - flbds.physics.tpl08_countercurrent; flbds.v10.families.HXFamily.

## THM_RADIATIVE_COOLING — Passive daytime radiative cooling roof skin

- **Domain:** thermal
- **Principle:** Lumped net cooling P_net = eps sigma (T_amb^4 - T_sky^4) - alpha_s G >= required (TPL_09 screen). Surface equilibrium eps sigma (T_s^4 - T_sky^4) + h (T_s - T_amb) + (k/d)(T_s - T_in) = alpha_s G solved for T_s; inner leakage q = (k/d)(T_s - T_in) <= cap. Substrate thickness and areal mass <= caps.
- **Biological exemplars:** Saharan silver ant (Cataglyphis bombycina) triangular hairs, white beetle Cyphochilus scales, longicorn beetle Neocerambyx gigas hairs
- **Design fields (bounds):**
  - `surface_emissivity` [0.05 … 0.98]
  - `solar_absorptivity` [0.02 … 0.95]
  - `substrate_thickness_m` [0.001 … 0.08]
  - `substrate_k_W_mK` [0.02 … 2]
  - `substrate_density_kg_m3` [15 … 2.5e+03]
- **Operating-condition inputs:** `solar_irradiance_W_m2`, `T_ambient_degC`, `T_sky_degC`, `T_inner_degC`, `h_conv_W_m2K`, `max_inner_leakage_W_m2`, `required_net_cooling_W_m2`, `thickness_max_m`, `mass_cap_kg_m2`
- **References:**
  - Raman A.P. et al. (2014) Passive radiative cooling below ambient air temperature under direct sunlight, Nature 515:540.
  - Shi N.N. et al. (2015) Keeping cool: enhanced optical reflection and radiative heat dissipation in Saharan silver ants, Science 349:298.
  - Incropera & DeWitt, Fundamentals of Heat and Mass Transfer, ch. 12.
  - flbds.physics.tpl09_radiative; flbds.v10.families.RADFamily.

## MT_PLASTRON_MEMBRANE — Plastron-type hydrophobic porous gas-exchange membrane (O2, 25 degC)

- **Domain:** mass_transfer
- **Principle:** Gas flux through air-filled hydrophobic pores J = D_eff dC / L with Bosanquet D_eff = (eps/tau)/(1/D_m + 1/D_K), Knudsen D_K = (d/3) sqrt(8RT/(pi M)); Young-Laplace breakthrough head h = 4 gamma |cos theta| /(d rho g) >= hydrostatic head; pore diameter >= fouling minimum; mass Fourier number D_eff t/L^2 >= 1.
- **Biological exemplars:** diving bell spider (Argyroneta aquatica) air bell, Aphelocheirus aestivalis plastron, Salvinia molesta air-retaining hairs, backswimmer Notonecta
- **Design fields (bounds):**
  - `membrane_thickness_m` [1e-06 … 0.001]
  - `porosity` [0.05 … 0.9]
  - `pore_diameter_m` [5e-09 … 5e-06]
  - `tortuosity` [1 … 5]
  - `contact_angle_deg` [91 … 160]
- **Operating-condition inputs:** `required_flux_mol_m2_s`, `min_pore_diameter_m`, `hydrostatic_head_m`, `delta_concentration_mol_m3`
- **References:**
  - Thorpe W.H., Crisp D.J. (1947) Studies on plastron respiration, J. Exp. Biol. 24:227.
  - Flynn M.R., Bush J.W.M. (2008) Underwater breathing: the mechanics of plastron respiration, J. Fluid Mech. 608:275.
  - Cussler E.L. Diffusion: Mass Transfer in Fluid Systems (Bosanquet, Knudsen).
  - flbds.physics.tpl10_diffusion; flbds.v10.families.MEMFamily.

## STR_SANDWICH_HONEYCOMB — Honeycomb-core sandwich panel/beam (Al 5052 hexagonal core)

- **Domain:** structures
- **Principle:** Gibson-Ashby: honeycomb out-of-plane modulus E_c = E_s rho*, transverse shear modulus G_c = 0.5 rho* G_s, core shear strength ~0.5 rho* tau_ys (or wall buckling E_s (t/l)^3). Allen sandwich beam, 3-point bending: D = E_f b t d^2/2, S = G_c b d^2/c, delta = P L^3/(48D) + P L/(4S). Failure loads: face yield 4 sigma_f t d b/L, core shear 2 tau_c b d, face wrinkling sigma = 0.5 (E_f E_c G_c)^(1/3), intracell dimpling 2E_f/(1-nu^2)(t/s)^2. Mass/area = 2 rho_f t + rho* rho_s c.
- **Biological exemplars:** honeybee comb (hexagonal wax cells), bird skull/wing bone sandwich (diploe), beetle elytra (trabecular sandwich), cuttlebone lamellar septa
- **Design fields (bounds):**
  - `face_thickness_m` [0.0001 … 0.005]
  - `core_thickness_m` [0.002 … 0.15]
  - `core_relative_density` [0.003 … 0.25]
  - `cell_size_m` [0.0015 … 0.025]
- **Operating-condition inputs:** `span_m`, `width_m`, `design_load_N`, `stiffness_min_N_m`, `areal_mass_cap_kg_m2`, `thickness_cap_m`, `face_modulus_Pa`, `face_strength_Pa`, `face_density_kg_m3`, `min_foil_thickness_m`
- **References:**
  - Allen H.G. (1969) Analysis and Design of Structural Sandwich Panels, Pergamon (D = E_f b t d^2/2, S = G_c b d^2/c).
  - Zenkert D. (1995) An Introduction to Sandwich Construction, EMAS (failure modes, wrinkling 0.5(E_f E_c G_c)^(1/3)).
  - Hoff N.J., Mautner S.E. (1945) The buckling of sandwich-type panels, J. Aeronaut. Sci. 12:285.
  - Gibson L.J., Ashby M.F. (1997) Cellular Solids: Structure and Properties, 2nd ed., CUP, ch. 4.
  - Hexcel (2016) HexWeb Honeycomb Sandwich Design Technology, publication AGU 075b (dimpling, Norris).

## STR_LATTICE_TRUSS — Truss-lattice-core sandwich panel (L-PBF AlSi10Mg core; pyramidal or BCC)

- **Domain:** structures
- **Principle:** Maxwell connectivity: Z>=12 nodes give stretch-dominated trusses (pyramidal/octet: E ~ rho* E_s, tau ~ rho* sigma_strut) whereas Z~8 (BCC) bend (E ~ rho*^2 E_s, tau ~ 0.2 rho*^1.5 sigma_ys). Strut Euler buckling sigma = pi^2 E_s (r/l)^2 caps the stretch-dominated strength. Core properties feed Allen sandwich-beam stiffness (bending + shear deflection), face yield, core shear and face wrinkling checks; strut diameter >= additive-manufacturing minimum.
- **Biological exemplars:** bird bone trabeculae (graded strut lattice), Euplectella glass sponge skeleton, cuttlebone pillared chambers, sea urchin stereom
- **Design fields (bounds):**
  - `face_thickness_m` [0.0001 … 0.005]
  - `core_thickness_m` [0.002 … 0.15]
  - `core_relative_density` [0.01 … 0.4]
  - `strut_length_m` [0.001 … 0.02]
  - `nodal_connectivity` [8 … 12]
- **Operating-condition inputs:** `span_m`, `width_m`, `design_load_N`, `stiffness_min_N_m`, `areal_mass_cap_kg_m2`, `thickness_cap_m`, `face_modulus_Pa`, `face_strength_Pa`, `face_density_kg_m3`, `min_strut_diameter_m`
- **References:**
  - Allen H.G. (1969) Analysis and Design of Structural Sandwich Panels, Pergamon (D = E_f b t d^2/2, S = G_c b d^2/c).
  - Zenkert D. (1995) An Introduction to Sandwich Construction, EMAS (failure modes, wrinkling 0.5(E_f E_c G_c)^(1/3)).
  - Hoff N.J., Mautner S.E. (1945) The buckling of sandwich-type panels, J. Aeronaut. Sci. 12:285.
  - Deshpande V.S., Fleck N.A. (2001) Collapse of truss core sandwich beams in 3-point bending, Int. J. Solids Struct. 38:6275.
  - Deshpande V.S., Ashby M.F., Fleck N.A. (2001) Foam topology: bending versus stretching dominated architectures, Acta Mater. 49:1035.
  - Gibson L.J., Ashby M.F. (1997) Cellular Solids, 2nd ed., ch. 5 (open-cell scaling).

## FLD_RIBLET_DRAG — Streamwise riblet film for turbulent skin-friction reduction

- **Domain:** fluids
- **Principle:** Riblets of spacing s reduce turbulent skin friction when s+ = s u_tau/nu is small (viscous regime, DR ~ m_s s+), with optimum near s+ ~ 15 (l_g+ = sqrt(A_g)/nu*u_tau ~ 10.7) and up to ~10 % reduction for thin blades (h/s ~ 0.5); beyond s+ ~ 25 Kelvin-Helmholtz rollers cause breakdown and drag increase. u_tau = U sqrt(Cf/2) with turbulent flat-plate Cf = 0.0592 Re_x^-0.2.
- **Biological exemplars:** shark skin dermal denticles (Isurus oxyrinchus, Carcharhinus), sailfish/bird flight-feather grooves
- **Design fields (bounds):**
  - `riblet_spacing_m` [5e-06 … 0.002]
  - `height_to_spacing` [0.2 … 1]
  - `coverage_fraction` [0.1 … 1]
- **Operating-condition inputs:** `flow_velocity_m_s`, `kinematic_viscosity_m2_s`, `reference_length_m`, `target_drag_reduction_pct`, `min_feature_m`
- **References:**
  - Bechert D.W., Bruse M., Hage W., van der Hoeven J.G.T., Hoppe G. (1997) Experiments on drag-reducing surfaces and their optimization with an adjustable geometry, J. Fluid Mech. 338:59-87.
  - Garcia-Mayoral R., Jimenez J. (2011) Drag reduction by riblets, Phil. Trans. R. Soc. A 369:1412-1427.
  - Schlichting H., Gersten K. Boundary-Layer Theory (turbulent flat-plate Cf = 0.0592 Re_x^-0.2).
  - Dean B., Bhushan B. (2010) Shark-skin surfaces for fluid-drag reduction in turbulent flow: a review, Phil. Trans. R. Soc. A 368:4775.

## ADH_FIBRILLAR — Fibrillar (gecko-type) dry adhesive pad

- **Domain:** adhesion
- **Principle:** Contact splitting: n = phi/(pi a^2) fibrils each with JKR pull-off F = 1.5 pi W a give adhesion pressure sigma = 1.5 phi W / a (rises as fibrils shrink), capped by theoretical strength phi W/b. Limits: lateral collapse of neighbouring fibrils (bending energy vs side adhesion, L <= (3 pi E a^3 g^2/4W)^(1/4)); Euler buckling under preload; array effective modulus E_eff = 0.75 phi E (a/L)^2 sin/cos^2 <= Dahlquist 100 kPa for tack; preload E_eff*roughness/(L sin) <= allowable.
- **Biological exemplars:** gecko setae and spatulae (Gekko gecko), beetle tarsal hairy pads (Chrysomelidae), fly pulvilli setae, jumping spider scopulae
- **Design fields (bounds):**
  - `fibril_radius_m` [5e-08 … 5e-05]
  - `fibril_length_m` [1e-06 … 0.002]
  - `packing_fraction` [0.05 … 0.7]
  - `fibril_modulus_Pa` [1e+06 … 4e+09]
- **Operating-condition inputs:** `required_adhesion_pressure_Pa`, `work_of_adhesion_J_m2`, `max_preload_pressure_Pa`, `surface_roughness_amplitude_m`, `min_feature_m`
- **References:**
  - Arzt E., Gorb S., Spolenak R. (2003) From micro to nano contacts in biological attachment devices, PNAS 100:10603.
  - Johnson K.L., Kendall K., Roberts A.D. (1971) Surface energy and the contact of elastic solids, Proc. R. Soc. A 324:301.
  - Hui C.Y., Jagota A., Lin Y.Y., Kramer E.J. (2002) Constraints on microcontact printing imposed by stamp deformation, Langmuir 18:1394.
  - Glassmaker N.J., Jagota A., Hui C.Y., Kim J. (2004) Design of biomimetic fibrillar interfaces: 1, J. R. Soc. Interface 1:23.
  - Autumn K., Majidi C., Groff R.E., Dittmore A., Fearing R. (2006) Effective elastic modulus of isolated gecko setal arrays, J. Exp. Biol. 209:3558.
  - Gao H., Yao H. (2004) Shape insensitive optimal adhesion of nanoscale fibrillar structures, PNAS 101:7851.

## WET_SUPERHYDROPHOBIC — Superhydrophobic micropillar texture (Cassie-Baxter, impalement-robust)

- **Domain:** wetting
- **Principle:** Square pillars width a, pitch p, height h on a hydrophobic coating (Young angle theta): solid fraction phi = (a/p)^2, Cassie-Baxter cos theta* = phi(cos theta + 1) - 1, Wenzel cos theta_W = r cos theta, r = 1 + 4ah/p^2. Cassie robustness: depinning breakthrough pressure -gamma cos theta * 4a/(p^2 - a^2) and meniscus sag (sqrt2 p - a)^2 P/(8 gamma) <= h must resist the impact pressure 0.5 rho V^2 (+ rho g H).
- **Biological exemplars:** lotus leaf (Nelumbo nucifera) papillae, springtail (Collembola) cuticle, water strider legs, Salvinia leaf hairs, rice leaf
- **Design fields (bounds):**
  - `pillar_width_m` [1e-07 … 0.0001]
  - `pillar_pitch_m` [2e-07 … 0.0005]
  - `pillar_height_m` [1e-07 … 0.0002]
  - `intrinsic_contact_angle_deg` [70 … 125]
- **Operating-condition inputs:** `target_apparent_angle_deg`, `droplet_impact_speed_m_s`, `droplet_diameter_m`, `hydrostatic_head_m`, `min_feature_m`, `min_solid_fraction`
- **References:**
  - Cassie A.B.D., Baxter S. (1944) Wettability of porous surfaces, Trans. Faraday Soc. 40:546.
  - Wenzel R.N. (1936) Resistance of solid surfaces to wetting by water, Ind. Eng. Chem. 28:988.
  - Bico J., Thiele U., Quere D. (2002) Wetting of textured surfaces, Colloids Surf. A 206:41.
  - Zheng Q.-S., Yu Y., Zhao Z.-H. (2005) Effects of hydraulic pressure on the stability and transition of wetting modes of superhydrophobic surfaces, Langmuir 21:12207.
  - Bartolo D. et al. (2006) Bouncing or sticky droplets: impalement transitions on superhydrophobic micropatterned surfaces, Europhys. Lett. 74:299.
  - Barthlott W., Neinhuis C. (1997) Purity of the sacred lotus, Planta 202:1.

## OPT_BRAGG_STRUCTURAL_COLOR — Multilayer Bragg reflector for structural colour / spectral mirror

- **Domain:** optics
- **Principle:** N bilayers of indices n1, n2 and thicknesses d1, d2 reflect constructively at lambda = 2(n1 d1 + n2 d2) (normal incidence, first order). For quarter-wave layers the peak reflectance is R = ((1 - (ns/n0)(nH/nL)^2N)/(1 + (ns/n0)(nH/nL)^2N))^2 and the stop-band width is (4 lambda/pi) asin(|n1-n2|/(n1+n2)). Total thickness N(d1+d2).
- **Biological exemplars:** Morpho butterfly wing-scale lamellae, jewel beetle (Buprestidae) cuticle multilayer, silver fish scales (guanine platelets), Pollia condensata fruit (helicoidal multilayer)
- **Design fields (bounds):**
  - `n_layer1` [1.3 … 2.6]
  - `thickness_layer1_m` [2e-08 … 5e-07]
  - `n_layer2` [1 … 2.6]
  - `thickness_layer2_m` [2e-08 … 5e-07]
  - `n_pairs` [1 … 40]
- **Operating-condition inputs:** `target_wavelength_m`, `wavelength_tolerance_m`, `min_peak_reflectance`, `max_total_thickness_m`, `max_bandwidth_m`, `min_layer_thickness_m`, `incident_index`, `substrate_index`
- **References:**
  - Macleod H.A. (2010) Thin-Film Optical Filters, 4th ed., CRC (quarter-wave stack reflectance, stop band).
  - Hecht E. Optics, 5th ed., sec. 9.7 (multilayer films).
  - Kinoshita S., Yoshioka S. (2005) Structural colors in nature: the role of regularity and irregularity, ChemPhysChem 6:1442.
  - Vukusic P., Sambles J.R. (2003) Photonic structures in biology, Nature 424:852.

## MT_FOG_HARVEST_MESH — Fog-collection mesh (aerodynamic x deposition x drainage efficiency)

- **Domain:** mass_transfer
- **Principle:** Collection efficiency eta = eta_a * eta_d * eta_drain. Aerodynamic (Rivera 2011): eta_a = SC/(1 + sqrt(C0/C_D)), C_D = 1.3 SC + (SC/(1-SC))^2, C0 = 1.18. Deposition by inertial impaction on fibres: eta_d = St/(St + pi/2), St = rho_w d^2 U/(9 mu D_f). Yield = eta LWC U A t_fog >= target; storm wind load 0.5 rho C_D U_design^2 A <= frame capacity.
- **Biological exemplars:** Namib desert beetle (Onymacris unguicularis / Stenocara) elytra, cactus spines (Opuntia microdasys), spider silk spindle knots (Uloborus walckenaerius), Namib dune grass (Stipagrostis sabulicola)
- **Design fields (bounds):**
  - `fibre_radius_m` [2e-05 … 0.002]
  - `shade_coefficient` [0.05 … 0.95]
  - `mesh_area_m2` [0.1 … 200]
- **Operating-condition inputs:** `wind_speed_m_s`, `liquid_water_content_kg_m3`, `droplet_diameter_m`, `fog_hours_per_day`, `drainage_efficiency`, `target_yield_L_day`, `max_mesh_area_m2`, `design_wind_speed_m_s`, `max_wind_load_N`, `min_feature_m`
- **References:**
  - Rivera J. de D. (2011) Aerodynamic collection efficiency of fog water collectors, Atmos. Res. 102:335.
  - Park K.-C., Chhatre S.S., Srinivasan S., Cohen R.E., McKinley G.H. (2013) Optimal design of permeable fiber network structures for fog harvesting, Langmuir 29:13269.
  - Langmuir I., Blodgett K.B. (1946) A mathematical investigation of water droplet trajectories, GE RL-225.
  - Schemenauer R.S., Cereceda P. (1994) A proposed standard fog collector for use in high-elevation regions, J. Appl. Meteorol. 33:1313.
  - Parker A.R., Lawrence C.R. (2001) Water capture by a desert beetle, Nature 414:33.
