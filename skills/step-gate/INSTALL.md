# step-gate 安装说明

把本目录整体复制到你的 agent 的 skill 目录（目录名保持 step-gate）：

- Claude Code:      ~/.claude/skills/step-gate/
- DSH / Cursor / OpenCode / Gemini CLI（项目级）:  <项目根>/.agents/skills/step-gate/
- 上述 agent（全局）:   ~/.agents/skills/step-gate/

包内已含 5 平台 step-gate 二进制（windows-x64 / linux-x64 / linux-arm64 / macos-x64 / macos-arm64），
无需任何运行时安装。

## 使用

装好后对 Agent 说："用 step-gate 改造我的 <某个 skill>"。Agent 将按 3 步执行：

1. 理解目标 skill（产出 notes/understanding.md）
2. 运行 tools/skill-converter.py 生成治理版母包，并编辑 flow.yaml validators 与 guides 必达内容（产出 notes/operation-log.md）
3. 用 scripts/run status/next/complete 验收，再用 tools/skill-pack.py 分发（产出 notes/package-log.md）

每步前先执行 scripts/run(.cmd|.sh) status 查看当前步；scripts/run next 取下一步
（自动交付该步必达 guide 并记录回执）；scripts/run complete 校验产物并推进。
被门控（exit 1）时修复产物后重试，禁止跳过或手改 .step-gate/state.json。

## 要求

- 运行时零依赖（二进制内置）
- tools/ 仅需 Python 3 标准库（无第三方包）
- 许可证：Apache-2.0（本目录 LICENSE.txt）