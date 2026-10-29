# 第四轮：场景与模型静态审计

日期：2026-10-30

## 已完成的检查

652 个原始模型版本均已解析，其中 650 个为文本编码，2 个为二进制编码。按原始包中最后追加的数据偏移选取的当前版本为 538 个；这一选择策略仍需结合原游戏加载行为验证。

| 项目 | 全部版本 | 当前版本 |
|---|---:|---:|
| 模型文件 | 652 | 538 |
| 顶点 | 484,160 | 435,354 |
| 多边形面 | 386,622 | 345,002 |

共有 1,049 个 Mesh 块。顶点、法线、材质索引均未发现越界；UV 数量与顶点数量一致，法线面布局与原多边形布局一致。检查包含已解析顶点、UV、法线和帧矩阵数值的有限性，模型副本 SHA-256 与来源清单逐项一致。

2 个二进制文件版本均为 `sp/sk_0396a.X`，包含动画数据，没有 Mesh。它们已经按原字节完整消费，不再标记为无法解析；原二进制文件没有改写。

二进制解析依据微软的 [Token Records](https://learn.microsoft.com/en-us/windows/win32/direct3d9/token-records) 和 [Tokens](https://learn.microsoft.com/en-us/windows/win32/direct3d9/tokens) 格式说明实现，保留原数值并接入相同几何检查。

## 需要保留的异常与语义

- 发现 256 个近零面积三角面，全部位于当前版本中。判据为原局部坐标下叉积长度平方小于 `1e-20`，不是按真实米制面积作出的判断；没有自动删除或修复。
- UV 超出 0–1 的数值按原值保留，不能在没有验证采样规则时截断。
- 每个 Mesh 的局部范围、FrameTransformMatrix 与场景变换分开保存。没有把局部范围冒充完整场景的世界范围。
- 4 个带 SkinWeights 块的模型文件为 `M05/m05_boss.X`、`M11/boss.X`、`M11/boss_2.X`、`M35/m35boss.X`。这不能证明主要人物存在现成三维骨骼模型。
- 384 个模型版本含 AnimationSet。动画数据存在不等于已经验证蒙皮、插值或播放效果。

当前 PATH 中未发现 game-dev、Blender 或 Godot 命令，因此本轮完成的是原始字节与结构审计，没有执行三维渲染、模型格式转换或 Godot 导入。

## 场景与背景关系

已解析 70 份场景配置和 140 份场景元素文件，保留 290 个 Earth 槽位，以及 56 个由源配置显式声明的 background 节点。

逐场景记录包括模型、材质效果、背景和其他元素引用、光照、雾、矩阵及递归依赖。70 份场景全部通过结构检查；139 份场景元素通过，另有一份源文件 `SceneElement/WF5_Par_M41_ghost.se` 缺少最外层闭合括号。它的已读字段和问题记录均保留，没有擅自补括号。

以 `Scene/map004.sce` 为例：6 个 Earth 槽位关联 11 个递归可达模型和 11 张图片，显式依赖没有未匹配项。Earth 槽位模型与由背景、雾等元素引入的模型分别可追溯，不把它们合并成虚构的单一网格。

## 海面序列的新证据

上一轮保留的 `sea/sea.tl` 有 31 个 BMP/JPG 扩展名差异。对本轮 70 个场景的显式依赖闭包检查，没有发现任何场景可达该列表。

场景实际可达的多份 `WF5_m_sea*.tl`、`wm_sea.tl` 已有精确匹配的帧引用。例如世界地图场景 `wf5_wmap/001.sce` 的相关海面图片依赖能够直接关联。

因此可以继续整理这些已明确引用的海面序列；无需为了让计数归零而改写旧 `sea/sea.tl`。这里的“不可达”只针对已解析的静态引用，仍不能证明原运行时永远不会动态加载它。

## 查看与复现

查看入口：`original_resources/organized/scene_audit.html`。

可以按路径筛选场景，检查模型顶点/面数量、蒙皮与动画集数量、关联贴图、Earth 槽位、光照雾参数和未匹配依赖。页面展示的是原贴图与结构统计，尚不是场景渲染。

输出均在 `original_resources/` 下：

| 路径 | 内容 |
|---|---|
| `manifests/model_geometry_index.json` | 模型几何统计、局部范围与原始矩阵 |
| `manifests/model_geometry_summary.json` | 模型版本及几何覆盖统计 |
| `manifests/scene_index.json` | 70 份场景索引 |
| `manifests/scene_element_index.json` | 140 份场景元素索引 |
| `manifests/declared_background_index.json` | 显式 background 声明 |
| `manifests/scene_texture_list_usage.json` | 贴图序列的逐场景可达关系 |
| `organized/scenes/` | 原始节点、字段、槽位与依赖的结构数据 |
| `manifests/scene_verification.json` | 全量结构与回归验证 |

运行：

```sh
python3 tools/resource_pipeline/model_geometry.py
python3 tools/resource_pipeline/scenes.py
python3 tools/resource_pipeline/scene_viewer.py
python3 tools/resource_pipeline/verify_scenes.py
```

验证覆盖模型索引、UV/法线/材质布局、场景属性源行、二进制字节边界，并确认截断的二进制副本会被拒绝、无效索引样本能被检测。已知未闭合场景元素保留为待解决项。浏览器已检查场景筛选、模型表、贴图显示与控制台。

## Godot 导入约定草案

已保存 `godot/import_contract.json`。它规定来源 ID、SHA-256、历史版本、派生资源复制、原始坐标/矩阵、贴图序列、事件和缺口的处理边界。

Godot 版本、长度单位、轴向、坐标系手性、时间单位和混合枚举映射暂留空。没有自动把演示动作组与人物姓名绑定，也没有把候选扩展名别名变为正式映射。

后续可据此选择一个依赖闭合的场景，验证坐标与材质转换，再开展 Godot 最小工程；整体模型导入与完整演出仍需实际引擎验证。
