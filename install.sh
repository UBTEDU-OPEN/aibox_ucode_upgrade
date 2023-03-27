#!/bin/bash

PKT_NAME="ucode_upgrade"
cat <<-EOF
/*
 * Install $PKT_NAME
 */
EOF
CP_DST=
PKT_SUB_NAME="ucode"
PKT_DIR="/usr/local/lib/"
ROOT_PATH=$(cd "$(dirname "$0")";pwd)
UCODE_CONF_DIR="/home/oneai/.config/uCode_upgrade"
pushd $ROOT_PATH &> /dev/null


echo "1.Clean up"
rm -rf build dist


echo "2.Installing $PKT_NAME"

python3 setup.py install
if [ $? -ne 0 ]; then
    echo "fail to install"
    exit 1
fi

echo "3.Copying configuration file"
#模糊查找 ucode_upgrade*
for item in `find $PKT_DIR -name "$PKT_NAME*" -type d`
do  
    #判断目录下有无ucode
    for file in `ls $item`
    do
        if [ $file == "ucode" ]; then
            CP_DST=$item"/"
            break
        fi
    done
done
if [ ! $CP_DST ]; then
    echo "fail to install"
    exit 1
fi
#配置
if [ ! -d ${UCODE_CONF_DIR} ];then
    mkdir -p -m=755 $UCODE_CONF_DIR
fi
cp -rfp ucode/config/locale $UCODE_CONF_DIR

cp -r aibox.xml $CP_DST

popd &> /dev/null

echo "Finished install"