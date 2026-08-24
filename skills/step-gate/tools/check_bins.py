import struct, os, glob
BASE = r"E:/github/skill steps/dist/bin"
def check(p):
    d = open(p, "rb").read(4096)
    if d[:2] == b"MZ":
        off = struct.unpack_from("<I", d, 0x3C)[0]
        d2 = open(p, "rb").read(off + 64)
        m = struct.unpack_from("<H", d2, off + 4)[0]
        arch = {0x8664: "x64", 0xAA64: "arm64", 0x14C: "x86"}.get(m, hex(m))
        return f"PE {arch} {os.path.getsize(p)} bytes"
    if d[:4] == b"\x7fELF":
        machine = struct.unpack_from("<H", d, 18)[0]
        arch = {62: "x86-64", 183: "aarch64"}.get(machine, hex(machine))
        return f"ELF {arch} {os.path.getsize(p)} bytes"
    if d[:4] in (b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xce"):
        cputype = struct.unpack_from("<I", d, 4)[0] & 0x7FFFFFFF
        arch = {7: "x86-64", 12: "arm64"}.get(cputype, hex(cputype))
        return f"Mach-O {arch} {os.path.getsize(p)} bytes"
    return "unknown"
for root, dirs, files in os.walk(BASE):
    for f in sorted(files):
        p = os.path.join(root, f)
        print(os.path.relpath(p, BASE), "->", check(p))
