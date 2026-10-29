# 第三轮：粒子材质、引用缺口与攻击组合实验

日期：2026-10-30

## 本轮结果

配置依赖索引已修正：支持中文文件名、粒子 `.par`、贴图序列 `.tl` 等格式；仅从赋值右侧提取引用，排除顶点着色器中的寄存器分量。此前 `Effect/VA/WF5_180_北_頂點VA.xef` 被截成 `va.xef`，现在恢复为完整路径并能匹配。

新的统计口径下，GameData 配置有 **22,630 行引用，22,364 行精确匹配，266 行未匹配**。上一轮未匹配为 489 行；本轮既消除了误识别，也补入了之前未统计的粒子与材质序列引用，因此应以新索引为准。

原文件、完整解包结果和已有故事文件均保留，未按推测重命名或替换资源。

## 粒子到图片的依赖已经接通

完整解析 **196 份粒子配置、55 份贴图序列**，保留 4,642 个粒子属性。贴图序列形成 664 行图片依赖，其中 633 行精确匹配、31 行待验证。

例如：

```text
BattleScript/common0065.txt
  → Particle/music_01.par
    → Texture/particle/music_01.tl
      → particle/music_p01.bmp … music_p05.bmp
```

另有 23 份贴图序列使用 TextureBatch 批量编号。已按源文本的起止编号和补零位数展开 **104 条引用，全部精确匹配**。同时保留原始批量表达式，供复查。

贴图列表可以重复使用 `tex00` 作为属性名。解析结果按行保存，避免使用字典后只留下最后一张图。明确列表与批量回退分别保存；有明确列表时，不把回退批次混入列表。本规则依据文件内的优先级说明，运行时行为仍需单独核验。

`common0065` 当前递归可达资源 **55 个**，显式资源依赖没有未匹配项。这表示它引用的素材已找到，不代表脚本的条件、镜头和粒子运动已正确重放。

## 剩余缺口的判断依据

当前引用问题按行计数如下：

| 类型 | 行数 |
|---|---:|
| 动画图片引用 | 183 |
| GameData 配置引用 | 266 |
| 模型贴图引用 | 32 |
| 贴图序列图片引用 | 31 |

这 512 行引用中，211 行在其他路径存在同文件名候选；36 行在相同路径主名下存在不同扩展名候选；265 行没有这两类候选。候选仅用于诊断，不写入“已精确匹配”的索引。

其中 31 行来自 `sea/sea.tl`：它声明 `sea000.bmp` 等文件，而包内对应路径主名为 `sea000.jpg` 等。图片本身已完整提取，尚未证明原加载器如何处理扩展名差异；因此没有擅自把 BMP 引用改成 JPG。

183 行动画图片缺口仍为 56 个不同路径。只有 1 行所属动画在当前显式配置引用中出现，但角色动作会按编号动态加载，因此不能把其余动画判定为“未使用”并删除。

除此之外，仍保留 3 个配置解码问题和 1 个 ANI 资源表读取问题。

## PSD 源图

另已为包内两份 PSD 导出合成预览，尺寸为 2667×2000 和 480×640，并检查 PNG 像素往返一致。入口为 `original_resources/organized/source_art/index.html`；原 PSD 的图层信息保持在原始文件中，合成 PNG 仅用于浏览参考。合成预览另列于 `manifests/source_art_index.json`，不与首轮运行时贴图数量混为一谈。

## 控制关系与外部判定

已为 747 份战斗演出脚本生成条件边和消息路由图。

- 1,717 条 SendMessage 路由只有一个当前入口候选。
- 621 条存在多个入口候选，例如 Hit 可能进入命中或闪避处理。
- 193 条尚无对应的当前脚本入口，可能依赖外部处理或额外规则。

图中保留父节点、`dwConditionOfStart`、源行号以及入口候选。条件 0 按源注释标记为父节点结束，正值保留为候选事件编号。没有自动选择命中、闪避或死亡分支，也没有将所有节点强制换算成绝对时间。

## 基础攻击组合实验

入口：`original_resources/organized/attack_sample.html`。

实验使用 `BattleScript/attack00.txt` 中的真实资源和消息节点，组合五个动画片段：施动者待机、攻击、目标待机、受击、命中特效；引用 61 张不同图片和 1 个音效文件。动作组 0001/0002 是演示绑定，没有据此确认人物姓名。

操作流程：

1. 点击“开始攻击片段”。
2. 攻击片段到第 9 帧时，在候选事件标记 1 处暂停；原始累计偏移为 375。
3. 手动确认“命中、目标存活”分支，检查消息链、命中特效和受击片段的组合。
4. 可切换纯绿色预览抠除、近似加亮合成；音效默认关闭，勾选后才播放。

消息链对应的源节点：

| 源行 | 节点作用 |
|---:|---|
| 43 | ActivePerson 设置 Attack 姿态 |
| 54 | 等待父动作事件 1 |
| 60 | 向 ActivePerson 发送 Hit |
| 99 | 命中分支向 PassivePerson 发送 Hit |
| 295 | 显示 Hit000，资源为 `sp/hit000.ant` |
| 320 | 向 PassivePerson 发送 Result |
| 213 | 选择 ResultLive 后设置 HurtBelly 姿态 |

这里的“第 9 帧”和“偏移 375”来自动作组 0001 的 `17a.ant`；把第一标记字段的值 1 解释为脚本事件 1 仍是待运行验证的假设，所以保留手动确认按钮。

演示使用固定二维布局、可调的原始时间单位和近似合成。姿态工作时长、三维投影、镜头、命中计算与结果判定并未由原引擎执行。攻击和受击片段完成后保持末帧，特效播完隐藏，属于预览策略。

本轮已在浏览器检查待机、攻击、事件等待、确认命中、受击显示与重置流程，控制台没有错误。另检查了全部演示片段的变换边界，避免剑光等图层被画布截断。

## wrap 容器的进一步证据

十个 wrap 文件均有 `WFAPe` 标识。它们都满足以下大小关系：

- 固定头部为 40 字节。
- 头部偏移 32 的整数作为条目数候选，偏移 36 的整数作为尾部表偏移候选。
- `文件长度 − 尾部表偏移 = 条目数 × 268`，十个文件全部成立。

例如，StaticData.wrap 对应 358 个条目候选；四个 NewGame 文件各为 12 个。尾部内容尚未解码，这个关系只证明候选边界和记录大小，不能恢复条目名称、角色数据或技能数值。角色姓名与战斗动作组的直接绑定仍未解决。

## 输出与复现

所有下列 manifests、organized 路径相对于 `original_resources/`：

| 输出 | 内容 |
|---|---|
| `manifests/particle_index.json` | 196 份粒子配置索引 |
| `manifests/texture_list_index.json` | 55 份贴图序列索引 |
| `manifests/material_dependencies.json` | 列表及批量展开的图片依赖 |
| `organized/effects/material_data/` | 粒子、材质的完整节点与参数 |
| `manifests/battle_control_graph_index.json` | 747 份条件与消息图索引 |
| `organized/effects/control_graphs/` | 每份演出脚本的控制边 |
| `organized/effects/samples/attack00/bundle.json` | 攻击实验的数据包、证据与演示策略 |
| `manifests/gap_diagnostics.json` | 缺口候选及匹配证据 |
| `manifests/wrap_structure_inventory.json` | wrap 头部与大小关系记录 |
| `manifests/reference_verification.json` | 中文路径、粒子、批量列表、重复键及事件门控验证 |

已有前两轮产物时运行：

```sh
python3 tools/resource_pipeline/source_art.py
python3 tools/resource_pipeline/index_resources.py
python3 tools/resource_pipeline/materials.py
python3 tools/resource_pipeline/battle_scripts.py
python3 tools/resource_pipeline/script_graphs.py
python3 tools/resource_pipeline/attack_sample.py
python3 tools/resource_pipeline/gap_audit.py
python3 tools/resource_pipeline/verify_references.py
python3 tools/resource_pipeline/verify_animations.py
python3 tools/resource_pipeline/verify.py
```

源文件、完整资源哈希、919 个受版本控制的故事文件、动画源行覆盖及本轮引用回归检查均通过。

下一步可继续核验场景与模型材质，并把已有中间数据整理为 Godot 导入约定；完整演出验证还需要确认原引擎的事件、时间、投影和材质规则。
