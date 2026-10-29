# 原始资源提取交付报告

日期：2026-10-30。按最新要求，本阶段专注原始资源提取与整理，暂停 Godot 人物制作及进一步模型转换。

## 完成范围

五个 JBF 的目录、数据块及历史文件已经完整提取，原件和已提取文件均保留。当前目录包含 **48,737 个完整文件版本**：45,358 个当前版本、3,379 个历史版本。归档的全部字节均由文件数据与保留的容器元数据覆盖，无遗漏区间。

- 归档图片：32,355 个版本已经导出 PNG，包含 29,116 个当前版本，零图片解码失败。当前分类包含人物精灵 22,251、头像 540、特效 3,396、背景 446、UI 2,060、模型贴图 423；分类仍以源目录为依据。
- 2 份 PSD 原稿保留，并提供合成图预览。6 份散装 GIF 导出 PNG，ICO 的 32×32、48×48 两种尺寸均已导出；这些 8 张新增 PNG 单独列于 loose_media_exports.json，不混入归档图片数。
- 551 份散装媒体保留原名原字节，包含 490 份 WAV、35 份 MP3、19 份 JPG、6 份 GIF 和 1 份 ICO。
- 6,573 份 ANT 动画全部完成帧/图层结构解析，保留 45,204 帧、61,361 个图层；全部 23 份 `.ani.bak` 资源表新增独立索引，未替代正式动画。
- 747 份战斗演出脚本、196 份粒子配置、55 份贴图列表、70 份场景、140 份场景元素及 652 个模型版本均已保留，并有对应结构或依赖索引。数量不是独立人物或技能数量。
- 919 份受版本控制的故事文件保持不变。
- 581 个现有源文件逐项有处理归属。13 份辅助文件（包括 wrap、字体、设置、日志）另存整理副本。运行程序/依赖和系统元数据仍保留在 source。
- 原始 ZIP 的 580 个文件成员全部读取、校验 CRC 与 SHA256；575 个与已有展开文件一致，另外 5 个说明/链接文件已保存原字节，没有访问其中链接。
- 51,756 个资源目录输出全部计算 SHA256，便于后续核查派生文件是否变动。新增辅助副本和 GIF/ICO 导出各有独立清单，不计入此数。

**结论：现有输入中的原始文件提取已经完成；不等于所有专有格式都已解码，也不等于人物身份、技能执行规则或原游戏效果已还原。**

## 剩余问题及边界

现有 unresolved.json 共 517 行，分为：

| 问题 | 行数 | 对提取结果的影响 |
|---|---:|---|
| 动画图片引用未匹配 | 183（56 个不同路径） | 引用文本已提取；不能据此补造不存在的图片 |
| 配置引用未匹配 | 266 | 需进一步核验路径规则、占位数据或源包缺失 |
| 模型贴图引用未匹配 | 32 | 模型与现有贴图均已提取，未擅自选择同名贴图 |
| 贴图列表引用未匹配 | 31 | 旧 sea 列表声明 BMP，已有 JPG；保留差异 |
| CP950 严格解码失败 | 3 | 2 份对话文本及 1 份二进制版本控制元数据；原字节完整，UTF-8 派生文本含替换符 |
| ANI 资源表解析失败 | 1 | 原 ANI 与对应 ANT 均保留，不能把 ANT 已解析当作 ANI 已解码 |
| 场景元素源结构不闭合 | 1 | 原文件缺闭合括号；保留源文件及问题标记 |

另有 10 个 wrap 已完整保留并验证容器边界，但有效载荷尚未解码。因此人物姓名到动作目录、技能数值到演出脚本的完整绑定仍未确认。Thumbs.db、版本控制元数据、备份文件等制作期附带数据也按原字节保留；桌面缩略图缓存不作为正式游戏素材。渲染参数、帧时间、方向、混合方式属于后续语义验证，不阻碍原始字节提取验收。

## 使用入口

- `original_resources/organized/index.html`：图片分类预览。
- `original_resources/organized/animation_viewer.html`：动画抽样预览。
- `original_resources/organized/attack_sample.html`：带人工事件确认的攻击实验。
- `original_resources/organized/scene_audit.html`：场景依赖与模型审计。
- `original_resources/unpacked_verified_v1/`：按源路径恢复的完整文件，历史版本置于 `__versions__`。
- `original_resources/manifests/resource_catalog.json`：正式资源清单。
- `original_resources/manifests/extraction_completion.json`：本次汇总。
- `original_resources/manifests/organized_output_checksums.json`：整理输出 SHA256 收据。
- `original_resources/manifests/loose_source_coverage.json`：源文件归属清单。
- `original_resources/manifests/distribution_zip_audit.json`：ZIP 成员逐项验证与额外文件保存位置。
- `original_resources/manifests/loose_media_exports.json`、`backup_animation_tables.json`：本次补提取结果。

## 复现与验收

在仓库根目录运行：

```sh
python3 tools/resource_pipeline/extraction_closure.py
python3 tools/resource_pipeline/verify.py
python3 tools/resource_pipeline/verify_animations.py
python3 tools/resource_pipeline/verify_references.py
python3 tools/resource_pipeline/verify_scenes.py
```

完整初次解包顺序见 `tools/resource_pipeline/README.md`。上述收尾脚本可重复执行，辅助原件副本不允许覆盖不同内容的文件；不会重写 source、完整解包原件或故事目录。Godot 目录保持本轮开始时的状态。
