# ZN-M2 旁路由固件（LibWrt 25.12-nss）

给 **兆能 ZN-M2**（高通 IPQ6000 / 256MB 内存 / 256MB NAND）编译的旁路由固件，
目标是跑 **OpenClash + mihomo 全局模式**，接美国住宅 IP，实现 iPhone 全量走美国、PC 分流。

## 为什么是 LibWrt 而不是 immortalwrt

| | VIKINGYFY/immortalwrt | **LiBwrt/LibWrt** |
|---|---|---|
| 内核 | 6.18.55 ❌ 实测刷进去不启动 | **6.12.116** ✅ 实测能启动 |
| zn_m2 支持 | 手加补丁 | **原生 `ipq6000-m2.dts`，`compatible = "zn,m2"`** |
| 内存 | — | 关 WiFi 后 ~157MB（还有优化空间） |

## 编译的 6 个变体

| 变体 | 源码 | 分支 | 特点 |
|---|---|---|---|
| libwrt | LiBwrt/LibWrt | 25.12-nss | 基线，与已验证固件同源 |
| libwrt-ram | LiBwrt/LibWrt | 25.12-nss | 关 WiFi + 缩 q6_region，抢回 ~20MB |
| lienol | Lienol/openwrt | 25.12 | 上游同源，交叉验证 |
| lienol-ram | Lienol/openwrt | 25.12 | 同上 + 内存优化 |
| upstream | laipeng668/openwrt-6.x | 25.12-nss | LibWrt 的上游 |
| minimal | LiBwrt/LibWrt | 25.12-nss | 极简，只 LuCI + OpenClash |

## 产物

- `*-squashfs-factory.ubi` — U-Boot 网页刷写用（`/img.html`）
- `*-initramfs-uImage.itb` — U-Boot 内存启动测试用（`/uimage.html`），不写 flash，最安全
- `*-squashfs-sysupgrade.bin` — 已经是 OpenWrt 时升级用

## 刷机

**先测 initramfs**（不写 flash，断电即恢复）：

1. 电脑网线直连 M2 的 LAN 口，电脑 IP 设静态 `192.168.1.10 / 255.255.255.0`
2. 浏览器开 `http://192.168.1.1` → `/uimage.html` → 上传 `.itb`
3. 等 2–3 分钟，`ping 192.168.1.1` 通了就是成功
4. 成功后断电重启，会自动回到 U-Boot

**确认能用再刷 factory.ubi**：

1. 同样进 `http://192.168.1.1` → `/img.html` → 上传 `.ubi`
2. 等 3–5 分钟
3. 5 分钟没起来就断电重插，M2 自动回落到 U-Boot，**不会变砖**

## 默认值

- LAN IP：`192.168.1.2`（旁路由）
- 主机名：`ZNM2`
- root 密码：无（首次登录请自己设）

## 怎么用

刷完按 `deploy-kit/` 目录里的文档操作：配旁路由 → 装 OpenClash → 全局模式 → iPhone/PC 设置。
