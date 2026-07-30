# Mobius Ticket Pilot 🎫✈️

**多 Agent 通用的 Mobius Issue 管理 Skill。**

Mobius Ticket Pilot 让任何 AI Agent（Hermes、Claude Code、Codex、OpenClaw、Cursor、Gemini CLI）都能读写 FeedMob 内部 Issue 系统 Mobius。Agent 可以：

- 读取 / 创建 / 更新 Mobius issue
- 分析团队 Issue 优先级（只读模式，不动任何东西）
- 自动发进度评论、改状态
- 追踪团队成员工作进展
- 通过 REST API 或 MCP Server 操作

> **与 Linear 版 ticket-pilot 的区别**：Mobius 是自包含系统，不需要 GitHub 镜像同步。所有 Issue、评论、状态都在 Mobius 上。

## 安装

### 方式一：curl 一键安装（推荐）

```bash
# 默认装到 Claude Code
curl -fsSL https://raw.githubusercontent.com/RachelXiaolan/mobius-ticket-pilot/main/install.sh | bash

# 指定 agent（逗号分隔可装多个）
curl -fsSL https://raw.githubusercontent.com/RachelXiaolan/mobius-ticket-pilot/main/install.sh | bash -s -- --agent hermes
curl -fsSL https://raw.githubusercontent.com/RachelXiaolan/mobius-ticket-pilot/main/install.sh | bash -s -- --agent claude,codex,hermes
```

可选 agent：`claude` `codex` `hermes` `openclaw` `cursor` `gemini`

### 方式二：手动安装

```bash
git clone https://github.com/RachelXiaolan/mobius-ticket-pilot.git
cp -r mobius-ticket-pilot/ ~/.claude/skills/mobius-ticket-pilot/    # 换成你的 agent 路径
```

| Agent | Skills 目录 |
|-------|------------|
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/` |
| Hermes | `~/.hermes/skills/productivity/` |
| OpenClaw | `~/.openclaw/skills/` |
| Cursor | `.cursor/skills/` |
| Gemini CLI | `.gemini/skills/` |

## 前置条件

### Mobius API Token

Mobius 使用 Bearer Token 认证（格式：`mob_...`）：

1. 从 Mobius 设置页面获取 Token（或联系 Mobius 管理员——目前是 Teammate-A）
2. 设置为环境变量 `MOBIUS_API_KEY`

```bash
export MOBIUS_API_KEY="mob_your_token_here"
```

快速验证：
```bash
curl -s https://mobius.feedmob.com/api/teams \
  -H "Authorization: Bearer $MOBIUS_API_KEY" | python3 -m json.tool
```

### 系统依赖

- `curl` — API 调用
- `python3` — CLI 辅助脚本

## 快速上手

装好后，直接用自然语言跟 Agent 说就行：

```
看一下 AI-1234
```

Agent 会读取 Issue 内容并总结，**不会改动任何东西**。

```
整理一下团队最新情况，分析优先级
```

Agent 会拉取所有活跃 Issue，分析哪些卡住了、哪些值得推，生成报告。

### 常见触发方式

| 你说的话 | Agent 会做什么 |
|---------|--------------|
| `看一下 AI-XXXX` / `看看这个 issue` | **只读**：读取并总结 issue，不动任何东西 |
| `看看团队在做什么` / `分析优先级` | **只读**：拉取所有活跃 issue，分析优先级，生成 8 列表格报告 |
| `开始做 AI-XXXX` | 读取 issue → In Progress → 发"开始"评论 → 开工 |
| `AI-XXXX 改完了` | 验证 → In Review/Done → 发完成评论 |
| `建个 issue：xxx` | 用团队命名规范创建新 issue |
| 不确定 | Agent 会问："你是想看一下，还是开始做？" |

> 💡 **"看一下" ≠ "开始做"。** Agent 不会因为你提了一个 issue 就自动改状态。只有你明确说"开始/处理/做"才会启动完整流程。

## 团队优先级分析（只读模式）

这是本 Skill 的核心功能之一。当你说"整理整理最新情况"、"分析优先级"时：

1. 拉取团队所有活跃 Issue（`GET /api/issues?teamId=<uuid>&limit=500`）
2. 过滤掉已完成/取消/重复的
3. 按负责人分组，识别卡住的 Issue
4. 输出 **8 列表格报告**：

```
| Issue | 状态 | Label(→负责人) | 创建 | 最后更新 | 简介 | 建议原因 | 建议处理方式 |
```

5. 重点关注：In Review 堆积、未分配 Issue、古老僵尸 Issue、开发人员负载
6. 同步到 notes vault

**全程只读，不会修改任何 Issue。**

## 自动进度追踪（auto_progress.py）

Skill 内置一个**自动进度追踪脚本**，在任务的关键节点自动更新 Issue 状态 + 发格式化评论，不用手动 PATCH + POST：

```bash
SCRIPT="$(find ~/.hermes ~/.claude ~/.codex 2>/dev/null -path '*/mobius-ticket-pilot/scripts/auto_progress.py' | head -1)"

python3 "$SCRIPT" start AI-1234 --scope "写 MCP 配置文档" --plan "先调研"        # 🚀 → In Progress
python3 "$SCRIPT" progress AI-1234 --summary "文档完成" --next "提交PR"          # 💬 阶段评论
python3 "$SCRIPT" blocker AI-1234 --error "编译报错" --check "检查依赖"          # 🛑 阻塞
python3 "$SCRIPT" review AI-1234 --summary "文档+PR已提交" --links "PR链接"      # 🎉 → In Review
python3 "$SCRIPT" done AI-1234 --summary "PR merged" --links "PR链接"           # ✅ → Done
```

Agent 在处理 Issue 时会自动调用这些命令，你不需要操心状态更新和评论发布。

## CLI 辅助工具

装好后可以用命令行快速操作：

```bash
SCRIPT="$(find ~/.hermes ~/.claude ~/.codex 2>/dev/null -path '*/mobius-ticket-pilot/scripts/mobius_cli.py' | head -1)"

python3 "$SCRIPT" list-active          # 列出活跃 issue
python3 "$SCRIPT" get AI-1234          # 查看单个 issue
python3 "$SCRIPT" get AI-1234 --comments   # 含评论
python3 "$SCRIPT" update-status AI-1234 "In Review"  # 改状态
python3 "$SCRIPT" add-comment AI-1234 "开始处理"      # 发评论
python3 "$SCRIPT" create "issue标题" --description "内容" --label "<your label>"  # 建issue
python3 "$SCRIPT" search "bidding"     # 搜索
python3 "$SCRIPT" team-status          # 团队状态总览
```

## Mobius MCP Server

除了 REST API，Mobius 还提供内置 MCP Server（23 个工具，REST 的超集）：

- AI 工具：`triage_issue` / `workspace_briefing` / `ask_mobius`
- 软删除（archive）/ 附件管理 / 评论编辑 / 项目管理 / 外部链接

Hermes 配置：
```yaml
mcp_servers:
  mobius:
    url: "https://mobius.feedmob.com/api/mcp"
    headers:
      Authorization: "Bearer mob_YOUR_TOKEN"
    timeout: 180
```

详见 `references/mcp-setup-guide.md`（支持 Hermes / Claude Desktop / Cursor / Cline / Continue）。

## 工作原理

```
Mobius（唯一真相源）
  ├── REST API (/api/issues, /api/teams, /api/labels ...)
  │     └── curl / python3 直接调用
  ├── MCP Server (/api/mcp, JSON-RPC, 23 tools)
  │     └── Hermes / Claude / Cursor 等 MCP 客户端
  └── Web UI (https://mobius.feedmob.com/issue/AI-XXXX)
        └── 报告/评论中的链接格式
```

### 认证

| Agent | Mobius |
|-------|--------|
| 所有 Agent | `$MOBIUS_API_KEY`（环境变量） |

Skill 会自动检测 Token 并用 Bearer 认证，无需 Agent 专属配置。

## 关键设计决策

1. **只读优先**：不确定意图时默认只读，不动任何 Issue
2. **Mobius = 唯一真相源**：不需要 GitHub 同步
3. **Label = 实际负责人**：Mobius assignee 只能一个人，多人任务用 label 表示
4. **评论按阶段发**：不是一个 prompt 一条评论，而是完成一个阶段才发一条
5. **Web UI 链接用 `/issue/`**：`/issue/AI-XXXX` 是详情页，`/all/AI-XXXX` 是看板页（会空白）

## 文件结构

```
mobius-ticket-pilot/
├── SKILL.md                              # 主技能文件
├── README.md                             # 本文件（中文版）
├── README_EN.md                          # 英文版
├── LICENSE                               # MIT
├── CHANGELOG.md                          # 版本历史
├── install.sh                            # 一键安装脚本
├── references/
│   ├── onboarding-settings.md            # 首次配置格式
│   ├── state-model.md                    # Mobius 状态模型 + 评论契约
│   ├── issue-audit-workflow.md           # 只读团队优先级分析完整流程
│   ├── mcp-setup-guide.md               # MCP Server 多客户端配置指南
│   ├── web-ui-navigation-analysis.md     # Mobius 前端导航结构分析
│   ├── frontend-codebase.md              # Mobius 前端代码库地图（贡献 PR 用）
│   └── agent-automation.md               # Agent 自动化字段陷阱（delegatedAgentId）
└── scripts/
    ├── auto_progress.py                  # 🆕 自动状态+评论（start/progress/blocker/review/done）
    └── mobius_cli.py                     # Python CLI 辅助工具
```

## License

MIT

## 作者

Rachel Lu (@RachelXiaolan)
