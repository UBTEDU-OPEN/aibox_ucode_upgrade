#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: ucode_upgrade.py
# Created: 2020-12-09 18:12:14
# Author: ChenglongXiong (chenglong.xiong@ubtrobot.com)
# Copyright 2020 - 2020 Ubtech Robotics Corp. All rights reserved.
# -----
# Description:升级弹窗
###
import os
import sys
from ucode import ucode_upgrade_rc
import logging
import json
import time
import gettext
import xml.etree.ElementTree as ET
from ucode.ucode_dialog import UcodeDialog, UserLabel
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QThread, pyqtSignal, QCoreApplication, QTimer
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap
from oneai.common.config.default_config import DeFaultConfig
from multiprocessing import Queue

class UcodeUpgrade(UcodeDialog):

    def __init__(self, que):
        super(UcodeUpgrade, self).__init__()
        #self.m_xml_path = os.path.dirname(os.path.realpath(__file__)) + '/../aibox.xml'
        #语言配置 
        locale_dir = '/home/oneai/.config/uCode_upgrade/locale/'
        ret = gettext.find("ucode_upgrade_locale", locale_dir)
        gettext.translation("ucode_upgrade_locale", localedir = locale_dir, languages = ['en'] if ret is None else None).install()

        #读取xml配置文件
        xml_tree = ET.parse(os.path.dirname(os.path.realpath(__file__)) + '/../aibox.xml')
        self.m_xml_root = xml_tree.getroot()

        #弹窗中lable
        self.m_install_lable = None
        self.m_load_lable = None
        self.m_status_lable = None
        self.m_error_lable = None
        self.m_close_lable = None

        #线程处理弹窗状态
        self.m_status_thread = DialogThread(que)
        self.m_status_thread.dialog_trigger.connect(self.dialog_show)
        self.m_status_thread.start()

        #线程
        self.m_loading_lable = None

        #正在安装帧统计
        self.m_index = 0

        #成功安装定时器
        self.m_success_timer = None
        #成功安装界面停留时长
        self.m_success_timeout = 2*1000 #(ms)

        #正在安装帧显示标志
        self.m_install_flag = True

    def close_label_event(self, val):
        """关闭按钮事件处理

        Args:
            val (int): 0关闭 1鼠标进入 2鼠标离开
        """        
        if val == 0:
            self.release()
        elif val == 1:
            close_img = ':assets/pop_icon_close.png'
            self.m_close_lable.setPixmap(QPixmap(close_img))
        elif val == 2:
            close_img = ':assets/pop_icon_close_dis.png'
            self.m_close_lable.setPixmap(QPixmap(close_img))

    def __installing_status(self):
        """帧显示
        """
        if self.m_install_flag:
            img = ':assets/installing/install' + '{:0=4}'.format(self.m_index) + '.jpg'
            self.m_load_lable.setPixmap(QPixmap(img))
            self.m_index = self.m_index + 1 if self.m_index < 11 else 0

    def __installing_dialog(self):
        """正在安装
        """        
        self.m_loading_lable = LoadingThread()
        self.m_loading_lable.load_trigger.connect(self.__installing_status)
        self.m_loading_lable.start()

    def __success_dialog(self):
        """安装成功
        """        
        #退出线程，停止显示
        if self.m_loading_lable is not None:
            self.m_install_flag = False
            self.m_loading_lable.m_run = False
            self.m_loading_lable.wait()
            self.m_loading_lable = None

        #读取xml文件       
        ucode_update = self.__get_xml_node(['upgrade', 'ui', 'dialog'])

        #调整lable位置
        lable_rect = self.__get_lable(1, 'img_update_lable', ucode_update)['rect'][1]
        self.m_load_lable.setGeometry(QtCore.QRect(lable_rect[0], lable_rect[1], 
                                       lable_rect[2], lable_rect[3]))

        lable_rect = self.__get_lable(1, 'info_lable', ucode_update)['rect'][1]
        self.m_status_lable.setGeometry(QtCore.QRect(lable_rect[0], lable_rect[1], 
                                       lable_rect[2], lable_rect[3]))
        #删除原控件
        self.m_close_lable.deleteLater()

        #创建关闭控件
        lable_dict = self.__get_lable(0, 'close_lable', ucode_update)
        lable_rect = lable_dict['rect'][0]
        self.m_close_lable = UserLabel(self.m_dialog)
        self.m_close_lable.setObjectName(lable_dict['name'])
        self.m_close_lable.setGeometry(QtCore.QRect(lable_rect[0], lable_rect[1], 
                                       lable_rect[2], lable_rect[3]))
    
        #可选属性
        if 'stylesheet' in lable_dict:
            self.m_close_lable.setStyleSheet(lable_dict['stylesheet'])
    
        #更新内容
        close_img = ':assets/pop_icon_close_dis.png'
        self.m_close_lable.setPixmap(QPixmap(close_img))
        self.m_close_lable.show()

        #信号处理
        self.m_close_lable.mouse_trigger.connect(self.close_label_event)

        #更新lable内容
        img = ':assets/img_update_success.png'
        self.m_load_lable.setPixmap(QPixmap(img))
        self.m_status_lable.setText(QCoreApplication.translate('Dialog', _('ubt_ucodeupgrade_success')))
        self.m_status_lable.setAlignment(QtCore.Qt.AlignCenter)
        #创建定时器
        self.m_success_timer = QTimer()
        self.m_success_timer.timeout.connect(self.release)
        self.m_success_timer.start(self.m_success_timeout)


    def release(self):
        """释放资源
        """      
        #释放线程
        if self.m_status_thread is not None:
            self.m_status_thread.m_run = False
            self.m_status_thread.wait()
            self.m_status_thread = None
        if self.m_loading_lable is not None:
            self.m_install_flag = False
            self.m_loading_lable.m_run = False
            self.m_loading_lable.wait()
            self.m_loading_lable = None
        
        #释放定时器
        if self.m_success_timer is not None:
            self.m_success_timer.stop()
        
        sys.exit()

    def __get_xml_node(self, nodes):
        """获取xml节点

        Args:
            nodes (list): 节点

        Returns:
            object: xml节点
        """        
        ucode_update = self.m_xml_root
        for item in nodes:
            ucode_update = ucode_update.find(item)
            
        return ucode_update

    def __get_lable(self, index, id, xml):
        """获取指定lable

        Args:
            index (int): 索引
            id (string): 标识
            xml (objext): xml

        Returns:
            object: lable
        """        

        xml_path = ".//label[@id=" + "'" + id + "'"+ "]"
        lable_json = xml.find(xml_path).text
        lable_dict = json.loads(lable_json)

        return lable_dict

    def __error_dialog(self):
        """安装失败
        """        
        #退出线程，停止显示
        if self.m_loading_lable is not None:
            self.m_install_flag = False
            self.m_loading_lable.m_run = False
            self.m_loading_lable.wait()
            self.m_loading_lable = None

        #读取xml文件       
        ucode_update = self.__get_xml_node(['upgrade', 'ui', 'dialog'])

        #调整lable位置
        lable_rect = self.__get_lable(2, 'img_update_lable', ucode_update)['rect'][2]
        self.m_load_lable.setGeometry(QtCore.QRect(lable_rect[0], lable_rect[1], 
                                       lable_rect[2], lable_rect[3]))
        lable_rect = self.__get_lable(2, 'info_lable', ucode_update)['rect'][2]
        self.m_status_lable.setGeometry(QtCore.QRect(lable_rect[0], lable_rect[1], 
                                       lable_rect[2], lable_rect[3]))

        #删除原控件
        self.m_close_lable.deleteLater()

        #创建关闭控件
        lable_dict = self.__get_lable(0, 'close_lable', ucode_update)
        lable_rect = lable_dict['rect'][0]
        self.m_close_lable = UserLabel(self.m_dialog)
        self.m_close_lable.setObjectName(lable_dict['name'])
        self.m_close_lable.setGeometry(QtCore.QRect(lable_rect[0], lable_rect[1], 
                                       lable_rect[2], lable_rect[3]))
    
        #可选属性
        if 'stylesheet' in lable_dict:
            self.m_close_lable.setStyleSheet(lable_dict['stylesheet'])
    
        #更新内容
        close_img = ':assets/pop_icon_close_dis.png'
        self.m_close_lable.setPixmap(QPixmap(close_img))
        self.m_close_lable.show()

        #信号处理
        self.m_close_lable.mouse_trigger.connect(self.close_label_event)

        #更新lable内容
        img = ':assets/img_update_fail.png'
        self.m_load_lable.setPixmap(QPixmap(img))
        self.m_status_lable.setText(QCoreApplication.translate('Dialog', _('ubt_ucodeupgrade_fail')))
        self.m_status_lable.setAlignment(QtCore.Qt.AlignCenter)

        #创建lable
        lable_dict = self.__get_lable(0, 'error_lable', ucode_update)
        lable_rect = lable_dict['rect'][0]
        self.m_error_lable = QLabel(self.m_dialog)
        
        #配置lable
        self.m_error_lable.setObjectName(lable_dict['name'])
        lable_rect = lable_dict['rect'][0]
        self.m_error_lable.setGeometry(QtCore.QRect(lable_rect[0], lable_rect[1], 
                                       lable_rect[2], lable_rect[3]))
    
        #可选属性
        if 'stylesheet' in lable_dict:
            self.m_error_lable.setStyleSheet(lable_dict['stylesheet'])
        if 'font' in lable_dict:
            font = QtGui.QFont()
            font.setFamily(lable_dict['font']['family'])
            self.m_error_lable.setFont(font)
        
        #self.m_error_lable.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.m_error_lable.setText(QCoreApplication.translate('Dialog', _('ubt_ucodeupgrade_reminder')))
        self.m_error_lable.setAlignment(QtCore.Qt.AlignCenter)
        self.m_error_lable.setWordWrap(True)
        self.m_error_lable.show()

    def __init_dialog(self):
        """初始化窗口
        """        
        self.dialog_make(self.m_xml_root)
        
        #图片
        install_img = ':assets/installation_img_1.png'
        load_img = ':assets/installing/install0000.jpg'
        close_img = ':assets/pop_icon_close_dis.png'

        #获取dialog中的lable
        self.m_install_lable = self.m_dialog.findChild(QLabel, 'installing_lable')
        self.m_load_lable = self.m_dialog.findChild(QLabel, 'img_update_lable')
        self.m_status_lable = self.m_dialog.findChild(QLabel, 'info_lable')
        self.m_error_lable = self.m_dialog.findChild(QLabel, 'error_lable')
        self.m_close_lable = self.m_dialog.findChild(QLabel, 'close_lable')
        
        #对lable进行设置
        self.m_install_lable.setPixmap(QPixmap(install_img))
        self.m_load_lable.setPixmap(QPixmap(load_img))
        self.m_status_lable.setText(QCoreApplication.translate('Dialog', _('ubt_ucodeupgrade_doing')))
        self.m_status_lable.setAlignment(QtCore.Qt.AlignCenter)
        self.m_close_lable.setPixmap(QPixmap(close_img))

    def start(self):
        """启动
        """        
        logging.debug('upgrade ui start====')
        self.__init_dialog()
        self.m_dialog.show()
    
    def dialog_show(self, index):
        #正在安装
        if index == 0:
            self.__installing_dialog()
        #安装成功
        elif index == 1:
            self.__success_dialog()
        #安装失败
        elif index == 2:
            self.__error_dialog()

class LoadingThread(QThread):
    """正在安装弹窗

    Args:
        QThread (object): QThread
    """    
    load_trigger = pyqtSignal()
    
    def __init__(self):
        """初始化线程
        """        
        super(LoadingThread, self).__init__()
        self.m_run = True

    def run(self):
        """运行
        """    
        while self.m_run:
            time.sleep(0.05)
            self.load_trigger.emit()    

class DialogThread(QThread):
    """处理弹窗状态变化线程

    Args:
        QThread (object): QThread
    """    
    dialog_trigger = pyqtSignal(int)
    
    def __init__(self, que):
        """初始化类

        Args:
            que (object)): 队列
        """        
        super(DialogThread, self).__init__()
        self.m_queue = que
        #运行标志
        self.m_run = True

    def run(self):
        """运行
        """        
        while self.m_run:
            if not self.m_queue.empty():
                data = self.m_queue.get_nowait()
                try:
                    logging.debug('status:{}'.format(data['ucode']['status']))
                    self.dialog_trigger.emit(data['ucode']['status'])
                except Exception as e:
                    error_info = 'Error:{} {}'.format(e.__class__.__name__, e)
                    logging.debug(error_info)
                    sys.exit(DeFaultConfig.unknow_error)
    
            time.sleep(0.04)