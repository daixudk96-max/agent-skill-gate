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
   产物为母包（flow.yaml + guides/ + scripts/run.cmd|.sh + bin/ 全平台二进制）。
4. 编辑母包 flow.yaml：为每步填 validators 与 guides/<id>.md 必达内容（不能含 TODO: REQUIRED-GUIDE
   占位，否则 skill-pack 拒绝）。validator 四型：
   - type: file + path —— 产物存在（path 相对 Agent 调用启动器时的工作目录，下同）
   - type: non-empty + path —— 产物存在且非空白
   - type: contains + path + pattern —— 产物文本含指定子串（字段校验）
   - type: heading + path + pattern [+ level] —— 产物含指定级别 Markdown 井号标题且标题文本含 pattern；level 缺省任意 1..=6
   条件流程用 branches（when: 条件 + then: 步骤，else 省略 when）：
   条件 type 同 file/non-empty/contains，由程序判定，未走备选自动标 skipped。
5. 改写母包 SKILL.md：在开头注入下节完整前导。
6. 验收（从工作目录调用 scripts/run.cmd|.sh 绝对路径，必须全部通过）：
   - status   -> 显示当前步与每步 delivery 状态（required/pending/delivered）
   - next     -> 两阶段交付当前步契约并提交回执（必须先 next 才能 complete）
   - complete -> 无产物/字段缺失/无回执/契约被改时必须失败退出(exit 1)
   - 修复产物后 complete -> 恢复推进
   - status --json -> 验证 admission_status/admission_valid 与 proofs
7. 分发：运行 tools/skill-pack.py <名> --zip（严格校验，失败 exit 2 不产出），得到 6 份 agent 分发包。

## 硬约束（不可违背）

- 状态文件 .step-gate/state.json 与链文件 .step-gate/chain.json 只由 step-gate 程序读写，禁止手改。
- Agent 只允许通过 status/next/complete 与 chain status 交互；step-gate 未输出 next 前，
  Agent 不得开始下一步工作；complete 未通过（exit 1）时不得进入下一步。
- 失败处理只有两条路：修复产物后再次 complete（自动 recover 重试），或 operator 介入。
- validators 允许 type: file / non-empty / contains / heading；pattern 必填于 contains/heading。
- 步骤顺序以 flow.yaml 的 steps 数组为准，与 SKILL.md 叙述顺序必须一致。
- validators 与 branches 条件的 path 均相对 Agent 调用启动器时的工作目录（启动器会把调用时的
  当前目录记为 --workdir 传给 step-gate），不是 skill 安装目录；因此必须从项目工作目录用绝对路径
  调用启动器，不要 cd 进 skill 目录。若 Agent 踩错目录，complete/next 会以 cannot read 报出它找的
  路径——回到原工作目录重跑同一命令即可，状态文件不受影响，无需任何重置。
- reset / fail / init / chain init / chain advance 是 operator-only（admin token），不得尝试。

## 必须注入目标 SKILL.md 的前导（逐字复制）

## Step-Gate Workflow (MANDATORY)

This skill is governed by a step gate. You MUST follow it exactly:

0. MANDATORY: BEFORE doing anything else, run the status command (item 1), then mirror BOTH views into your environment's task/todo list tool (todo, task list, plan board, checklist, to-do, todos, task tracker, kanban, issue list, agenda, work items, plan, tasks — whatever your environment provides): (a) the chain progress shown under "chain:" (one entry per member, e.g. "1/2 skill-creator", "2/2 <this skill>") and (b) every flow step of THIS skill as checklist items. Update the mirror after every complete. The gate is the source of truth; the checklist is only a mirror. If no such tool exists, skip this step.
1. Run the launcher's status command once — its output already contains your chain position ("chain: ... cursor i/n", with any chain warning) AND this skill's steps. That single call is all you need; standalone chain inspection is diagnostics only.
2. Work ONLY on the step printed by next, and DO NOT jump ahead. Each step MUST be delivered first: run next — it pushes the current step's full guide (the step's MUST-DELIVER content) into your context and records a delivery receipt. A step you have not run next on cannot be completed.
3. After producing a step's real artifacts, run complete. It only advances when (a) next delivered the current step's contract (receipt committed) AND (b) the machine validators pass. If rejected, fix what the message names and retry through the gate; if it says "run next" or "contract changed", re-run next first. Never edit .step-gate/state.json or .step-gate/chain.json; never fabricate artifacts.
4. If status warns that a previous chain skill is unfinished ("链上一步未完成"), you may NOT work on this skill yet: say so and stop, or ask the user. Only the operator may advance or rebuild the chain.
5. reset / fail / init / chain init / chain advance are operator-only (admin token required). Never attempt them, even by calling the gate binary directly.
6. Create each step's artifacts where flow.yaml validators expect them (paths are relative to your current working directory).
7. If a gate command rejects you with `cannot read ...` / `... does not exist` / `does not contain ...` while the artifact you produced is real and in place, you almost certainly invoked the launcher from the wrong working directory — the error path shows exactly where the gate looked. Go back to the project working directory you started in and re-run the same command there. This mistake never corrupts state (.step-gate/) and never requires a reset.

Invocation: call the launcher from your current working directory using its ABSOLUTE path — do NOT cd into the skill directory. The skill loader reports this skill's base directory; use '<base dir>\scripts\run.cmd <command>' on Windows (PowerShell: & '<base dir>\scripts\run.cmd' <command>) or '<base dir>/scripts/run.sh <command>' on Unix/Git Bash. The launcher records your current directory as the artifact root (--workdir), so step artifacts are validated relative to where you invoked it — NOT inside the skill package.
