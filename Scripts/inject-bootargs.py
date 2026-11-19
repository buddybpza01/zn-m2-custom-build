#!/usr/bin/env python3
# 往 DTS 的 chosen/bootargs-append 里注入内核日志参数
# 用途：M2 一启动就能把内核日志通过 netconsole 发到电脑，panic 也有记录
import os
import re
import sys

NETCONSOLE_TARGET_IP = "192.168.1.10"
NETCONSOLE_TARGET_PORT = "6666"
LOCAL_IP = "192.168.1.2"
LOCAL_PORT = "6666"
LOCAL_IFACE = "eth0"

EXTRA = (
    " loglevel=8 ignore_loglevel panic=10 oops=panic printk.time=1"
    " netconsole=%s@%s/ff:ff:ff:ff:ff:ff,%s@%s/%s"
    % (
        NETCONSOLE_TARGET_PORT,
        NETCONSOLE_TARGET_IP,
        LOCAL_PORT,
        LOCAL_IP,
        LOCAL_IFACE,
    )
)


def find_dts(base):
    """找要改的 DTS 文件：优先 ipq6000-m2.dts，其次包含 cmiot 的 dtsi"""
    cands = [
        os.path.join(base, "ipq6000-m2.dts"),
    ]
    for c in cands:
        if os.path.exists(c):
            return c
    # 退而求其次：任何包含 zn,m2 compatible 的文件
    for root, _dirs, files in os.walk(base):
        for fn in files:
            if not fn.endswith((".dts", ".dtsi")):
                continue
            p = os.path.join(root, fn)
            try:
                t = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            if "zn,m2" in t:
                return p
    return None


def main():
    base = "target/linux/qualcommax/files/arch/arm64/boot/dts/qcom"
    if not os.path.isdir(base):
        print("!!! DTS 目录不存在: %s" % base)
        return 1

    # 列出可改的候选
    print("=== DTS 目录里的 zn_m2 相关文件 ===")
    for fn in sorted(os.listdir(base)):
        if "m2" in fn.lower() or "cmiot" in fn.lower():
            print("   " + fn)

    target = find_dts(base)
    if not target:
        print("!!! 找不到 zn_m2 的 DTS")
        return 1
    print("=== 目标 DTS: %s ===" % target)

    txt = open(target, encoding="utf-8").read()

    if "loglevel=8" in txt:
        print("已包含 loglevel，跳过（避免重复注入）")
        return 0

    # 情况 A：已有 bootargs-append
    m = re.search(r'bootargs-append\s*=\s*"([^"]*)"\s*;', txt)
    if m:
        old = m.group(1)
        new_val = old + EXTRA
        txt = txt[: m.start()] + 'bootargs-append = "%s";' % new_val + txt[m.end():]
        print("已追加到已有 bootargs-append")
    else:
        # 情况 B：有 chosen 节点但没有 bootargs-append
        if re.search(r"chosen\s*\{", txt):
            def add(mo):
                return mo.group(0) + '\n\t\tbootargs-append = "%s";' % EXTRA.strip()

            txt, n = re.subn(r"chosen\s*\{", add, txt, count=1)
            print("已在 chosen 节点内新建 bootargs-append (替换 %d 处)" % n)
        else:
            # 情况 C：完全没有 chosen，新建一个
            txt = txt.rstrip() + (
                '\n\n/ {\n\tchosen {\n\t\tbootargs-append = "%s";\n\t};\n};\n'
                % EXTRA.strip()
            )
            print("已新建 chosen 节点并写入 bootargs-append")

    open(target, "w", encoding="utf-8").write(txt)
    print("=== 写入完成 ===")

    # 回读确认
    out = open(target, encoding="utf-8").read()
    for line in out.split("\n"):
        if "bootargs" in line or "netconsole" in line or "loglevel" in line:
            print("   " + line.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
