#! /bin/bash

# File: find_lost_photos.sh
# Desc: 查找缺少的照片,原因是从数码相机复制照片时，
# 有几张没有复制上来，这个程序的目的就是要找出哪几张
# 照片没有复制到电脑上。 
# Theory: 相机上的照片都是按顺序编号的，缺少的编号就
# 是没有复制的照片

i=1
END=532

while [ $i -le $END ]
do
    file=`echo $i |awk '{printf("0832 %03d",$0)}'`
    if [ ! -e "$file.MOV" ] && [ ! -e "$file.jpg" ] 
    then
	echo "The file [${file}] is lost!"
    fi 
    i=`expr $i + 1 `
done

echo "OK"
