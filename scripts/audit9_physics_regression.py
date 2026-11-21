import numpy as np
from flbds.schema.enums import BoundaryTypeEnum, TemplateEnum
from flbds.schema.templates import TPL02Params
from flbds.physics.tpl02_pcm import (
    eval_tpl02,
    compute_composite_properties,
    neumann_analytical_lambda,
    solve_1d_enthalpy_stefan,
)

print('=== 1. PURE PARAFFIN 50 mm ===')
p_pure = TPL02Params(
    template_id=TemplateEnum.TPL_02,
    thickness_m=0.050,
    pcm_density_kg_m3=820.0,
    pcm_latent_heat_J_kg=210000.0,
    pcm_specific_heat_J_kgK=2000.0,
    matrix_volume_fraction=0.0,
    matrix_density_kg_m3=2700.0,
    matrix_specific_heat_J_kgK=900.0,
    k_eff_W_mK=0.2,
    melting_temp_degC=28.0,
    superheat_limit_K=10.0,
    heat_flux_W_m2=200.0,
    charge_hours=8.0,
    required_energy_J_m2=5.76e6,
)
res_pure = eval_tpl02(p_pure, bc_type=BoundaryTypeEnum.BC_FLUX, N_mesh=100)
print(f'Passed: {res_pure.passed}')
print(f"Surface superheat: {res_pure.metrics['surface_superheat_K']:.2f} K (target ~26.5 K)")
print(f"Melt depth: {res_pure.metrics['melt_depth_m']*1e3:.2f} mm (target ~29.5 mm)")

print('\n=== 2. COMPOSITE 40 mm (88/12 paraffin+foam) ===')
p_comp = TPL02Params(
    template_id=TemplateEnum.TPL_02,
    thickness_m=0.040,
    pcm_density_kg_m3=820.0,
    pcm_latent_heat_J_kg=210000.0,
    pcm_specific_heat_J_kgK=2000.0,
    matrix_volume_fraction=0.12,
    matrix_density_kg_m3=2700.0,
    matrix_specific_heat_J_kgK=900.0,
    k_eff_W_mK=2.8,
    melting_temp_degC=28.0,
    superheat_limit_K=10.0,
    heat_flux_W_m2=200.0,
    charge_hours=8.0,
    required_energy_J_m2=5.76e6,
)
rho_eff, L_eff, cp_eff, k_eff = compute_composite_properties(p_comp)
res_comp = eval_tpl02(p_comp, bc_type=BoundaryTypeEnum.BC_FLUX, N_mesh=60)
print(f'Passed: {res_comp.passed}')
print(f'Mass per area: {rho_eff * p_comp.thickness_m:.2f} kg/m2')
print(f"Surface superheat: {res_comp.metrics['surface_superheat_K']:.2f} K (target ~2.62 K)")
print(f"Melt depth: {res_comp.metrics['melt_depth_m']*1e3:.2f} mm (target ~37.6 mm)")

print('\n=== 3. NEUMANN ANALYTICAL STEFAN SOLUTION ===')
cp = 2000.0
L_fus = 210000.0
dT = 10.0
k = 0.2
rho = 820.0
alpha = k / (rho * cp)
t = 3600.0
stefan_num = cp * dT / L_fus
lam = neumann_analytical_lambda(stefan_num)
s_analytical = 2.0 * lam * np.sqrt(alpha * t)
num_res = solve_1d_enthalpy_stefan(
    L=0.05, k=k, rho=rho, cp=cp, L_fus=L_fus,
    bc_type=BoundaryTypeEnum.BC_TEMP, bc_val=dT, t_end=t, N=100
)
s_numerical = num_res['melt_depth_m']
rel_diff = abs(s_numerical - s_analytical) / s_analytical
print(f'Analytical melt depth: {s_analytical*1e3:.4f} mm')
print(f'Numerical melt depth:  {s_numerical*1e3:.4f} mm')
print(f'Relative difference:   {rel_diff*100:.3f}%')
print(f'Tolerance threshold:   < 1.000% (tolerance: 0.01)')

print('\n=== 4. MESH REFINEMENT CONVERGENCE ===')
N_values = [50, 100, 200]
melt_depths = []
for n in N_values:
    nr = solve_1d_enthalpy_stefan(
        L=0.05, k=k, rho=rho, cp=cp, L_fus=L_fus,
        bc_type=BoundaryTypeEnum.BC_TEMP, bc_val=dT, t_end=t, N=n
    )
    md = nr['melt_depth_m'] * 1e3
    melt_depths.append(md)
    print(f'N={n:3d}: melt depth = {md:.4f} mm')

print(f'Difference N=50 to N=100:  {abs(melt_depths[1] - melt_depths[0]):.4f} mm ({abs(melt_depths[1] - melt_depths[0])/melt_depths[0]*100:.3f}%)')
print(f'Difference N=100 to N=200: {abs(melt_depths[2] - melt_depths[1]):.4f} mm ({abs(melt_depths[2] - melt_depths[1])/melt_depths[1]*100:.3f}%)')
