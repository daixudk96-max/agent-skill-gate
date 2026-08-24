# 改造并治理

当前步骤为 operate（必达内容）。
- 运行 tools/skill-converter.py <目标目录> <skill名> [--steps "id|标题|描述,..."] 生成母包。
- 编辑 flow.yaml：为每步填 validators（file/non-empty）机器校验规则。
- 编辑 guides/<id>.md：把转换器生成的占位草稿替换为当前步骤真实必达内容。
- 把 Step-Gate 前导注入/改写目标 SKILL.md。
- 产出 notes/operation-log.md（非空），记录改动。