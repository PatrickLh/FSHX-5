# BattleScript/common0065.txt 演出资源核验

来源：`original_resources/organized/effects/configs/GameData/BattleScript/common0065.txt.utf8.txt`

文件名尚未绑定游戏中文技能名；动作表中的延迟、时长按源文本保留，未折算成绝对时间。人物动作、粒子发射、3D 模型、镜头与条件触发尚未组合渲染。

## 显式依赖

| 行 | 原引用 | 匹配资源数 |
|---:|---|---:|
| 20 | `sp\sk_magic009.ant` | 1 |
| 83 | `SP\SK_0666_2.X` | 1 |
| 215 | `BattleScript\\cen015.txt` | 1 |
| 335 | `sp\hit010.ant` | 1 |
| 370 | `sp\sk_0631.ant` | 1 |
| 411 | `Particle\music_01.par` | 1 |
| 449 | `Particle\hit_z07.par` | 1 |
| 734 | `magic\004.wav` | 1 |
| 820 | `BattleScript\\statemiss.txt` | 1 |

## 动作节点

| 行 | 节点 | Type | 对象 | 触发条件 | 延迟原值 | 时长原值 |
|---:|---|---|---|---|---|---|
| 16 | Ani | Ani |  |  |  |  |
| 79 | XFile | XFile |  |  |  |  |
| 168 | 空白工作 | Nothing | Script | 0 | 0.0 | 0.0 |
| 176 | sk移動設定 | SetPosition | SK666 | 0 | 0.0 | 0.0 |
| 192 | 位移 | SetPosition | magic | 0 | 0.0 | 0.0 |
| 209 | 呼叫腳本 | CallScript |  | 0 | 0.1 | 0.0 |
| 222 | 主動者 攻擊 | SetPose | Person | 0 | 0.0 | 5.0 |
| 233 | 第01個訊號 | Nothing | Script | 0 |  |  |
| 239 | 發出訊息給其他物件 | SendMessage |  | 0 |  |  |
| 249 | 魔法陣 | Nothing | Script | 0 | 0.0 | 0.5 |
| 257 | 顯示物件 | SetShow | magic | 0 |  |  |
| 265 | 節點物件縮放設定 | SetScale | magic | 0 | 0.0 | 1.0 |
| 276 | 設定物件顏色 | SetColor | magic | 0 | 1.5 | 0.5 |
| 295 | 發出訊息給其他物件 | SendMessage |  | 0 |  |  |
| 311 | 發出訊息給其他物件 | SendMessage |  | 0 |  |  |
| 332 | Ani  Hit000 | Ani |  |  |  |  |
| 367 | SK_XXX | Ani |  |  |  |  |
| 408 | 音符分子 | Particle |  |  |  |  |
| 445 | Particle | Particle |  |  |  |  |
| 513 | 被動者 受傷 | SetPose | Person | 0 | 0.0 | 1.0 |
| 529 | 主動者 擊飛 | SetPose | Person | 0 | 0.0 | 50.0 |
| 545 | 主動者 擊飛 | SetPose | Person | 0 | 0.0 | 50.0 |
| 566 | 移動設定 | Nothing | Script | 0 | 0.5 | 0.0 |
| 574 | hit_z07移動設定 | SetPosition | hit_z07 | 0 | 0.0 | 0.0 |
| 591 | Hit000移動設定 | SetPosition | Hit000 | 0 | 0.0 | 0.0 |
| 609 | sk_XXX移動設定 | SetPosition | SK_XXX | 0 | 0.0 | 0.0 |
| 625 | Par_00移動設定 | SetPosition | Par_00 | 0 | 0.0 | 0.0 |
| 642 | 加時間用 | Nothing | Script | 0 | 0.2 | 0.0 |
| 650 | 顯示物件 | SetShow | SK666 | 0 |  |  |
| 658 | 發出訊息給其他物件 | SendMessage |  | 0 |  |  |
| 667 | 分子 | Nothing | Script | 555 | 0.5 | 0.0 |
| 675 | 繪圖物件設定 | SetRenderObj | Person | 0 |  |  |
| 685 | 設定物件顏色 | SetColor | Person | 0 | 0.0 | 0.0 |
| 694 | 設定物件顏色 | SetColor | Person | 0 | 0.0 | 0.5 |
| 703 | 設定物件顏色 | SetColor | Person | 0 | 1.5 | 0.25 |
| 712 | 繪圖物件設定 | SetRenderObj | Person | 0 |  |  |
| 728 | 撥放音效 | PlaySound |  | 0 | 0.0 | 0.0 |
| 737 | 秀hit_z07 | SetShow | hit_z07 | 0 |  |  |
| 745 | 分子 | Nothing | Script | 0 | 0.5 | 0.0 |
| 753 | SK_XXX上移 | SetPosition | SK_XXX | 0 | 0.0 | 2.0 |
| 769 | SK_XXX旋轉設定 | SetRotation | SK_XXX | 0 | 0.0 | 2.0 |
| 780 | show Par_00 | SetShow | Par_00 | 0 |  |  |
| 788 | 加時間用 | Nothing | Script | 0 | 0.0 | 1.5 |
| 796 | unshow Par_00 | SetShow | Par_00 | 0 |  |  |
| 814 | 呼叫其他腳本 | CallScript |  | 0 | 0.0 | 0.0 |

递归可达资源 55 个；未匹配依赖 0 条。结构数据：`original_resources/organized/effects/script_data/BattleScript/common0065.json`。

## 待验证依赖

