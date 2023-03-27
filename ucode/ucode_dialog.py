#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: ucode_dialog.py
# Created: 2020-12-09 18:12:51
# Author: ChenglongXiong (chenglong.xiong@ubtrobot.com)
# Copyright 2020 - 2020 Ubtech Robotics Corp. All rights reserved.
# -----
# Description:弹窗
###
import json
import xml.etree.ElementTree as ET
from oneai.common.config.default_config import DeFaultConfig
from PyQt5 import QtGui,QtCore
from PyQt5.QtWidgets import QDialog, QLabel
from abc import abstractmethod
from PyQt5.QtCore import pyqtSignal, Qt

class UserLabel(QLabel):
    """label

    Args:
        QLabel (object): QLabel
    """    
    #鼠标信号 0单击 1进入 2离开
    mouse_trigger = pyqtSignal(int)

    def __init__(self, dialog):
        """初始化

        Args:
            dialog (object): QDialog
        """        
        super(UserLabel, self).__init__(dialog)

    def mousePressEvent(self, QMouseEvent):
        """重载鼠标单击事件

        Args:
            QMouseEvent (object): QMouseEvent
        """        
        self.mouse_trigger.emit(0)

    def enterEvent(self, QMouseEvent):
        """重载鼠标进入事件

        Args:
            QMouseEvent (object): QMouseEvent
        """        
        self.mouse_trigger.emit(1)
    
    def leaveEvent(self, QMouseEvent):
        """重载鼠标离开事件

        Args:
            QMouseEvent (object): QMouseEvent
        """        
        self.mouse_trigger.emit(2)

class UcodeDialog():
    """ucode 弹窗
    """    
    def __init__(self):
        self.m_dialog = QDialog()
        self.m_dialog.setObjectName('ucode_dialog')

    def dialog_make(self, xml_root):
        """创建弹窗

        Args:
            xml_path (string): xml配置文件

        Returns:
            int: 成功返回DeFaultConfig.ok
        """ 
        #读取xml文件       
        ucode_update = xml_root.find('upgrade').find('ui').find('dialog')
        
        #dialog配置
        dialog_json = ucode_update.text
        dialog_pict = json.loads(dialog_json)
        self.m_dialog.resize(dialog_pict['size'][0], dialog_pict['size'][1])
        self.m_dialog.setMinimumSize(QtCore.QSize(dialog_pict['mini_size'][0], dialog_pict['size'][1]))
        self.m_dialog.setMaximumSize(QtCore.QSize(dialog_pict['max_size'][0], dialog_pict['size'][1]))
        self.m_dialog.setStyleSheet(dialog_pict['stylesheet'])
        #self.m_dialog.setWindowFlags(dialog_pict['window_flags'])
        self.m_dialog.setWindowFlags(Qt.ToolTip)
        
        #lable配置
        lable_list = list(ucode_update.iter("label"))
        for lable in lable_list:
            lable_json = lable.text
            lable_pict = json.loads(lable_json)
            if lable_pict['name'] != 'error_lable':
                self.__lable_make(lable_pict)

        return DeFaultConfig.ok

    def __lable_make(self, data):
        """制作lable

        Args:
            data (dict): 配置

        Returns:
            object: lable
        """        
        #创建lable
        lable = QLabel(self.m_dialog)
        
        #配置lable
        lable.setObjectName(data['name'])
        lable_rect = data['rect'][0]
        lable.setGeometry(QtCore.QRect(lable_rect[0], lable_rect[1], 
                                       lable_rect[2], lable_rect[3]))
    
        #可选属性
        if 'stylesheet' in data:
            lable.setStyleSheet(data['stylesheet'])
        if 'font' in data:
            font = QtGui.QFont()
            font.setFamily(data['font']['family'])
            lable.setFont(font)

        return lable

    @abstractmethod
    def close_label_event(self, val):
        pass