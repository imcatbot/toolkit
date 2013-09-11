#! /bin/bash

# File: pseudo-hadoop.sh
# Desc: 设置hadoopa伪分布环境

HADOOP_DIR=$1

echo "设置hadoopa伪分布环境"
echo "Hadoop路径:[${HADOOP_DIR}]"

cp -a conf/ ${HADOOP_DIR}/

echo "设置ssh"
ssh-keygen -t dsa -P '' -f ~/.ssh/id_dsa 
cat ~/.ssh/id_dsa.pub >> ~/.ssh/authorized_keys

echo "格式化Hadoop"
export JAVA_HOME=/usr/lib/jvm/default-java
cd ${HADOOP_DIR}
bin/hadoop namenode -format

echo "设置完成，可以切换进入Hadoop目录"
echo "执行命令格式化Hadoop:bin/hadoop namenode -format"
echo "执行命令启动Hadoop:bin/start-all.sh"
echo

