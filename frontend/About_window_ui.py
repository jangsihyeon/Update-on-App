# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'About_window.ui'
##
## Created by: Qt User Interface Compiler version 6.6.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCommandLinkButton, QLabel, QSizePolicy,
    QWidget)

class Ui_About_Widget(object):
    def setupUi(self, About_Widget):
        if not About_Widget.objectName():
            About_Widget.setObjectName(u"About_Widget")
        About_Widget.setWindowModality(Qt.ApplicationModal)
        About_Widget.resize(500, 350)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(About_Widget.sizePolicy().hasHeightForWidth())
        About_Widget.setSizePolicy(sizePolicy)
        About_Widget.setMaximumSize(QSize(500, 16777215))
        font = QFont()
        font.setPointSize(10)
        About_Widget.setFont(font)
        self.widget = QWidget(About_Widget)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(0, 0, 501, 41))
        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 4, 481, 31))
        font1 = QFont()
        font1.setPointSize(15)
        font1.setBold(True)
        self.label.setFont(font1)
        self.label.setAlignment(Qt.AlignCenter)
        self.label_2 = QLabel(About_Widget)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(0, 290, 501, 51))
        font2 = QFont()
        font2.setPointSize(15)
        font2.setBold(True)
        font2.setItalic(True)
        self.label_2.setFont(font2)
        self.label_2.setStyleSheet(u"/*border: 1px dashed rgb(6, 6, 6);*/")
        self.label_2.setAlignment(Qt.AlignCenter)
        self.label_3 = QLabel(About_Widget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(7, 50, 481, 21))
        self.label_4 = QLabel(About_Widget)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(7, 80, 481, 21))
        self.label_5 = QLabel(About_Widget)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(7, 110, 481, 21))
        self.label_6 = QLabel(About_Widget)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(7, 140, 481, 21))
        self.label_7 = QLabel(About_Widget)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(7, 170, 481, 21))
        self.website_btn = QCommandLinkButton(About_Widget)
        self.website_btn.setObjectName(u"website_btn")
        self.website_btn.setGeometry(QRect(7, 250, 491, 41))
        self.website_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.label_8 = QLabel(About_Widget)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setGeometry(QRect(7, 200, 481, 21))
        self.label_9 = QLabel(About_Widget)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setGeometry(QRect(7, 230, 481, 21))

        self.retranslateUi(About_Widget)

        QMetaObject.connectSlotsByName(About_Widget)
    # setupUi

    def retranslateUi(self, About_Widget):
        About_Widget.setWindowTitle(QCoreApplication.translate("About_Widget", u"2232 GUI About", None))
        self.label.setText(QCoreApplication.translate("About_Widget", u"About 2232 GUI Program ", None))
        self.label_2.setText(QCoreApplication.translate("About_Widget", u"\"  Details make the Success \" ", None))
        self.label_3.setText(QCoreApplication.translate("About_Widget", u"\u25cf Made in Dings Korea", None))
        self.label_4.setText(QCoreApplication.translate("About_Widget", u"\u25cf GUI Version : 1.0.0", None))
        self.label_5.setText(QCoreApplication.translate("About_Widget", u"\u25cf Udate Release : Demo Version  ", None))
        self.label_6.setText(QCoreApplication.translate("About_Widget", u"\u25cf Program Contact Email : jayden@dingsmotion.com", None))
        self.label_7.setText(QCoreApplication.translate("About_Widget", u"\u25cf Company Contact Email : daniel@dingsmotion.com", None))
        self.website_btn.setText(QCoreApplication.translate("About_Widget", u"Website (Eng/Chn/Kor)", None))
        self.label_8.setText(QCoreApplication.translate("About_Widget", u"\u25cf Development Date : 2024-01-24", None))
        self.label_9.setText(QCoreApplication.translate("About_Widget", u"\u25cf Developer : Liz Jang", None))
    # retranslateUi

