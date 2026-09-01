# 06 · 踩坑 FAQ

全部为本机真踩过的坑，按疼的程度排序。

## 1. "Model Initializing" 卡死 27 分钟

**现象**：进程活着，日志停在模型初始化，27 分钟不动。而正常情况下采样一步只有 91 秒——瓶颈根本不在 GPU。

**根因**：12.5G 模型文件的磁盘加载 + staging 是 I/O 密集操作，被**杀毒软件实时扫描**逐块扫描拖慢（本机是火绒 HipsTray）。

**解法**：跑渲染前手动关闭杀软实时防护，跑完再开。长跑批任务额外配"检测卡死 → 干净重启 → 断点续跑"兜底（按图快照同种子重提）。

## 2. prompt_id 相同的重提被静默丢弃

**现象**：崩溃后重提同一个工作流，ComfyUI 悄悄不执行，也没有报错。

**根因**：H3 的 prompt_id 按**输入内容确定性生成**，输入不变 id 不变，前端会认为任务已存在。

**解法**：断点续跑时改一个无关节点值（如 seed+1）让输入变化；或清理历史 manifest 后重提。

## 3. ComfyUI 关停时队列残留

**现象**：进程被杀后，重启发现之前队列里的任务"复活"继续跑。

**根因**：队列状态持久化在磁盘，重启自动恢复。算力被意外占用时先查这里。

**解法**：想让重启后是干净状态，关停前清空队列；`.submit.claim` 并发锁文件在进程崩溃后可能残留，会挡住新提交——手动清理。

## 4. T8 BlockCache 节点注册失败

`MiniMaxH3BlockCacheT8` 在 sm_75 环境注册失败：依赖 ComfyUI v3 Layers API，且加速内核面向新架构。**Turing 上放弃这个节点**，compat 工作流已经绕开（详见 [01](01-hardware-limits.md)、[07](07-upgrade-watch.md)）。

## 5. aria2 下载的模型文件"幽灵消失"

**现象**：aria2 下载显示完成，文件过一会儿没了。

**根因**：特定沙箱/安全软件环境会静默删除 aria2 的临时下载文件（`.aria2` 控制文件 + 未落盘数据）。

**解法**：大文件用 Python 分块下载器（requests + 断点续传），稳定得多。本机 12.5G+ 模型全部改走这条路。

## 6. pinned memory 的 read_file_slice OOM

启动日志出现 `read_file_slice` 相关失败后 OOM。解法：启动参数直接 `--disable-pinned-memory`，无副作用，见启动模板。

## 7. 共享桌面 GPU 的 TDR 黑屏

ComfyUI 和桌面共用 2080Ti 时，显存吃紧会触发驱动 TDR 复位（屏幕黑一下，任务死亡）。解法：`--reserve-vram 2.5 --vram-headroom 0.5` 留足桌面余量，见启动模板。

## 8. KJNodes 里藏着一个没启用的宝贝

翻 KJNodes 源码发现内置了 `MiniMaxH3MemoryEfficientSageAttentionPatch`（fused qkv + RMSRoPE，只补丁 DiT 自注意力）——这是 H3 专属的原生 Sage 补丁，理论上兼容性比第三方 PatchSageAttentionKJ 好。**截至本文尚未在 sm_75 验证通过**，挂在待测清单里（见 [07](07-upgrade-watch.md)）。

---

下一篇：[07 · 升级窗口追踪](07-upgrade-watch.md)
