# 09 · PDD 提前落地：不等 release 的 master backport 实录

> 2026-09-03。「等含 #15908 的 release」是稳妥路线，但我们选择自己把 PDD 移植进来——一次成功，附带三个坑的完整解法。同 seed 对照：**PDD 8步 + T8 = 210s/镜（-34%），同时拿官方蒸馏画质**。

## TL;DR

| 配置（同 seed 3013，master@345c919，热跑） | 时长 | 说明 |
|---|---|---|
| Turbo 4 步（无 T8） | 320s | master 环境基线（0.33.1 为 280s） |
| PDD 8 步（无 T8） | 600s | 官方蒸馏画质，**可复现** |
| **PDD 8 步 + T8（阈值 1.0）** | **210s** | **命中 6/8**，最快档且画质最高档 |

PDD LoRA：`Kijai/MiniMax-H3-experimental` 仓 `loras/MiniMax-H3-FL2VA-Acc-8Step_comfy.safetensors`（t2v；另有 Ref2VA 版给 i2v）。采样：`simple` 8 步 + shifts 12/3，无需新节点。

## Backport 路线（三条坑，一次讲完）

### 坑 1：单文件替换不够，最终走全量升级

最初只替换 `comfy/ldm/minimax/model.py`（PDD 核心确实在这个文件：`FinalLayer` head bank + `_pdd_head` 区间混合，约 +195 行）。普通 Turbo 冒烟**逐像素一致**（帧差 MAE=0）——但 PDD LoRA 一加载就报：

```
ERROR lora diffusion_model.blocks.N.adaln_proj.linear.weight
shape '[96768, 8]' is invalid for input of size 260112384
```

根因链：PDD LoRA 含 adaln_proj 层 delta（Turbo 不含，所以从没暴露）→ adaln_proj 是量化权重 → 0.33.1 的「量化权重 + LoRA」路径有 bug → 修复在 `model_patcher.py` 的 `calculate_shape` 强制重载逻辑（4 处）。依赖闭包滚雪球（ops/model_base/samplers 都有 diff），逐文件换不如全量。

**最终方案**：jsdelivr 逐文件升级到 master 精确 commit（483→519 文件，89+36 变更，~4 分钟）。备份目录齐全，回滚 = 拷回。

### 坑 2：升级脚本的目录盲区——comfy_api/

升级脚本只覆盖 `comfy/` 和 `comfy_extras/`，但 master 时代 **`comfy_api/` 成了活跃目录**（v3 节点 API）。漏掉它的症状是 `SaveVideo`/`CreateVideo` 节点消失（`module 'comfy_api.latest._io_public' has no attribute 'VideoEdit'`）。修：过滤前缀加 `comfy_api/`。

### 坑 3：PyAV 太老 + T8 节点与 master 接口断裂

- master 的 `nodes_video.py` 需要新版 PyAV 的 `av.video.reformatter.ColorPrimaries`——`pip install -U av`（升到 18.x）
- **T8 BlockCache 节点（8-24 版）按 0.33.x 的 4 参数签名调 `FinalLayer.forward`**，master 改成 7 参数（+sigma, sample_sigmas, shifts），组合 PDD+T8 时报 `missing 3 required positional arguments`

T8 适配补丁（`custom_nodes/comfyui-minimax-h3-blockcache-T8-main/nodes.py` 的 hit 路径，自适应双版本）：

```python
try:
    _shift_v = float(transformer_options.get("minimax_h3_sigma_shift_video", model.sigma_shift_video))
    _shift_a = float(transformer_options.get("minimax_h3_sigma_shift_audio", model.sigma_shift_audio))
    _sigma_v = (timestep.flatten()[0] / 1000.0).float().clamp(min=1e-6)
    video_rows, audio_rows = model.final_layer(
        hit.hidden, hit.t_emb, hit.video_segment, hit.audio_segment,
        _sigma_v, transformer_options.get("sample_sigmas"), (_shift_v, _shift_a))
except TypeError:
    video_rows, audio_rows = model.final_layer(hit.hidden, hit.t_emb, hit.video_segment, hit.audio_segment)
```

关键点：**hit 路径必须把 `sample_sigmas` 传给 final_layer**——PDD 的 head bank 靠它找当前 sigma 区间做输出头混合，不传的话缓存命中会输出错乱的 bank 结果。

## 数据与机理

- 8 步给 T8 的命中窗口是 6/8（首步 warmup 必算 + 1 步 refresh），实测正好 **cached 6/8**
- 每次命中省一次完整 forward（8 步时每步 ~75s）：600s − 6×75s + 缓存开销 ≈ 210s，账完全对上
- PDD+T8 输出：构图完整无伪影（head bank 在 hit 路径按步混合正常）；音频 mean −27.6dB / max −13.8dB 无削波，电平偏低 ~8dB（cache 路径已知特性，后期统一响度）
- 可复现性：PDD 8 步无 T8 = 可复现（成片档）；PDD+T8 = 同 seed 不可复现（草稿档，与 [08](08-t8-blockcache-4step.md) 的 T8 特性一致）

## 档位体系（2026-09-03 起）

| 档位 | 配置 | 速度 | 用途 |
|---|---|---|---|
| ⚡ 极速草稿 | **PDD 8步 + T8** | **210s** | 选镜头/试 prompt，画质最高的草稿 |
| ✅ 成片 | **PDD 8 步** | 600s | 可复现 + 蒸馏画质（若审片确认优于 Turbo，可整体替换成片档） |
| 旧成片 | Turbo 4 步 | 320s | 兼容旧项目 |

> ⚠️ PDD 各档需要 master 环境（本页 backport 或未来的 v0.34.1+）；0.33.1 环境请用 [workflows](../workflows/README.md) 四件套。

## 未尽事项

- PDD vs Turbo 的**成片画质 A/B 盲测**（同 seed 8 步 vs 4 步目检打分）待做——决定成片档是否整体切换
- Ref2VA 版 PDD（i2v 路线）未测
- T8 适配补丁待回馈上游（T8mars issue #4 追评或 PR）
- master 环境 Turbo 基线慢 14%（320 vs 280s）的原因未深究（新转码路径开销嫌疑）
