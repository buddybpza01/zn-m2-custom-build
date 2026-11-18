#!/bin/bash
set -e

echo "=== 配置软件源 ==="
sed -i 's/# src-git packages/src-git packages/' feeds.conf.default 2>/dev/null || true

echo "=== 更新 feeds ==="
./scripts/feeds update -a

echo "=== 安装 OpenClash 源 ==="
# 从 vernesong 仓库拉取 OpenClash
git clone --depth 1 -b master https://github.com/vernesong/OpenClash.git /tmp/openclash-src
mkdir -p package/luci-app-openclash
cp -r /tmp/openclash-src/luci-app-openclash/* package/luci-app-openclash/

echo "=== 安装 feeds ==="
./scripts/feeds install -a

echo "=== 应用自定义配置 ==="
cp ../configs/.config .config
make defconfig

echo "=== 检查关键包 ==="
grep -E 'CONFIG_PACKAGE_luci-app-openclash|CONFIG_PACKAGE_kmod-tun' .config || echo "警告：关键包未启用"

echo "=== 开始编译 ==="
make -j$(nproc) || make -j1 V=s

echo "=== 编译完成 ==="
ls -la bin/targets/qualcommax/ipq60xx/
