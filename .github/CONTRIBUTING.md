# 贡献指南 / Contributing Guide

感谢你对 obsidian-agent-kb 的关注！这个项目旨在解决一个具体的问题：**让 AI Agent 安全地管理 Obsidian 知识库，不乱改笔记。**

## 如何贡献

### 报告 Bug

1. 先在 [Issues](https://github.com/hxlvcl/obsidian-agent-kb/issues) 里搜索是否已有相同问题
2. 如果没有，新建 Issue，使用 Bug Report 模板
3. 尽量提供：操作步骤、预期结果、实际结果、错误日志片段

### 提交功能建议

1. 先在 Issues 里搜索是否已有类似建议
2. 描述你遇到的具体场景（为什么需要这个功能）
3. 如果有设想方案，欢迎描述

### 贡献代码

1. Fork 本仓库
2. 新建分支：`git checkout -b feat/xxx`
3. 修改代码，添加测试（如果涉及脚本变更）
4. 确保现有测试通过
5. 提交 PR，描述做了什么、为什么这样做

## 开发设置

```bash
git clone https://github.com/hxlvcl/obsidian-agent-kb.git
cd obsidian-agent-kb
```

本项目是纯 Python 脚本 + Markdown 文档，无需额外依赖即可运行。

### 运行测试（如已有）

```bash
python -m pytest tests/
```

## 项目结构

```
obsidian-agent-kb/
├── README.md              # 项目文档
├── agent/                 # Agent 定义文件
├── skills/                # Agent 技能
├── scripts/               # 核心脚本
│   ├── safe_link_appender.py    # 安全建链
│   ├── git_control.py           # Git 版本控制
│   ├── supplement_linker.py     # 补充链接
│   ├── wiki_audit.py            # Wiki 体检
│   └── audit_rules.py           # 规则自检
├── vault/                 # Obsidian Vault 模板
└── tests/                 # 测试用例
```

## 注意事项

- `scripts/` 下的脚本使用了 `{{VAULT_PATH}}` 占位符，这是故意的——用户需要替换为自己的路径
- 脚本设计为在 Agent 调用链中运行，不适合直接作为命令行工具使用
- README 中的路径示例使用占位符是为了通用性

## 行为准则

本项目遵循 [Contributor Covenant](CODE_OF_CONDUCT.md)。
