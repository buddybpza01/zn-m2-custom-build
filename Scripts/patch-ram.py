#!/usr/bin/env python3
"""ZN-M2 内存优化补丁（按源码树真实情况选择目标，不静默失效）。

已证实的差异（2026-11-19 抓源码核实）：
- LibWrt 25.12-nss：q6_region 在 ipq6018-512m.dtsi，值 0x3700000(55MB)，M2 dts = ipq6000-m2.dts
- Lienol 25.12   ：q6_region 在 ipq6018-256m.dtsi，值 0x2800000(40MB)，M2 dts = ipq6000-zn-m2.dts
  （Lienol 的 cmiot.dtsi include 的是 ipq6018-256m.dtsi，512m.dtsi 根本不参与编译，
   所以上一轮改 512m 完全无效 —— 这是 run#36 之前一直没生效的原因之一）

wifi / q6v5_wcss 节点定义在内核源码 arch/arm64/boot/dts/qcom/ipq6018.dtsi 里，
不在 target 覆盖目录，因此不能用 label 探测；改用节点绝对路径覆盖。

另外：Lienol 的 M2 dts 里有 `&wifi { qcom,ath11k-calibration-variant = "ZN-M2"; };`，
必须保留这段，只在末尾追加 status="disabled"。
"""
import os
import re
import sys

BASE = "target/linux/qualcommax/files/arch/arm64/boot/dts/qcom"

Q6_CANDIDATES = [
    ("ipq6018-256m.dtsi", "reg = <0x0 0x4ab00000 0x0 0x2800000>;",
     "reg = <0x0 0x4ab00000 0x0 0x2000000>;", "40MB -> 32MB (Lienol)"),
    ("ipq6018-512m.dtsi", "reg = <0x0 0x4ab00000 0x0 0x3700000>;",
     "reg = <0x0 0x4ab00000 0x0 0x2000000>;", "55MB -> 32MB (LibWrt)"),
]

M2_DTS_NAMES = ("ipq6000-zn-m2.dts", "ipq6000-m2.dts")

MARKER = "ipq_m2_disable_wifi"

DISABLE_BLOCK = (
    "\n/* %s: 旁路由不用 WiFi，同时关闭 Q6/WCSS 远程处理器 */\n"
    "&{/soc@0/wifi@c000000} {\n"
    "\tstatus = \"disabled\";\n"
    "};\n\n"
    "&{/soc@0/remoteproc@cd00000} {\n"
    "\tstatus = \"disabled\";\n"
    "};\n" % MARKER
)


def pick_m2_dts():
    for name in M2_DTS_NAMES:
        p = os.path.join(BASE, name)
        if os.path.exists(p):
            return p
    return None


def patch_q6():
    seen = 0
    done = 0
    for fn, old, new, desc in Q6_CANDIDATES:
        p = os.path.join(BASE, fn)
        if not os.path.exists(p):
            print("[q6] %s: not present" % fn)
            continue
        seen += 1
        txt = open(p, encoding="utf-8").read()
        if new in txt:
            print("[q6] %s: already 32MB" % fn)
            done += 1
            continue
        if old in txt:
            open(p, "w", encoding="utf-8").write(txt.replace(old, new))
            print("[q6] %s: %s" % (fn, desc))
            done += 1
        else:
            print("[q6] %s: pattern not found (value differs), skipped" % fn)
    if seen == 0:
        print("ERROR: neither memory dtsi exists")
        return False
    if done == 0:
        print("ERROR: no q6_region patch applied")
        return False
    return True


def main():
    if not os.path.isdir(BASE):
        print("DTS dir missing: " + BASE)
        return 1

    dts = pick_m2_dts()
    if not dts:
        print("ERROR: ZN-M2 dts not found (tried %s)" % ", ".join(M2_DTS_NAMES))
        return 1
    print("Target M2 DTS: " + dts)

    txt = open(dts, encoding="utf-8").read()
    inc = re.findall(r'#include\s+"([^"]+)"', txt)
    print("Includes: " + ", ".join(inc))

    if not patch_q6():
        return 1

    txt = open(dts, encoding="utf-8").read()
    if MARKER in txt:
        print("Disable block already present")
    else:
        open(dts, "a", encoding="utf-8").write(DISABLE_BLOCK)
        print("Appended disable block via absolute node paths")

    check = open(dts, encoding="utf-8").read()
    if MARKER not in check:
        print("ERROR: marker missing after write")
        return 1
    if check.count('status = "disabled"') < 2:
        print("ERROR: expected >=2 disabled entries")
        return 1
    if "ath11k-calibration-variant" in txt and "ath11k-calibration-variant" not in check:
        print("ERROR: original calibration variant got lost")
        return 1
    print("Post-write check OK")
    for line in check.splitlines()[-11:]:
        print("  " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
