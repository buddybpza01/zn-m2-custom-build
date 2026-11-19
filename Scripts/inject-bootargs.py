#!/usr/bin/env python3
"""为 ZN-M2 注入可审计的启动日志参数。

重要边界：
- bootargs-append 是 OpenWrt 镜像构建使用的参数，不应假定它等价于内核最终 cmdline。
- 保留已有 root= 和 stdout-path；不覆盖原值。
- 只追加 loglevel/ignore_loglevel/panic=10/printk.time。
- netconsole 不在此注入：若内核编译为模块，早期启动时不会仅因该参数自动可用；
  必须另行提供模块与初始化，否则不要伪装成已生效。
"""
import os
import re
import sys

EXTRA = " loglevel=8 ignore_loglevel panic=10 printk.time=1"


def find_dts(base):
    preferred = [
        os.path.join(base, "ipq6000-m2.dts"),       # LibWrt
        os.path.join(base, "ipq6000-zn-m2.dts"),    # Lienol
    ]
    for p in preferred:
        if os.path.exists(p):
            return p
    for root, _dirs, files in os.walk(base):
        for fn in files:
            if not fn.endswith(".dts"):
                continue
            fp = os.path.join(root, fn)
            try:
                t = open(fp, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            if '"zn,m2"' in t:
                return fp
    return None


def merge_args(old):
    # 原参数全部保留，不额外补 root=，防止掩盖原 DTS 缺失 root= 的问题。
    result = old.rstrip()
    for arg in EXTRA.strip().split():
        if arg not in result.split():
            result += " " + arg
    return result


def main():
    base = "target/linux/qualcommax/files/arch/arm64/boot/dts/qcom"
    if not os.path.isdir(base):
        print("DTS directory missing: " + base)
        return 1

    target = find_dts(base)
    if not target:
        print("ZN-M2 DTS not found")
        return 1
    print("Target DTS: " + target)
    txt = open(target, encoding="utf-8").read()

    if "ignore_loglevel" in txt and "panic=10" in txt:
        print("Logging args already present; skip")
        return 0

    m = re.search(r'bootargs-append\s*=\s*"([^"]*)"\s*;', txt)
    if m:
        old = m.group(1)
        new_val = merge_args(old)
        txt = txt[:m.start()] + 'bootargs-append = "%s";' % new_val + txt[m.end():]
        print("Merged into existing bootargs-append")
        if "root=" not in old:
            print("ERROR: original DTS bootargs-append has no root=; not fabricating one")
            return 1
    else:
        # 当前 zn_m2 DTS 不在自身定义 root=；它由父 DTSI 提供。
        # 只在 chosen 中添加纯日志参数，不写 bootargs-append，避免覆盖语义不清。
        logargs = EXTRA.strip()
        chosen = re.search(r"chosen\s*\{", txt)
        if chosen:
            txt = txt[:chosen.end()] + '\n\t\tbootargs = "%s";' % logargs + txt[chosen.end():]
            print("Added logging args to existing chosen/bootargs")
        else:
            txt = txt.rstrip() + '\n\n/ {\n\tchosen {\n\t\tbootargs = "%s";\n\t};\n};\n' % logargs
            print("Created chosen/bootargs with logging args only")

    open(target, "w", encoding="utf-8").write(txt)
    out = open(target, encoding="utf-8").read()
    for line in out.splitlines():
        if "bootargs" in line:
            print("Final: " + line.strip())
    print("No netconsole claim injected; module setup is separate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
