#!/usr/bin/env python3
# 往 DTS 的 chosen/bootargs-append 里注入内核日志参数
#
# ★★★ 致命教训 ★★★
# ipq6000-cmiot.dtsi 里已有:  bootargs-append = " root=/dev/ubiblock0_1";
# 它是 ipq6000-m2.dts 的 #include 父文件。
# DTS 规则：子文件里同名属性会【完全覆盖】父文件的，不是追加！
# 所以我在 ipq6000-m2.dts 里写 bootargs-append 时，
# 必须把 " root=/dev/ubiblock0_1" 一起带上，
# 否则内核不知道根文件系统在哪 → 永远起不来。
import os
import re
import sys

NETCONSOLE_TARGET_IP = "192.168.1.10"
NETCONSOLE_TARGET_PORT = "6666"
LOCAL_IP = "192.168.1.2"
LOCAL_PORT = "6666"
LOCAL_IFACE = "eth0"

# root= 必须放在最前面，且必须保留！
ROOT_ARG = " root=/dev/ubiblock0_1"

EXTRA = (
    " loglevel=8 ignore_loglevel panic=10 printk.time=1"
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
    """找要改的 DTS：优先 ipq6000-m2.dts"""
    p = os.path.join(base, "ipq6000-m2.dts")
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
            if "zn,m2" in t:
                return fp
    return None


def main():
    base = "target/linux/qualcommax/files/arch/arm64/boot/dts/qcom"
    if not os.path.isdir(base):
        print("!!! DTS 目录不存在: %s" % base)
        return 1

    target = find_dts(base)
    if not target:
        print("!!! 找不到 zn_m2 的 DTS")
        return 1
    print("=== 目标 DTS: %s ===" % target)

    txt = open(target, encoding="utf-8").read()

    # 完整的 bootargs-append 值：root= 必须在内
    FULL = ROOT_ARG + EXTRA

    if "netconsole=" in txt:
        print("已包含 netconsole，跳过")
        return 0

    # 如果子 DTS 里已有 bootargs-append，替换成完整版
    m = re.search(r'bootargs-append\s*=\s*"([^"]*)"\s*;', txt)
    if m:
        old = m.group(1)
        print("原有 bootargs-append = \"%s\"" % old)
        # 保留原有的 root= 部分，再拼上我们的
        if "root=" in old:
            # 已有 root=，直接追加日志参数（不用再加 ROOT_ARG）
            new_val = old + EXTRA
        else:
            new_val = ROOT_ARG + old + EXTRA
        txt = txt[: m.start()] + 'bootargs-append = "%s";' % new_val + txt[m.end():]
        print("已替换为: %s" % new_val)
    else:
        # 没有就新建，必须带上 ROOT_ARG
        if re.search(r"chosen\s*\{", txt):
            def add(mo):
                return mo.group(0) + '\n\t\tbootargs-append = "%s";' % FULL

            txt, n = re.subn(r"chosen\s*\{", add, txt, count=1)
            print("已在 chosen 内新建 bootargs-append (n=%d)" % n)
        else:
            txt = txt.rstrip() + (
                '\n\n/ {\n\tchosen {\n\t\tbootargs-append = "%s";\n\t};\n};\n' % FULL
            )
            print("已新建 chosen 节点")
        print("写入值: %s" % FULL)

    open(target, "w", encoding="utf-8").write(txt)
    print("=== 写入完成 ===")

    # 校验：root= 必须在
    out = open(target, encoding="utf-8").read()
    ok = False
    for line in out.split("\n"):
        if "bootargs-append" in line:
            print("   最终: %s" % line.strip())
            if "root=/dev/ubiblock" in line:
                ok = True
    if not ok:
        print("!!! 危险：bootargs 里没有 root=，内核将找不到根文件系统 !!!")
        return 1
    print("OK: root= 已保留")
    return 0


if __name__ == "__main__":
    sys.exit(main())
