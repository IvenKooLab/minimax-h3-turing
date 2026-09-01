# minimax-h3-turing

**在 2080Ti 22G 魔改卡（Turing / sm_75）上跑通 MiniMax H3 本地视频生成的实测手册。**

包含硬件限制分析、量化路线选择（W4A8 vs W4A4）、SageAttention 兼容性崩溃实录、社区经验验证、可直接导入的 compat 工作流，以及一整页踩坑 FAQ。全部结论来自真实产线运行，非纸面推演。

> 适用范围：所有 Turing 架构（sm_75）显卡——2080Ti 魔改 22G / 2080Ti 11G 可参考，显存越接近 22G 越接近本文配置。

## TL;DR 速览

| 问题 | 结论 |
|---|---|
| 2080Ti 22G 能跑 H3 吗？ | ✅ 能。W4A8 compat 快路线，640×352·124 帧·4 步·原生音频，**最低 3.5-4 分钟/条**（标准镜头约 5.7 分钟） |
| 量化怎么选？ | **DiT 必须 INT8（W4A8）**。W4A4 误差 18 倍，出彩色撕裂 |
| SageAttention 能用吗？ | ⚠️ 孤立内核可用，接入 H3 管线在 torch 2.9 + triton 下**原生崩溃**（详见 03） |
| 速度还能更快吗？ | ⚠️ **T8 BlockCache 激进档 -43%（2.7 分钟/镜，草稿可用）**，成片保 5.7 分钟基线；PDD 等升级窗口（详见 07/08） |
| 最优启动参数？ | `--reserve-vram 2.5 --vram-headroom 0.5 --disable-pinned-memory`（5-6 秒短片） |
| 低分辨率不够用？ | 生成 640×352 → 抽帧 → **RTX VSR 超分 1080p**，47ms/帧，Turing 可用 |

## 目录

| 文档 | 内容 |
|---|---|
| [01 硬件先天限制](docs/01-hardware-limits.md) | sm_75 缺什么、带宽差距、为什么 W4A8 是唯一路线 |
| [02 量化路线实测](docs/02-w4a8-vs-w4a4.md) | W4A4 vs W4A8 误差数据、产线速度、社区同款卡成绩 |
| [03 SageAttention 崩溃实录](docs/03-sageattention-crash.md) | 2.2.0 wheel 接入管线崩溃 → 定位 → 回滚验证全过程 |
| [04 社区经验验证](docs/04-community-tips.md) | 可直接抄的三点 + 适用条件 |
| [05 工作流说明](docs/05-workflows.md) | compat t2v/i2v 工作流导入与占位符替换 |
| [06 踩坑 FAQ](docs/06-faq.md) | 火绒/staging 卡死、prompt_id 去重、TE-Speed 排除、音频削波等 10 个坑 |
| [07 升级窗口追踪](docs/07-upgrade-watch.md) | 提速路线判决全景、v0.34 评估、PDD LoRA #15908、T8 官方开源 |
| [08 T8 四步实测](docs/08-t8-blockcache-4step.md) | 43% 提速实测：默认参数零命中、激进档 2.7 分钟/镜、同 seed 复现性代价 |
| [workflows/](workflows/) | 可导入的 compat 工作流 JSON |
| [scripts/](scripts/) | 防黑屏启动参数示例 |

## 环境

- GPU：2080Ti 22G 魔改（Turing，sm_75）
- ComfyUI：v0.33.1（H3 W4A8 路线已内置原生 AV 采样修复）
- 路线：h3lite W4A8 compat（T8 BlockCache 节点在 sm_75 不可用，见 07）

## 双平台镜像

| 平台 | 地址 |
|---|---|
| Gitee（主站） | https://gitee.com/IvenKooLab/minimax-h3-turing |
| GitHub | https://github.com/IvenKooLab/minimax-h3-turing |

两边内容自动同步（Gitee 为权威源）。Issue/PR 请到 Gitee。

## License

MIT
