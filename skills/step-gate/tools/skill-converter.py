#!/usr/bin/env python3
"""skill-converter: 把普通 skill（只有 SKILL.md）改造成受 step-gate 治理的母包

用法:
  python tools/skill-converter.py <src-dir> <name> [--steps "id1|标题1|描述1,id2|标题2|描述2"]
                                     [--version 0.1.0] [--out skills-src]

步骤提取优先级:
  1. --steps 参数（推荐，人工确认步骤边界；第三段为可选步骤描述）
  2. SKILL.md 中的 "## " 二级标题（自动候选，需人工复核）
  3. 都没有则报错退出

产物: <out>/<name>/ 母包（SKILL.md + flow.yaml + guides/ + scripts/ + bin/）
每步生成 guide: guides/<id>.md 草稿，内含 TODO: REQUIRED-GUIDE 占位标记，
必须由人工/迁移脚本替换为真实必达内容后才能通过 skill-pack 严格校验。
随后可执行: python tools/skill-pack.py <name> --zip
"""
import argparse, os, re, shutil, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, "skills-src", "_template")
DIST_BIN = os.path.join(ROOT, "dist", "bin")

PLACEHOLDER_MARKER = "TODO: REQUIRED-GUIDE"

def parse_steps_arg(steps_arg):
    """解析 --steps "id|标题|描述,..."。描述可选，缺省用通用占位。"""
    steps = []
    for i, item in enumerate(steps_arg.split(",")):
        item = item.strip()
        if not item:
            continue
        parts = item.split("|")
        sid = parts[0].strip().replace(" ", "-").lower()
        title = parts[1].strip() if len(parts) > 1 else parts[0].strip()
        desc = parts[2].strip() if len(parts) > 2 else ("完成「" + title + "」并产出对应产物")
        steps.append([sid, title, desc])
    return steps

def extract_steps_from_md(text):
    """从 SKILL.md 的 ## 标题提取候选步骤。"""
    steps = []
    for m in re.finditer(r"^##\s+(.+)$", text, re.M):
        t = m.group(1).strip()
        if t.lower() in ("frontmatter", "overview", "usage", "安装", "使用", "示例", "examples"):
            continue
        sid = "step-%d" % (len(steps) + 1)
        steps.append([sid, t, "完成「" + t + "」并产出对应产物"])
    return steps

def ensure_frontmatter(skill_dir, name):
    md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(md):
        print("[skill-converter] ERROR: 源目录没有 SKILL.md:", skill_dir)
        sys.exit(2)
    text = open(md, encoding="utf-8").read()
    has_name = re.search(r"^name:", text, re.M)
    has_desc = re.search(r"^description:", text, re.M)
    if not (has_name and has_desc):
        head = "---\n" if not text.startswith("---") else ""
        new_text = "---\nname: " + name + "\ndescription: 待补充: 该 skill 的用途说明\n---\n\n" + text
        open(md, "w", encoding="utf-8").write(new_text)
        print("[skill-converter] INFO: 已补写 frontmatter (name=" + name + ")")

def inject_intro(skill_dir):
    """若 SKILL.md 尚无 Step-Gate 前导，则从模板注入（含 to-do 镜像第 0 条）。"""
    md = os.path.join(skill_dir, "SKILL.md")
    text = open(md, encoding="utf-8").read()
    if "Step-Gate Workflow" in text:
        return
    intro = open(os.path.join(TPL, "STEPGATE_INTRO.md"), encoding="utf-8").read()
    if text.startswith("---"):
        idx = text.find("\n---", 3)
        pos = idx + 4 if idx != -1 else 0
    else:
        pos = 0
    new_text = text[:pos] + "\n" + intro + text[pos:]
    open(md, "w", encoding="utf-8").write(new_text)
    print("[skill-converter] INFO: 已注入 Step-Gate 前导 (STEPGATE_INTRO.md)")

def build(src_dir, name, steps, out_root):
    out = os.path.join(out_root, name)
    if os.path.abspath(out) == os.path.abspath(src_dir):
        print("[skill-converter] INFO: 就地改造模式（out==src），不复制源目录")
    else:
        if os.path.exists(out):
            shutil.rmtree(out)
        shutil.copytree(src_dir, out)
    inject_intro(out)
    # 写 flow.yaml（每步带 guide 字段）
    lines = ["skill: " + name, "version: 0.1.0", "steps:"]
    for i, (sid, title, desc) in enumerate(steps, 1):
        lines.append("  - id: " + sid)
        lines.append("    title: " + title)
        lines.append("    description: " + desc)
        lines.append("    guide: guides/" + sid + ".md")
        lines.append("    validators: []")
    open(os.path.join(out, "flow.yaml"), "w", encoding="utf-8").write("\n".join(lines))
    # guides 目录（每步一个必达内容草稿，含占位标记）
    gdir = os.path.join(out, "guides")
    os.makedirs(gdir, exist_ok=True)
    for sid, title, desc in steps:
        scaffold = ("# " + title + "\n\n" + PLACEHOLDER_MARKER + "\n\n"
                     "此步的必达内容（guide）尚未编写。请把本文件替换为当前步骤必须交付给 agent 的"
                     "完整说明（必达内容，非按需参考）。同时把 flow.yaml 对应步骤的 validators"
                     "数组填入 file/non-empty 机器校验规则。\n例：\n  - type: non-empty\n    path: notes/plan.md\n")
        open(os.path.join(gdir, sid + ".md"), "w", encoding="utf-8").write(scaffold)
    # scripts/run 启动器（来自模板）
    os.makedirs(os.path.join(out, "scripts"), exist_ok=True)
    for fn in ("run.cmd", "run.sh"):
        src = os.path.join(TPL, "scripts", fn)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(out, "scripts", fn))
    # bin 已发布平台
    bdir = os.path.join(out, "bin")
    os.makedirs(bdir, exist_ok=True)
    for plat in sorted(os.listdir(DIST_BIN)):
        srcp = os.path.join(DIST_BIN, plat)
        if os.path.isdir(srcp):
            shutil.copytree(srcp, os.path.join(bdir, plat), dirs_exist_ok=True)
    print("[skill-converter] OK:", out)
    print("[skill-converter] 下一步: 编辑 guides/<id>.md 替换占位标记，然后")
    print("[skill-converter]   python tools/skill-pack.py " + name + " --zip")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src_dir")
    ap.add_argument("name")
    ap.add_argument("--steps")
    ap.add_argument("--out", default=os.path.join(ROOT, "skills-src"))
    a = ap.parse_args()
    ensure_frontmatter(a.src_dir, a.name)
    if a.steps:
        steps = parse_steps_arg(a.steps)
    else:
        steps = extract_steps_from_md(open(os.path.join(a.src_dir, "SKILL.md"), encoding="utf-8").read())
        print("[skill-converter] INFO: 从 SKILL.md 标题提取 " + str(len(steps)) + " 个步骤")
    if not steps:
        print("[skill-converter] ERROR: 无法确定步骤，请用 --steps 提供")
        sys.exit(2)
    build(a.src_dir, a.name, steps, a.out)
