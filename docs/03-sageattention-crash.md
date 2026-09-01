# 03 · SageAttention 崩溃实录（Turing + torch 2.9）

这是一篇"失败报告"——但它能帮你省掉一整天的折腾。

## 背景

社区有明确结论：SageAttention 在 Turing 上**照开也能快 16.8%**，且 "fallback 是噪音不是病徵"。听起来 2080Ti 也能白捡 17%，于是我们做了完整的接入实验。

## 实验环境

| 组件 | 版本 |
|---|---|
| sageattention wheel | **2.2.0**（+cu130/torch2.9-and-higher.post4，cp39-abi3） |
| triton | triton-windows |
| 节点包 | ComfyUI-KJNodes（含 PatchSageAttentionKJ 及 H3 专属节点） |
| ComfyUI | v0.33.1 |
| GPU | 2080Ti 22G（sm_75） |

## 实验结果

### ✅ 孤立内核：可用

`sageattn_qk_int8_pv_fp16_cuda` 这个 CUDA 内核在 sm_75 上**编译并运行成功**。这说明 SageAttention 的 CUDA 路径（非 Triton 路径）在 Turing 上是活的。

### ❌ 接入 H3 真实管线：原生崩溃

把 Sage 补丁接进 H3 工作流后，ComfyUI 进程触发 `python313.dll` 原生崩溃（不是 Python 异常，是进程级死亡）。定位：**SageAttention 2.2.0 的 Triton 路径在 sm_75 上直接编译失败**，失败发生在管线内部，无法被 try/except 兜住。

### 回滚验证

- 全部卸载/移除补丁 → 产线对照镜头 **340s 正常出片**，回到基线
- 崩溃现场的工作流已存档（供升级窗口后复测）

## 为什么社区说"能用"而我们崩了

关键在**版本组合**：

| | 社区 16.8% 结论的环境 | 本机环境 |
|---|---|---|
| torch | 2.6.0 + cu124 | 2.9.x |
| triton | 3.2.0 | 更新的 triton-windows |
| sageattention | 1.0.6 | 2.2.0 |

1.0.6 时代的 Turing 路径和 2.2.0 的 Triton 化实现不是一套代码。**别拿新版本 wheel 硬上，也别拿旧结论安慰自己。**

## 给 Turing 用户的行动建议

1. torch 2.6.0 + cu124 环境可以试 sageattention **1.0.6**（社区验证过的组合）
2. torch ≥ 2.9 环境装 2.2.0：孤立内核能跑，**接管线必炸，不要在生产环境试**
3. 等升级窗口：SageAttention 新版本若恢复非 Triton 路径或 triton-windows 支持 sm_75 编译，复测一次即可
4. 崩溃是进程级的——任何自动化产线都要有"看门狗 + 断点续跑"兜底（本机用同种子重提机制，崩溃后自动恢复）

---

下一篇：[04 · 社区经验验证](04-community-tips.md)
