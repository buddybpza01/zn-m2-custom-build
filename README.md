# ZN-M2 定制固件（无 WiFi + OpenClash）

专为 **兆能 ZN-M2 / CMIOT AX18 (IPQ6000, 256MB)** 旁路由分流设计。

## 核心特点

| 项目 | 状态 |
|---|---|
| WiFi (ath11k) | ❌ **已移除**（释放约 60MB 内存） |
| OpenClash | ✅ 已内置 + 全套依赖 |
| NSS 硬件加速 | ✅ 已启用（高通 IPQ6000） |
| 中文界面 | ✅ |
| Docker / ZeroTier / DDNS / udpxy / Samba | ❌ 全部移除 |
| 预置订阅/节点 | ❌ 无，刷完自己加 |

## 编译

Actions → Build ZN-M2 Custom → Run workflow

约 40-60 分钟。

## 刷机

1. 下载 Release 中的 `*factory.ubi`
2. 进 U-Boot（192.168.1.1）上传刷写
3. 刷完访问 `192.168.1.1`，无密码

## 使用

刷完后进 LuCI → 服务 → OpenClash → 版本更新 → 下载 Meta 内核（arm64）→ 配置订阅。

不预置任何节点，完全由你自己管理。
