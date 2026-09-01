# 07 · ComfyUI 升级窗口追踪

本机立场：**不是最新版教徒，每个版本都要回答"对 Turing + H3 有什么好处"再决定动不动刀。**

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
