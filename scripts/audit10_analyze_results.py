import json

def print_summary(data, name):
    s = data["summary"]
    print(f"\n{'='*70}")
    print(f"BENCHMARK: {name}")
    print(f"{'='*70}")
    print(f"Total Runs: {s.get('total_runs')}")
    print(f"Total Passes: {s.get('total_passes')} ({s.get('pass_rate', 0)*100:.1f}%)")
    print(f"95% Wilson CI: [{s.get('wilson_ci', [0,0])[0]*100:.1f}%, {s.get('wilson_ci', [0,0])[1]*100:.1f}%]")
    print(f"Parse Failures: {s.get('parse_failures', 0)}")
    print(f"Schema Failures: {s.get('schema_failures', 0)}")
    print(f"Template Errors: {s.get('template_choice_errors', 0)}")
    print(f"Physics Failures: {s.get('physics_failures', 0)}")
    print("\nPer-Split Breakdown:")
    for sp_name, sp in s.get("splits", {}).items():
        print(f"  {sp_name}: {sp.get('passes')}/{sp.get('total')} ({sp.get('pass_rate')*100:.1f}%) [CI: {sp.get('ci')[0]*100:.1f}%, {sp.get('ci')[1]*100:.1f}%]")

def main():
    # 1. B0 Self Critique
    with open("flbds_data/audit10/b0_self_critique_results.json") as f:
        b0_data = json.load(f)
    print_summary(b0_data, "B0 (3 Turns Text Self-Critique)")

    # 2. Oracle Feedback
    with open("flbds_data/audit10/oracle_feedback_results.json") as f:
        ora_data = json.load(f)
    print_summary(ora_data, "Oracle (3 Turns Evaluator-Tier Feedback)")

    # 3. Screen-Only
    with open("flbds_data/audit10/screen_only_results.json") as f:
        scr_data = json.load(f)
    ss = scr_data["summary"]
    print(f"\n{'='*70}")
    print(f"BENCHMARK: Screen-Only (Lumped M5-Screen Capacity Feedback)")
    print(f"{'='*70}")
    print(f"Total Runs: {ss.get('total_runs')}")
    print(f"PVR_screen: {ss.get('pvr_screen_count')}/{ss.get('total_runs')} ({ss.get('pvr_screen')*100:.1f}%) [CI: {ss.get('pvr_screen_ci')[0]*100:.1f}%, {ss.get('pvr_screen_ci')[1]*100:.1f}%]")
    print(f"PVR_eval: {ss.get('pvr_eval_count')}/{ss.get('total_runs')} ({ss.get('pvr_eval')*100:.1f}%) [CI: {ss.get('pvr_eval_ci')[0]*100:.1f}%, {ss.get('pvr_eval_ci')[1]*100:.1f}%]")
    print(f"Screen-to-Eval Gap: {ss.get('overall_screen_to_eval_gap')*100:.1f}%")
    print("\nPer-Split Screen vs Eval:")
    for sp_name, sp in ss.get("splits", {}).items():
        print(f"  {sp_name}: PVR_screen={sp.get('pvr_screen')*100:.1f}% | PVR_eval={sp.get('pvr_eval')*100:.1f}% | Gap={sp.get('screen_to_eval_gap')*100:.1f}%")

if __name__ == "__main__":
    main()
