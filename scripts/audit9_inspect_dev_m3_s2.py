import json

with open('/home/abhishek24024/flbds_data/audit8/b0_t07_exposed_seeds1to5.json') as f:
    data = json.load(f)

for r in data['results']:
    if r['case_id'] == 'DEV-M3-S2':
        s = r['seed']
        p = r.get('parsed_json', {})
        passed = r['passed']
        print(f"Seed {s}: passed={passed}")
        print(f"  solar_irradiance_W_m2: {p.get('solar_irradiance_W_m2')}")
        print(f"  T_sky_degC: {p.get('T_sky_degC')}")
        print(f"  T_ambient_degC: {p.get('T_ambient_degC')}")
        print(f"  T_inner_degC: {p.get('T_inner_degC')}")
        print(f"  h_conv_W_m2K: {p.get('h_conv_W_m2K')}")
        print(f"  absorptivity_solar: {p.get('absorptivity_solar')}")
        print(f"  emissivity_thermal: {p.get('emissivity_thermal')}")
        print(f"  reason: {r.get('reason')}")
