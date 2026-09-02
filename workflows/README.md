# Workflows · 可直接导入的三件套

全部在本机 2080Ti 22G + ComfyUI v0.33.1 + W4A8 mixed 权重上实测验证（2026-09-01，同晚同 seed A/B）。

| 工作流 | 用途 | 单镜实测 | 选它之前必读 |
|---|---|---|---|
| [h3_w4a8_t2v_compat_api.json](h3_w4a8_t2v_compat_api.json) | **文生视频 · 成片档** | 280 s（4.7 min） | 无 T8，同 seed 可复现——失败镜头可原样重提、审片结果可重现，**一切进正片的镜头用它** |
| [h3_w4a8_t2v_t8draft_api.json](h3_w4a8_t2v_t8draft_api.json) | **文生视频 · 草稿快跑档** | 160 s（2.7 min，**-43%**） | T8 BlockCache 阈值 1.0；**同 seed 不可复现**（缓存命中改变采样轨迹）→ 只用于试 prompt / 选镜头方向，选中的是"方向"不是成片。依据见 [docs/08](../docs/08-t8-blockcache-4step.md) |
| [h3_w4a8_i2v_compat_api.json](h3_w4a8_i2v_compat_api.json) | **图生视频（首帧锚定 / 锁脸）** | — | 需要自己准备首帧图；文件名指向你本地实际权重 |

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
