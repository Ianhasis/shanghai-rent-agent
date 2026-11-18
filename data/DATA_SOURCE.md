# 数据来源与许可

## 当前主数据（Step1 起启用）
| 项 | 内容 |
|----|------|
| 名称 | 上海链家租房挂牌数据（含经纬度） |
| 文件 | `data/raw/lianjia_rent_gps.csv` |
| 来源仓库 | https://github.com/Junru-Sheng/lianjia_Crawler |
| 规模 | 原始约 2.0 万条；清洗后见 `preprocess_meta.txt` |
| 字段 | 标题、小区、户型、面积、价格、时间、链接、经度、纬度 |
| 使用说明 | 仓库声明仅供学习研究交流，勿商用；本课程原型仅本地分析与演示 |
| 为何换数据 | 旧版自如数据多为**合租单间卧室面积**（常见 8–20㎡），观感异常；链家数据为**整套出租面积**（常见 30–100㎡），更符合“租一套房”场景 |

## 旧数据（保留对照，不再作为主训练数据）
| 项 | 内容 |
|----|------|
| 名称 | ZiRoomAgent shanghai.csv |
| 文件 | `data/raw/ziroom_shanghai.csv` |
| 来源 | https://github.com/yrjyrj123/ZiRoomAgent |
| 许可证 | Unlicense |
| 说明 | 合租单间为主，已不作为 Agent 主房源库 |

## 边界
历史挂牌价可能与当前市场不同；预测仅供课程评估与筛选参考，不作真实成交依据。
