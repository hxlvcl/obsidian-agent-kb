# Obsidian + AI Agent 本地知识库管理方案

一套让 AI Agent 帮你管理 Obsidian 知识库的完整方案——Agent 身份定义、入库技能、安全脚本、规则文档，开箱即用。

---

## 这是什么

你在 Obsidian 里存文章，AI Agent 帮你整理、分类、建双链、编译 Wiki——但你怕它乱改你的笔记。

这个项目解决的就是这个：**用权限分区 + 脚本硬约束，让 AI 能干活但不会闯祸。**

核心思路：
- **四区权限**：活动区（随便改）、需授权区（脚本拦截）、半只读区（只能追加）、禁止区（碰都不行）
- **三阶段入库**：整理分类 → 编译 Wiki → 脚本建链，每阶段你审核一次
- **版本控制**：每次操作前 Git 快照，搞坏了随时回滚

---

## 怎么用（三步跑起来）

### 第一步：下载项目

```bash
git clone https://github.com/{{GITHUB_USER}}/obsidian-agent-kb.git
```

### 第二步：改配置

打开以下文件，把 `{{...}}` 替换成你自己的路径：

| 文件 | 占位符 | 改成什么 |
|------|--------|----------|
| `scripts/safe_link_appender.py` | `{{VAULT_PATH}}` | 你的 Obsidian Vault 路径，如 `D:\MyObsidian` |
| `scripts/git_control.py` | `{{VAULT_PATH}}` | 同上 |
| `scripts/audit_rules.py` | `{{VAULT_PATH}}` | 同上 |
| `agent/AGENTS.md` | `{{VAULT_PATH}}` | 同上 |
| `agent/MEMORY.md` | `{{VAULT_PATH}}` 等 | 同上 + 你的 GitHub |
| `vault/知识库管理指南.md` | `{{VAULT_PATH}}` | 同上 |

### 第三步：放进去

1. 把 `vault/` 里的所有内容**复制到**你的 Obsidian Vault 根目录
2. 把 `agent/`、`skills/`、`scripts/` 放在你的 Agent 工作区
3. 初始化 Vault 的 Git：
   ```bash
   cd "你的Vault路径"
   git init && git add -A && git commit -m "init"
   ```
4. 对 Agent 说"入库"——它就按流程跑起来了

---

## 文件结构

```
obsidian-agent-kb/
│
├── README.md                         # 你正在读的文件
│
├── agent/                            # Agent 身份定义
│   ├── SOUL.md                       #   灵魂——信念与原则
│   ├── PROFILE.md                    #   角色——职责与能力
│   ├── BOOTSTRAP.md                  #   启动——初始化检查清单
│   ├── AGENTS.md                     #   手册——操作规范
│   ├── HEARTBEAT.md                  #   心跳——定时任务
│   └── MEMORY.md                     #   记忆——跨会话保留
│
├── skills/
│   └── obsidian入库/
│       └── SKILL.md                  # 入库技能——三阶段流程
│
├── scripts/
│   ├── safe_link_appender.py         # 建链脚本——白名单硬约束
│   ├── git_control.py                # Git 版本控制——快照/提交/回滚
│   └── audit_rules.py                # 规则自检——错误日志→聚类分析
│
└── vault/                            # 扔进 Obsidian 根目录
    ├── 知识库管理指南.md               # 核心规则——权限、分区、流程
    ├── CLAUDE.md                      # 入口规则
    │
    ├── 00-收件箱/                     # 🔵 活动区——入库暂留
    ├── 01-素材库/                     # 🟡 需授权——脚本硬拦截
    ├── 02-Wiki/                       # 🟢 半只读——只允许追加
    │   └── _index.md
    ├── 04-项目/
    │   ├── 管理日志.md                #   操作追溯
    │   └── 错误日志.md                #   事故复盘
    └── 06-系统/                       # 🔴 禁止区
        ├── 入库流程完整版.md
        └── 模板/
            ├── 新笔记.md
            └── Wiki概念页.md
```

---

## 权限分区

这是整套方案的基石。AI 做任何操作前先检查自己在哪个区：

| 颜色 | 区域 | 权限 | 举例 |
|------|------|------|------|
| 🔵 | `00-收件箱/` | 自由读写 | 新文章暂存、建链 |
| 🟡 | `01-素材库/` `03-思考/` `04-项目/` `05-产出/` | 需用户授权 | 已归档文章，脚本硬拦截 |
| 🟢 | `02-Wiki/` | 只能追加 | 追加关联文章和索引条目 |
| 🔴 | `06-系统/` | 完全禁止 | 模板、规则文件 |

---

## 入库流程（简化版）

```
你说"入库"
  │
  ├── 阶段一：AI 读文章 → 提分类 → 你确认 → 清理 frontmatter → 暂留收件箱
  │
  ├── 阶段二：AI 提 Wiki 变更方案 → 你审核 → 执行
  │
  └── 阶段三：AI 提关联方案 → 你审核 → 脚本建链 → 移动到素材库
```

每一步都有你的审核点，AI 不会自己闷头改。

---

## 关键文件说明

### 管理日志（`vault/04-项目/管理日志.md`）

**作用**：每次操作后立即更新，记录做了什么。

**为什么要写**：不写管理日志的 AI 不是好搭档。三天后问"上次入库了什么"，AI 翻管理日志比翻 git log 快。

### 错误日志（`vault/04-项目/错误日志.md`）

**作用**：回滚失败、入库事故、脚本异常全部记这里。

**为什么要写**：不记错误日志的系统修不了 bug。出问题时，先看错误日志→找根因→改规则→避免再犯。这是我们踩坑踩出来的经验。

---

## 依赖

- Python 3.8+
- Git
- Obsidian（建议 v1.5+）

---

## 常见问题

**Q: 我能改目录结构吗？**
可以。改完后同步更新 `safe_link_appender.py` 里的 `ALLOWED` 和 `BLOCKED` 列表。

**Q: Agent 不听话怎么办？**
看错误日志——大概率是权限拦截了。`scripts/safe_link_appender.py` 会打印 `[REJECT]` 说明原因。

**Q: 怎么回滚？**
```bash
cd "你的Vault路径"
python scripts/git_control.py rollback
```

---

## License

MIT
