import re

def update_handover():
    with open("docs/HANDOVER.md", "r") as f:
        content = f.read()

    # 1. Update Martins DOI in Verified Ledger table
    old_martins = r'\| Martins 2018 title is \*Locally-curved geometry generates bending cracks in the African elephant skin\* \| `api_responses/martins_2018_crossref.json` \| `python3 scripts/verify_quotes.py --doc_id martins_2018_crossref --quote "Locally-curved geometry"` \|'
    new_martins = '| Martins 2018 (DOI: `10.1038/s41467-018-06257-3`) title is *Locally-curved geometry generates bending cracks in the African elephant skin* | `api_responses/martins_2018_crossref.json` | `python3 scripts/verify_quotes.py --doc_id martins_2018_crossref --quote "Locally-curved geometry"` |'
    
    if old_martins in content:
        content = content.replace(old_martins, new_martins)
    else:
        # Regex replacement if exact match fails
        content = re.sub(
            r'\| Martins 2018 title is \*Locally-curved geometry.*',
            new_martins,
            content
        )

    # 2. Add Invalid Round 7 Run, Round 8 Reversals Withdrawal, and Pooled Table Withdrawal to Withdrawn Ledger (Section 5)
    withdrawn_needle = r'| **PMC9234854 Duality** | **Withdrawn**. Document does not exist in corpus; appeared as both dropped and accepted due to drafting hallucination. |'
    withdrawn_additions = """| **PMC9234854 Duality** | **Withdrawn**. Document does not exist in corpus; appeared as both dropped and accepted due to drafting hallucination. |
| **Round 7 B0 "Exposed Limits" Re-Run** | **Withdrawn (Invalid Execution)**. Round 7 run was identical to earlier run (broker jobs 7769 and 7772 did not execute new prompts; md5 identical). Valid re-run executed in Round 8/9 (`audit8/b0_t07_exposed_seeds1to5.json`). |
| **Round 8 Card Reversals** | **Withdrawn**. Round 8 reversals for `PMC8593863`, `US-PAT-E-0478`, `US-PAT-E-0427`, and `US-PAT-F-0220` were agent opinion. Historical Round 3 MAJOR verdicts stand based on grounded flaws in pilot silver cards. |
| **22/27/1 Pooled Card Quality Table** | **Withdrawn**. Merged heterogeneous sample distributions without re-deriving card verdicts from corpus text. |"""

    content = content.replace(withdrawn_needle, withdrawn_additions)

    # 3. Update B0 baseline numbers in Section 4 and Section 6
    # In Section 4:
    old_b0_sec4 = r'| B0 unassisted physics pass rate is 25.0% (T=0.0) and 20.0% (T=0.7) | `benchmark/b0_redo_results.json`, `b0_temp07_results.json` | `jq .categories.pass benchmark/b0_redo_results.json` |'
    new_b0_sec4 = '| B0 unassisted physics pass rate is 23.3% (14/60, valid exposed limits run; 33.3% under card environment rescore) | `audit8/b0_t07_exposed_seeds1to5.json`, `audit9/b0_rescore_environment_flips.json` | `jq .total_passes flbds_data/audit8/b0_t07_exposed_seeds1to5.json` |'
    content = content.replace(old_b0_sec4, new_b0_sec4)

    # In Section 6: Add Audit Round 9 Valid Exposed Limits and A-NoOp benchmarks
    old_b0_table_header = "| Metric | B0 at T=0.0 (N=60) | B0 at T=0.7 (N=60) | Artifact Path |"
    new_b0_table_header = "| Metric | B0 Valid Exposed (N=60) | A-NoOp 3-Turn Feedback (N=60) | Artifact Path |"
    
    b0_table_old = """| Metric | B0 at T=0.0 (N=60) | B0 at T=0.7 (N=60) | Artifact Path |
| :--- | :---: | :---: | :--- |
| **Parse Failures** | **0 / 60 (0.0%)** [0.0%, 6.0%] | **0 / 60 (0.0%)** [0.0%, 6.0%] | `benchmark/b0_redo_results.json` |
| **Schema Failures** | **0 / 60 (0.0%)** [0.0%, 6.0%] | **0 / 60 (0.0%)** [0.0%, 6.0%] | `benchmark/b0_redo_results.json` |
| **Template Errors** | **3 / 60 (5.0%)** [1.7%, 13.7%] | **4 / 60 (6.7%)** [2.6%, 15.9%] | `benchmark/b0_temp07_results.json` |
| **Physics Failures**| **42 / 60 (70.0%)** [57.5%, 80.1%] | **44 / 73.3%** [61.0%, 82.9%] | `benchmark/b0_temp07_results.json` |
| **Satisfiable Passes**| **15 / 60 (25.0%)** [15.8%, 37.2%] | **12 / 60 (20.0%)** [11.8%, 31.8%] | `benchmark/b0_temp07_results.json` |
| Split 1 Pass Rate | 6 / 20 (30.0%) [14.5%, 51.9%] | 2 / 20 (10.0%) [2.8%, 30.1%] | `benchmark/b0_temp07_results.json` |
| Split 2 Pass Rate | 4 / 20 (20.0%) [8.1%, 41.6%] | 6 / 20 (30.0%) [14.5%, 51.9%] | `benchmark/b0_temp07_results.json` |
| Split 3 Pass Rate | 5 / 20 (25.0%) [11.2%, 46.9%] | 4 / 20 (20.0%) [8.1%, 41.6%] | `benchmark/b0_temp07_results.json` |"""

    b0_table_new = """| Metric | B0 Valid Exposed (T=0.7, N=60) | A-NoOp Feedback (T=0.7, N=60) | Artifact Path |
| :--- | :---: | :---: | :--- |
| **Parse Failures** | **0 / 60 (0.0%)** [0.0%, 6.0%] | **0 / 60 (0.0%)** [0.0%, 6.0%] | `audit8/b0_t07_exposed_seeds1to5.json` |
| **Schema Failures** | **0 / 60 (0.0%)** [0.0%, 6.0%] | **0 / 60 (0.0%)** [0.0%, 6.0%] | `audit8/b0_t07_exposed_seeds1to5.json` |
| **Template Errors** | **0 / 60 (0.0%)** [0.0%, 6.0%] | **0 / 60 (0.0%)** [0.0%, 6.0%] | `audit8/b0_t07_exposed_seeds1to5.json` |
| **Physics Failures**| **46 / 60 (76.7%)** [64.6%, 85.6%] | **15 / 60 (25.0%)** [15.8%, 37.2%] | `audit9/a_noop_results.json` |
| **Satisfiable Passes**| **14 / 60 (23.3%)** [14.4%, 35.4%] | **45 / 60 (75.0%)** [62.8%, 84.2%] | `audit9/a_noop_results.json` |
| Split 1 Pass Rate | 2 / 20 (10.0%) [2.8%, 30.1%] | 14 / 20 (70.0%) [48.1%, 85.5%] | `audit9/a_noop_results.json` |
| Split 2 Pass Rate | 7 / 20 (35.0%) [18.1%, 56.7%] | 16 / 20 (80.0%) [58.4%, 91.9%] | `audit9/a_noop_results.json` |
| Split 3 Pass Rate | 5 / 20 (25.0%) [11.2%, 46.9%] | 15 / 20 (75.0%) [53.1%, 88.8%] | `audit9/a_noop_results.json` |

*(Note: Under ground-truth card environment rescoring with fixed 10 K superheat caps, B0 baseline passes reach 20 / 60 (33.3%) [22.7%, 45.9%]; artifact: `audit9/b0_rescore_environment_flips.json`)*"""

    content = content.replace(b0_table_old, b0_table_new)

    with open("docs/HANDOVER.md", "w") as f:
        f.write(content)

    print("Updated docs/HANDOVER.md successfully.")

if __name__ == "__main__":
    update_handover()
