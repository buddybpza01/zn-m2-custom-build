# ZN-M2 Custom Firmware Build

定制 OpenWrt 固件，专为 兆能 ZN-M2 (IPQ6000 / 256MB) 旁路由分流设计。

## 特点
- ❌ 无 WiFi（ath11k 移除，省 60MB 内存）
- ❌ 无 USB、Docker、ZeroTier 等无用组件
- ✅ OpenClash + 全套依赖
- ✅ NSS 硬件加速
- ✅ 中文界面

## 编译
Actions 页面 → Build ZN-M2 Custom Firmware → Run workflow

## 刷机
1. 下载 Release 里的 *-factory.ubi
2. 进 U-Boot (192.168.1.1) 上传刷写
3. 默认地址 192.168.1.1，无密码

## 使用
刷完后在 OpenClash 界面自己添加订阅，不预置任何节点。
