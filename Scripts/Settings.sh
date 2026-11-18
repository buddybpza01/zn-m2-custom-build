#!/bin/bash

#移除luci-app-attendedsysupgrade
sed -i "/attendedsysupgrade/d" $(find ./feeds/luci/collections/ -type f -name "Makefile") 2>/dev/null || true
#修改默认IP
CFG_FILE="./package/base-files/files/bin/config_generate"
sed -i "s/192\.168\.[0-9]*\.[0-9]*/$WRT_IP/g" $CFG_FILE 2>/dev/null || true
#修改主机名
sed -i "s/hostname='.*'/hostname='$WRT_NAME'/g" $CFG_FILE 2>/dev/null || true
#添加编译日期标识
sed -i "s/(\(luciversion || ''\))/(\1) + (' \/ $WRT_MARK-$WRT_DATE')/g" $(find ./feeds/luci/modules/luci-mod-status/ -type f -name "10_system.js") 2>/dev/null || true

#基础配置
echo "CONFIG_PACKAGE_luci=y" >> ./.config
echo "CONFIG_LUCI_LANG_zh_Hans=y" >> ./.config

#手动调整的插件
if [ -n "$WRT_PACKAGE" ]; then
	echo -e "$WRT_PACKAGE" >> ./.config
fi

# 注意：不加任何 NSS 相关配置！
# VIKINGYFY/immortalwrt 的 qualcommax 加速走 in-tree 内核补丁，无需额外包。
