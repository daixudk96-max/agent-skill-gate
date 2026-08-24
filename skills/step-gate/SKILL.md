---
name: step-gate
description: 把任意现有 skill 改造成受 step-gate 步骤门控的治理版（meta-skill：改造别的 skill 的 skill）
---

# step-gate

用途：当用户希望"保证 Agent 不能跳步骤"时，用本 skill 把任意未治理 skill
改造为带 step-gate 运行时门控的版本。门控由程序（step-gate 二进制）而非模型保证。

## 工作流程（必须按序执行）

1. 定位目标 skill 目录（含 SKILL.md 的目录，如 ~/.claude/skills/foo）。
2. 阅读 SKILL.md，确定步骤边界：优先人工确认，或取二级标题为候选。
3. 转换：运行本目录 tools/skill-converter.py <目标目录> <skill名> [--steps "id1|标题1|描述1,id2|标题2|描述2"]
   产物为 skills-src/<名>/ 母包（flow.yaml + guides/ + scripts/run + bin/step-gate 全平台）。
4. 编辑母包 flow.yaml：为每步填 validators（type: file 或 non-empty + path），并把 guides/<id>.md
   的占位草稿替换为当前步骤真实必达内容（不能含 TODO: REQUIRED-GUIDE 占位，否则 skill-pack 拒绝）。
5. 改写母包 SKILL.md：在开头注入前导说明（见下节"必须注入的前导"）。
6. 验收（在母包目录执行，必须全部通过）：
   - scripts/run status          -> 显示当前步与每步 delivery 状态（required/pending/delivered）
   - scripts/run next            -> 两阶段交付当前步契约并提交回执（必须先 next 才能 complete）
   - scripts/run complete        -> 无产物/无回执/契约被改时必须失败退出(exit 1)
   - 修复产物后 complete         -> 恢复推进
   - scripts/run status --json   -> 验证 admission_status/admission_valid 与 proofs
7. 分发：运行 tools/skill-pack.py <名> --zip（严格校验，失败 exit 2 不产出），得到 dist/<名>-<agent> 6 份分发包。

## 硬约束（不可违背）

- 状态文件 .step-gate/state.json 只由 step-gate 程序读写，禁止手改。
- Agent 只允许通过 status/next/complete/fail/reset 交互；step-gate 未输出 next 前，
  Agent 不得开始下一步工作；complete 未通过（exit 1）时不得进入下一步。
- 失败处理只有两条路：修复产物后再次 complete（自动 recover 重试），或 fail 记录原因。
- validators 仅允许 type: file / type: non-empty 两种规则。
- 步骤顺序以 flow.yaml 的 steps 数组为准，与 SKILL.md 叙述顺序必须一致。
- 每步产物必须落在 skill 目录内（validators 的 path 相对 skill 目录）。

## 前置说明（注入目标 SKILL.md 的片段）

本 skill 已启用 step-gate 步骤门控。执行任何工作前先运行
scripts/run(.cmd|.sh) status 查看当前步骤；每一步完成产物后运行
scripts/run complete 校验并推进；被门控（exit 1）时修复产物后重试，
禁止跳过或手动改写 .step-gate/state.json。
