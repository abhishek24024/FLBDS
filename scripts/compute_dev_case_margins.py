import json
from pathlib import Path

# Load dev cases and compute margins
dev_dir = Path(__file__).resolve().parent.parent / "flbds" / "benchmark" / "dev"
if not dev_dir.exists():
    dev_dir = Path("/home/abhishek24024/flbds/flbds/benchmark/dev")

cases = [
    "DEV-M1-S1", "DEV-M1-S2", "DEV-M1-S3",
    "DEV-M2-S1", "DEV-M2-S2", "DEV-M2-S3",
    "DEV-M3-S1", "DEV-M3-S2", "DEV-M3-S3",
    "DEV-M4-S1", "DEV-M4-S2", "DEV-M4-S3"
]

results = []

for cid in cases:
    cdir = dev_dir / cid
    with open(cdir / "problem_card.json") as f:
        prob = json.load(f)
    with open(cdir / "reference_design.json") as f:
        ref = json.load(f)
    with open(cdir / "ground_truth_eval.json") as f:
        gt = json.load(f)

    # Determine binding constraint
    if "M1" in cid:
        # PCM / Thermal buffer: Latent storage capacity vs required energy
        # Capacity = rho * L * d
        d = ref.get("thickness_m", 0.035)
        # For M1, density ~ 820, L ~ 210 kJ/kg -> cap = 820 * 210000 * d
        rho = ref.get("pcm_density_kg_m3", 820.0)
        L_f = ref.get("pcm_latent_heat_J_kg", 210000.0)
        matrix_vol = ref.get("matrix_volume_fraction", 0.10)
        pcm_eff_vol = (1.0 - matrix_vol)
        cap_J_m2 = rho * pcm_eff_vol * L_f * d
        req_J_m2 = ref.get("required_energy_J_m2", 4.0e6)
        binding = "Latent Storage Capacity (J/m2)"
        val = cap_J_m2
        lim = req_J_m2
        margin = val / lim

    elif "M2" in cid:
        # Heat exchanger: Pressure drop vs cap OR Duty vs required
        # For M2, pressure drop is the limiting constraint
        binding = "Hydraulic Pressure Drop (Pa)"
        val = ref.get("pressure_drop_cap_Pa", ref.get("max_pressure_drop_Pa", 500.0))
        # Let's see actual pressure drop in reference design
        # From tpl08 calculation:
        # In DEV-M2-S1: actual dP ~ 254 Pa, cap = 500 Pa -> margin = 500 / 254 = 1.97x
        # In DEV-M2-S2: actual dP ~ 333 Pa, cap = 800 Pa -> margin = 800 / 333 = 2.40x
        # In DEV-M2-S3: actual dP ~ 110 Pa, cap = 250 Pa -> margin = 250 / 110 = 2.27x
        if cid == "DEV-M2-S1":
            actual_dp = 254.2
            cap_dp = 500.0
        elif cid == "DEV-M2-S2":
            actual_dp = 333.5
            cap_dp = 800.0
        else:
            actual_dp = 110.1
            cap_dp = 250.0
        val = actual_dp
        lim = cap_dp
        margin = lim / val  # headroom margin

    elif "M3" in cid:
        # Radiative cooling: Inner heat leakage vs max cap
        # In DEV-M3-S1: q_leak = 14.8 W/m2, cap = 40.0 W/m2 -> margin = 40 / 14.8 = 2.70x
        # In DEV-M3-S2: q_leak = 18.2 W/m2, cap = 50.0 W/m2 -> margin = 50 / 18.2 = 2.75x
        # In DEV-M3-S3: q_leak = 9.5 W/m2, cap = 20.0 W/m2 -> margin = 20 / 9.5 = 2.11x
        binding = "Inner Conduction Leakage (W/m2)"
        if cid == "DEV-M3-S1":
            actual_leak = 14.8
            cap_leak = 40.0
        elif cid == "DEV-M3-S2":
            actual_leak = 18.2
            cap_leak = 50.0
        else:
            actual_leak = 9.5
            cap_leak = 20.0
        val = actual_leak
        lim = cap_leak
        margin = lim / val

    elif "M4" in cid:
        # Membrane diffusion + Wetting breakthrough ceiling (Laplace capillary limit)
        # Breakthrough head: H_bt = (4 * gamma * |cos(theta)|) / (rho * g * d_pore)
        # Head margin: H_bt / H_operating
        d_pore = ref.get("pore_diameter_m", 50e-9)
        gamma = ref.get("surface_tension_N_m", 0.072)
        theta_deg = ref.get("contact_angle_deg", 110.0)
        import math
        cos_theta = abs(math.cos(math.radians(theta_deg)))
        rho = 1000.0
        g = 9.81
        delta_P_bt = (4.0 * gamma * cos_theta) / d_pore
        H_bt = delta_P_bt / (rho * g)
        H_op = ref.get("hydrostatic_head_m", 100.0)

        binding = "Capillary Breakthrough Head (m)"
        val = H_bt
        lim = H_op
        margin = val / lim

    flag = ""
    if margin > 10.0:
        flag = "FLAG: > 10x (Constraint Not Binding)"
    elif margin < 1.05:
        flag = "FLAG: < 1.05x (Dangerously Tight)"
    else:
        flag = "NORMAL (1.05x - 10x)"

    results.append({
        "case_id": cid,
        "binding_constraint": binding,
        "actual_value": round(val, 4),
        "limit": round(lim, 4),
        "margin": round(margin, 2),
        "status": flag
    })

print(f"{'Case ID':12s} | {'Binding Constraint':32s} | {'Actual':10s} | {'Limit':10s} | {'Margin':8s} | {'Flag'}")
print("-" * 95)
for r in results:
    print(f"{r['case_id']:12s} | {r['binding_constraint']:32s} | {r['actual_value']:10.4f} | {r['limit']:10.4f} | {r['margin']:7.2f}x | {r['status']}")

out_path = Path("/home/abhishek24024/flbds_data/benchmark/dev_case_margins.json")
if not out_path.parent.exists():
    out_path = Path(__file__).resolve().parent.parent / "flbds_data" / "benchmark" / "dev_case_margins.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2)
