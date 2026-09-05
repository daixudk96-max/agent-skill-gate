# 改造并治理

当前步骤为 operate（必达内容）。
- 运行 tools/skill-converter.py <目标目录> <skill名> [--steps "id|标题|描述,..."] 生成母包。
- 编辑 flow.yaml：为每步填 validators 机器校验规则。类型：
  - file：产物存在（path 相对工作目录）。
  - non-empty：产物存在且非空白。
  - contains：产物文本中含指定子串（字段校验）：
    validators: [{type: contains, path: notes/requirements.md, pattern: repoRoot}]。
  - heading：产物含指定级别的 Markdown ATX 标题（标题文本含 pattern），level 可选（缺省任意 1..=6，只认井号标题不认下划线）：
    validators: [{type: heading, path: notes/requirements.md, level: 1, pattern: repoRoot}]。
  选择原则：能机械验证的约束都用 validator 表达（存在性/非空/关键字段/标题结构），其余才写进 guide 让模型执行。
- 若原 skill 含条件流程（"如果 X 就做 A，否则做 B"），用 branches 表达：
  branches: [{when: {type: file|non-empty|contains, path}, then: <step>}, {then: <else-step>}]；
  条件由程序判定（路径相对工作目录），未走备选自动标 skipped。
- 编辑 guides/<id>.md：把转换器生成的占位草稿替换为当前步骤真实必达内容。
- 参考内容归位（核心原则）：
  - 原 skill 的提示/例子/do/don't/进阶说明，逐字复制到用到它的步骤的 guide 末尾。
  - 哪一步用到就复制到哪一步；多步用到就多步复制、多步重复（允许上下文膨胀）。
  - 逐字不改写：只做章节切分与搬运，不重写原内容。
  - 找不到对应步骤的内容，保留在原位置（references/ 等），不删除。
  - 不设"高级内容/按需阅读"桶：所有内容都附在具体步骤上。
- 把 Step-Gate 前导注入/改写目标 SKILL.md。
- 产出 notes/operation-log.md（非空），记录改动与归位映射。