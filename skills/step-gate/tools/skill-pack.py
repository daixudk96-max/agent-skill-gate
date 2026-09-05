#!/usr/bin/env python3
"""skill-pack: 母包 skills-src/<skill>/ -> dist/<skill>-<agent>/ 多 agent 分发包

用法:
  python tools/skill-pack.py <skill> [--agents a,b,...] [--zip] [--out dist]

严格校验（AC13）: 任一失败 -> exit 2，不产出任何 agent 目录/zip。
  - frontmatter name == 父目录名 且 description 存在（ERROR，非 WARN）
  - flow.yaml 可解析、step id 唯一、description 非空
  - 每步 guide 存在、非空、无占位标记、<=64 KiB、路径安全（不逃逸 skill 根）
  - 每步 >=1 个 validator，type 仅 file/non-empty，path 非空
  - 未知 validator type -> ERROR

每个包内含: SKILL.md + flow.yaml + guides/ + validators/ + assets/ + scripts/run(.cmd|.sh)
          + bin/<platform>/step-gate(所有已发布平台) + INSTALL.md
"""
import argparse, os, re, shutil, sys, zipfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "skills-src")
DIST_BIN = os.path.join(ROOT, "dist", "bin")

AGENTS = [
    ("universal",   ".agents/skills/<name>/          (Cursor/OpenCode/Gemini 原生读取)"),
    ("claude-code", ".claude/skills/<name>/          (项目或全局 ~/.claude/skills)"),
    ("codex",       ".agents/skills/<name>/          (全局 ~/.codex/skills)"),
    ("cursor",      ".agents/skills/<name>/          (全局 ~/.cursor/skills)"),
    ("opencode",    "xdg-config/opencode/skills/<name>/"),
    ("gemini-cli",  "~/.gemini/skills/<name>/"),
]

PLACEHOLDER_MARKER = "TODO: REQUIRED-GUIDE"
VALID_TYPES = ("file", "non-empty", "contains", "heading")

def _err(msg):
    print("[skill-pack] ERROR: " + msg)
    sys.exit(2)

def _warn(msg):
    print("[skill-pack] WARN: " + msg)

def _is_abs(p):
    """跨平台绝对路径检测：os.path.isabs OR 盘符正则 OR UNC 前缀。"""
    if os.path.isabs(p):
        return True
    if re.match(r"^[A-Za-z]:[\\/]", p):
        return True
    if p.startswith("\\\\") or p.startswith("//"):
        return True
    return False

def _resolve_contained(root, rel):
    """解析 rel 并确认其规范路径位于 root 内（组件级，非字符串前缀）。
    返回 (ok, reason)。"""
    if not rel or rel.strip() != rel:
        return False, "guide 路径为空或含首尾空白"
    if _is_abs(rel):
        return False, "guide 路径必须是相对路径: " + rel
    parts = rel.replace("\\", "/").split("/")
    if any(p == ".." for p in parts):
        return False, "guide 路径不得包含 ..: " + rel
    if any(p == "" for p in parts):
        return False, "guide 路径含空组件: " + rel
    cand = os.path.normpath(os.path.join(root, rel))
    rootn = os.path.normpath(root)
    try:
        candr = os.path.realpath(cand)
        rootr = os.path.realpath(rootn)
    except OSError as e:
        return False, "无法解析 guide 路径: " + str(e)
    if not os.path.isfile(candr):
        return False, "guide 不是常规文件: " + rel
    if not os.path.commonpath([candr, rootr]) == rootr:
        return False, "guide 逃逸 skill 根目录: " + rel
    return True, ""

def check_frontmatter(skill_dir):
    md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(md):
        _err("SKILL.md missing: " + md)
    text = open(md, encoding="utf-8").read(4000)
    m = re.search(r"^name:\s*(.+)$", text, re.M)
    name = m.group(1).strip().strip("\"\'").rstrip("\r") if m else ""
    base = os.path.basename(os.path.normpath(skill_dir))
    if name != base:
        _err("frontmatter name %r != 父目录名 %r (Universal 要求相等)" % (name, base))
    if not re.search(r"^description:\s*(.+)$", text, re.M):
        _err("SKILL.md 缺 description frontmatter")
    return base

def validate_flow(skill_dir):
    """校验 flow.yaml + guides + validators。返回 (skill_name, step_ids)。"""
    fp = os.path.join(skill_dir, "flow.yaml")
    if not os.path.exists(fp):
        _err("flow.yaml missing: " + fp)
    try:
        import yaml
    except ImportError:
        _err("需要 PyYAML（pip install pyyaml）")
    try:
        with open(fp, encoding="utf-8") as f:
            flow = yaml.safe_load(f)
    except Exception as e:
        _err("flow.yaml 解析失败: " + str(e))
    if not isinstance(flow, dict) or not flow.get("skill") or not flow.get("version"):
        _err("flow.yaml 缺 skill/version")
    steps = flow.get("steps") or []
    if not isinstance(steps, list) or not steps:
        _err("flow.yaml 至少需要一个 step")
    ids = []
    for i, st in enumerate(steps):
        if not isinstance(st, dict):
            _err("step %d 不是对象" % i)
        sid = st.get("id")
        if not sid or not isinstance(sid, str):
            _err("step %d 缺 id" % i)
        if sid in ids:
            _err("step id 重复: " + sid)
        ids.append(sid)
        desc = st.get("description")
        if not desc or not str(desc).strip():
            _err("step %s 缺非空 description" % sid)
        guide = st.get("guide")
        if not guide or not isinstance(guide, str):
            _err("step %s 缺 guide（旧包需迁移）" % sid)
        ok, reason = _resolve_contained(skill_dir, guide)
        if not ok:
            _err("step %s guide 校验失败: %s" % (sid, reason))
        gpath = os.path.join(skill_dir, guide)
        gsize = os.path.getsize(gpath)
        if gsize == 0:
            _err("step %s guide 为空: %s" % (sid, guide))
        if gsize > 64 * 1024:
            _err("step %s guide 超过 64 KiB: %s" % (sid, guide))
        gtext = open(gpath, encoding="utf-8").read()
        if PLACEHOLDER_MARKER in gtext:
            _err("step %s guide 含占位标记 %s（未编写必达内容）" % (sid, PLACEHOLDER_MARKER))
        if gtext.count("\n") > 100:
            _warn("step %s guide 超过 100 行（建议精简）" % sid)
        v = st.get("validators")
        if not isinstance(v, list) or not v:
            _err("step %s 至少需要一个 validator" % sid)
        for vv in v:
            if not isinstance(vv, dict):
                _err("step %s validator 不是对象" % sid)
            vt = vv.get("type")
            if vt not in VALID_TYPES:
                _err("step %s 未知 validator type: %r（仅 file/non-empty/contains/heading）" % (sid, vt))
            vp = vv.get("path")
            if not vp or not isinstance(vp, str) or not vp.strip():
                _err("step %s validator path 非空" % sid)
            if vt in ("contains", "heading"):
                pat = vv.get("pattern")
                if not pat or not isinstance(pat, str) or not pat.strip():
                    _err("step %s validator pattern 非空（type=%s）" % (sid, vt))
                if vt == "heading" and vv.get("level") is not None:
                    lv = vv.get("level")
                    if not isinstance(lv, int) or lv < 1 or lv > 6:
                        _err("step %s heading level 须为 1..=6" % sid)
    return flow.get("skill"), ids

def build(skill, agents, make_zip, out_root):
    skill_dir = os.path.join(SRC, skill)
    if not os.path.isdir(skill_dir):
        _err("母包不存在: " + skill_dir)
    name = check_frontmatter(skill_dir)
    validate_flow(skill_dir)
    os.makedirs(out_root, exist_ok=True)
    for agent in agents:
        loc = None
        for k, v in AGENTS:
            if k == agent:
                loc = v
                break
        if loc is None:
            print("[skill-pack] WARN: 未知 agent %r，跳过" % agent)
            continue
        out = os.path.join(out_root, name + "-" + agent)
        if os.path.exists(out):
            shutil.rmtree(out)
        shutil.copytree(skill_dir, out, ignore=shutil.ignore_patterns(".step-gate", "__pycache__"))
        bdir = os.path.join(out, "bin")
        if os.path.isdir(bdir):
            for plat in os.listdir(bdir):
                if not os.path.isdir(os.path.join(DIST_BIN, plat)):
                    shutil.rmtree(os.path.join(bdir, plat))
            for plat in sorted(os.listdir(DIST_BIN)):
                srcp = os.path.join(DIST_BIN, plat)
                dstp = os.path.join(bdir, plat)
                if os.path.isdir(srcp):
                    if os.path.exists(dstp):
                        shutil.rmtree(dstp)
                    shutil.copytree(srcp, dstp)
        inst_lines = [
            "# %s 安装说明（%s）" % (name, agent),
            "",
            "把本目录整体复制到: " + loc,
            "",
            "包内已含全部已实现平台 step-gate 二进制，无需任何运行时安装。",
            "使用: 在 skill 目录内执行 scripts/run(.cmd|.sh) status 查看当前步，",
            "      scripts/run next 取下一步（自动交付当前步必达 guide），",
            "      scripts/run complete 校验产物并推进。",
            "",
        ]
        with open(os.path.join(out, "INSTALL.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(inst_lines))
        if make_zip:
            zp = out + ".zip"
            if os.path.exists(zp):
                os.remove(zp)
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
                for root, dirs, files in os.walk(out):
                    for fn in files:
                        fp = os.path.join(root, fn)
                        z.write(fp, os.path.relpath(fp, os.path.dirname(out)))
        print("[skill-pack] OK:", out, (" (zip)" if make_zip else ""))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("skill")
    ap.add_argument("--agents", default="universal,claude-code,codex,cursor,opencode,gemini-cli")
    ap.add_argument("--zip", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"))
    a = ap.parse_args()
    build(a.skill, [x.strip() for x in a.agents.split(",") if x.strip()], a.zip, a.out)
