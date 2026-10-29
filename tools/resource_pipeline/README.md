# 资源提取管线

从仓库根目录运行，Python 3；图片导出额外需要 Pillow。无需运行游戏。

```sh
python3 tools/resource_pipeline/audit.py
python3 tools/resource_pipeline/organize.py
python3 tools/resource_pipeline/source_art.py
python3 tools/resource_pipeline/animations.py
python3 tools/resource_pipeline/index_resources.py
python3 tools/resource_pipeline/materials.py
python3 tools/resource_pipeline/battle_scripts.py
python3 tools/resource_pipeline/script_graphs.py
python3 tools/resource_pipeline/attack_sample.py
python3 tools/resource_pipeline/gap_audit.py
python3 tools/resource_pipeline/model_geometry.py
python3 tools/resource_pipeline/scenes.py
python3 tools/resource_pipeline/scene_viewer.py
python3 tools/resource_pipeline/verify_scenes.py
python3 tools/resource_pipeline/verify_references.py
python3 tools/resource_pipeline/verify_animations.py
python3 tools/resource_pipeline/verify.py
```

- `audit.py`：扫描全部源文件并计算 SHA-256；从带时间戳的 JBF 文件目录项恢复路径，校验文件偏移、压缩长度、块长度表、压缩标志、解压大小和 zlib 校验和。合并分块，保留未压缩块；完整覆盖文件数据和索引元数据区间。
- `organize.py`：按原目录做初步分类，图片转 PNG 并逐像素检查往返一致性；复制动画、模型与配置，配置另存 UTF-8；导出动画帧引用、模型贴图引用和散装音频。PNG 保留原色；不做绿幕删除、黑色透明化或混合效果烘焙。
- `index_resources.py`：关联人物表与头像动画，解析配置中显式文件引用，生成依赖图、缺口清单与 `original_resources/organized/index.html`。
- `verify.py`：重新核验源文件和全部完整解包文件的哈希、归档字节区间覆盖、输出文件存在性，以及受版本控制故事文件的原样保留。

## 数据与输出

完整解包位置是 `original_resources/unpacked_verified_v1/`；旧的 `unpacked/` 保持不变。`manifests/baseline_audit.json` 指明有效解包根目录，不再将旧流文件作为完整资源使用。

JBF 含单块、多块、未压缩块和历史目录表。多块文件布局为连续数据块、N 个 u32 块长度、N 个 u32 压缩标志（0=原样、1=zlib）；目录项给出块数、压缩总长、存储总长和数据偏移。本规则已经逐文件校验当前五个包，不代表支持任意其他游戏的 JBF。

目录表解析目前恢复并验证文件项；目录本身的全部字段尚未命名。中间历史目录与尾部元数据按原字节保留，并记录偏移、长度和哈希。保留全部历史条目；同名路径以最高数据偏移作为最后追加版本，其他版本存于 `__versions__/偏移/原路径`。这是文件存储版本策略，最终游戏实际采用的版本仍需结合加载行为验证。

输出稳定 ID 为 `包名:原路径@源偏移`，避免同名历史版本互相覆盖。所有自动命名来自目录项，不再使用立绘顺序 DP 推断。资源语义分类仍属初步分组：例如 AVCG 同时可能含人物插画与过场素材，模型目录中的图片是模型贴图，不能当作独立场景。

重新执行时，完整解包和非图片输出遇到内容冲突会拒绝覆盖；已有 PNG 会与当前源像素比较。自动索引、UTF-8 派生文本和 HTML 会重新生成，请勿将手动修改直接写入这些派生文件。

动画现已按帧/图层解析，见 `animations.py` 与 `organized/animation_data/`。`battle_scripts.py` 保存演出节点树及条件触发原值，`verify_animations.py` 校验全部源行、帧数与脚本属性覆盖。预览模板为 `animation_viewer.html`；逻辑尺寸、XY 变换及原始时间值用于试播，尚未将时间单位、锚点、方向和混合规则全部验证为 Godot 参数。技能文件名数字分组不能直接当作战斗技能 ID。未命中的引用保留为未解决项，禁止自动用“同名相近图片”替代。

## 第三轮工具

`source_art.py` 为 PSD 源图导出并逐像素验证合成 PNG，向总索引追加派生预览，保留原分层文件。应在 organize.py 后执行。

- `config_refs.py`：从赋值右侧读取 Unicode 路径，涵盖 `.par`、`.tl` 等依赖；排除着色器寄存器误命中。
- `materials.py`：保留粒子与材质节点、列表顺序、重复键和批量规则；明确列表与回退批次分别保存。
- `script_graphs.py`：生成条件边和 SendMessage 入口候选，保留外部命中/闪避判定。
- `attack_sample.py`：编译基础攻击组合实验，内嵌必要的片段数据；角色绑定、事件确认和预览策略显式保留。
- `gap_audit.py`：整理同名/扩展名候选，记录 wrap 大小关系；诊断候选不会自动替换已解析资源。
- `verify_references.py`：运行真实语料上的引用回归、材质行覆盖、事件门控与预览边界检查。

`materials.py` 应先于 `battle_scripts.py`，这样递归依赖才会包含贴图序列的图片。重复执行这些步骤会重建相应派生索引，手工标注应保存在独立文件中。

## 第四轮工具

`model_geometry.py` 解析文本与二进制 .x 的原始几何并检查索引和布局；不转换坐标、不三角化或修补。`scenes.py` 保留场景/元素节点、材质和背景依赖，`scene_viewer.py` 生成审计页；`verify_scenes.py` 检查语料覆盖、已知源缺口以及截断和无效索引回归。

静态模型验证样本：`python3 tools/resource_pipeline/static_sample.py`；随后用 Blender `--background --python tools/resource_pipeline/blender_static_sample.py` 验证载入并渲染。仅 map004 六个地形的局部几何/UV，不含源材质、变换和动画。详细限制见 `docs/static-sample-validation.md`。

原始提取收尾：`python3 tools/resource_pipeline/extraction_closure.py`。逐个核验原始 ZIP 成员与现有展开文件，补存说明/链接原字节；复制辅助原件，导出 GIF/ICO 尺寸变体，索引 ANI 备份资源表，对全部正式整理输出计算 SHA256。生成 `extraction_completion.json`、`loose_source_coverage.json`、`distribution_zip_audit.json`、`organized_output_checksums.json`、`loose_media_exports.json` 和 `backup_animation_tables.json`。不访问保存的 URL，不执行源游戏程序，不修改 Godot。
