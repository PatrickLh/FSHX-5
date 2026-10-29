# Godot 资源验证工程

用 Godot 4.x 打开 `project.godot`，等待 OBJ 导入后运行主场景。左键拖动旋转查看。当前尚未在 Godot 引擎实际运行；精确版本待确定。

本次样本来自 map004 的 6 个 Earth 模型、9 个网格，使用原始局部 XYZ 和 UV。使用诊断颜色，未应用 Frame/场景变换、源材质、法线、顶点色、动画或特效，不能作为原游戏场景还原结果。

- `assets/static_sample/`：派生 OBJ、完整多边形/UV JSON、来源 ID 与 SHA256 清单。
- `scenes/`、`scripts/`：独立静态模型检查入口。
- `diagnostics/`：Blender 验证文件，以 `.gdignore` 隔离，避免额外自动导入。
- `import_contract.json`：来源策略和待核验约定。

原件保存在 `../original_resources/`。复现命令及结果见 `../docs/static-sample-validation.md`。
