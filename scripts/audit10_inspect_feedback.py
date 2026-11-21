import json

def inspect_feedback():
    with open("flbds_data/audit9/a_noop_results.json") as f:
        data = json.load(f)

    runs = data.get("results", [])
    
    # Select 5 diverse runs that received feedback
    runs_with_feedback = [r for r in runs if len(r.get("feedback_history", [])) > 0]
    
    print(f"Total runs with feedback: {len(runs_with_feedback)}")
    
    sample_indices = [0, 5, 10, 15, 20]
    if len(runs_with_feedback) < 25:
        sample_indices = list(range(min(5, len(runs_with_feedback))))

    print("="*80)
    print("AUDIT ROUND 10 - SECTION B1: FEEDBACK TEXT INSPECTION")
    print("="*80)

    for i, idx in enumerate(sample_indices, 1):
        r = runs_with_feedback[idx]
        cid = r["case_id"]
        seed = r["seed"]
        first_fb = r["feedback_history"][0]
        fb_text = first_fb.get("previous_reason")
        
        # Determine producing function and tier
        tier = "Unknown"
        func_name = "Unknown"
        
        if "Screen check failed:" in fb_text or "Capacity bound violated:" in fb_text:
            tier = "Screen Tier (M5-Screen lumped capacity bound)"
            func_name = "flbds.physics.capacity_bound.check_problem_satisfiability"
        elif "Physics check failed:" in fb_text:
            tier = "Evaluator Tier (M5-Eval numerical / PDE solver)"
            if "TPL_02" in str(r.get("turn3_response")) or "1D Stefan" in fb_text or "Melt depth" in fb_text or "superheat" in fb_text:
                func_name = "flbds.physics.tpl02_pcm.eval_tpl02"
            elif "TPL_08" in str(r.get("turn3_response")) or "duty" in fb_text or "Pressure drop" in fb_text or "eps=" in fb_text:
                func_name = "flbds.physics.tpl08_countercurrent.eval_tpl08"
            elif "TPL_09" in str(r.get("turn3_response")) or "Inner heat leakage" in fb_text or "sub-ambient" in fb_text:
                func_name = "flbds.physics.tpl09_radiative.eval_tpl09"
            elif "TPL_10" in str(r.get("turn3_response")) or "Bosanquet" in fb_text or "Coupled flux" in fb_text or "R_pore" in fb_text:
                func_name = "flbds.physics.tpl10_diffusion.eval_tpl10"
            elif "TPL_03" in str(r.get("turn3_response")) or "Water budget" in fb_text or "RH=" in fb_text:
                func_name = "flbds.physics.tpl03_evaporation.eval_tpl03"
            else:
                func_name = "flbds.physics.tplXX_evaluator"
        elif "Selected template" in fb_text:
            tier = "Scorer Own Message (Template Selection Gate)"
            func_name = "run_a_noop_benchmark.evaluate_design (template checker)"
        elif "JSON" in fb_text or "parse" in fb_text:
            tier = "Scorer Own Message (Syntax/Schema Gate)"
            func_name = "run_a_noop_benchmark.evaluate_design (schema parser)"
            
        print(f"\nExample {i}:")
        print(f"  Case: {cid} (Seed {seed})")
        print(f"  Exact Feedback Text: \"{fb_text}\"")
        print(f"  Producing Function: `{func_name}`")
        print(f"  Tier Classification: {tier}")

if __name__ == "__main__":
    inspect_feedback()
