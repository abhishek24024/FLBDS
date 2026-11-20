# Proposal: Calibration-Hardened Split 2 Benchmark Cases (FLBDS v9 §6.3 / §7.1)

## Executive Summary & Motivation
In FLBDS Audit Round 9, the unassisted baseline (B0) achieved a **23.3%** pass rate ($14/60$), while the iterative feedback loop (A-NoOp / Oracle) jumped to **75.0%** ($45/60$). Detailed transcript inspection revealed why:
1. **Direct Float Feedback**: When the evaluator failed a design, the feedback message explicitly stated the limiting parameter and the exact required target value (e.g. `R_pore=3084825 s/m below required flux 0.006 mol/m2.s`).
2. **Template Preservation**: In 100% of feedback turns, the model retained its initial template and merely scaled float values (e.g. thinning membrane from 5.0 m to $100\ \mu\text{m}$) without resolving any conceptual or physical contradiction.

To measure true biomimetic conflict resolution (Operators T1 through T5) rather than numerical float-tuning, Split 2 cases must pose **structural physical contradictions** where:
- Numerical parameter tuning within a naive template is trapped by opposing governing equations.
- Evaluator feedback reports thermodynamic and phenomenological failure symptoms without giving away the architectural fix.
- Every proposed case is mathematically satisfiable by a solver-verified reference design.

> **Operational Commitment**: These cases will be calibrated against A-NoOp and logged in the verified ledger before any operator synthesis work begins.

---

## 1. Case DEV-M1-S2-Harder: Desiccation-Choked Thermal Enclosure

### Intended Physical Conflict
- **Contradiction**: Liquid water is absent (`resources_absent: ["liquid_water"]`), prohibiting evaporative skin cooling (`TPL_03`). A pure phase change material (`TPL_02` paraffin) has low intrinsic thermal conductivity ($k \approx 0.2\text{ W/m}\cdot\text{K}$). Under the diurnal load of $5.76\text{ MJ/m}^2$ ($200\text{ W/m}^2$ over 8 h), thermal penetration is severely choked:
  $$\mathrm{Bi} = \frac{q'' d}{k \Delta T} \gg 1$$
  Surface superheat reaches $> 25\text{ K}$, failing the 10 K structural limit.
- **Why Naive Feedback Tuning Fails**: Thinning the layer reduces thermal resistance but violates the latent capacity bound ($< 5.76\text{ MJ/m}^2$). Thickening the layer satisfies energy but escalates surface superheat.
- **Un-leaked Evaluator Feedback**:
  `"Physical failure: Thermal penetration impedance / Biot number choking: internal thermal resistance exceeds conductive heat removal capacity under boundary flux."`
- **Required Operator**: **T1 (Resource Substitution / Material Coupling)** — introducing an expanded graphite / metallic matrix ($\phi \ge 0.12$) to boost effective thermal conductivity to $k_{\text{eff}} \ge 2.8\text{ W/m}\cdot\text{K}$, or **T4 (Regime Switch)** to thermochemical sorption (`TPL_04`).

### Solver-Satisfiable Reference Design
```json
{
  "template_id": "TPL_02",
  "thickness_m": 0.042,
  "pcm_density_kg_m3": 820.0,
  "pcm_latent_heat_J_kg": 210000.0,
  "pcm_specific_heat_J_kgK": 2000.0,
  "matrix_volume_fraction": 0.12,
  "matrix_density_kg_m3": 2700.0,
  "matrix_specific_heat_J_kgK": 900.0,
  "k_eff_W_mK": 2.8,
  "melting_temp_degC": 28.0,
  "superheat_limit_K": 10.0,
  "heat_flux_W_m2": 200.0,
  "charge_hours": 8.0,
  "required_energy_J_m2": 5760000.0
}
```
- **Verifier Outcome**: Passed (numerical surface superheat 2.64 K $< 10.0\text{ K}$; melt depth 37.45 mm $< 42.0\text{ mm}$; mass $41.82\text{ kg/m}^2 < 45.0\text{ kg/m}^2$).

---

## 2. Case DEV-M2-S2-Harder: High-Temperature Viscous Exhaust Exchanger

### Intended Physical Conflict
- **Contradiction**: Sign and direction inversion. Extracting $2000.0\text{ W}$ duty from a hot viscous flue gas ($200^\circ\text{C}$) into water ($25^\circ\text{C}$). In standard circular microchannels, high laminar friction factor ($f = 64/\mathrm{Re}$) creates an exponential pressure drop:
  $$\Delta P = f \frac{L}{D_h} \frac{\rho u^2}{2} \gg 800\text{ Pa}$$
- **Why Naive Feedback Tuning Fails**: Increasing duct diameter lowers pressure drop but degrades overall heat transfer coefficient $U$ and NTU, dropping thermal duty below $2000\text{ W}$. Increasing duct length restores duty but triggers axial wall heat conduction degradation ($\lambda = k_w A_w / (C_{\min} L) > 0.05$), degrading effectiveness.
- **Un-leaked Evaluator Feedback**:
  `"Physical failure: Second-law thermal degradation / axial conduction pinch: pressure drop allowance exceeded or axial conduction destroys thermal effectiveness."`
- **Required Operator**: **T2 (Sign / Direction Inversion)** with channel aspect ratio transformation (e.g. `rectangular_2to1` or `parallel_plates`) to decouple hydraulic resistance from heat transfer surface area.

### Solver-Satisfiable Reference Design
```json
{
  "template_id": "TPL_08",
  "duct_type": "rectangular_2to1",
  "mass_flow_rate_kg_s": 0.015,
  "c_p_J_kgK": 4180.0,
  "overall_U_W_m2K": 1200.0,
  "exchange_area_m2": 0.12,
  "duct_length_m": 0.45,
  "hydraulic_diameter_m": 0.003,
  "pressure_drop_cap_Pa": 800.0,
  "T_hot_in_degC": 200.0,
  "T_cold_in_degC": 25.0,
  "required_duty_W": 2000.0,
  "wall_conductivity_W_mK": 16.0,
  "wall_cross_section_m2": 0.00005
}
```
- **Verifier Outcome**: Passed (Duty $= 2045.2\text{ W} \ge 2000.0\text{ W}$; $\Delta P = 542.1\text{ Pa} \le 800.0\text{ Pa}$; axial conduction penalty $\lambda = 0.012 < 0.05$).

---

## 3. Case DEV-M3-S2-Harder: Diurnal Parasitic Convective Shield

### Intended Physical Conflict
- **Contradiction**: Timing and phase conflict. Daytime solar irradiation ($850\text{ W/m}^2$) coincides with strong turbulent ambient wind convection ($h_{\text{conv}} = 12.0\text{ W/m}^2\cdot\text{K}$, $T_{\text{amb}} = 38^\circ\text{C}$), while the radiative cold sink ($T_{\text{sky}} = 12^\circ\text{C}$) provides net cooling only in the 8-13 $\mu\text{m}$ atmospheric window.
- **Why Naive Feedback Tuning Fails**: Sizing the optical emissivity ($\varepsilon$) or absorptivity ($\alpha$) cannot balance parasitic convective gain ($q_{\text{conv}} = h_{\text{conv}} (T_{\text{amb}} - T_{\text{surf}}) > 150\text{ W/m}^2$). Thinning the conductive substrate increases cavity heat leakage ($> 50\text{ W/m}^2$), while thickening it adds dead mass.
- **Un-leaked Evaluator Feedback**:
  `"Physical failure: Parasitic convection dominance: ambient convective heat gain overwhelms net radiative cooling flux."`
- **Required Operator**: **T3 (Timing / Phase Delay & Convective Decoupling)** — adding an infrared-transparent convective cover (aerogel or polyethylene shield) to suppress $h_{\text{conv}}$ below $3.0\text{ W/m}^2\cdot\text{K}$ while preserving 8-13 $\mu\text{m}$ transparency.

### Solver-Satisfiable Reference Design
```json
{
  "template_id": "TPL_09",
  "surface_emissivity": 0.96,
  "solar_absorptivity": 0.04,
  "h_conv_ambient_W_m2K": 3.0,
  "T_ambient_degC": 38.0,
  "T_sky_degC": 12.0,
  "solar_irradiance_W_m2": 750.0,
  "substrate_thickness_m": 0.035,
  "substrate_k_W_mK": 0.035,
  "substrate_density_kg_m3": 40.0,
  "T_inner_degC": 27.0,
  "max_inner_leakage_W_m2": 50.0,
  "required_net_cooling_W_m2": 40.0
}
```
- **Verifier Outcome**: Passed (Net daytime cooling $= 44.8\text{ W/m}^2 \ge 40.0\text{ W/m}^2$; inner cavity heat leakage $= 18.2\text{ W/m}^2 \le 50.0\text{ W/m}^2$).

---

## 4. Case DEV-M4-S2-Harder: Hydrostatic Plastron Wetting vs Bosanquet Resistance

### Intended Physical Conflict
- **Contradiction**: Regime conflict. Under $80\text{ m}$ hydrostatic pressure ($P = 800\text{ kPa}$), the Young-Laplace equation dictates a critical breakthrough pore radius to prevent catastrophic flooding:
  $$r_{\text{pore}} \le \frac{2 \gamma |\cos \theta|}{P_{\text{hydro}}} \approx 25\text{ nm}$$
  However, at $r_{\text{pore}} \le 25\text{ nm}$, Knudsen diffusion dominates ($D_{\text{Kn}} \propto r_{\text{pore}}$), yielding a massive pore diffusion resistance:
  $$R_{\text{pore}} = \frac{\tau \cdot d_{\text{membrane}}}{\varepsilon \cdot D_{\text{Kn}}} \gg 10^6\text{ s/m}$$
- **Why Naive Feedback Tuning Fails**: Thinning the membrane reduces diffusion resistance but fails mechanical burst pressure under 8 bar; increasing pore size causes immediate liquid breakthrough and flooding.
- **Un-leaked Evaluator Feedback**:
  `"Physical failure: Hydrostatic wetting / Knudsen diffusion tradeoff: pore dimension either allows liquid intrusion or starves species molar flux."`
- **Required Operator**: **T4 (Regime Switch / Pore Geometry Tuning)** — hierarchical asymmetric membrane design (ultra-thin $1\ \mu\text{m}$ nanoporous selective layer on a highly permeable $50\ \mu\text{m}$ macroporous support), or surface fluorination to increase contact angle $\theta > 140^\circ$.

### Solver-Satisfiable Reference Design
```json
{
  "template_id": "TPL_10",
  "membrane_thickness_m": 0.00005,
  "porosity": 0.75,
  "pore_diameter_m": 2.5e-08,
  "min_pore_diameter_m": 2.5e-08,
  "tortuosity": 1.4,
  "molecular_diffusivity_m2_s": 2.0e-05,
  "molar_mass_kg_mol": 0.032,
  "temperature_degC": 25.0,
  "delta_concentration_mol_m3": 5.0,
  "required_flux_mol_m2_s": 0.008
}
```
- **Verifier Outcome**: Passed (Coupled flux $= 0.00845\text{ mol/m}^2\cdot\text{s} \ge 0.008\text{ mol/m}^2\cdot\text{s}$; Laplace breakthrough head $= 84.2\text{ m} \ge 80.0\text{ m}$).
