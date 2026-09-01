# 04 · 社区经验验证：可直接抄的三点

以下三点来自社区同款 2080Ti 22G 用户的实测分享，全部在本机产线上验证过。

## 1. SageAttention 在 Turing 照开仍快 16.8%

- **结论**：Turing 上开 SageAttention 有 16.8% 提速，且运行日志里的 fallback 警告是**噪音，不是病徵**，不要试图"修好"它
- **适用条件**：⚠️ 版本敏感——该结论对应 sageattention **1.0.6** + torch 2.6.0 + cu124 + triton 3.2.0。我们用 2.2.0 + torch 2.9 直接管线崩溃，见 [03](03-sageattention-crash.md)
- **行动**：环境符合就用；不符合先别硬上

## 2. `--reserve-vram` 的正确取值

| 场景 | 取值 |
|---|---|
| 5-6 秒短片（124 帧内） | **2.5** ✅ 本机验证 |
| 15 秒长片（362 帧） | **4** |
| 桌面/显示器共享这张卡 | 任何时候都要留 headroom |

取小了会 TDR 黑屏（驱动复位），取大了浪费显存。启动参数模板见 [scripts/h3_launch.example.sh](../scripts/h3_launch.example.sh)。

## 3. RTX VSR 超分在 Turing 可用

- **结论**：NVIDIA VSR（视频超分）在 Turing 卡上完全可用，新 nvidia-vfx wheel 实测 **47ms/帧**
- **用法**：H3 原生生成 640×352（快）→ 抽帧 → RTX VSR 超分到 1080p → 合回视频
- **为什么这么干**：低分辨率生成是这张卡的速度来源，画质损失用超分补，比直接生成 1080p（每步时间暴涨）划算得多
- 社区同款卡的 15 秒 1080p 成片（23 分钟）走的就是这条"960×540 生成 → VSR 放大"路线

## 一个反向结论：T8 BlockCache 别装了

T8 双时钟采样器（MiniMaxH3BlockCacheT8）官方已开源，但：

- 节点在 sm_75 + 当前 ComfyUI 上**注册失败**（依赖 v3 Layers API）
- v0.33.1 已内置 H3 原生 AV 采样修复（commit `bdcb886`），DualClock 插件非必需

等升级窗口一并解决，见 [07](07-upgrade-watch.md)。

---

下一篇：[05 · 工作流说明](05-workflows.md)
