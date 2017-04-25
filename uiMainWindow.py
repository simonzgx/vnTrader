# encoding: UTF-8

import psutil

from uiBasicWidget import *
from ctaAlgo.uiCtaWidget import CtaEngineManager
from dataRecorder.uiDrWidget import DrEngineManager
from riskManager.uiRmWidget import RmEngineManager


class connectIBWindow(QtGui.QDialog):

    def __init__(self,mainEngine):
	super(connectIBWindow,self).__init__()
	self.mainEngine = mainEngine
	self.fileName = 'ibGateway/IB_connect.json'
	self.port = QtGui.QLabel(u'port', self)
	self.clientId = QtGui.QLabel(u'clientId', self)
	self.accountCode = QtGui.QLabel(u'accountCode', self)
	self.portEdit = QtGui.QLineEdit(self)
	self.clientIdEdit = QtGui.QLineEdit(self)
	self.accountCodeEdit = QtGui.QLineEdit(self)
	self.connectButton = QtGui.QPushButton(u"连接",self)
	self.connectButton.clicked.connect(self.connect)
	self.initUI()

    def showParam(self):
	
	self.dic = {}
	with open(self.fileName, 'r') as f:
	    self.dic = json.load(f)
	self.clientIdEdit.setText(str(self.dic['clientId']))
	self.accountCodeEdit.setText(str(self.dic['accountCode']))
	self.portEdit.setText(str(self.dic['port']))

    def connect(self):
	self.dic['clientId'] = str(self.clientIdEdit.text())
	self.dic['accountCode'] = str(self.accountCodeEdit.text())
	self.dic['port'] = str(self.portEdit.text())
	d = json.dumps(self.dic,sort_keys=True,indent=4)
	with open(self.fileName, 'w') as f:
	    f.write(d)
	    f.close()
	self.mainEngine.connect("IB")

    def initUI(self):
	self.resize(380,160)
	self.center()
	layout = QtGui.QGridLayout()
	layout.addWidget(self.port,0,0)
	layout.addWidget(self.portEdit,0,1,1,2)
	layout.addWidget(self.clientId,1,0)
	layout.addWidget(self.clientIdEdit,1,1,1,2)	
	layout.addWidget(self.accountCode,2,0)
	layout.addWidget(self.accountCodeEdit,2,1,1,2)
	layout.addWidget(self.connectButton,3,1)
	self.setLayout(layout)		
	self.showParam()

    def center(self):
	screen = QtGui.QDesktopWidget().screenGeometry()
	size = self.geometry()
	self.move((screen.width() - size.width())/2, (screen.height() - size.height())/2)




########################################################################
class connectCTPWindow(QtGui.QDialog):

    def __init__(self,mainEngine):
	QtGui.QWidget.__init__(self, parent=None)
	self.mainEngine = mainEngine
	self.userID = QtGui.QLabel(u'帐号', self)
	self.pwd = QtGui.QLabel(u'密码', self)
	self.address = QtGui.QLabel(u'服务器', self)
	self.hisUser = QtGui.QLabel(u'历史登录', self)
	self.idEdit = QtGui.QLineEdit(self)
	self.pwdEdit = QtGui.QLineEdit(self)
	self.combo = QtGui.QComboBox(self)
	self.combo.addItem(u'实盘行情')
	self.combo.addItem(u'模拟行情')
	self.combo.addItem(u'中信建投')
	self.hisUserCombo = QtGui.QComboBox(self)
	self.addUsers()	
	self.hisUserCombo.currentIndexChanged.connect(self.loadAccount)
	self.isSaveAccount = QtGui.QCheckBox(u'记住帐号', self)
	self.login = QtGui.QPushButton(u'登录', self)
	self.cancel = QtGui.QPushButton(u'取消', self)
	self.login.clicked.connect(self.connect)
	#self.cancel.clicked.connect(self.quit)

	self.initUI()

    def initUI(self):

	self.resize(380,160)
	self.center()
	self.pwdEdit.setEchoMode(QtGui.QLineEdit.Password)

	layout = QtGui.QGridLayout()
	layout.addWidget(self.hisUser,0,0)
	layout.addWidget(self.hisUserCombo,0,1)
	layout.addWidget(self.userID,1,0)
	layout.addWidget(self.idEdit,1,1,1,2)
	layout.addWidget(self.pwd,2,0)
	layout.addWidget(self.pwdEdit,2,1,1,2)
	layout.addWidget(self.address,0,2)
	layout.addWidget(self.combo,0,3)
	layout.addWidget(self.isSaveAccount,3,1,1,1)
	layout.addWidget(self.login,3,2,1,1)
	layout.addWidget(self.cancel,3,3,1,1)
	#layout.setMargin(10)
	#layout.setSpacing(10)
	self.setLayout(layout)

    def connect(self):
	
	simTDAddress = "tcp://180.168.146.187:10030"
	simMDAddress = "tcp://180.168.146.187:10031"
	tdAddress = "tcp://116.236.239.137:41205"
	mdAddress = "tcp://116.236.239.137:41213"
	zxjtTdAddress = 'tcp://180.166.25.17:41205'
	zxjtMdAddress = 'tcp://180.166.25.17:41213'
	userId = str(self.idEdit.text())
	password = str(self.pwdEdit.text())
	account = {}
	account['userID'] = userId
	account['password'] = password
	if self.combo.currentText() == u'实盘行情':
	    account['tdAddress'] = tdAddress
	    account['mdAddress'] = mdAddress
	    bookId = "7070"
	elif self.combo.currentText() == u'模拟行情':
	    account['tdAddress'] = simTDAddress
	    account['mdAddress'] = simMDAddress
	    bookId = "9999"
	elif self.combo.currentText() == u'中信建投':
	    account['tdAddress'] = zxjtTdAddress
	    account['mdAddress'] = zxjtMdAddress
	    bookId = '9080'
	account['brokerID'] = bookId
	d = json.dumps(account,sort_keys=True,indent=4)
	with open('ctpGateway/CTP_connect.json', 'w') as f:
	    f.write(d)
	    f.close()
	if self.isSaveAccount.isChecked():
	    users = {}
	    with open('ctpGateway/CTP_users.json', 'r') as f:
		users = json.load(f)
		f.close()
	    users[account['userID']] = account['password']
	    d = json.dumps(users,sort_keys=True,indent=4)
	    with open('ctpGateway/CTP_users.json', 'w') as f:
		f.write(d)
		f.close()
	
	self.mainEngine.connect("CTP")
    def center(self):
	screen = QtGui.QDesktopWidget().screenGeometry()
	size = self.geometry()
	self.move((screen.width() - size.width())/2, (screen.height() - size.height())/2)


    def addUsers(self):
	fileName = 'ctpGateway/CTP_users.json'
	self.dic = {}
	with open(fileName, 'r') as f:
	    self.dic = json.load(f)
	self.hisUserCombo.addItem('')
	for x in self.dic.keys():
	    self.hisUserCombo.addItem(x)

    def loadAccount(self):
	userID = str(self.hisUserCombo.currentText())
	self.idEdit.setText(userID)
	self.pwdEdit.setText(self.dic[userID])



class MainWindow(QtGui.QMainWindow):
    """主窗口"""
    signalStatusBar = QtCore.pyqtSignal(type(Event()))

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        super(MainWindow, self).__init__()
        
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        
        self.widgetDict = {}    # 用来保存子窗口的字典
        
        self.initUi()
        self.loadWindowSettings('custom')
        
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle('VnTrader')
        self.initCentral()
        self.initMenu()
        self.initStatusBar()
        
    #----------------------------------------------------------------------
    def initCentral(self):
        """初始化中心区域"""
        widgetMarketM, dockMarketM = self.createDock(MarketMonitor, u'行情', QtCore.Qt.RightDockWidgetArea)
        widgetLogM, dockLogM = self.createDock(LogMonitor, u'日志', QtCore.Qt.BottomDockWidgetArea)
        widgetErrorM, dockErrorM = self.createDock(ErrorMonitor, u'错误', QtCore.Qt.BottomDockWidgetArea)
        widgetTradeM, dockTradeM = self.createDock(TradeMonitor, u'成交', QtCore.Qt.BottomDockWidgetArea)
        widgetOrderM, dockOrderM = self.createDock(OrderMonitor, u'委托', QtCore.Qt.RightDockWidgetArea)
        widgetPositionM, dockPositionM = self.createDock(PositionMonitor, u'持仓', QtCore.Qt.BottomDockWidgetArea)
        widgetAccountM, dockAccountM = self.createDock(AccountMonitor, u'资金', QtCore.Qt.BottomDockWidgetArea)
        widgetTradingW, dockTradingW = self.createDock(TradingWidget, u'交易', QtCore.Qt.LeftDockWidgetArea)
    
        self.tabifyDockWidget(dockTradeM, dockErrorM)
        self.tabifyDockWidget(dockTradeM, dockLogM)
        self.tabifyDockWidget(dockPositionM, dockAccountM)
    
        dockTradeM.raise_()
        dockPositionM.raise_()
    
        # 连接组件之间的信号
        widgetPositionM.itemDoubleClicked.connect(widgetTradingW.closePosition)
        
        # 保存默认设置
        self.saveWindowSettings('default')
        
    #----------------------------------------------------------------------
    def initMenu(self):
        """初始化菜单"""
        # 创建菜单
        menubar = self.menuBar()
        
        # 设计为只显示存在的接口
        sysMenu = menubar.addMenu(u'系统')
        self.addConnectAction(sysMenu, 'CTP')
        self.addConnectAction(sysMenu, 'LTS')
        self.addConnectAction(sysMenu, 'XTP')
        self.addConnectAction(sysMenu, 'FEMAS', u'飞马')
        self.addConnectAction(sysMenu, 'XSPEED', u'飞创')
        self.addConnectAction(sysMenu, 'QDP')
        self.addConnectAction(sysMenu, 'KSOTP', u'金仕达期权')
        self.addConnectAction(sysMenu, 'KSGOLD', u'金仕达黄金')
        self.addConnectAction(sysMenu, 'SGIT', u'飞鼠')
        sysMenu.addSeparator()
        self.addConnectAction(sysMenu, 'IB')
        self.addConnectAction(sysMenu, 'SHZD', u'直达')
        self.addConnectAction(sysMenu, 'OANDA')
        self.addConnectAction(sysMenu, 'OKCOIN')     
        sysMenu.addSeparator()
        self.addConnectAction(sysMenu, 'Wind')
        
        sysMenu.addSeparator()
        sysMenu.addAction(self.createAction(u'连接数据库', self.mainEngine.dbConnect))
        sysMenu.addSeparator()
        sysMenu.addAction(self.createAction(u'退出', self.close))
        
        functionMenu = menubar.addMenu(u'功能')
        functionMenu.addAction(self.createAction(u'查询合约', self.openContract))
        functionMenu.addAction(self.createAction(u'行情记录', self.openDr))
        functionMenu.addAction(self.createAction(u'风控管理', self.openRm))
        
        # 算法相关
        algoMenu = menubar.addMenu(u'算法')
        algoMenu.addAction(self.createAction(u'CTA策略', self.openCta))
        
        # 帮助
        helpMenu = menubar.addMenu(u'帮助')
        helpMenu.addAction(self.createAction(u'还原', self.restoreWindow))
        helpMenu.addAction(self.createAction(u'关于', self.openAbout))
        helpMenu.addAction(self.createAction(u'测试', self.test))
    
    #----------------------------------------------------------------------
    def initStatusBar(self):
        """初始化状态栏"""
        self.statusLabel = QtGui.QLabel()
        self.statusLabel.setAlignment(QtCore.Qt.AlignLeft)
        
        self.statusBar().addPermanentWidget(self.statusLabel)
        self.statusLabel.setText(self.getCpuMemory())
        
        self.sbCount = 0
        self.sbTrigger = 10     # 10秒刷新一次
        self.signalStatusBar.connect(self.updateStatusBar)
        self.eventEngine.register(EVENT_TIMER, self.signalStatusBar.emit)
        
    #----------------------------------------------------------------------
    def updateStatusBar(self, event):
        """在状态栏更新CPU和内存信息"""
        self.sbCount += 1
        
        if self.sbCount == self.sbTrigger:
            self.sbCount = 0
            self.statusLabel.setText(self.getCpuMemory())
    
    #----------------------------------------------------------------------
    def getCpuMemory(self):
        """获取CPU和内存状态信息"""
        cpuPercent = psutil.cpu_percent()
        memoryPercent = psutil.virtual_memory().percent
        return u'CPU使用率：%d%%   内存使用率：%d%%' % (cpuPercent, memoryPercent)        
        
    #----------------------------------------------------------------------
    def addConnectAction(self, menu, gatewayName, displayName=''):
        """增加连接功能"""
        if gatewayName not in self.mainEngine.getAllGatewayNames():
            return
        if gatewayName == 'CTP':
	    def connect():
	    	self.connectWindow = connectCTPWindow(self.mainEngine)
		self.connectWindow.show()
	elif gatewayName == "IB":
	    def connect():
	    	self.connectWindow = connectIBWindow(self.mainEngine)
		self.connectWindow.show()
	else :
            def connect():
                self.mainEngine.connect(gatewayName)
        
        if not displayName:
            displayName = gatewayName
        actionName = u'连接' + displayName
        
        menu.addAction(self.createAction(actionName, connect))
        
    #----------------------------------------------------------------------
    def createAction(self, actionName, function):
        """创建操作功能"""
        action = QtGui.QAction(actionName, self)
        action.triggered.connect(function)
        return action
        
    #----------------------------------------------------------------------
    def test(self):
        """测试按钮用的函数"""
        # 有需要使用手动触发的测试函数可以写在这里
        pass

    #----------------------------------------------------------------------
    def openAbout(self):
        """打开关于"""
        try:
            self.widgetDict['aboutW'].show()
        except KeyError:
            self.widgetDict['aboutW'] = AboutWidget(self)
            self.widgetDict['aboutW'].show()
    
    #----------------------------------------------------------------------
    def openContract(self):
        """打开合约查询"""
        try:
            self.widgetDict['contractM'].show()
        except KeyError:
            self.widgetDict['contractM'] = ContractMonitor(self.mainEngine)
            self.widgetDict['contractM'].show()
            
    #----------------------------------------------------------------------
    def openCta(self):
        """打开CTA组件"""
        try:
            self.widgetDict['ctaM'].showMaximized()
        except KeyError:
            self.widgetDict['ctaM'] = CtaEngineManager(self.mainEngine.ctaEngine, self.eventEngine)
            self.widgetDict['ctaM'].showMaximized()
            
    #----------------------------------------------------------------------
    def openDr(self):
        """打开行情数据记录组件"""
        try:
            self.widgetDict['drM'].showMaximized()
        except KeyError:
            self.widgetDict['drM'] = DrEngineManager(self.mainEngine.drEngine, self.eventEngine)
            self.widgetDict['drM'].showMaximized()
            
    #----------------------------------------------------------------------
    def openRm(self):
        """打开组件"""
        try:
            self.widgetDict['rmM'].show()
        except KeyError:
            self.widgetDict['rmM'] = RmEngineManager(self.mainEngine.rmEngine, self.eventEngine)
            self.widgetDict['rmM'].show()      
    
    #----------------------------------------------------------------------
    def closeEvent(self, event):
        """关闭事件"""
        reply = QtGui.QMessageBox.question(self, u'退出',
                                           u'确认退出?', QtGui.QMessageBox.Yes | 
                                           QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes: 
            for widget in self.widgetDict.values():
                widget.close()
            self.saveWindowSettings('custom')
            
            self.mainEngine.exit()
            event.accept()
        else:
            event.ignore()
            
    #----------------------------------------------------------------------
    def createDock(self, widgetClass, widgetName, widgetArea):
        """创建停靠组件"""
        widget = widgetClass(self.mainEngine, self.eventEngine)
        dock = QtGui.QDockWidget(widgetName)
        dock.setWidget(widget)
        dock.setObjectName(widgetName)
        dock.setFeatures(dock.DockWidgetFloatable|dock.DockWidgetMovable)
        self.addDockWidget(widgetArea, dock)
        return widget, dock
    
    #----------------------------------------------------------------------
    def saveWindowSettings(self, settingName):
        """保存窗口设置"""
        settings = QtCore.QSettings('vn.trader', settingName)
        settings.setValue('state', self.saveState())
        settings.setValue('geometry', self.saveGeometry())
        
    #----------------------------------------------------------------------
    def loadWindowSettings(self, settingName):
        """载入窗口设置"""
        settings = QtCore.QSettings('vn.trader', settingName)
        # 这里由于PyQt4的版本不同，settings.value('state')调用返回的结果可能是：
        # 1. None（初次调用，注册表里无相应记录，因此为空）
        # 2. QByteArray（比较新的PyQt4）
        # 3. QVariant（以下代码正确执行所需的返回结果）
        # 所以为了兼容考虑，这里加了一个try...except，如果是1、2的情况就pass
        # 可能导致主界面的设置无法载入（每次退出时的保存其实是成功了）
        try:
            self.restoreState(settings.value('state').toByteArray())
            self.restoreGeometry(settings.value('geometry').toByteArray())    
        except AttributeError:
            pass
        
    #----------------------------------------------------------------------
    def restoreWindow(self):
        """还原默认窗口设置（还原停靠组件位置）"""
        self.loadWindowSettings('default')
        self.showMaximized()


########################################################################
class AboutWidget(QtGui.QDialog):
    """显示关于信息"""

    #----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(AboutWidget, self).__init__(parent)

        self.initUi()

    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        self.setWindowTitle(u'关于VnTrader')

        text = u"""
            Developed by Traders, for Traders.

            License：MIT
            
            Website：www.vnpy.org

            Github：www.github.com/vnpy/vnpy
            
            """

        label = QtGui.QLabel()
        label.setText(text)
        label.setMinimumWidth(500)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(label)

        self.setLayout(vbox)
    
