# encoding: UTF-8

import json
from ctaBase import *
from ctaTemplate import CtaTemplate
import smtplib
from uiBasicWidget import *

import numpy as np
import datetime

########################################################################
class CtpAndIB(CtaTemplate):
    """策略"""
    className = 'CtpAndIB'
    author = u'Simon'

    # 策略参数
    initDays = 0   # 初始化数据所用的天数


    # 策略变量
    bar = {}
    closelist={}
    barMinute = {}
    lasttick={}

    bartime={}
    signal={}

    longsymbol=EMPTY_STRING
    shortsymbol=EMPTY_STRING
    poslimit=1
    posstate={}
    postoday={}         #今日持仓
    tradestate={}       #交易状态
    productClass = PRODUCT_FUTURES    # 产品类型（只有IB接口需要）
    currency = CURRENCY_USD        # 货币（只有IB接口需要） 
    tradeid=EMPTY_STRING
    cdnum=0
#=========================================
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol']    
    
    # 变量列表，保存了变量的名称

    varList = [ 'inited',
                'trading',
		'buyPrice',
		'postoday',
		'dfr',
		'dfr_2']
    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting, fileName):
	self.fileName = fileName
	self.filterDic = {}
        """Constructor"""
        super(CtpAndIB, self).__init__(ctaEngine, setting)
	ce = ctaEngine
	ce.doCheck()
        if setting :
            self.longsymbol=setting['longSymbol']
            self.shortsymbol=setting['shortSymbol']
        for vts in self.vtSymbol :
            self.tradestate[vts]=0
            self.postoday[vts]=0
            self.posstate[vts]=0
	self.loadParameter()
        self.flag = 0
        self.isOrder = {}

        self.dfr = 0
        self.dfr_2 = 0
    #----------------------------------------------------------------------
    def onInit(self):
	self.loadPosInfo()
        self.loadParameter()
        """初始化策略（必须由用户继承实现）"""
        if self.initDays==0:
            return
        self.writeCtaLog(u'策略初始化')
        for vtsymbol in self.vtSymbol:
            initData = self.loadTick(self.initDays,vtsymbol)
            for tick in initData:
                self.onTick(tick)
        
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onStart(self):
        self.loadParameter()
	self.loadPosInfo()
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'策略启动')
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
	self.filterDic = {}
	self.loadPosInfo()
        self.saveParameter()
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'macdpbx策略停止')
        self.putEvent()
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        self.lastOrder=order


    #----------------------------------------------------------------------
    def onTick(self, tick):

	print tick.vtSymbol,tick.askPrice1
    def doFilter(self, tick):
	if tick.vtSymbol not in self.filterDic.keys():
	    self.filterDic[tick.vtSymbol] = {'ask':[], 'bid':[]}
	self.filterDic[tick.vtSymbol]['ask'].append(tick.askPrice1)
	self.filterDic[tick.vtSymbol]['bid'].append(tick.bidPrice1)

	if len(self.filterDic[tick.vtSymbol]['bid'] <= 10):
	    return False
	askVar = self.filterDic[tick.vtSymbol]['ask'][-1]*10 / sum(self.filterDic[tick.vtSymbol]['ask'][:-1]) - 1
	bidVar = self.filterDic[tick.vtSymbol]['bid'][-1]*10 / sum(self.filterDic[tick.vtSymbol]['bid'][:-1]) - 1 
	if abs(askVar)  >= self.var/100 :
	    return False
	if abs(bidVar) >= self.var/100 :
	    return False
	return True

    def doFilter(self, tick):
	if tick.vtSymbol not in self.filterDic.keys():
	    self.filterDic[tick.vtSymbol] = {}
	    self.filterDic[tick.vtSymbol]['ask'] = []
	    self.filterDic[tick.vtSymbol]['bid'] = []
	self.filterDic[tick.vtSymbol]['ask'].append(tick.askPrice1)
	self.filterDic[tick.vtSymbol]['bid'].append(tick.bidPrice1)
	if len(self.filterDic[tick.vtSymbol]['bid']) <= 10:
	    return False
	if self.filterDic[tick.vtSymbol]['ask'][-1]*10 / sum(self.filterDic[tick.vtSymbol]['ask'][:-1]) - 1  >= self.var/100 :
	    return False
	if self.filterDic[tick.vtSymbol]['bid'][-1]*10 / sum(self.filterDic[tick.vtSymbol]['bid'][:-1]) - 1  >= self.var/100 :
	    return False
	self.filterDic[tick.vtSymbol]['bid'].pop(0)
	self.filterDic[tick.vtSymbol]['ask'].pop(0)
	return True

#----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""

        #计算基础变量macd，pbx .by hw
        vtsymbol=bar.vtSymbol
        if vtsymbol in self.closelist.keys():
            l=self.closelist[vtsymbol]
        else:
            l=[]
            self.closelist[vtsymbol]=l

        l.append(bar.close)           
        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder

        #self.postoday[trade.vtSymbol]=self.postoday[trade.vtSymbol]+self.tradestate[trade.vtSymbol]
        #self.tradestate[trade.vtSymbol]=0
        print 'trade',trade.vtSymbol,self.postoday[trade.vtSymbol],self.tradestate[trade.vtSymbol]

        all_text = "trade: " + trade.vtSymbol 
        title = u"策略 " + self.className + u' 成交信息'
        self.saveParameter()
    def loadParameter(self) :

        param = {}
        with open(self.fileName, 'r') as f:
            param = json.load(f)
	self.closeFirst = param['closeFirst']
        self.stpProfit = param["stpProfit"]
        self.slippage = param["slippage"]
        self.buyPrice = param["buyPrice"]
        self.postoday = param["postoday"]
        self.shortBuyUnit = param['shortBuyUnit']
        self.longBuyUnit = param['longBuyUnit']
        self.shortPriceCoe = param['shortPriceCoe']
        self.longPriceCoe = param['longPriceCoe']
        self.receivers = param['receivers']
	self.stopTime = param['stoptime']
	self.isFilter = param['isFilter']
	if self.isFilter == True:
	    self.var = param['var']
    def saveParameter(self) :

        param = {}
	param['closeFirst'] = self.closeFirst
        param["stpProfit"] = self.stpProfit
        param["slippage"] = self.slippage
        param["buyPrice"] = self.buyPrice
        param["postoday"] = self.postoday
        param['shortBuyUnit'] = self.shortBuyUnit
        param['longBuyUnit'] = self.longBuyUnit
        param['shortPriceCoe'] = self.shortPriceCoe
        param['longPriceCoe'] = self.longPriceCoe
        param['receivers'] = self.receivers
	param['stoptime'] = self.stopTime
	param['isFilter'] = self.isFilter
	if param['isFilter'] == True:
	    param['var'] = self.var
	d1 = json.dumps(param,sort_keys=True,indent=4)
        with open(self.fileName, "w") as f:
            f.write(d1)
	    f.close()
########################################################################################
class ParamWindow3(QtGui.QMainWindow):
    def __init__(self,name=None, longsymbol=None, shortsymbol=None,CtaEngineManager=None):
	super(ParamWindow3,self).__init__()
	self.resize(350, 480)
	self.shortsymbol = shortsymbol
	self.longsymbol = longsymbol
	self.ce = CtaEngineManager
	self.saveButton = QtGui.QPushButton(u"保存",self)
	self.cancelButton = QtGui.QPushButton(u"取消",self)
	self.setWindowTitle(u"参数")
	self.setting = {}
	self.paramters = {}
	self.strategyName = ""
	self.name = name
	self.firstSave = True
	self.fileName = ""
	if name != "":
	    self.fileName = "parameter_" + name + ".json"
	self.center()
	self.onInit()

    def onInit(self):
	self.saveButton.resize(50, 27)
	self.cancelButton.resize(50, 27)
	self.saveButton.move(220,450)
	self.cancelButton.move(280,450)
	self.saveButton.clicked.connect(self.saveParameter)
	self.cancelButton.clicked.connect(self.cancel) 
	self.initLabel()
	self.paramters = self.loadParameter()
	if self.fileName != "":
	    self.showParam()

    def initLabel(self):
	if self.name == "":
	    strategyname_label = QtGui.QLabel(u"策略名",self)
	    strategyname_label.setGeometry(QtCore.QRect(25,25,70,22))
	    self.strategyname_label = QtGui.QLineEdit(self)
	    self.strategyname_label.setGeometry(QtCore.QRect(120,25,70,22))

	self.closeFirst = QtGui.QCheckBox(u'平仓优先',self)
	self.closeFirst.setGeometry(QtCore.QRect(210,25,90,22))

	label_longsymbol = QtGui.QLabel(u"多方向合约",self)
	label_longsymbol.setGeometry(QtCore.QRect(25,50,70,22))
	self.lineEdit_label_longsymbol = QtGui.QLineEdit(self)
	self.lineEdit_label_longsymbol.setGeometry(QtCore.QRect(120,50,70,22))

	label_longBuyUnit = QtGui.QLabel(u"每笔数量",self)
	label_longBuyUnit.setGeometry(QtCore.QRect(50,75,50,22))
	self.lineEdit_label_longBuyUnit = QtGui.QLineEdit(self)
	self.lineEdit_label_longBuyUnit.setGeometry(QtCore.QRect(120,75,70,22))

	label_longPriceCoe = QtGui.QLabel(u"价格系数",self)
	label_longPriceCoe.setGeometry(QtCore.QRect(50,100,50,22))
	self.lineEdit_label_longPriceCoe = QtGui.QLineEdit(self)
	self.lineEdit_label_longPriceCoe.setGeometry(QtCore.QRect(120,100,70,22))

	label_longPosition = QtGui.QLabel(u"当前持仓量", self)
	label_longPosition.setGeometry(QtCore.QRect(50,125,50,22))
	self.lineEdit_label_longPosition = QtGui.QLineEdit(self)
	self.lineEdit_label_longPosition.setGeometry(QtCore.QRect(120,125,70,22))

	label_shortsymbol = QtGui.QLabel(u"空方向合约", self)
	label_shortsymbol.setGeometry(QtCore.QRect(25,150,70,22))
	self.lineEdit_label_shortsymbol = QtGui.QLineEdit(self)
	self.lineEdit_label_shortsymbol.setGeometry(QtCore.QRect(120,150,70,22))

	label_shortBuyUnit = QtGui.QLabel(u"每笔数量", self)
	label_shortBuyUnit.setGeometry(QtCore.QRect(50,175,50,22))
	self.lineEdit_label_shortBuyUnit = QtGui.QLineEdit(self)
	self.lineEdit_label_shortBuyUnit.setGeometry(QtCore.QRect(120,175,70,22))

	label_shortPriceCoe = QtGui.QLabel(u"价格系数", self)
	label_shortPriceCoe.setGeometry(QtCore.QRect(50,200,50,22))
	self.lineEdit_label_shortPriceCoe = QtGui.QLineEdit(self)
	self.lineEdit_label_shortPriceCoe.setGeometry(QtCore.QRect(120,200,70,22))

	label_shortPosition = QtGui.QLabel(u"当前持仓量", self)
	label_shortPosition.setGeometry(QtCore.QRect(50,225,50,22))
	self.lineEdit_label_shortPosition = QtGui.QLineEdit(self)
	self.lineEdit_label_shortPosition.setGeometry(QtCore.QRect(120,225,70,22))

	label_stpProfit = QtGui.QLabel(u"止赢", self)
	label_stpProfit.setGeometry(QtCore.QRect(25,250,50,22))
	self.lineEdit_label_stpProfit = QtGui.QLineEdit(self)
	self.lineEdit_label_stpProfit.setGeometry(QtCore.QRect(120,250,70,22))

	label_slippage = QtGui.QLabel(u"滑点", self)
	label_slippage.setGeometry(QtCore.QRect(210,250,50,22))
	self.lineEdit_label_slippage = QtGui.QLineEdit(self)
	self.lineEdit_label_slippage.setGeometry(QtCore.QRect(240,250,70,22))

	label_mail = QtGui.QLabel(u"邮箱", self)
	label_mail.setGeometry(QtCore.QRect(25,300,50,22))
	self.lineEdit_label_mail = QtGui.QLineEdit(self)
	self.lineEdit_label_mail.setGeometry(QtCore.QRect(120,300,200,22))

	label_buyPrice = QtGui.QLabel(u"开仓价差", self)
	label_buyPrice.setGeometry(QtCore.QRect(25,325,50,22))
	self.lineEdit_label_buyPrice = QtGui.QLineEdit(self)
	self.lineEdit_label_buyPrice.setGeometry(QtCore.QRect(120,325,200,22))

	label_stoptime = QtGui.QLabel(u"停止时间", self)
	label_stoptime.setGeometry(QtCore.QRect(25,350,50,22))
	self.lineEdit_label_stoptime = QtGui.QLineEdit(self)
	self.lineEdit_label_stoptime.setGeometry(QtCore.QRect(120,350,200,22))

	self.isFilter = QtGui.QCheckBox(u'当波动大于', self)
	self.isFilter.setGeometry(QtCore.QRect(25,275,150,22))
	self.lineEdit_label_var = QtGui.QLineEdit(self)
	self.lineEdit_label_var.setGeometry(QtCore.QRect(120,275,20,22))
	label_pct = QtGui.QLabel(u'% 时忽略',self)
	label_pct.setGeometry(QtCore.QRect(141,275,80,22))


    def center(self):
	screen = QtGui.QDesktopWidget().screenGeometry()
	size = self.geometry()
	self.move((screen.width() - size.width())/2, (screen.height() - size.height())/2)

    def showParam(self):
	self.lineEdit_label_longsymbol.setText(self.longsymbol)
	self.lineEdit_label_longBuyUnit.setText(str(self.paramters["longBuyUnit"]))
	self.lineEdit_label_longPriceCoe.setText(str(self.paramters["longPriceCoe"]))
	self.lineEdit_label_longPosition.setText(str(self.paramters["postoday"][self.longsymbol]))
	self.lineEdit_label_shortsymbol.setText(self.shortsymbol)
	self.lineEdit_label_shortBuyUnit.setText(str(self.paramters["shortBuyUnit"]))
	self.lineEdit_label_shortPriceCoe.setText(str(self.paramters["shortPriceCoe"]))
	self.lineEdit_label_shortPosition.setText(str(self.paramters["postoday"][self.shortsymbol]))
	self.lineEdit_label_stpProfit.setText(str(self.paramters["stpProfit"]))
	self.lineEdit_label_slippage.setText(str(self.paramters["slippage"]))
	self.lineEdit_label_stoptime.setText(str(self.paramters["stoptime"]))

	if self.paramters['closeFirst'] == True:
	    self.closeFirst.setChecked(True)
	else :
	    self.closeFirst.setChecked(False)

	if self.paramters['isFilter'] == True:
	    self.isFilter.setChecked(True)
	else :
	    self.isFilter.setChecked(False)

	rec = ""
	for x in self.paramters["receivers"]:
	    rec += x
	    rec += ","
	rec = rec[:-1]
	self.lineEdit_label_mail.setText(rec)
	bp = ""
	for x in self.paramters["buyPrice"]:
	    bp += str(x)
	    bp += ','
	bp = bp[:-1]
	self.lineEdit_label_buyPrice.setText(bp)
	

    def cancel(self):

	self.showParam()

    def loadParameter(self) :
	param = {}
	if self.fileName == "":
	    return param
	with open(self.fileName, 'r') as f:
	    param = json.load(f)
	return param

    def saveParameter(self) :
	
	param = {}
	try :
	    param["stpProfit"] = int(self.lineEdit_label_stpProfit.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'止赢应该是一个数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	    return
	try:	
	    param["slippage"] = int(self.lineEdit_label_slippage.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'滑点应该是一个数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	    return
	bp = []
	m = ""
	try:
	    for x in self.lineEdit_label_buyPrice.text():
	        if x == ',':
		    bp.append(int(m))
		    m = ''
		    continue
	        m += str(x)
	    bp.append(int(m))
	except Exception, e:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'开仓价应是用英文逗号分隔的一组数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	    return
	param["buyPrice"] = bp
	pos = {}
	if self.lineEdit_label_longsymbol.text() == '':
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写longsymbol！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return
	else :
	    self.longsymbol = str(self.lineEdit_label_longsymbol.text())

	if self.lineEdit_label_shortsymbol.text() == '':
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写shortsymbol！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return
	else :
	    self.shortsymbol = str(self.lineEdit_label_shortsymbol.text())

	try:
	    pos[self.longsymbol] = int(self.lineEdit_label_longPosition.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写longsymbol的持仓！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return

	try:
	    pos[self.shortsymbol] = int(self.lineEdit_label_shortPosition.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写shortsymbol的持仓！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return
	try:
	    param['shortBuyUnit'] = int(self.lineEdit_label_shortBuyUnit.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写shortsymbol开仓手数！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return
	try:
	    param['longBuyUnit'] = int(self.lineEdit_label_longBuyUnit.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写longsymbol的开仓手数！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return
	try:
	    param['shortPriceCoe'] = int(self.lineEdit_label_shortPriceCoe.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写shortsymbol的系数！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return
	try:
	    param['longPriceCoe'] = int(self.lineEdit_label_longPriceCoe.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写longsymbol的系数！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return
	self.paramters = self.loadParameter()
	param["postoday"] = pos
	if self.closeFirst.isChecked():
	    param['closeFirst'] = True
	else :
	    param['closeFirst'] = False

	if self.isFilter.isChecked():
	    param['isFilter'] = True
	else :
	    param['isFilter'] = False
	if self.isFilter.isChecked():
	    try :
	        param["var"] = int(self.lineEdit_label_var.text())
	    except ValueError:
	        reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'波动率应该是一个数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	        return

	stpTime = str(self.lineEdit_label_stoptime.text())
	if stpTime == "":
	    param['stoptime'] = '9999'
	else :
	    param['stoptime'] = stpTime
	rec = []
	m = ""
	for x in str(self.lineEdit_label_mail.text()):
	    if x == ',':
		rec.append(m)
		m = ""
		continue
	    m += x
	if m != '':
	    rec.append(m)
	param['receivers'] = rec
	if self.name == "" and self.firstSave:
	    if self.strategyname_label.text() == '':
	        reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'策略名不能为空！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
		return
	    else :
	        self.strategyName = self.strategyname_label.text()
	    self.fileName = "parameter_" + self.strategyName + ".json"
	    with open(self.fileName, 'a') as f:
		f.write("{}")
		f.close()
	self.paramters = param
	d1 = json.dumps(param,sort_keys=True,indent=4)

	with open(self.fileName, "w") as f:
	    
	    f.write(d1)
	    f.close()
	self.setting['name'] = str(self.strategyName)
	self.setting['className'] = 'CtpAndIB'
	self.setting['vtSymbol'] = self.longsymbol + ',' + self.shortsymbol
	self.setting['longSymbol'] = self.longsymbol
	self.setting['shortSymbol'] = self.shortsymbol
	if self.name == "" and self.firstSave :
	    self.ce.ctaEngine.addStrategy(self.setting,self.strategyName)
	    self.firstSave = False
