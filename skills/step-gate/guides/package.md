# 验收并分发

当前步骤为 package（必达内容）。
- 用 scripts/run(.cmd|.sh) 依次执行 status -> next -> complete -> status --json 验收。
- 运行 tools/skill-pack.py <skill名> --zip 生成 6-agent 分发包。
- 产出 notes/package-log.md（非空），记录验收与分发结果。