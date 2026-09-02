# Workflows · 可直接导入的四件套

全部在本机 2080Ti 22G + ComfyUI v0.33.1 + W4A8 mixed 权重上实测验证（同晚同 seed A/B，t2v 于 09-01、i2v 于 09-02）。

| 工作流 | 用途 | 单镜实测 |
|---|---|---|
| [t2v 成片档](#1-文生视频--成片档) | 一切进正片的镜头 | 280 s（4.7 min） |
| [t2v 草稿快跑档](#2-文生视频--草稿快跑档-t8--43) | 试 prompt / 选镜头方向 | 160 s（2.7 min，**-43%**） |
| [i2v 成片档](#3-图生视频--首帧锚定锁脸) | 锁脸 / 画面续接·正片 | 420 s（7.0 min） |
| [i2v 草稿快跑档](#4-图生视频--草稿快跑档-t8--38) | 锁脸镜头的草稿预览 | 260 s（4.3 min，**-38%**） |

---

## 1. 文生视频 · 成片档

![t2v final](preview/t2v_final.jpg)

**文件**：[h3_w4a8_t2v_compat_api.json](h3_w4a8_t2v_compat_api.json) · **实测 280 s/镜**

无 T8，同 seed **可复现**——失败镜头可原样重提、审片结果可重现。**一切要进正片的镜头用它。**

## 2. 文生视频 · 草稿快跑档（T8，-43%）

![t2v draft](preview/t2v_draft.jpg)

**文件**：[h3_w4a8_t2v_t8draft_api.json](h3_w4a8_t2v_t8draft_api.json) · **实测 160 s/镜**

T8 BlockCache 阈值 1.0，快 43%。**同 seed 不可复现**（缓存命中改变采样轨迹）→ 只用于试 prompt / 选镜头方向，选中的是"方向"不是成片。依据见 [docs/08](../docs/08-t8-blockcache-4step.md)。

> **上面两张预览图是同一个 seed（3013）、同一条提示词生成的**——这正是 T8 的核心特性：轨迹分叉，产出**同质量、不同画面**（构图/细节/光影同级，内容有偏移）。含义：草稿档选的是「这个 prompt 大概出什么方向」，成片档重跑得到可复现的正式镜头。

## 3. 图生视频 · 首帧锚定（锁脸）· 成片档

![i2v](preview/i2v.jpg)

**文件**：[h3_w4a8_i2v_compat_api.json](h3_w4a8_i2v_compat_api.json) · **实测 420 s/镜（热跑）**

需要一个首帧图（角色标准帧/已验收镜头抽帧），`Picture 1 is fully referenced` 锚定——脸一致率显著高于纯文生视频。同 seed 可复现。仓库用默认首帧占位，导入后换成你自己的图。

## 4. 图生视频 · 草稿快跑档（T8，-38%）

![i2v draft](preview/i2v_draft.jpg)

**文件**：[h3_w4a8_i2v_t8draft_api.json](h3_w4a8_i2v_t8draft_api.json) · **实测 260 s/镜**

锁脸镜头的草稿预览：快 38%，**绝对省 160s/镜比 t2v 草稿档（省 120s）更多**——镜头越贵 T8 省得越多。用法与铁律同 t2v 草稿档：只看方向，成片用成片档重跑。

---

## 导入三步

1. ComfyUI 界面拖入 JSON，或放到 `user/default/workflows/`
2. 把文本节点的 `__H3_PROMPT__` 占位符换成你的提示词（i2v 另需换首帧加载节点）
3. 核对模型文件名与你本地 `models/` 一致（不同时间下载的 W4A8 权重命名带不同 hash 后缀，改成本地的名字即可）

## 前置依赖

- 模型组：W4A8 mixed DiT + 双 VAE（video fp16 / audio fp32）+ qwen3vl_4b text encoder + ClipProj + fl2v Turbo 4step LoRA（清单见 [docs/05](../docs/05-workflows.md)）
- **草稿档额外需要**：[T8mars/comfyui-minimax-h3-blockcache-T8](https://github.com/T8mars/comfyui-minimax-h3-blockcache-T8) 节点包（装到 `custom_nodes/` 重启即注册，v0.33.1 可用——无需升级 ComfyUI）
- 启动参数（防 TDR/OOM）：`--reserve-vram 2.5 --vram-headroom 0.5 --disable-pinned-memory`，模板见 [scripts/h3_launch.example.sh](../scripts/h3_launch.example.sh)

## 两个已知的坑（草稿档必读）

1. **T8 节点是 v3 API 节点**：在 ComfyUI 界面里手拖参数没问题，但如果你用 `/prompt` API 提交，**全部 8 个输入必须显式给全**——v3 节点不走服务端默认值，缺一个就 400 `required_input_missing`（工作流 JSON 里已全部显式写好，直接用不会踩）。
2. **默认阈值 0.12 在 4 步路线是负优化**：0 次命中还白付缓存管理开销（实测 290s vs 280s）。别手贱改回默认值——想要 4 步提速就得 1.0，机理与数据见 [docs/08](../docs/08-t8-blockcache-4step.md)。
