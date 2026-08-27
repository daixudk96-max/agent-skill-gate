# 验收并分发

当前步骤为 package（必达内容）。
- 用 scripts/run(.cmd|.sh) 依次执行 status -> next -> complete -> status --json 验收。
- 归位验收：确认每个 guide 已含该步全部必达内容；无"高级内容/按需阅读"桶残留；
  若有内容因找不到对应步骤而保留原位置，须在 notes/package-log.md 记录保留理由。
- 运行 tools/skill-pack.py <skill名> --zip 生成 6-agent 分发包。
- 产出 notes/package-log.md（非空），记录验收与分发结果。