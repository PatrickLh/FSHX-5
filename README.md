# FSHX-5

整理《风色幻想 5》原游戏资源，并为后续 Godot 重建准备可追溯的素材与动画资料。

- `original_resources/source/`：原始发行文件与压缩包。
- `original_resources/unpacked/`：旧解包流，保留作历史对照。
- `original_resources/unpacked_verified_v1/`：已按原名重组并校验的完整资源。
- `original_resources/organized/`：故事、人物、背景、技能动效、模型、UI、音频。
- `original_resources/manifests/`：来源索引、校验和迁移记录。
- `godot/`：后续 Godot 工程目录。
- `tools/`：提取和分析脚本，从仓库根目录运行。
- `docs/plan.md`：整体实施计划、阶段状态与验收标准。

首轮已提取并校验 48,737 个完整文件版本，导出 32,355 张 PNG（含历史版本）。动画参数语义、角色动作绑定和技能组合演出仍待核验。

- [提取结果与剩余问题](docs/resource-extraction-report.md)
- [资源可视预览](original_resources/organized/index.html)
- [人物与特效动画预览](original_resources/organized/animation_viewer.html)
- [第二轮动画与技能脚本分析](docs/animation-analysis.md)
- [基础攻击组合实验](original_resources/organized/attack_sample.html)
- [第三轮粒子材质与引用报告](docs/resource-linkage-analysis.md)
- [场景与模型审计](original_resources/organized/scene_audit.html)
- [第四轮场景与模型报告](docs/scene-model-analysis.md)
- [提取管线与复现命令](tools/resource_pipeline/README.md)

历史资产说明位于 `original_resources/organized/legacy_assets/README.md`，其中的旧推断以本轮校验报告为准。
