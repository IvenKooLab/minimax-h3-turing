# 05 · compat 工作流说明

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
