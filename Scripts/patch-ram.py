#!/usr/bin/env python3
"""ZN-M2 内存优化补丁（可审计、不静默失败）。

做两件事：
1. 把 q6_region 从 55MB 缩到 32MB（只改 ipq6018-512m.dtsi）。
2. 在“实际被编译的” zn_m2 DTS 末尾禁用 wifi 与 Q6/WCSS 节点。

关键点：
- 不同源码树 DTS 文件名不同（LibWrt: ipq6000-m2.dts；Lienol: ipq6000-zn-m2.dts）。
- 禁用节点必须用该树真实存在的 label 或真实节点路径，否则 dtc 会编译失败。
- 找不到任何可用写法就退出 1，不允许“看起来打了补丁其实没生效”。
"""
import os
import re
import sys

BASE = "target/linux/qualcommax/files/arch/arm64/boot/dts/qcom"
Q6_DTSI = os.path.join(BASE, "ipq6018-512m.dtsi")
Q6_OLD = "reg = <0x0 0x4ab00000 0x0 0x3700000>;"
Q6_NEW = "reg = <0x0 0x4ab00000 0x0 0x2000000>;"


def pick_m2_dts():
    for name in ("ipq6000-m2.dts", "ipq6000-zn-m2.dts"):
        p = os.path.join(BASE, name)
        if os.path.exists(p):
            return p
    for root, _d, files in os.walk(BASE):
        for fn in files:
            if not fn.endswith(".dts"):
                continue
            fp = os.path.join(root, fn)
            t = open(fp, encoding="utf-8", errors="replace").read()
            if '"zn,m2"' in t:
                return fp
    return None


def collect_tree_text():
    """把 dts 目录下所有源文件拼起来，用于找 label / 节点路径。"""
    buf = []
    for root, _d, files in os.walk(BASE):
        for fn in files:
            if fn.endswith((".dts", ".dtsi")):
                fp = os.path.join(root, fn)
                try:
                    buf.append(open(fp, encoding="utf-8", errors="replace").read())
                except OSError:
                    pass
    return "\n".join(buf)


def find_wifi_ref(tree):
    """返回可用于覆盖 wifi 节点的 DTS 引用。"""
    if re.search(r"\bwifi:\s*wifi@", tree):
        return "label", "&wifi"
    m = re.search(r"(\w[\w\-]*)@([0-9a-fA-F]+)\s*\{\s*compatible\s*=\s*\"qcom,ipq6018-wifi\"", tree)
    if m:
        node = "%s@%s" % (m.group(1), m.group(2))
        # 找父节点路径：优先 /soc@0，其次 /soc
        for parent in ("/soc@0", "/soc"):
            if re.search(r"%s\s*\{\s*" % re.escape(parent), tree):
                return "path", "&{%s/%s}" % (parent, node)
        return "path", "&{/%s}" % node
    return None, None


def find_q6_ref(tree):
    if re.search(r"\bq6v5_wcss:\s*", tree):
        return "label", "&q6v5_wcss"
    m = re.search(r"(\w[\w\-]*)@(cd00000)\s*\{\s*compatible\s*=\s*\"qcom,ipq6018-wcss-pil\"", tree)
    if m:
        node = "%s@%s" % (m.group(1), m.group(2))
        for parent in ("/soc@0", "/soc"):
            if re.search(r"%s\s*\{\s*" % re.escape(parent), tree):
                return "path", "&{%s/%s}" % (parent, node)
        return "path", "&{/%s}" % node
    return None, None


def main():
    if not os.path.isdir(BASE):
        print("DTS dir missing: " + BASE)
        return 1

    # --- 1) q6_region ---
    if not os.path.exists(Q6_DTSI):
        print("q6 dtsi missing: " + Q6_DTSI)
        return 1
    q6 = open(Q6_DTSI, encoding="utf-8").read()
    if Q6_OLD in q6:
        q6 = q6.replace(Q6_OLD, Q6_NEW)
        open(Q6_DTSI, "w", encoding="utf-8").write(q6)
        print("q6_region: 55MB -> 32MB (applied)")
    elif Q6_NEW in q6:
        print("q6_region already 32MB")
    else:
        print("ERROR: q6_region original value not found; refusing to guess")
        print(q6)
        return 1

    # --- 2) wifi / q6v5_wcss ---
    dts = pick_m2_dts()
    if not dts:
        print("ERROR: ZN-M2 DTS not found")
        return 1
    print("Target M2 DTS: " + dts)

    tree = collect_tree_text()
    wifi_kind, wifi_ref = find_wifi_ref(tree)
    q6_kind, q6_ref = find_q6_ref(tree)
    print("wifi ref: %s (%s)" % (wifi_ref, wifi_kind))
    print("q6  ref: %s (%s)" % (q6_ref, q6_kind))

    if not wifi_ref or not q6_ref:
        print("ERROR: cannot build valid override refs; abort (no silent no-op)")
        return 1

    txt = open(dts, encoding="utf-8").read()
    if "ipq_m2_disable_wifi" in txt:
        print("disable block already present")
    else:
        block = (
            "\n/* ipq_m2_disable_wifi: 旁路由不使用 WiFi，同时释放 Q6/WCSS 依赖 */\n"
            "%s {\n\tstatus = \"disabled\";\n};\n\n"
            "%s {\n\tstatus = \"disabled\";\n};\n" % (wifi_ref, q6_ref)
        )
        open(dts, "a", encoding="utf-8").write(block)
        print("Appended disable block to M2 DTS")

    # --- 3) 回读校验 ---
    check = open(dts, encoding="utf-8").read()
    if "ipq_m2_disable_wifi" not in check or "disabled" not in check:
        print("ERROR: post-write verification failed")
        return 1
    print("Post-write check OK")
    for line in check.splitlines()[-12:]:
        print("  " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
