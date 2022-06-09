import os
import sys
import io
from time import time
import folium # pip install folium
import psutil
import time
import urllib.parse

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTime, QTimer, QUrl
from datetime import datetime
from PyQt5.QtWidgets import QProgressBar, QSizePolicy, QApplication, QDialogButtonBox, QDialog
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog,QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView # pip install PyQtWebEngine
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QMovie

from qt_material import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import neurokit2 as nk

from ui_interface02 import *

shadow_elements = { 
    "left_menu_frame",
    "frame_3",
    "frame_5",
    "header_frame",
    "frame_9"
}

PBstyle1 = """
QProgressBar{
    border: 2px solid grey;
    border-radius: 5px;
    text-align: center
}

QProgressBar::chunk {
    background-color: #04B431;
    margin: 1px;
}
"""

PBstyle01 = """
QProgressBar{
    border: 2px solid grey;
    border-radius: 5px;
    text-align: center
}

QProgressBar::chunk {
    background-color: #FFBF00;
    margin: 1px;
}
"""

PBstyle0 = """
QProgressBar{
    border: 2px solid grey;
    border-radius: 5px;
    text-align: center
}

QProgressBar::chunk {
    background-color: #F80303;
    margin: 1px;
}
"""

class MainWindow(QMainWindow):
    def setHeureBat(self): # L'heure système
        htime = datetime.now()
        formatted_time = htime.strftime("%H:%M:%S")
        self.ui.label_heure.setText(formatted_time)
        batterie0 = psutil.sensors_battery()
        batterie = batterie0.percent
        self.ui.progressBar.setValue(batterie0.percent)
        return batterie
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)  
        image = QtGui.QPixmap()
        image.load(':/images/images/RDC2.png')
        image = image.scaled(self.width(), self.height())
        palette = QtGui.QPalette()
        palette.setBrush(self.backgroundRole(), QtGui.QBrush(image))
        self.setPalette(palette)
        apply_stylesheet(app, theme='dark_cyan.xml')
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint) 
        
        
        ###################################################################
        ########## Date (barre) ###########################################
        self.ddate = self.ui.label_date
        self.timer = QTimer()
        self.timer.timeout.connect(self.ladate)
        self.timer.start(1000)
        self.ladate()
        
        ########## Heure (barre) ##########################################
        self.timer = QTimer()
        self.timer.timeout.connect(self.setHeureBat)
        self.timer.start(1000)
        self.setHeureBat()

        ########## Niveau batterie (barre) ################################
        self.ui.progressBar.setAlignment(QtCore.Qt.AlignCenter)
        self.timer = QTimer()
        self.timer.timeout.connect(self.setHeureBat)
        self.timer.start(1000)
        batterie = self.setHeureBat()
        if batterie<30:
            self.ui.progressBar.setStyleSheet(PBstyle0)
        elif 30<=batterie<70:
            self.ui.progressBar.setStyleSheet(PBstyle01)
        else:
            self.ui.progressBar.setStyleSheet(PBstyle1)
        
        ########## Affichage Graphe ECG ###################################
        with plt.style.context('dark_background'):
            m = MplCanvas(self, width=5, height=4, dpi=100)
        t0 = 0
        t1 = 10
        FreqEch = 200
        N = FreqEch*(t1 - t0)
        t = np.linspace(t0, t1, N)
        ecg_simule = nk.ecg_simulate(duration=t1-t0, sampling_rate=200, heart_rate=80)
        self.xdata = t
        self.ydata = ecg_simule
        m.axes.plot(t, ecg_simule, linewidth=2, color='orange')
        m.axes.set_xlabel('Temps (s)'); m.axes.set_ylabel('Amplitude')
        m.axes.grid()
        toolbar = NavigationToolbar(m, self)
        self.ui.gridLayout.addWidget(toolbar)
        self.ui.gridLayout.addWidget(m)

        #####################################################################
        ########## Affichage Carte GPS #####################################
        coordinate = (44.35526129302216, 2.5568000391291035)
        m = folium.Map(
        	tiles='Stamen Terrain',
        	zoom_start=13,
        	location=coordinate
        )
        folium.Marker(
            location=[44.35526129302216, 2.5568000391291035],
            popup='Localisation de l\'ECG',
            icon=folium.Icon(prefix='fa',icon='heartbeat')
            ).add_to(m)
        folium.Marker(
            location=[44.360093, 2.551674],
            popup='Localisation de l\'hopital',
            icon=folium.Icon(prefix='fa',icon='h-square', markerColor='darkblue') 
            ).add_to(m)
        data = io.BytesIO()
        m.save(data, close_file=False)
        webView = QWebEngineView()
        webView.setHtml(data.getvalue().decode())
        self.ui.horizontalLayout_10.addWidget(webView)



        ########## Taille fenêtre ##########################################
        self.ui.maxi_btn.clicked.connect(lambda: self.restore_or_maximize_window())
        
        ########## Menu latéral gauche #####################################
        self.ui.pushButton_2.clicked.connect(lambda: self.slideLeftMenu())
        self.ui.pushButton.clicked.connect(lambda: self.slideLeftMenu2())
        

        ########## Redimensionner fenêtre  #################################
        self.gripSize = 10
        QtWidgets.QSizeGrip(self.ui.size_grip)
        self.ui.size_grip.resize(self.gripSize, self.gripSize)


        ########## Réduire la fenêtre ######################################
        self.ui.lower_btn.clicked.connect(lambda: self.showMinimized())

        ########## Fermer la fenêtre #######################################
        self.ui.close_btn.clicked.connect(lambda: self.close())

        ########## Déplacer la fenêtre #####################################
        def moveWindow(e):
            if self.isMaximized() == False:
                if e.buttons() == QtCore.Qt.LeftButton:  
                    self.move(self.pos() + e.globalPos() - self.clickPosition)
                    self.clickPosition = e.globalPos()
                    e.accept()
        self.ui.header_frame.mouseMoveEvent = moveWindow

        ########## Liens internet ##########################################
        self.ui.git_label.setOpenExternalLinks(True)
        self.ui.git_label.setText("<a href='https://www.github.com/'>Github</a>")
        self.ui.insta_label.setOpenExternalLinks(True)
        self.ui.insta_label.setText("<a href='https://www.instagram.com/lyceecharlescarnusrodez/'>Instagram</a>")
        self.ui.mail_label.setOpenExternalLinks(True)
        self.ui.mail_label.setText("<a href='https://www.carnus.fr/'>Mail LTP CC</a>")


        #####################################################################

        ########## GIF ######################################################
        gif1 = QMovie(":/images/images/ECG5.gif") 
        gif1.setScaledSize(QSize().scaled(120, 40, QtCore.Qt.KeepAspectRatio))
        self.ui.label_7.setMovie(gif1)
        gif1.start()

        ####################### Navigateur WEB ##############################
        ####################### Navigateur WEB ##############################
        ####################### Navigateur WEB ##############################
        ########## Boutons R-D-X du navigateur ##############################
        self.ui.pushButton_5.clicked.connect(self.ui.centralwidget.showMinimized)
        self.ui.pushButton_4.clicked.connect(self.winShowMaximized)
        self.ui.pushButton_3.clicked.connect(self.ui.nav_frame.hide) #.close .show
        
        ########## Affichage page web #######################################
        self.ui.nav_btn.clicked.connect(self.recherche)
        self.ui.search_btn.clicked.connect(self.recherche)

        self.ui.search_lineEdit.returnPressed.connect(self.loadP)
        self.ui.lineEdit.returnPressed.connect(self.loadP)

        ########## Boutons de navigation ####################################
        self.ui.pushButton_9.clicked.connect(self.backward)
        self.ui.pushButton_8.clicked.connect(self.forward)
        self.ui.pushButton_7.clicked.connect(self.reload)
        self.ui.pushButton_10.clicked.connect(self.navigate_home)
        #####################################################################



        ########################## SHOW #####################################
        ########################## SHOW #####################################
        ########################## SHOW #####################################
        self.show()
        self.battery()

    
    ################### Pages ###############################################
        self.ui.ecg_btn.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.ecg_page))
        self.ui.gps_btn.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.gps_page))
        self.ui.search_btn.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.internet_page))
        self.ui.nav_btn.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.internet_page))
        #
        self.ui.search_btn.clicked.connect(self.ui.internet_page.show)
        self.ui.nav_btn.clicked.connect(self.ui.internet_page.show)
        #
        self.ui.storage_btn.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.Storage_page))

    #########################################################################
    def loadP(self):
        url = QtCore.QUrl.fromUserInput(self.ui.lineEdit.text())
        if url.isValid():
            self.ui.webEngineView.load(url)
    
    ########################################################################
    ##### Bouton Rechercher : aller à internet #############################
    def recherche(self):
        cherch = self.ui.search_lineEdit.text()
        #site2 = QWebEngineView()
        url1 = 'https://google.com/search?q'
        params1 = {'': cherch}
        url2= url1 + urllib.parse.urlencode(params1)
        self.ui.webEngineView.load(QUrl(url2))
   
    def backward(self):
        self.ui.webEngineView.page().triggerAction(QWebEnginePage.Back)
    def forward(self):
        self.ui.webEngineView.page().triggerAction(QWebEnginePage.Forward)
    def reload(self):
        self.ui.webEngineView.page().triggerAction(QWebEnginePage.Reload)
    def navigate_home(self):
        self.ui.webEngineView.setUrl(QUrl('https://google.com')) 
    def add_new_tab(self, qurl=None, label="Blank"):
        if qurl is None:
            qurl = QUrl('')
            browser = QWebEngineView()
            browser.setUrl(qurl)
            i = self.ui.webEngineView.addTab(browser, label)
            self.ui.webEngineView.setCurrentIndex(i)
    def tab_open(self, i):
        if i== -1:
            self.add_new_tab()
    def close_current_tab(self, i):
        if self.ui.webEngineView.count() < 2:
            return
        self.ui.webEngineView.removeTab(i)
    def insertTab(self, widget):
        self.ui.verticalLayout_31.addWidget(widget)
        #self.ui.webEngineView.addWidget(widget)
    def winShowMaximized(self):
            if self.ui.maxi_btn.isChecked():
                self.ui.centralwidget.setStyleSheet("QWidget#widget{background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 255), stop:0.495 rgba(255, 255, 255, 255), stop:0.505 rgba(255, 0, 0, 255), stop:1 rgba(255, 0, 0, 255));border: 0px solid rgb(45, 45, 45);border-radius: 0px;}")
                self.ui.centralwidget.showMaximized()
            else:
                self.ui.centralwidget.setStyleSheet("QWidget#widget{border: 4px solid rgb(45, 45, 45);border-radius: 20px;}")
                self.ui.centralwidget.showNormal()


    ########################################################################
    ##### Min Max fenêtre ##################################################
    def restore_or_maximize_window(self):
        # Si fenêtre max
        if self.isMaximized():
            self.showNormal()
            # Changer Icone
            self.ui.maxi_btn.setIcon(QtGui.QIcon(u":/icones/icones/maximize-2.svg"))
        else:
            self.showMaximized()
            # Changer Icone
            self.ui.maxi_btn.setIcon(QtGui.QIcon(u":/icones/icones/minimize-2.svg"))

    def mousePressEvent(self, event):
        self.clickPosition = event.globalPos()
    
    def slideLeftMenu(self):
        width = self.ui.left_menu_frame.width()
        # Si minimisé
        if width == 0:
            # Développer menu
            newWidth = 225
            self.ui.pushButton_2.setIcon(QtGui.QIcon(u":/icones/icones/chevrons-left.svg"))
        # Si maximisé
        else:
            # Remettre menu
            newWidth = 0
            self.ui.pushButton_2.setIcon(QtGui.QIcon(u":/icones/icones/chevrons-right.svg"))
        # Animation de la transition
        self.animation = QtCore.QPropertyAnimation(self.ui.left_menu_frame, b"maximumWidth")#Animation minLargeur
        self.animation.setDuration(550)
        self.animation.setStartValue(width)# Valeur départ est celle de largeur menu
        self.animation.setEndValue(newWidth)# Valeur de fin est la nouvelle largeur
        self.animation.setEasingCurve(QtCore.QEasingCurve.OutBounce)
        self.animation.start()
    ############################
    def slideLeftMenu2(self):
        width = self.ui.profileCont.height()
        # Si minimisé
        if width == 0:
            # Développer menu
            newWidth = 300
        # Si maximisé
        else:
            # Remettre menu
            newWidth = 0
        # Animation de la transition
        self.animation = QtCore.QPropertyAnimation(self.ui.profileCont, b"maximumHeight")#Animation minLargeur
        self.animation.setDuration(550)
        self.animation.setStartValue(width)# Valeur départ est celle de largeur menu
        self.animation.setEndValue(newWidth)# Valeur de fin est la nouvelle largeur
        self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
        self.animation.start()
    
    ########################################################################

    ##### Fonction date ####################################################
    def ladate(self):
        hdate = datetime.today()
        #formatted_date = hdate.strftime('%Y-%m-%d')
        formatted_date = hdate.strftime('%A %d %B %Y')
        self.ddate.setText(formatted_date)
    
    #########################################################################  
    ########## Batterie menu latéral #####################################
    def battery(self):
        batt = psutil.sensors_battery()
        if not hasattr(psutil, "sensors_battery"):
            self.ui.et1_label2.setText("OS inconnu")
        if batt is None:
            self.ui.et1_label2.setText("Pas de batterie")
        if batt.power_plugged:
            self.ui.et2_label2.setText(str(round(batt.percent, 2))+"%")
            if batt.percent < 100:
                self.ui.et1_label2.setText("Chargement")
            else:
                self.ui.et1_label2.setText("Chargée")
            self.ui.et3_label2.setText("Oui")
        else:
            self.ui.et2_label2.setText(str(round(batt.percent, 2))+"%")
            if batt.percent < 100:
                self.ui.et1_label2.setText("Déchargée")
            else:
                self.ui.et1_label2.setText("Chargée")
            self.ui.et3_label2.setText("Non")
        #self.ui.et4_label2.rpb_setMaximum(100)
        self.ui.et4_pb.setValue(batt.percent)
        #self.ui.et4_label2.rpb_setValue(batt.percent)

    
##### Classe plot
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

############################################################################

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())