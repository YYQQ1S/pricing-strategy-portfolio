"""
异乡好居 · AI智能客服数据分析 · 模拟面试数据库
运行：python create_ai_cs_db.py
生成：ai_customer_service.db
"""
import sqlite3
import random
from datetime import datetime, timedelta

random.seed(42)
conn = sqlite3.connect("ai_customer_service.db")
c = conn.cursor()

# ============================================================
# 建表
# ============================================================
c.executescript("""
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    user_id    INTEGER PRIMARY KEY,
    user_name  TEXT,
    user_type  TEXT,        -- 'new' / 'returning'
    region     TEXT,        -- '中国大陆','美国','英国','澳大利亚','欧洲其他'
    source     TEXT,        -- '搜索','社媒','推荐','广告'
    register_date DATE
);

DROP TABLE IF EXISTS intent_category;
CREATE TABLE intent_category (
    category_id   INTEGER PRIMARY KEY,
    category_name TEXT,     -- '房源咨询','租房流程','支付问题','退改政策','维修报修','签证咨询','其他'
    description   TEXT
);

DROP TABLE IF EXISTS conversations;
CREATE TABLE conversations (
    session_id        INTEGER PRIMARY KEY,
    user_id           INTEGER,
    dt                DATE,
    intent_category   TEXT,
    turn_count        INTEGER,       -- 对话轮数
    ai_handled        INTEGER,       -- 1=AI处理, 0=纯人工
    transfer_to_human INTEGER,       -- 1=转人工, 0=未转
    response_time_sec REAL,          -- AI平均响应时间(秒)
    user_satisfaction INTEGER,       -- 1~5
    resolved          INTEGER,       -- 1=已解决, 0=未解决
    experiment_group  TEXT,          -- 'A'(对照组), 'B'(实验组)
    language          TEXT,          -- 'zh','en'
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

DROP TABLE IF EXISTS human_tickets;
CREATE TABLE human_tickets (
    ticket_id         INTEGER PRIMARY KEY,
    session_id        INTEGER,
    agent_id          INTEGER,
    handle_time_min   INTEGER,       -- 人工处理时长(分钟)
    resolution_status TEXT,          -- '已解决','未解决','已转交'
    FOREIGN KEY(session_id) REFERENCES conversations(session_id)
);

DROP TABLE IF EXISTS daily_cost;
CREATE TABLE daily_cost (
    dt              DATE PRIMARY KEY,
    total_sessions  INTEGER,
    ai_sessions     INTEGER,
    api_calls       INTEGER,
    total_tokens    INTEGER,
    api_cost_cny    REAL
);
""")

# ============================================================
# 用户数据 (50人)
# ============================================================
names = ["赵明","钱小丽","孙强","李芳","周晓","吴磊","郑悦","王浩","冯婷","陈然",
         "褚思","卫华","蒋敏","沈鑫","韩露","杨帆","朱婷","秦岭","许瑞","何静",
         "吕刚","施雨","张弛","孔琳","曹阳","严浩","华蕊","金鑫","魏岚","陶然",
         "姜晨","戚薇","谢安","邹琪","柏楠","水心","窦鹏","章雪","苏扬","潘悦",
         "葛林","范瑶","彭博","鲁敏","马超","方芳","任杰","袁浩","柳青","丰雪"]

user_types = ["new"]*20 + ["returning"]*30
regions  = ["中国大陆"]*20 + ["美国"]*10 + ["英国"]*8 + ["澳大利亚"]*7 + ["欧洲其他"]*5
sources  = ["搜索"]*18 + ["社媒"]*12 + ["推荐"]*10 + ["广告"]*10

random.shuffle(user_types)
random.shuffle(sources)

base_date = datetime(2026, 3, 1)
users = []
for i, name in enumerate(names):
    reg_date = base_date + timedelta(days=random.randint(0, 90))
    users.append((i+1, name, user_types[i], random.choice(regions), sources[i], reg_date.strftime("%Y-%m-%d")))
c.executemany("INSERT INTO users VALUES (?,?,?,?,?,?)", users)

# ============================================================
# 意图分类
# ============================================================
intents = [
    (1, "房源咨询", "用户咨询房源详情、价格、位置等"),
    (2, "租房流程", "用户询问租房步骤、所需材料、签约流程"),
    (3, "支付问题", "支付方式、汇率、退款等问题"),
    (4, "退改政策", "退租、改签、取消预订相关政策"),
    (5, "维修报修", "入住后维修、设施故障报修"),
    (6, "签证咨询", "留学签证、租房证明相关问题"),
    (7, "其他", "不属于以上分类的杂项问题"),
]
c.executemany("INSERT INTO intent_category VALUES (?,?,?)", intents)

# ============================================================
# 会话数据 (500条, 覆盖近30天)
# ============================================================
intent_list = ["房源咨询"]*180 + ["租房流程"]*90 + ["支付问题"]*70 + ["退改政策"]*50 + ["维修报修"]*40 + ["签证咨询"]*40 + ["其他"]*30
exp_groups = ["A"]*250 + ["B"]*250

random.shuffle(intent_list)
random.shuffle(exp_groups)

conversations = []
session_id = 1
conv_date = datetime(2026, 5, 5)
for day_offset in range(30):
    dt = conv_date + timedelta(days=day_offset)
    daily_sessions = random.randint(12, 22)
    for _ in range(daily_sessions):
        uid  = random.randint(1, 50)
        intent = random.choice(intent_list)
        # B组(新版AI) 转人工率更低、满意度更高
        group = random.choice(["A","B"])
        if group == "A":
            transfer = 1 if random.random() < 0.22 else 0  # 22%转人工
            sat = random.choices([3,4,5,2,1], weights=[15,30,35,12,8])[0]
            resolved = 1 if random.random() < 0.68 else 0
            resp = round(random.uniform(1.5, 8.0), 1)
        else:
            transfer = 1 if random.random() < 0.14 else 0  # 14%转人工
            sat = random.choices([3,4,5,2,1], weights=[10,28,45,10,7])[0]
            resolved = 1 if random.random() < 0.78 else 0
            resp = round(random.uniform(0.8, 5.0), 1)

        turns = random.randint(1, 12)
        lang = "zh" if random.random() < 0.65 else "en"
        ai_handled = 1 if random.random() < 0.85 else 0

        conversations.append((session_id, uid, dt.strftime("%Y-%m-%d"), intent,
                             turns, ai_handled, transfer, resp, sat, resolved, group, lang))
        session_id += 1

c.executemany("INSERT INTO conversations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", conversations)

# ============================================================
# 人工工单 (转人工的会话)
# ============================================================
human = []
ticket_id = 1
for conv in conversations:
    if conv[6] == 1:  # transfer_to_human = 1
        human.append((ticket_id, conv[0], random.randint(101,110),
                      random.randint(5, 120),
                      random.choice(["已解决","未解决","已转交"])))
        ticket_id += 1
c.executemany("INSERT INTO human_tickets VALUES (?,?,?,?,?)", human)

# ============================================================
# 每日成本
# ============================================================
daily = []
for day_offset in range(30):
    dt = (conv_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
    total = random.randint(30, 80)
    ai_s  = int(total * random.uniform(0.75, 0.90))
    calls = ai_s * random.randint(3, 8)
    tokens = calls * random.randint(800, 3000)
    cost  = round(tokens / 1000 * 0.02, 2)  # 每千token 0.02元
    daily.append((dt, total, ai_s, calls, tokens, cost))
c.executemany("INSERT INTO daily_cost VALUES (?,?,?,?,?,?)", daily)

conn.commit()
conn.close()

print("Database ai_customer_service.db created!")
print(f"   - users:          {len(users)} rows")
print(f"   - conversations:  {len(conversations)} rows")
print(f"   - human_tickets:  {len(human)} rows")
print(f"   - daily_cost:     {len(daily)} rows")
print(f"   - intent_category:{len(intents)} rows")