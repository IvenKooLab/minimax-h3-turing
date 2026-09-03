# 05 · compat 工作流说明

## 模型下载清单（先看这个）

工作流引用的文件名来自 h3lite W4A8 组件集 A（网盘分发名）；本仓库全部实测基于**路线 B（HF 直链等价版）**——下表右列即推荐下载源：

| 工作流引用名 | 推荐实际下载 | 来源 | 放置目录 |
|---|---|---|---|
| minimax_h3_fl2va_pruned_w4a8_mixed_ax1y2jp.safetensors (12.5G) | minimax_h3_fl2va_pruned_w4a8_mixed.safetensors | [Kijai/MiniMax-H3-experimental](https://huggingface.co/Kijai/MiniMax-H3-experimental) | models/diffusion_models/ |
| qwen3vl_4b_int4_convrot.safetensors (2.8G) | qwen3vl_4b_fp8_scaled.safetensors (5.2G) | [Comfy-Org/Krea-2](https://huggingface.co/Comfy-Org/Krea-2) → text_encoders/ | models/text_encoders/ |
| mmh3-4b-ClipProj-celeb-mlp.safetensors (304M) | 同名直下 | [NicoLab28/ClipProj-MiniMax-H3](https://huggingface.co/NicoLab28/ClipProj-MiniMax-H3) | models/clip_projections/ |
| minimax_h3_video_vae_fp16 / audio_vae_fp32 | 同名直下 | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) → vae/ | models/vae/ |
| Turbo 4step LoRA（fl2v/ref2v） | 同名直下 | 同上 → loras/ | models/loras/ |
| PDD Acc-8Step LoRA（草稿档第五件套用） | 同名直下 | Kijai 仓 → loras/ | models/loras/ |

- **改名规则**：用替代版时，把工作流 JSON 里 loader 节点的文件名改成实际下载名（或反向重命名文件）；两个 W4A8 版本仅差约 26KB（量化配置微调），实测输出一致
- **坚持要 ax1y2jp 原名版**：h3lite Set A 百度盘 `pan.baidu.com/s/1x5GGuJv0h8chApgVoDgIaQ`（提取码 1hjx）
- **国内镜像**：huggingface.co 直连不动时换 hf-mirror.com，路径不变；大文件建议多线程分块下载

## 为什么是 "compat"

H3 官方完整版工作流引用了 T8 BlockCache 节点和完整精度模型名，在 Turing 卡 + 未装 T8 的环境里是**死图**（节点缺失、模型对不上）。compat 版是社区维护的降级适配：

- 去掉 sm_75 跑不了的加速节点
- 模型文件名对齐 W4A8 mixed 现役权重
- 保留 4 步 Turbo 路线 + 原生音频

实测这张卡上 compat + W4A8 就是最优解（见 [01](01-hardware-limits.md)），不存在"升回完整版"的损失。

## 文件

> 完整用途矩阵、导入三步与坑提示见 [workflows/README](../workflows/README.md)。

| 文件 | 用途 |
|---|---|
| [h3_w4a8_t2v_compat_api.json](../workflows/h3_w4a8_t2v_compat_api.json) | 文生视频 · 成片档（280s/镜，可复现） |
| [h3_w4a8_t2v_t8draft_api.json](../workflows/h3_w4a8_t2v_t8draft_api.json) | 文生视频 · 草稿快跑档（160s/镜，-43%，同 seed 不可复现） |
| [h3_w4a8_i2v_compat_api.json](../workflows/h3_w4a8_i2v_compat_api.json) | 图生视频（需要首帧） |

## 导入与替换

1. ComfyUI 界面拖入 JSON，或放到 `user/default/workflows/`
2. 检查模型加载节点里的文件名与你本地 `models/` 下实际文件一致（不同时间下载的 W4A8 权重命名不同）
3. **图生视频**：把首帧图加载节点指向你自己的图片（本仓库不含示例图）
4. 默认参数：640×352 · 124 帧 · 4 步 · 带原生音频

## 产线参数建议

- 短片（5-6 秒）直接用默认值，`--reserve-vram 2.5`（见 [04](04-community-tips.md)）
- 要 1080p 成片：保持 640×352 生成 → 抽帧 → RTX VSR 超分，**不要**直接改工作流分辨率（显存和时间都不划算）
- prompt 按三段式写：主体 → 动作/运镜 → 环境与光线，具体参考 h3lite 官方方法论

## 常见导入失败

| 现象 | 原因 |
|---|---|
| 节点红色缺失 | 没装 H3 支持节点包（KJNodes 等），或 ComfyUI 版本过老 |
| 模型加载节点报错 | 权重文件名不匹配，双击节点改成你本地实际文件名 |
| 出图彩色撕裂 | 用错了 W4A4 权重，换 W4A8 mixed |
