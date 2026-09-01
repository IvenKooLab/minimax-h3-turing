# 07 · ComfyUI 升级窗口追踪

本机立场：**不是最新版教徒，每个版本都要回答"对 Turing + H3 有什么好处"再决定动不动刀。**

## 提速路线判决全景（截至本文）

先把"还能不能更快"一次说清：当前软件栈下 **5.7 分钟/镜（640×352 W4A8 4步）已经是这张卡的物理极限**，不存在马上能白捡的加速。剩余提速空间全部压在升级窗口上：

| 路线 | 判决 | 说明 |
|---|---|---|
| cu130 硬件反量化 | ✅ 已吃到 | kitchen CUDA 后端满血，当前速度的根因（见 [01](01-hardware-limits.md)），无额外动作 |
| SageAttention | ❌ 判死 | Triton INT8 内核 sm_75 编译失败（3.2.0–3.8.0 全版本）；CUDA 内核孤立可跑、接管线原生崩溃（见 [03](03-sageattention-crash.md)），升级窗口可重验 |
| T8 双时钟 | ⏳ 等版本 | 节点已装好，需要 v3 Layers API（ComfyUI ≥0.34），官方宣称配合加速 LoRA 再 +100% |
| PDD LoRA | ⏳ 等版本 | PR #15908 已进 master，等 release（见下文） |
| TE-Speed | ❌ 永久排除 | 短步数下语义崩坏，作品报废（见 [06](06-faq.md) 第 9 条） |
| RTX VSR 超分 | ✅ 可用 | 不是提速是补分辨率：640×352 → 1080p，47ms/帧 |

升级窗口全开后（T8 + PDD + 修复版 sage）的合计目标：**3 分钟/镜**。

## 当前基线

- ComfyUI **v0.33.1**：H3 W4A8 路线全绿，原生 AV 采样修复已内置（commit `bdcb886`）
- 升级方式：GitHub 直连不稳，走 jsdelivr 逐文件升级（同款网络环境的参考）

## v0.34.0 评估结论（已发布，决定：暂不升级）

- 主打稳定性和 bug 修复，亮点是视频转码流式化（不再全帧缓冲进内存）
- **无 H3 专属改动、无加载机制变化**
- 社区有 breaking bug 反馈，第一版不踩

现状全绿时不值得动刀。

## 升级触发条件（已达成一半）

**PR #15908「MiniMax-H3: Support PDD LoRA」已进 master**（未随 v0.34.0 发布）：

- PDD = Parallel Decoding Distillation（阿里 PAI 官方蒸馏加速）
- rank-64 + PDD Head Bank，8/4 步无 CFG
- 官方 4 步模式画质**可能优于**社区 Turbo LoRA

**行动项**：等包含 #15908 的 release（v0.34.1+）发布 → 触发升级演练 → PDD LoRA 与现役 Turbo LoRA 同 seed 对比 → 赢了换产线标配。

## 升级演练流程（到时照这个走）

1. 备份整个 ComfyUI 目录
2. jsdelivr 逐文件升级
3. 三件套冒烟：H3 t2v 出片 / 生图链路 / 批次产线
4. 任一失败 → 回滚备份
5. 顺手复测：SageAttention 新版本 on sm_75（见 [03](03-sageattention-crash.md)）、KJNodes 内置 H3 Sage 补丁（见 [06](06-faq.md) 第 8 条）

## 时效性情报

- **T8 双时钟采样器官方已开源**（hailuoai.com/h3-open），官方宣称 +100%——但它依赖 v3 Layers API，Turing 能不能吃上要看实现，升级窗口里一并验证
- H3 Max（fal.ai 联合后训练版）：**API 专属无开源权重**，本地不可用；关键镜头可付费走 API，本地党观望开源版跟进
