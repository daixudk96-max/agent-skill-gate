# step-gate

Agent Skill 步进治理：**由程序（而非模型）保证 Agent 不能跳步骤**。

这是一个标准格式的 agent skill（SKILL.md + 运行时 + 工具）。把它装进你的 agent 后，
对 Agent 说一句"用 step-gate 改造我的 <skill>"，它就会把任意现有 skill 改造成步骤门控版：
每一步只有通过程序校验（产物 + 交付回执）才能推进，跳过或乱序在物理上不可能。

## 安装

把 skills/step-gate/ 整个目录复制到你的 agent 的 skill 目录（目录名保持 step-gate）：

- **Claude Code**：~/.claude/skills/step-gate/
- **DSH / Cursor / OpenCode / Gemini CLI**（项目级）：<项目根>/.agents/skills/step-gate/
- 同上（全局）：~/.agents/skills/step-gate/

复制即用——包内已内置 5 平台二进制（windows-x64 / linux-x64 / linux-arm64 / macos-x64 / macos-arm64），零运行时依赖。

## 使用

装好后对 Agent 说：

> 用 step-gate 改造我的 <skill>

Agent 会按 3 个门控步骤执行：**理解目标 skill → 改造并治理（生成 flow.yaml / guides / validators）→ 验收并分发**。
每一步由 step-gate 程序校验产物并记录交付回执；产物缺失、跳过 next、契约被改都会 exit 1 被拦。
改造时遵循**内容归位原则**：原 skill 的提示/例子/do/don't 逐字复制到用到它的步骤指南里（多步用到就多步复制），不设"高级内容"桶。

## 原理（30 秒版）

- **flow.yaml**：声明步骤与每步产物规则（validators：file / non-empty）
- **状态机**：pending -> current -> done（分支备选 skipped）；只有当前步可 complete，失败 failed 可修复重试
- **交付门**：next 把该步完整指南推送给 Agent 并写入回执（admission），complete 无回执即拒绝——
  Agent 不可能"没看到步骤说明"就完成
- **链治理**：多个 skill 可串成链（chain.json），跨 skill 顺序同样由程序门控
- **分支状态机**：flow.yaml 支持条件分支（file / non-empty / contains 判定 + else 兜底），"如果 X 就做 A 否则做 B"由程序判定，未走备选自动标 skipped
- **防绕过**：状态文件只由程序读写；管理员命令（reset/fail/init）需要 operator token，启动器对 Agent 白名单化

## 目录结构

    step-gate/
      SKILL.md        # 标准 Anthropic 格式（frontmatter + 渐进披露）
      flow.yaml       # 本 skill 自身的步骤门控声明
      guides/         # 每步必达指南（由 next 交付）
      bin/            # 5 平台 step-gate 二进制
      scripts/        # run.cmd / run.sh 启动器（自动选平台 + 命令白名单）
      tools/          # skill-converter.py / skill-pack.py / check_bins.py（纯标准库）
      INSTALL.md / LICENSE.txt

## 验证

治理化的核心保障已通过 84 项单元测试 + DSH 空会话四轨迹实测（直接 complete 被拒、跳过 next 被拒、
旧包迁移门、标准流程全过）+ 分支状态机端到端三场景（else 兜底 / when 命中 / meta 决策记录）。

## 许可证

Apache-2.0（见 LICENSE）。包内 skills/step-gate/LICENSE.txt 同款。