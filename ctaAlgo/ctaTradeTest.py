# encoding: UTF-8

"""
这里的Demo是一个最简单的策略实现，并未考虑太多实盘中的交易细节，如：
1. 委托价格超出涨跌停价导致的委托失败
2. 委托未成交，需要撤单后重新委托
3. 断网后恢复交易状态
4. 等等
这些点是作者选择特意忽略不去实现，因此想实盘的朋友请自己多多研究CTA交易的一些细节，
做到了然于胸后再去交易，对自己的money和时间负责。
也希望社区能做出一个解决了以上潜在风险的Demo出来。
"""

import json
from ctaBase import *
from ctaTemplate import CtaTemplate
import smtplib
from uiBasicWidget import *
import re
import numpy as np
import datetime
########################################################################
class tradeTest(CtaTemplate):
    """策略"""
    className = 'tradeTest'
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
    tradeid=EMPTY_STRING
    cdnum=0
    
#以下代码更新于2016/11/21==================


    longsymbolAskPrice = 0
    longsymbolBidPrice = 0
    shortsymbolAskPrice = 0
    shortsymbolBidPrice = 0	

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
    def __init__(self, ctaEngine, setting,fileName):
	self.fileName = fileName
	self.filterDic = {}
        """Constructor"""
        super(tradeTest, self).__init__(ctaEngine, setting)
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
	self.isStart = False
        self.dfr = 0
        self.dfr_2 = 0
	self.longCheckList = []
	self.shortCheckList = []
	self.second = -1
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
	self.isStart = True
        self.loadParameter()
	self.loadPosInfo()
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'策略启动')
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
	self.isSatrt = False
	self.filterDic = {}
	self.loadPosInfo()
        self.saveParameter()
        """停止策略（必须由用户继承实现）"""
	log = self.name + u'策略停止'
        self.writeCtaLog(log)
        self.putEvent()
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        self.lastOrder=order


    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        # 计算K线
	
	if not self.isTrade():
	    return
	if self.isFilter :
	    if not self.doFilter(tick) :
		return
	now = datetime.datetime.now()
	if self.second != now.second:
	    self.second = now.second
	    self.longCheckList = []
	    self.shortCheckList = []


#2016/11/21=============================================================
        if tick.vtSymbol==self.shortsymbol :
            self.shortsymbolAskPrice = tick.askPrice1
            self.shortsymbolBidPrice = tick.bidPrice1
        else :
            self.longsymbolAskPrice = tick.askPrice1
            self.longsymbolBidPrice = tick.bidPrice1
        self.dfr = self.shortsymbolBidPrice*self.shortPriceCoe - self.longsymbolAskPrice*self.longPriceCoe        
        self.dfr_2 = self.shortsymbolAskPrice*self.shortPriceCoe - self.longsymbolBidPrice*self.longPriceCoe
	if not self.isStart:
	    self.putEvent()
	    return
	if tick.askPrice1 == tick.lowerLimit or tick.bidPrice1 == tick.upperLimit:
	    return 
        if self.shortsymbolAskPrice!=0 and self.longsymbolAskPrice!=0 and self.shortsymbolBidPrice!=0 and self.longsymbolBidPrice!=0:
            for i in range(0,len(self.buyPrice)):
	        if self.buyPrice[i] <= self.dfr and self.postoday[self.shortsymbol]<(i+1)*self.shortBuyUnit :
		    if i in self.shortCheckList:
			logs = u'策略' + self.name + u'在1秒内重复开单 ' + self.shortsymbol + u'停止运行！'
			self.isStart = False
			self.writeCtaLog(logs)
			return
		    else :
			self.shortCheckList.append(i)
		    tradeId = self.short(self.shortsymbolBidPrice-self.slippage, self.shortBuyUnit, self.shortsymbol)
		    
		    self.postoday[self.shortsymbol] += self.shortBuyUnit
		    self.saveParameter()
		if self.buyPrice[i] <= self.dfr and self.postoday[self.longsymbol]<(i+1)*self.longBuyUnit :
		    if i in self.longCheckList:
			logs = u'策略' + self.name + u'在1秒内重复开单 ' + self.longsymbol + u'停止运行！'
			self.isStart = False
			self.writeCtaLog(logs)
			return
		    else :
			self.longCheckList.append(i)
		    tradeId = self.buy(self.longsymbolAskPrice+self.slippage, self.longBuyUnit, self.longsymbol)
		    
		    self.postoday[self.longsymbol] += self.longBuyUnit
		    self.saveParameter()
	        if self.dfr_2 <= self.buyPrice[i] - self.stpProfit and self.postoday[self.shortsymbol]> i*self.shortBuyUnit :
		    if i in self.shortCheckList:
			logs = u'策略' + self.name + u'在1秒内重复开单 ' + self.shortsymbol + u'停止运行！'
			self.isStart = False
			self.writeCtaLog(logs)
			return
		    else :
			self.shortCheckList.append(i)	
		    tradeId = self.cover(self.shortsymbolAskPrice+self.slippage, self.shortBuyUnit, self.shortsymbol)
		    
		    self.postoday[self.shortsymbol] -= self.shortBuyUnit
		    self.saveParameter()
		if self.dfr_2 <= self.buyPrice[i] - self.stpProfit and self.postoday[self.longsymbol]> i*self.longBuyUnit :
		    if i in self.longCheckList:
			logs = u'策略' + self.name + u'在1秒内重复开单 ' + self.longsymbol + u'停止运行！'
			self.isStart = False
			self.writeCtaLog(logs)
			return
		    else :
			self.longCheckList.append(i)
		    tradeId = self.sell(self.longsymbolBidPrice-self.slippage, self.longBuyUnit, self.longsymbol)
		    
		    self.postoday[self.longsymbol] -= self.longBuyUnit
		    self.saveParameter()
        self.putEvent()

    def isTrade(self):
	
	h = datetime.datetime.now().hour
	m = datetime.datetime.now().minute
	for x in self.tradeTime.keys():
	    start = x.split(':')
	    end = self.tradeTime[x].split(':')
	    if h > int(start[0]) and h < int(end[0]) :
		return True
	    elif h == int(start[0]):
		if int(start[0]) != int(end[0]) :
		    if m >= int(start[1]) :
			return True
		elif  m >= int(start[1]) and m <= int(end[1]) :
		    return True
	    elif h == int(end[0]):
		if int(start[0]) != int(end[0]):
		    if m <= int(end[1]):
			return True
		elif  m >= int(start[1]) and m <= int(end[1]) :
		    return True
	return False


    def doFilter(self, tick):
	if tick.vtSymbol not in self.filterDic.keys():
	    self.filterDic[tick.vtSymbol] = {'ask':[], 'bid':[]}
	self.filterDic[tick.vtSymbol]['ask'].append(tick.askPrice1)
	self.filterDic[tick.vtSymbol]['bid'].append(tick.bidPrice1)

	if len(self.filterDic[tick.vtSymbol]['bid']) <= 10:
	    return False
	askVar = self.filterDic[tick.vtSymbol]['ask'][-1]*10 / sum(self.filterDic[tick.vtSymbol]['ask'][:-1]) - 1
	bidVar = self.filterDic[tick.vtSymbol]['bid'][-1]*10 / sum(self.filterDic[tick.vtSymbol]['bid'][:-1]) - 1 
	if abs(askVar)  >= self.var/100 :
	    return False
	if abs(bidVar) >= self.var/100 :
	    return False
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
	self.tradeTime = param['tradeTime']
	self.isFilter = param['isFilter']
	if self.isFilter == True:
	    self.var = param['var']
    def saveParameter(self) :
	if not self.isStart:
	    return
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
	param['tradeTime'] = self.tradeTime
	param['isFilter'] = self.isFilter
	if param['isFilter'] == True:
	    param['var'] = self.var
	d1 = json.dumps(param,sort_keys=True,indent=4)
        with open(self.fileName, "w") as f:
            f.write(d1)
	    f.close()

########################################################################################
class ParamWindow(QtGui.QWidget):
    def __init__(self,name=None, longsymbol=None, shortsymbol=None,CtaEngineManager=None):
	super(ParamWindow,self).__init__()
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
	self.saveButton.clicked.connect(self.saveParameter)
	self.cancelButton.clicked.connect(self.cancel) 
	self.initLabel()
	self.paramters = self.loadParameter()
	if self.fileName != "":
	    self.showParam()

    def initLabel(self):
	layout = QtGui.QGridLayout()
	layout.setSpacing(4)
	for j in range(0,9):
	    layout.addWidget(QtGui.QLabel("    ",self),0,j)
	for i in range(0,16):
	    layout.addWidget(QtGui.QLabel(" ",self),i,0)
	if self.name == "":
	    strategyname_label = QtGui.QLabel(u"策略名",self)
	    self.strategyname_label = QtGui.QLineEdit(self)
	    layout.addWidget(strategyname_label,0,0)
	    layout.addWidget(self.strategyname_label,0,1,1,3)
	
	self.closeFirst = QtGui.QCheckBox(u'平仓优先',self)
	layout.addWidget(self.closeFirst,0,5,1,7)
	label_longsymbol = QtGui.QLabel(u"多方向合约",self)
	self.lineEdit_label_longsymbol = QtGui.QLineEdit(self)
	layout.addWidget(self.lineEdit_label_longsymbol,1,1,1,3)
	layout.addWidget(label_longsymbol,1,0)
 
	label_longBuyUnit = QtGui.QLabel(u"    每笔数量",self)
	self.lineEdit_label_longBuyUnit = QtGui.QLineEdit(self)
	layout.addWidget(label_longBuyUnit,2,0)
	layout.addWidget(self.lineEdit_label_longBuyUnit,2,1,1,3)

	label_longPriceCoe = QtGui.QLabel(u"    价格系数",self)
	self.lineEdit_label_longPriceCoe = QtGui.QLineEdit(self)
	layout.addWidget(label_longPriceCoe,3,0)
	layout.addWidget(self.lineEdit_label_longPriceCoe,3,1,1,3)

	label_longPosition = QtGui.QLabel(u"    当前持仓", self)
	self.lineEdit_label_longPosition = QtGui.QLineEdit(self)
	layout.addWidget(label_longPosition,4,0)
	layout.addWidget(self.lineEdit_label_longPosition,4,1,1,3)

	label_shortsymbol = QtGui.QLabel(u"空方向合约", self)
	self.lineEdit_label_shortsymbol = QtGui.QLineEdit(self)
	layout.addWidget(label_shortsymbol,5,0)
	layout.addWidget(self.lineEdit_label_shortsymbol,5,1,1,3)

	label_shortBuyUnit = QtGui.QLabel(u"    每笔数量", self)
	self.lineEdit_label_shortBuyUnit = QtGui.QLineEdit(self)
	layout.addWidget(label_shortBuyUnit,6,0)
	layout.addWidget(self.lineEdit_label_shortBuyUnit,6,1,1,3)

	label_shortPriceCoe = QtGui.QLabel(u"    价格系数", self)
	self.lineEdit_label_shortPriceCoe = QtGui.QLineEdit(self)
	self.lineEdit_label_shortPriceCoe.resize(75,22)
	layout.addWidget(label_shortPriceCoe,7,0)
	layout.addWidget(self.lineEdit_label_shortPriceCoe,7,1,1,3)

	label_shortPosition = QtGui.QLabel(u"   当前持仓", self)
	self.lineEdit_label_shortPosition = QtGui.QLineEdit(self)
	layout.addWidget(label_shortPosition,8,0)
	layout.addWidget(self.lineEdit_label_shortPosition,8,1,1,3)

	label_stpProfit = QtGui.QLabel(u"止赢", self)
	self.lineEdit_label_stpProfit = QtGui.QLineEdit(self)
	layout.addWidget(label_stpProfit,9,0)
	layout.addWidget(self.lineEdit_label_stpProfit,9,1,1,3)


	label_slippage = QtGui.QLabel(u"滑点", self)
	self.lineEdit_label_slippage = QtGui.QLineEdit(self)
	layout.addWidget(label_slippage,9,5,1,1)
	layout.addWidget(self.lineEdit_label_slippage,9,7,1,2)

	self.isFilter = QtGui.QCheckBox(u'波动', self)
	self.lineEdit_label_var = QtGui.QLineEdit(self)
	layout.addWidget(self.isFilter,10,0)
	layout.addWidget(self.lineEdit_label_var,10,1,1,3)

	label_mail = QtGui.QLabel(u"邮箱", self)
	self.lineEdit_label_mail = QtGui.QLineEdit(self)
	layout.addWidget(label_mail,11,0)
	layout.addWidget(self.lineEdit_label_mail,11,1,1,8)

	label_buyPrice = QtGui.QLabel(u"开仓价差", self)
	self.lineEdit_label_buyPrice = QtGui.QLineEdit(self)
	layout.addWidget(label_buyPrice,12,0)
	layout.addWidget(self.lineEdit_label_buyPrice,12,1,1,8)

	self.tradeTimeButton = QtGui.QPushButton(u"交易时间",self)
	self.tradeTimeButton.clicked.connect(self.tradeTimeWidget)
	layout.addWidget(self.tradeTimeButton,13,0)


	layout.addWidget(self.saveButton,15,7)
	layout.addWidget(self.cancelButton,15,8)

	self.setLayout(layout)

    def tradeTimeWidget(self):
	if self.fileName == "":
	    self.saveParameter()
	self.st = strategyTimeQWidget(self)
	self.st.show()


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
	
	self.paramters = self.loadParameter()
	try :
	    self.paramters["stpProfit"] = int(self.lineEdit_label_stpProfit.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'止赢应该是一个数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	    return

	try:	
	    self.paramters["slippage"] = int(self.lineEdit_label_slippage.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'滑点应该是一个数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	    return
	bp = []
	m = ""
	try:
	    for x in self.lineEdit_label_buyPrice.text():
	        if x == ',':
		    if len(bp) > 0 and int(m) <= bp[-1]:
			reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'开仓价应是从小到大的一组数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	    		return
		    bp.append(int(m))
		    m = ''
		    continue
	        m += str(x)
	    if len(bp) > 0 and int(m) <= bp[-1]:
		reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'开仓价应是从小到大的一组数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	    	return
	    bp.append(int(m))
	except Exception, e:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'开仓价应是用英文逗号分隔的一组数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	    return
	self.paramters["buyPrice"] = bp
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
	    self.paramters['shortBuyUnit'] = int(self.lineEdit_label_shortBuyUnit.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写shortsymbol开仓手数！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return
	try:
	    self.paramters['longBuyUnit'] = int(self.lineEdit_label_longBuyUnit.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写longsymbol的开仓手数！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return
	try:
	    self.paramters['shortPriceCoe'] = int(self.lineEdit_label_shortPriceCoe.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写shortsymbol的系数！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return
	try:
	    self.paramters['longPriceCoe'] = int(self.lineEdit_label_longPriceCoe.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写longsymbol的系数！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return
	self.paramters["postoday"] = pos
	if self.closeFirst.isChecked():
	    self.paramters['closeFirst'] = True
	else :
	    self.paramters['closeFirst'] = False

	if self.isFilter.isChecked():
	    self.paramters['isFilter'] = True
	else :
	    self.paramters['isFilter'] = False
	if self.isFilter.isChecked():
	    try :
	        self.paramters["var"] = int(self.lineEdit_label_var.text())
	    except ValueError:
	        reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'波动率应该是一个数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	        return

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
	self.paramters['receivers'] = rec
	if self.name == "" and self.firstSave:
	    name = self.strategyname_label.text()
	    if re.match(r'\W', name):
	        reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'策略名应是英文字母和数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
		return
	    else :
	        self.strategyName = self.strategyname_label.text()
	    self.fileName = "parameter_" + self.strategyName + ".json"
	    with open(self.fileName, 'a') as f:
		f.write("{}")
		f.close()
	if 'tradeTime' not in self.paramters.keys():
	    self.paramters['tradeTime'] = {}
	self.saveP()

    def saveP(self):
	d1 = json.dumps(self.paramters,sort_keys=True,indent=4)

	with open(self.fileName, "w") as f:
	    
	    f.write(d1)
	    f.close()
	self.setting['name'] = str(self.strategyName)
	self.setting['className'] = 'tradeTest'
	self.setting['vtSymbol'] = self.longsymbol + ',' + self.shortsymbol
	self.setting['longSymbol'] = self.longsymbol
	self.setting['shortSymbol'] = self.shortsymbol
	if self.name == "" and self.firstSave :
	    self.ce.ctaEngine.addStrategy(self.setting,self.strategyName)
	    self.firstSave = False

class myButton(QtGui.QPushButton):

    def __init__(self, tag, name, buttonType, strategyTimeQWidget, parent):
	super(myButton, self).__init__(tag)
	self.name = str(name)
	if buttonType == 'del':
	    self.clicked.connect(self.delButtonOnClick)
	else :
	    self.clicked.connect(self.addButtonOnClick)
	self.st = strategyTimeQWidget
	self.parent = parent
    def delButtonOnClick(self):

	if str(self.name) in self.st.startTime:
	    self.st.startTime.remove(self.name)
	if self.name in self.st.timeDict.keys():
	    self.st.timeDict.pop(self.name)
	
	self.st.pw.paramters['tradeTime'] = self.st.timeDict
	d1 = json.dumps(self.st.pw.paramters,sort_keys=True,indent=4)
	with open(self.st.fileName, "w") as f:
	    
	    f.write(d1)
	    f.close()
	self.st.delTime(self.parent)

    def addButtonOnClick(self):
	start = str(self.st.hourCheckBox.currentText() +':'+ self.st.minuteCheckBox.currentText())
	end = str(self.st.hourCheckBox1.currentText() +':'+ self.st.minuteCheckBox1.currentText())
	self.st.startTime.append(start)
	self.st.timeDict[start] = end
	self.st.pw.paramters['tradeTime'] = self.st.timeDict
	d1 = json.dumps(self.st.pw.paramters,sort_keys=True,indent=4)
	with open(self.st.fileName, "w") as f:
	    
	    f.write(d1)
	    f.close()
	self.st.delTime(self.parent)
	self.st.addTime(start,end)



class strategyTimeQWidget(QtGui.QWidget):
    def __init__(self, paramWindow):
	super(strategyTimeQWidget,self).__init__()
	self.pw = paramWindow
	self.fileName = self.pw.fileName
	if 'tradeTime' in self.pw.paramters.keys():

	    self.startTime = self.pw.paramters['tradeTime'].keys()
	    self.timeDict = self.pw.paramters['tradeTime']
	else :
	    self.pw.paramters['tradeTime'] = {}
	    self.startTime = self.pw.paramters['tradeTime'].keys()
	    self.timeDict = self.pw.paramters['tradeTime']
	self.initUI()
	
    def initUI(self):
	self.resize(350, 510)
	self.center()
	self.setWindowTitle(u"交易时间")
	self.loadTime()   


    def loadTime(self):
	vbox1 = QtGui.QVBoxLayout()
	for x in self.startTime:	
	    newTable = QtGui.QTableWidget(1,3)
	    newTable.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers) 
	    newTable.setMaximumHeight(60)
	    newTable.setHorizontalHeaderLabels([u'time', u"start", u"end"])
	    delButton = myButton(u"del",str(x), 'del', self, newTable)
            newTable.setCellWidget(0,0,delButton)
            newItem = QtGui.QTableWidgetItem(str(x))  
            newTable.setItem(0, 1, newItem)
            newItem = QtGui.QTableWidgetItem(str(self.timeDict[x]))  
            newTable.setItem(0, 2, newItem)
	    vbox1.addWidget(newTable)

	self.vbox = vbox1
	self.createAddButton()
	self.setLayout(self.vbox)

    def addTime(self, start, end):
	newTable = QtGui.QTableWidget(1,3)
	newTable.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers) 
	newTable.setMaximumHeight(60)
	newTable.setHorizontalHeaderLabels([u'time', u"start", u"end"])
	delButton = myButton(u"del",str(start), 'del', self, newTable)
	newTable.setCellWidget(0,0,delButton)
	newItem = QtGui.QTableWidgetItem(start)  
	newTable.setItem(0, 1, newItem)
	newItem = QtGui.QTableWidgetItem(end)  
	newTable.setItem(0, 2, newItem)
	self.vbox.addWidget(newTable)
	self.createAddButton()


    def delTime(self,m):
	childList = self.vbox.children()
	self.vbox.removeWidget(m)
	m.setMaximumHeight(0)

    def createAddButton(self):
	self.addTable = QtGui.QTableWidget(2,3)
	self.addTable.setMaximumHeight(105)
	self.addTable.setHorizontalHeaderLabels([u'time', u"start", u"end"])
	delButton = myButton(u"add",'', 'add', self, self.addTable)
	self.addTable.setCellWidget(0,0,delButton)
	self.addTable.setSpan(0, 0, 2, 1)
	self.hourCheckBox = QtGui.QComboBox()
	self.hourCheckBox.setMaxVisibleItems(10)
	self.hourCheckBox1 = QtGui.QComboBox()
	self.hourCheckBox1.setMaxVisibleItems(10)
	for x in range(0,24):
	    self.hourCheckBox.addItem(str(x))
	    self.hourCheckBox1.addItem(str(x))
	self.addTable.setCellWidget(0,1,self.hourCheckBox)
	self.addTable.setCellWidget(0,2,self.hourCheckBox1)
	self.minuteCheckBox = QtGui.QComboBox()
	self.minuteCheckBox.setMaxVisibleItems(10)
	self.minuteCheckBox1 = QtGui.QComboBox()
	self.minuteCheckBox1.setMaxVisibleItems(10)
	for x in range(0,60):
	    self.minuteCheckBox.addItem(str(x))
	    self.minuteCheckBox1.addItem(str(x))

	self.addTable.setCellWidget(1,1,self.minuteCheckBox)
	self.addTable.setCellWidget(1,2,self.minuteCheckBox1)
	self.vbox.addWidget(self.addTable)


    #----------------------------------------------------------------------
    def createAction(self, actionName, function):
        action = QtGui.QAction(actionName, self)
        action.triggered.connect(function)
        return action


    def center(self):
	screen = QtGui.QDesktopWidget().screenGeometry()
	size = self.geometry()
	self.move((screen.width() - size.width())/2, (screen.height() - size.height())/2)






