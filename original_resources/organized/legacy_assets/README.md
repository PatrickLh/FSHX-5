> 历史整理记录：迁移时本目录仅有本说明，文中所述导出文件并未随目录存在；数量、映射与解码结论均需重新核验。旧路径保留用于理解历史记录，不代表当前目录。

# FSHX-5 资产目录（从风色幻想5 Steam 101261 版提取）

全部由 `tools/` 下脚本从原版 JBF 包解出。JBF = zlib 流拼接，无文件名；
命名通过「配置引用 + 保序 DP 对齐」恢复，置信度见各节说明。

## assets/portraits/ —— 角色立绘（v5 管线，主创已逐帧目检）

- `NNN_角色名/sfXXXX[a-z].png` —— 对话表情帧（抠除绿幕）
- `NNN_角色名/_art_*.png` —— 大图（主立绘在角色帧簇之前、Q版chibi在帧之后）
- 274 帧 + 104 大图 / 69 个角色目录；对照表 `portraits_index.json`
- **分类方法**：人物表(流00747)给出 角色→face\sfXXXX.ant；.ant 动画(Ani.JBF)给出
  每角色精确帧数与帧名；立绘区(AniTexture 流196-710)按簇存放。
  主创(c0-c24)逐帧目检硬编码；NPC 尾部用区间 DP（.ant 帧数作容量约束）
- 大图归属：结构规则（大图后仅有 void 隔着的第一命名帧所属角色 = 主立绘；
  否则归前一命名帧角色 = chibi）
- 已知缺口：部分帧以 16bpp raw 存储（void 流）无法解码，记入 unresolved；
  NPC 尾部个别簇的身份可能有偏差（主创 16 人已全部目检确认）

## assets/skills/ —— 技能

- `plates/0000.png … 0392.png` —— 技能名牌（ID=牌号，与战斗数据 H00xx0000 对应），
  387/387 全对齐（如 0000=斷龍斬 Physical Attack）
- `fusion.txt` —— 招式连锁合成表（GameData 流 01926），
  格式 `H技能A,H技能B,H结果`（如 奇蹟之拳+轟天碎龍擊=努力與奇蹟）
- **技能数值表（伤害/耗魔/属性）在加密的 `Data/StaticData*.wrap` 里**
  （WFAPe 容器，流加密，熵 7.99，静态破解不经济）。要拿全需运行游戏脱壳/内存 dump

## assets/models/ —— 3D 模型（DirectX .x 文本格式）

- `named/` —— 638 个模型，按主贴图名命名（201 个唯一名：
  `m11w01`=怪物、`wf5_m034_w01`=地图物件、`efc__*`=特效）
- `x/` 原始流、`tex/` 501 张模型贴图、`meta/` 56 个坐标 CSV、`other/`
- 映射表 `model_name_map.json`

## assets/ui_sprites/ —— 界面与杂项（Texture.JBF，1686 流）

- `icons_32/` 1200 张 32×32 图标（道具/装备/技能图标）
- `card/` 69 张 128×128（卡牌/称号图）
- `bg_large/` 33 张 ≥640 宽（标题/过场底图）
- `misc/` 197 张其余（特效、字牌等）

## assets/bg/sea/ —— 98 张海面动画帧（sea\sea000.jpg…，即原 assets/cg）

## 技能特效的构成（后续提取入口）

战斗演出由四层拼成：
1. `[Particle]` 配置流 ×219（GameData.JBF 流 01932+），引用 `particle\skXXXX_paNN.bmp`
   —— **粒子贴图按技能号命名（sk956 等），天然对齐技能 ID**
2. `efc__*.x` 特效模型（已在 assets/models/named/）
3. 特效贴图：Texture.JBF 的 32/64px 光效 sprite + AniTexture 开头的 512×512 16bpp raw
4. `[BattleScriptSys]` 流 ×299：每技能的演出编排（镜头/时机/粒子触发）

## 原始解包

- `extracted/GameData`（2398 流：剧本+配置+特效）、`extracted/XFile`、
  `extracted/Ani`（13145 流：.ant 动画定义）、`extracted/AniTexture`（31215 流：30252 BMP+raw）、
  `extracted/Texture`（1686 流）

## 未完成 / 已知缺口

1. **AniTexture 命名**：约 3 万张 BMP 中已命名 立绘 434 + 技能牌 388 + 模型贴图（在 XFile）；
   MAN 行走图（~2.6 万）、SCRIPTBG 对话背景（319）、SP 过场演出件（2271）、bg（54）未命名。
   方法已验证（同目录内按名排序 + DP），可按需扩展开挖。
2. **Data/*.wrap 加密**：静态数据表（角色/技能/道具数值）。WFAPe 头 8 字节
   `[u32 压缩大小][u32=1]` + 4 字节疑似密钥（头部 0x1C）；内容为流加密。
3. **剧本末 22 个 ref** 的对白 txt 不在发行包内（多为资料片/EX 文件）。
4. `Wave/`、`Music/` 为散装文件，未整理（音效 S000-S1xx、BGM M00-M33）。
