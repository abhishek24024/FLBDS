# Measured vLLM Throughput on NVIDIA H200 (141 GB SXM)

| Role | Model | Quantization | Prompts | Prompt Tokens | Output Tokens | Measured Decode (tok/s) | Doc Assumption Decode | Ratio (Measured/Assumed) | Peak VRAM (GB) |
|---|---|---|---|---|---|---|---|---|---|
| filter | Qwen2.5-7B-Instruct | BF16 | 10 | 11390 | 2560 | **1658.0** | 12000 | 0.14x | 0.0 GB |
| critic | Qwen2.5-32B-Instruct-FP8 | BF16 | 10 | 11390 | 2289 | **593.2** | 5000 | 0.12x | 0.0 GB |
| teacher | Qwen2.5-72B-Instruct-FP8 | BF16 | 10 | 11390 | 2390 | **325.3** | 2000 | 0.16x | 0.0 GB |
