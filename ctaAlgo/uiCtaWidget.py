# encoding: UTF-8

'''
CTA模块相关的GUI控制组件
'''


from uiBasicWidget import QtGui, QtCore, BasicCell
from eventEngine import *
from ctaTradeTest import ParamWindow
from strategyGirdTrading import ParamWindow2
from CtpAndIB import ParamWindow3
import json
import os

#========================================================================



#========================================================================
class strategyWindow(QtGui.QMainWindow):

    def __init__(self,ParamWindow,ParamWindow2,ParamWindow3,CtaEngineManager=None):
	super(strategyWindow,self).__init__()
	self.setWindowTitle(u"策略类型")
	self.pw = ParamWindow
	self.gt = ParamWindow2
	self.cai = ParamWindow3
	self.ce = CtaEngineManager
	self.tradeTestButton =  QtGui.QPushButton(u"配置双合约套利策略",self)
	self.tradeTestButton.clicked.connect(self.createTradeTest) 
	self.girdTradingButton = QtGui.QPushButton(u"配置单合约网格策略",self)
	self.girdTradingButton.clicked.connect(self.createGirdTrading)
	self.CtpAndIB =  QtGui.QPushButton(u"配置CTP IB套利策略",self)
	self.CtpAndIB.clicked.connect(self.createCtpAndIB)
	self.moreStrategyCoding =  QtGui.QPushButton(u"更多策略开发中",self)
	self.moreStrategyCoding.clicked.connect(self.coding) 
	self.initUI()
	
    def initUI(self):
	self.resize(350, 350)
	self.tradeTestButton.move(50,20)
	self.tradeTestButton.resize(160,50)
	self.girdTradingButton.move(50,90)
	self.girdTradingButton.resize(160,50)
	self.CtpAndIB.move(50,160)
	self.CtpAndIB.resize(160,50)
	self.moreStrategyCoding.move(50,230)
	self.moreStrategyCoding.resize(160,50)
	self.center()
    def createTradeTest(self):
	self.pw.show()
    
    def createGirdTrading(self):
	self.gt.show()	

    def createCtpAndIB(self):
	self.cai.show()

    def coding(self):
	pass

    def center(self):
	screen = QtGui.QDesktopWidget().screenGeometry()
	size = self.geometry()
	self.move((screen.width() - size.width())/2, (screen.height() - size.height())/2)
	
########################################################################
class CtaValueMonitor(QtGui.QTableWidget):
    """参数监控"""

    #----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(CtaValueMonitor, self).__init__(parent)
        
        self.keyCellDict = {}
        self.data = None
        self.inited = False
        
        self.initUi()
        
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setRowCount(1)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(self.NoEditTriggers)
        self.setMaximumHeight(self.sizeHint().height())
        
    #----------------------------------------------------------------------
    def updateData(self, data):
        """更新数据"""
        if not self.inited:
            self.setColumnCount(len(data))
            self.setHorizontalHeaderLabels(data.keys())
            
            col = 0
            for k, v in data.items():
                cell = QtGui.QTableWidgetItem(unicode(v))
                self.keyCellDict[k] = cell
                self.setItem(0, col, cell)
                col += 1
            
            self.inited = True
        else:
            for k, v in data.items():
                cell = self.keyCellDict[k]
                cell.setText(unicode(v))


########################################################################
class CtaStrategyManager(QtGui.QGroupBox):
    """策略管理组件"""
    signal = QtCore.pyqtSignal(type(Event()))

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, eventEngine, name, className=None, direction=None, vtSymbol=None, longsymbol=None, shortsymbol=None, parent=None):
        """Constructor"""
        super(CtaStrategyManager, self).__init__(parent)
        
        self.ctaEngine = ctaEngine
        self.eventEngine = eventEngine
        self.name = name
        self.initUi()
        self.updateMonitor()
        self.registerEvent()
	
	if className == 'tradeTest':
            self.paramWindow = ParamWindow(self.name,longsymbol,shortsymbol)
	elif className == "CtpAndIB":
            self.paramWindow = ParamWindow3(self.name,longsymbol,shortsymbol)
	else:
	    self.paramWindow = ParamWindow2(self.name, direction, vtSymbol)
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setTitle(self.name)
        
        self.paramMonitor = CtaValueMonitor(self)
        self.varMonitor = CtaValueMonitor(self)
        maxHeight = 60
        self.paramMonitor.setMaximumHeight(maxHeight)
        self.varMonitor.setMaximumHeight(maxHeight)  
        buttonInit = QtGui.QPushButton(u'初始化')
        buttonStart = QtGui.QPushButton(u'启动')
        buttonStop = QtGui.QPushButton(u'停止')
	buttonParam = QtGui.QPushButton(u'参数')
	buttonDelete = QtGui.QPushButton(u'删除')
	buttonDelete.clicked.connect(self.delete)
        buttonInit.clicked.connect(self.init)
        buttonStart.clicked.connect(self.start)
        buttonStop.clicked.connect(self.stop)
        buttonParam.clicked.connect(self.param)
        hbox1 = QtGui.QHBoxLayout()     
        hbox1.addWidget(buttonInit)
        hbox1.addWidget(buttonStart)
        hbox1.addWidget(buttonStop)
	hbox1.addWidget(buttonParam)
	hbox1.addWidget(buttonDelete)

        hbox1.addStretch()
        
        hbox2 = QtGui.QHBoxLayout()
        hbox2.addWidget(self.paramMonitor)
        
        hbox3 = QtGui.QHBoxLayout()
        hbox3.addWidget(self.varMonitor)
        
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)

        self.setLayout(vbox)
        
    #----------------------------------------------------------------------
    def updateMonitor(self, event=None):
        """显示策略最新状态"""
        paramDict = self.ctaEngine.getStrategyParam(self.name)
        if paramDict:
            self.paramMonitor.updateData(paramDict)
            self.paramMonitor.setColumnWidth(3,300) 
        varDict = self.ctaEngine.getStrategyVar(self.name)
        if varDict:
            self.varMonitor.updateData(varDict)        
            self.varMonitor.setColumnWidth(3,300) 
    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.signal.connect(self.updateMonitor)
        self.eventEngine.register(EVENT_CTA_STRATEGY+self.name, self.signal.emit)
    
    #----------------------------------------------------------------------
    def init(self):
        """初始化策略"""
        self.ctaEngine.initStrategy(self.name)
    
    #----------------------------------------------------------------------
    def start(self):
        """启动策略"""
        self.ctaEngine.startStrategy(self.name)
        
    #----------------------------------------------------------------------
    def stop(self):
        """停止策略"""
        self.ctaEngine.stopStrategy(self.name)
#==========================================================================================
    def param(self):
	
	self.paramWindow.paramters = self.paramWindow.loadParameter()
	self.paramWindow.showParam()
	self.paramWindow.show()
    #def position(self):
	#self.ctaEngine.excPos(self.name)

    #def updateInfo(self):
	
	#self.ctaEngine.loadPosInfo()
    def delete(self):
	settingFileName = 'ctaAlgo/CTA_setting.json'
        reply = QtGui.QMessageBox.question(self, u'删除',
                                           u'是否删除配置文件?', QtGui.QMessageBox.Yes | 
                                           QtGui.QMessageBox.No, QtGui.QMessageBox.No)
	with open(settingFileName,'r') as f:
            l = json.load(f)
	    f.close()	
	#flag = True
	for x in l :
	    if x['name'] == self.name:
		l.remove(x)
		#flag = False
	with open(settingFileName, 'w') as f:
	    json.dump(l, f)
	    f.close()
        if reply == QtGui.QMessageBox.Yes: 
	    fileName = "parameter_" + self.name + ".json"
	    os.remove(fileName)
	else :
	    pass0
#==========================================================================================
########################################################################
class CtaEngineManager(QtGui.QWidget):
    """CTA引擎管理组件"""
    signal = QtCore.pyqtSignal(type(Event()))

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, eventEngine, parent=None):
        """Constructor"""
        super(CtaEngineManager, self).__init__(parent)
        
        self.ctaEngine = ctaEngine
        self.eventEngine = eventEngine
        
        self.strategyLoaded = False
	self.pw = ParamWindow("","","",self)
	self.gt = ParamWindow2("","","",self)
	self.cai = ParamWindow3("","","",self)
        #self.sw = strategyWindow(self.pw, self.gt,self.cai)
        self.initUi()
        self.registerEvent()
        # 记录日志
        self.ctaEngine.writeCtaLog(u'CTA引擎启动成功')        
        
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(u'CTA策略')
        
        # 按钮
        loadButton = QtGui.QPushButton(u'加载策略')
        initAllButton = QtGui.QPushButton(u'全部初始化')
        startAllButton = QtGui.QPushButton(u'全部启动')
        stopAllButton = QtGui.QPushButton(u'全部停止')
	addStrategy = QtGui.QPushButton(u'添加策略')
        
        loadButton.clicked.connect(self.load)
        initAllButton.clicked.connect(self.initAll)
        startAllButton.clicked.connect(self.startAll)
        stopAllButton.clicked.connect(self.stopAll)
	addStrategy.clicked.connect(self.addStrategy)
        # 滚动区域，放置所有的CtaStrategyManager
        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        
        # CTA组件的日志监控
        self.ctaLogMonitor = QtGui.QTextEdit()
        self.ctaLogMonitor.setReadOnly(True)
        self.ctaLogMonitor.setMaximumHeight(200)
        
        # 设置布局
        hbox2 = QtGui.QHBoxLayout()
        hbox2.addWidget(loadButton)
        hbox2.addWidget(initAllButton)
        hbox2.addWidget(startAllButton)
        hbox2.addWidget(stopAllButton)
	hbox2.addWidget(addStrategy)
        hbox2.addStretch()
        
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox2)
        vbox.addWidget(self.scrollArea)
        vbox.addWidget(self.ctaLogMonitor)
        self.setLayout(vbox)
        
    #----------------------------------------------------------------------
    def initStrategyManager(self):
        """初始化策略管理组件界面"""        
        w = QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()
        
        for name in self.ctaEngine.strategyDict.keys():
	    p = self.ctaEngine.strategyDict[name]
	    if p.className == 'tradeTest' :
                strategyManager = CtaStrategyManager(self.ctaEngine, self.eventEngine, name, p.className, '', '', p.longsymbol, p.shortsymbol)
	    elif p.className == 'CtpAndIB' :
		strategyManager = CtaStrategyManager(self.ctaEngine, self.eventEngine, name, p.className, '', '', p.longsymbol, p.shortsymbol)
	    else:
		strategyManager = CtaStrategyManager(self.ctaEngine, self.eventEngine, name, p.className, p.direction, p.vtSymbol, '', '')
            vbox.addWidget(strategyManager)

        vbox.addStretch()
        
        w.setLayout(vbox)
        self.scrollArea.setWidget(w)   
        
    #----------------------------------------------------------------------
    def initAll(self):
        """全部初始化"""
        for name in self.ctaEngine.strategyDict.keys():
            self.ctaEngine.initStrategy(name)    
            
    #----------------------------------------------------------------------
    def startAll(self):
        """全部启动"""
        for name in self.ctaEngine.strategyDict.keys():
            self.ctaEngine.startStrategy(name)
            
    #----------------------------------------------------------------------
    def stopAll(self):
        """全部停止"""
        for name in self.ctaEngine.strategyDict.keys():
            self.ctaEngine.stopStrategy(name)
          
    #----------------------------------------------------------------------
    
    def addStrategy(self):
	self.pw = ParamWindow("","","",self)
	self.gt = ParamWindow2("","","",self)
	self.cai = ParamWindow3("","","",self)
	self.sw = strategyWindow(self.pw, self.gt,self.cai)
	self.sw.show()
 

    #----------------------------------------------------------------------
    def load(self):
        """加载策略"""
        if not self.strategyLoaded:
            self.ctaEngine.loadSetting()
            self.initStrategyManager()
            self.strategyLoaded = True
            self.ctaEngine.writeCtaLog(u'策略加载成功')
        
    #----------------------------------------------------------------------
    def updateCtaLog(self, event):
        """更新CTA相关日志"""
        log = event.dict_['data']
        content = '\t'.join([log.logTime, log.logContent])
        self.ctaLogMonitor.append(content)
    
    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.signal.connect(self.updateCtaLog)
        self.eventEngine.register(EVENT_CTA_LOG, self.signal.emit)
        
        
    
    



    
    
