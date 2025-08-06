<!--
SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Running DeepSeek-R1 Disaggregated with WideEP on GB200s (NVFP4)

Together with the SGLang team, we have implemented NVFP4 support for DeepSeek-R1 on Blackwell GPUs! While many performance optimization are still ongoing, we wanted to provide an initial recipe that allows you to deploy the WideEP + P/D disaggregation setup in NVFP4!

<details>
<summary>Some SGLangPRs that should improve performance</summary>

- [#7667](https://github.com/sgl-project/sglang/pull/7667): Add `--enable-flashinfer-fp4-allgather` for FlashInfer cutlass MoE DP (max throughput)  
  _10% e2e speedup_
- [#8638](https://github.com/sgl-project/sglang/pull/8638): FP8 KV Cache
- [#8588](https://github.com/sgl-project/sglang/pull/8588): Use FlashInfer's TRTLLM FP8 Blockscale GEMM  
  _6% e2e improvement for low latency_
- [#8280](https://github.com/sgl-project/sglang/pull/8280): Enables all-gather for DP when using padding  
  [#8539](https://github.com/sgl-project/sglang/pull/): Similar PR enables reducescatter instead of all-reduce following MOE/MLP layers in DeepSeek  
  _5% e2e improvement_
- [#8811](https://github.com/sgl-project/sglang/pull/8811): Fix trtllm_fp4_block_scale_moe API routing_logits dim check (num_experts consistency)
- [#8770](https://github.com/sgl-project/sglang/pull/8770): Add changes required for unit tests in fused routed scaling
- [#8690](https://github.com/sgl-project/sglang/pull/8690): [2/2] SGLang: Fuse routed scaling factor into select_experts 
  _Fuse multiply by routed_scaling_factor into select_experts, following TRT-LLM. 10% speed up on low latency_
- [#8330](https://github.com/sgl-project/sglang/pull/8330): Add unit test for flashinfer fp4 moe

</details>

## Instructions

1. Apply the following diff to the SGLang GB200 Dockerfile (temporary until [#8811](https://github.com/sgl-project/sglang/pull/8811) is merged)

```diff
diff --git a/docker/Dockerfile.gb200 b/docker/Dockerfile.gb200
index 90a80ec0b..6e1cd9245 100644
--- a/docker/Dockerfile.gb200
+++ b/docker/Dockerfile.gb200
@@ -53,10 +53,11 @@ RUN mkdir -p /tmp/gdrcopy && cd /tmp \
 RUN ln -sf /usr/lib/$(uname -m)-linux-gnu/libmlx5.so.1 /usr/lib/$(uname -m)-linux-gnu/libmlx5.so

 # Clone and install SGLang
+# Hack to get PR 8811
 WORKDIR /sgl-workspace
 RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel html5lib six \
- && git clone --depth 1 https://github.com/sgl-project/sglang.git \
- && cd sglang \
+ && git clone https://github.com/wenscarl/sglang.git \
+ && cd sglang && git checkout fix_trtllm_moe_create_weights \
  && case "$CUDA_VERSION" in \
       12.6.1) CUINDEX=126 ;; \
       12.8.1) CUINDEX=128 ;; \
```

2. Build the SGLang dockerfile

```bash
docker build \
  -f docker/Dockerfile.gb200 \
  -t sgl-blackwell-wideep-8811 \
  --build-arg BUILD_TYPE=blackwell \
  --build-arg CUDA_VERSION=12.8.1 \
  .
```

3. 