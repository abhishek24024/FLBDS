import os
import sys
os.environ["PATH"] = "/home/abhishek24024/flbds_env/bin:" + os.environ.get("PATH", "")
sys.path.insert(0, '/home/abhishek24024/flbds')
import json
from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams
from pydantic import TypeAdapter
from flbds.schema.templates import TemplateParameters

ta = TypeAdapter(TemplateParameters)
schema = ta.json_schema()

llm = LLM(
    model="/home/abhishek24024/flbds_data/models/Qwen2.5-7B-Instruct",
    max_model_len=4096,
    trust_remote_code=True,
    gpu_memory_utilization=0.3,
)

sop = StructuredOutputsParams(json=schema)
sp = SamplingParams(temperature=0.0, max_tokens=512, structured_outputs=sop)

prompt = "<|im_start|>user\nGenerate a JSON object conforming to TPL_02 for phase change material storage with thickness 0.05m and k_eff 1.5 W/mK.<|im_end|>\n<|im_start|>assistant\n"

out = llm.generate([prompt], sp)
text = out[0].outputs[0].text
print("=== GENERATED TEXT ===")
print(text)
parsed = ta.validate_python(json.loads(text))
print("=== VALIDATION SUCCESS ===")
print(type(parsed), parsed.template_id)
