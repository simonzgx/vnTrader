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
import numpy as np
import datetime

########################################################################
class strategyGirdTrading(CtaTemplate):
    """策略"""
    className = 'girdTrading'
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


    poslimit=1
    posstate={}
    postoday={}         #今日持仓
    tradestate={}       #交易状态
    tradeid=EMPTY_STRING
    cdnum=0
    

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol']    
    varList = [ 'inited',
                'trading',
		'buyPrice',
		'postoday',
		'curPrice']
    # 变量列表，保存了变量的名称


    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting,fileName):
	self.fileName = fileName
	self.filterDic = {}
        """Constructor"""

        super(strategyGirdTrading, self).__init__(ctaEngine, setting)
	ce = ctaEngine
	ce.doCheck()
        if setting :
            self.vtSymbol=setting['vtSymbol']
        for vts in self.vtSymbol :
            self.tradestate[vts]=0
            self.postoday[vts]=0
            self.posstate[vts]=0
	self.direction = ''
	self.loadParameter()
        self.flag = 0
	self.curPrice = 0
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
        """收到行情TICK推送（必须由用户继承实现）"""
        # 计算K线
	flag =False
	now = datetime.datetime.now()
	if now.hour >= 8 and now.hour <=11 :
	    flag = True
	    if now.hour == 11 and now.minute >= 30 :
		flag = False
	    if now.hour == 9 and now.minute <=1 :
		flag = False
	if now.hour >= 13 and now.hour <= 14:
	    flag = True
	    if now.hour ==13 and now.minute <= 30:
		flag = False
	if now.hour >=21 and now.hour <= 22:
	    flag = True
	    if now.hour == 21 and now.minute == 0 :
		flag = False 
	    if now.hour == 21 and now.minute == 1 :
	        self.loadPosInfo()
	if now.hour > int(self.stopTime[:2]):
	    flag = False
	if now.hour == int(self.stopTime[:2]) and now.minute >= int(self.stopTime[-2:]):
	    flag = False

	if self.isFilter :
	    if not self.doFilter(tick) :
		return
	if not flag:
	    return
        tickMinute = tick.datetime.minute   #by hw

	self.curPrice = tick.bidPrice1
	self.BidPrice = tick.bidPrice1
	self.AskPrice = tick.askPrice1
	if self.isStop :
	    return
	for i in range(0,len(self.buyPrice)):
	    if self.direction == 'long':
		if self.maxStpLos >= self.BidPrice :
		    tradeID = self.sell(self.BidPrice-self.slippage, self.postoday[self.vtSymbol], self.vtSymbol, self.closeFirst)
		    self.postoday[self.vtSymbol] = 0
		    self.isStop = True
		    self.saveParameter()
		    return
		if self.buyPrice[i] >= self.AskPrice and self.postoday[self.vtSymbol] <(i+1)*self.openUnit :

		    tradeID = self.buy(self.AskPrice+self.slippage, self.openUnit, self.vtSymbol, self.closeFirst)

		    self.postoday[self.vtSymbol] += self.openUnit
		    self.saveParameter()
		if self.buyPrice[i] + self.stpProfit <= self.BidPrice and self.postoday[self.vtSymbol] >(i)*self.openUnit :
		    tradeID = self.sell(self.BidPrice-self.slippage, self.openUnit, self.vtSymbol, self.closeFirst)
		    self.postoday[self.vtSymbol] -= self.openUnit
		    self.saveParameter()
	    if self.direction == 'short':
		if self.maxStpLos <= self.AskPrice :
		    tradeID = self.cover(self.AskPrice+self.slippage, self.postoday[self.vtSymbol], self.vtSymbol, self.closeFirst)
		    self.postoday[self.vtSymbol] = 0
		    self.isStop = True
		    self.saveParameter()
		    return
		if self.buyPrice[i] <= self.BidPrice and self.postoday[self.vtSymbol] <(i+1)*self.openUnit :
		    tradeID = self.short(self.BidPrice-self.slippage, self.openUnit, self.vtSymbol, self.closeFirst)
		    self.postoday[self.vtSymbol] += self.openUnit
		    self.saveParameter()
		if self.buyPrice[i] - self.stpProfit >= self.AskPrice and self.postoday[self.vtSymbol] >(i)*self.openUnit :
		    tradeID = self.cover(self.AskPrice+self.slippage, self.openUnit, self.vtSymbol, self.closeFirst)
		    self.postoday[self.vtSymbol] -= self.openUnit
		    self.saveParameter()
	self.putEvent()

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
        #print 'trade',trade.vtSymbol,self.postoday[trade.vtSymbol],self.tradestate[trade.vtSymbol]
        self.saveParameter()
    def loadParameter(self) :

        param = {}
        with open(self.fileName, 'r') as f:
            param = json.load(f)
        self.stpProfit = param["stpProfit"]
        self.slippage = param["slippage"]
        self.buyPrice = param["buyPrice"]
        self.postoday = param["postoday"]
	self.closeFirst = param['closeFirst']
        self.openUnit = param['openUnit']
	self.direction = param['direction']
        self.PriceCoe = param['PriceCoe']
        self.receivers = param['receivers']
	self.stopTime = param['stoptime']
	self.isStop = param['isStop']
	self.isFilter = param['isFilter']
	self.maxStpLos = param['maxStpLos']
	if self.isFilter == True:
	    self.var = param['var']
	
    def saveParameter(self) :

        param = {}
	param['closeFirst'] = self.closeFirst
        param["stpProfit"] = self.stpProfit
        param["slippage"] = self.slippage
        param["buyPrice"] = self.buyPrice
        param["postoday"] = self.postoday
        param['openUnit'] = self.openUnit
	param['direction'] = self.direction
        param['PriceCoe'] = self.PriceCoe
        param['receivers'] = self.receivers
	param['stoptime'] = self.stopTime
	param['isStop'] = self.isStop
	param['isFilter'] = self.isFilter
	param['maxStpLos'] = self.maxStpLos
 	if param['isFilter'] == True:
	    param['var'] = self.var
	d1 = json.dumps(param,sort_keys=True,indent=4)
        with open(self.fileName, "w") as f:
 
            f.write(d1)
	    f.close()
########################################################################################
class ParamWindow2(QtGui.QDialog):

    def __init__(self,name=None, direction=None, vtSymbol=None, CtaEngineManager=None):
	super(ParamWindow2,self).__init__()
	self.resize(350, 480)
	self.ce = CtaEngineManager
	self.saveButton = QtGui.QPushButton(u"保存",self)
	self.cancelButton = QtGui.QPushButton(u"取消",self)
	self.setWindowTitle(u"参数")
	self.vtSymbol = vtSymbol
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

	label_symbol = QtGui.QLabel(u"合约",self)
	label_symbol.setGeometry(QtCore.QRect(25,50,70,22))
	self.lineEdit_label_symbol = QtGui.QLineEdit(self)
	self.lineEdit_label_symbol.setGeometry(QtCore.QRect(120,50,70,22))

	symbolDirection = QtGui.QLabel(u"方向",self)
	symbolDirection.setGeometry(QtCore.QRect(210,50,70,22))
	self.directionCombo = QtGui.QComboBox(self)
	self.directionCombo.addItem("")
	self.directionCombo.addItem("long")
	self.directionCombo.addItem('short')
	self.directionCombo.setGeometry(QtCore.QRect(245,50,50,22))

	label_longBuyUnit = QtGui.QLabel(u"每笔数量",self)
	label_longBuyUnit.setGeometry(QtCore.QRect(25,75,50,22))
	self.lineEdit_label_longBuyUnit = QtGui.QLineEdit(self)
	self.lineEdit_label_longBuyUnit.setGeometry(QtCore.QRect(120,75,70,22))

	maxStpLos = QtGui.QLabel(u'止损', self)
	maxStpLos.setGeometry(QtCore.QRect(210,75,70,22))
	self.lineEdit_label_maxStpLos = QtGui.QLineEdit(self)
	self.lineEdit_label_maxStpLos.setGeometry(QtCore.QRect(245,75,60,22))

	label_longPriceCoe = QtGui.QLabel(u"价格系数",self)
	label_longPriceCoe.setGeometry(QtCore.QRect(25,100,50,22))
	self.lineEdit_label_longPriceCoe = QtGui.QLineEdit(self)
	self.lineEdit_label_longPriceCoe.setGeometry(QtCore.QRect(120,100,70,22))

	label_longPosition = QtGui.QLabel(u"当前持仓量", self)
	label_longPosition.setGeometry(QtCore.QRect(25,125,50,22))
	self.lineEdit_label_longPosition = QtGui.QLineEdit(self)
	self.lineEdit_label_longPosition.setGeometry(QtCore.QRect(120,125,70,22))


	label_stpProfit = QtGui.QLabel(u"止赢", self)
	label_stpProfit.setGeometry(QtCore.QRect(25,150,50,22))
	self.lineEdit_label_stpProfit = QtGui.QLineEdit(self)
	self.lineEdit_label_stpProfit.setGeometry(QtCore.QRect(120,150,70,22))

	label_slippage = QtGui.QLabel(u"滑点", self)
	label_slippage.setGeometry(QtCore.QRect(25,175,50,22))
	self.lineEdit_label_slippage = QtGui.QLineEdit(self)
	self.lineEdit_label_slippage.setGeometry(QtCore.QRect(120,175,70,22))

	label_mail = QtGui.QLabel(u"邮箱", self)
	label_mail.setGeometry(QtCore.QRect(25,200,50,22))
	self.lineEdit_label_mail = QtGui.QLineEdit(self)
	self.lineEdit_label_mail.setGeometry(QtCore.QRect(120,200,200,22))

	label_buyPrice = QtGui.QLabel(u"开仓价差", self)
	label_buyPrice.setGeometry(QtCore.QRect(25,225,50,22))
	self.lineEdit_label_buyPrice = QtGui.QLineEdit(self)
	self.lineEdit_label_buyPrice.setGeometry(QtCore.QRect(120,225,200,22))

	label_stoptime = QtGui.QLabel(u"停止时间", self)
	label_stoptime.setGeometry(QtCore.QRect(25,250,50,22))
	self.lineEdit_label_stoptime = QtGui.QLineEdit(self)
	self.lineEdit_label_stoptime.setGeometry(QtCore.QRect(120,250,200,22))

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
	self.lineEdit_label_symbol.setText(self.vtSymbol)
	self.lineEdit_label_longBuyUnit.setText(str(self.paramters["openUnit"]))
	self.lineEdit_label_longPriceCoe.setText(str(self.paramters["PriceCoe"]))
	self.lineEdit_label_longPosition.setText(str(self.paramters["postoday"][self.vtSymbol]))
	self.lineEdit_label_stpProfit.setText(str(self.paramters["stpProfit"]))
	self.lineEdit_label_slippage.setText(str(self.paramters["slippage"]))
	self.lineEdit_label_stoptime.setText(str(self.paramters["stoptime"]))
	self.lineEdit_label_maxStpLos.setText(str(self.paramters["maxStpLos"]))
	if self.paramters['direction'] =='long':
	    self.directionCombo.setCurrentIndex(1)
	else :
	    self.directionCombo.setCurrentIndex(2)

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

	self.vtSymbol = str(self.lineEdit_label_symbol.text())
	if self.lineEdit_label_symbol.text() == '':
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写longsymbol！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return
	else :
	    self.vtSymbol = str(self.lineEdit_label_symbol.text())

	try:
	    pos[self.vtSymbol] = int(self.lineEdit_label_longPosition.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写symbol的持仓！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
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

	try:
	    param['maxStpLos'] = int(self.lineEdit_label_maxStpLos.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'止损应该是一个数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return

	try:
	    param['openUnit'] = int(self.lineEdit_label_longBuyUnit.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写symbol开仓手数！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return


	try:
	    param['PriceCoe'] = int(self.lineEdit_label_longPriceCoe.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写symbol的系数！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
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
	if str(self.directionCombo.currentText()) == '':
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请选择交易方向！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	    return
	else :
	    param['direction'] = str(self.directionCombo.currentText())

	param['receivers'] = rec
	if self.name == "" and self.firstSave:
	    if self.strategyname_label.text() == '':
	        reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'策略名不能为空！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
		return
	    else :
	        self.strategyName = self.strategyname_label.text()
	    self.fileName = "parameter_" + self.strategyName + ".json"
	    param['isStop'] = False
	    with open(self.fileName, 'a') as f:
		f.write("{}")
		f.close()
	param['isStop'] = False
	self.paramters = param
	d1 = json.dumps(param,sort_keys=True,indent=4)
	with open(self.fileName, "w") as f:
	    f.write(d1)
	    f.close()
	self.setting['name'] = str(self.strategyName)
	self.setting['className'] = 'theGirdTrading'
	self.setting['vtSymbol'] = self.vtSymbol

	if self.name == "" and self.firstSave :
	    self.ce.ctaEngine.addStrategy(self.setting,self.strategyName)
	    self.firstSave = False
























