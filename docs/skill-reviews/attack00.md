# BattleScript/attack00.txt 演出资源核验

来源：`original_resources/organized/effects/configs/GameData/BattleScript/attack00.txt.utf8.txt`

文件名尚未绑定游戏中文技能名；动作表中的延迟、时长按源文本保留，未折算成绝对时间。人物动作、粒子发射、3D 模型、镜头与条件触发尚未组合渲染。

## 显式依赖

| 行 | 原引用 | 匹配资源数 |
|---:|---|---:|
| 167 | `sp\hit000.ant` | 1 |
| 343 | `BattleScript\\DodgeA.txt` | 1 |
| 363 | `BattleScript\\DodgeB.txt` | 1 |

## 动作节点

| 行 | 节点 | Type | 对象 | 触发条件 | 延迟原值 | 时长原值 |
|---:|---|---|---|---|---|---|
| 43 | 主動者 攻擊 | SetPose | Person | 0 | 0.0 | 5.0 |
| 54 | 第01個訊號 | Nothing | Script | 1 |  |  |
| 60 | 發出訊息給其他物件 | SendMessage |  | 0 |  |  |
| 69 | 加時間用 | Nothing | Script | 0 | 0.0 | 0.5 |
| 77 | 主動者 站立 | SetPose | Person | 0 | 0.0 | 1.0 |
| 99 | 發出訊息給其他物件 | SendMessage |  | 0 |  |  |
| 115 | 發出訊息給其他物件 | SendMessage |  | 0 |  |  |
| 164 | Ani  Hit000 | Ani |  |  |  |  |
| 213 | 被動者 受傷 | SetPose | Person | 0 | 0.0 | 1.0 |
| 224 | 站立動作 | SetPose | Person | 0 | 0.0 | 0.5 |
| 241 | 主動者 擊飛 | SetPose | Person | 0 | 0.0 | 50.0 |
| 257 | 主動者 擊飛 | SetPose | Person | 0 | 0.0 | 50.0 |
| 278 | Hit000移動設定 | SetPosition | Hit000 | 0 | 0.0 | 0.0 |
| 295 | 秀Hit0000 | SetShow | Hit000 | 0 |  |  |
| 303 | 加時間用 | Nothing | Script | 0 | 0.5 | 0.0 |
| 311 | 顯示戰鬥結果 | JumpResult | Person | 0 |  |  |
| 320 | 發出訊息給其他物件 | SendMessage |  | 0 |  |  |
| 337 | 呼叫其他腳本 | CallScript |  | 0 | 0.0 | 0.0 |
| 349 | 加時間用 | Nothing | Script | 0 | 0.5 | 0.0 |
| 357 | 呼叫其他腳本 | CallScript |  | 0 | 0.0 | 0.0 |

递归可达资源 32 个；未匹配依赖 0 条。结构数据：`original_resources/organized/effects/script_data/BattleScript/attack00.json`。

## 待验证依赖

