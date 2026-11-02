import json
import random

with open("/home/abhishek24024/flbds_data/audit7/b0_t07_exposed_seeds1to5.json") as f:
    d = json.load(f)

runs = d.get("results", [])
passes = [r for r in runs if r.get("passed") is True]
fails = [r for r in runs if r.get("passed") is False]

random.seed(61)
sampled_pass = random.sample(passes, 3)
sampled_fail = random.sample(fails, 3)

data = {
    "sampled_passes": sampled_pass,
    "sampled_fails": sampled_fail
}

with open("/home/abhishek24024/flbds_data/audit8/seed61_sampled_6_transcripts.json", "w") as f:
    json.dump(data, f, indent=2)

print("Saved 6 transcripts to /home/abhishek24024/flbds_data/audit8/seed61_sampled_6_transcripts.json")
