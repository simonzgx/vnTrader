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
import re
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
	if self.isFilter :
	    if not self.doFilter(tick) :
		return
        tickMinute = tick.datetime.minute   #by hw

	self.curPrice = tick.bidPrice1
	self.BidPrice = tick.bidPrice1
	self.AskPrice = tick.askPrice1
	if not self.isTrade():
	    return
	if tick.askPrice1 == tick.lowerLimit or tick.bidPrice1 == tick.upperLimit:
	    return 
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
        self.receivers = param['receivers']
	self.tradeTime = param['tradeTime']
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
        param['receivers'] = self.receivers
	param['tradeTime'] = self.tradeTime
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
class ParamWindow2(QtGui.QWidget):

    def __init__(self,name=None, direction=None, vtSymbol=None, CtaEngineManager=None):
	super(ParamWindow2,self).__init__()
	self.resize(365, 500)
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

	label_symbol = QtGui.QLabel(u"合约",self)
	self.lineEdit_label_symbol = QtGui.QLineEdit(self)
	layout.addWidget(self.lineEdit_label_symbol,1,1,1,3)
	layout.addWidget(label_symbol,1,0)

	symbolDirection = QtGui.QLabel(u"方向",self)
	self.directionCombo = QtGui.QComboBox(self)
	self.directionCombo.addItem("")
	self.directionCombo.addItem("long")
	self.directionCombo.addItem('short')
	layout.addWidget(symbolDirection,1,5,1,1)
	layout.addWidget(self.directionCombo,1,7,1,2)

	label_longBuyUnit = QtGui.QLabel(u"每笔数量",self)
	self.lineEdit_label_longBuyUnit = QtGui.QLineEdit(self)
	layout.addWidget(label_longBuyUnit,2,0)
	layout.addWidget(self.lineEdit_label_longBuyUnit,2,1,1,3)

	label_longPosition = QtGui.QLabel(u"当前持仓量", self)
	self.lineEdit_label_longPosition = QtGui.QLineEdit(self)
	layout.addWidget(label_longPosition,3,0)
	layout.addWidget(self.lineEdit_label_longPosition,3,1,1,3)

	maxStpLos = QtGui.QLabel(u'止损', self)
	self.lineEdit_label_maxStpLos = QtGui.QLineEdit(self)
	layout.addWidget(maxStpLos,4,0)
	layout.addWidget(self.lineEdit_label_maxStpLos,4,1,1,3)

	label_stpProfit = QtGui.QLabel(u"止赢", self)
	self.lineEdit_label_stpProfit = QtGui.QLineEdit(self)
	layout.addWidget(label_stpProfit,5,0)
	layout.addWidget(self.lineEdit_label_stpProfit,5,1,1,3)

	label_slippage = QtGui.QLabel(u"滑点", self)
	self.lineEdit_label_slippage = QtGui.QLineEdit(self)
	layout.addWidget(label_slippage,6,0)
	layout.addWidget(self.lineEdit_label_slippage,6,1,1,3)

	self.isFilter = QtGui.QCheckBox(u'波动', self)
	self.lineEdit_label_var = QtGui.QLineEdit(self)
	layout.addWidget(self.isFilter,7,0)
	layout.addWidget(self.lineEdit_label_var,7,1,1,3)

	label_mail = QtGui.QLabel(u"邮箱", self)
	self.lineEdit_label_mail = QtGui.QLineEdit(self)
	layout.addWidget(label_mail,8,0)
	layout.addWidget(self.lineEdit_label_mail,8,1,1,8)

	label_buyPrice = QtGui.QLabel(u"开仓价差", self)
	self.lineEdit_label_buyPrice = QtGui.QLineEdit(self)
	layout.addWidget(label_buyPrice,9,0)
	layout.addWidget(self.lineEdit_label_buyPrice,9,1,1,8)

	self.tradeTimeButton = QtGui.QPushButton(u"交易时间", self)
	self.tradeTimeButton.clicked.connect(self.tradeTimeWidget)
	layout.addWidget(self.tradeTimeButton,10,0)

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
	self.lineEdit_label_symbol.setText(self.vtSymbol)
	self.lineEdit_label_longBuyUnit.setText(str(self.paramters["openUnit"]))
	self.lineEdit_label_longPosition.setText(str(self.paramters["postoday"][self.vtSymbol]))
	self.lineEdit_label_stpProfit.setText(str(self.paramters["stpProfit"]))
	self.lineEdit_label_slippage.setText(str(self.paramters["slippage"]))
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

	pos = {}

	self.vtSymbol = str(self.lineEdit_label_symbol.text())
	if self.lineEdit_label_symbol.text() == '':
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写合约代码！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return
	else :
	    self.vtSymbol = str(self.lineEdit_label_symbol.text())

	try:
	    pos[self.vtSymbol] = int(self.lineEdit_label_longPosition.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写symbol的持仓！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
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

	try:
	    self.paramters['maxStpLos'] = int(self.lineEdit_label_maxStpLos.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'止损应该是一个数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
	    return

	try:
	    self.paramters['openUnit'] = int(self.lineEdit_label_longBuyUnit.text())
	except ValueError:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请正确填写symbol开仓手数！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes) 
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
	if str(self.directionCombo.currentText()) == '':
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'请选择交易方向！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	    return
	else :
	    self.paramters['direction'] = str(self.directionCombo.currentText())

	bp = []
	m = ""

	try:
	    for x in self.lineEdit_label_buyPrice.text():
	        if x == ',':
		    if self.paramters['direction'] == 'long' and len(bp) > 0 and int(m) >= bp[-1]:
		    	reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'开仓价应是从大到小的一组数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	    	    	return
		    if self.paramters['direction'] == 'short' and len(bp) > 0 and int(m) <= bp[-1]:
		    	reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'开仓价应是从小到大的一组数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	    	    	return
		    bp.append(int(m))
		    m = ''
		    continue
	        m += str(x)
	    if self.paramters['direction'] == 'long' and len(bp) > 0 and int(m) >= bp[-1]:
		reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'开仓价应是从大到小的一组数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	    	return
	    if self.paramters['direction'] == 'short' and len(bp) > 0 and int(m) <= bp[-1]:
		reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'开仓价应是从小到大的一组数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	        return
	    bp.append(int(m))
	except Exception, e:
	    reply = QtGui.QMessageBox.question(self, u'ERROR!',
                                           u'开仓价应是用英文逗号分隔的一组数字！', QtGui.QMessageBox.Yes, QtGui.QMessageBox.Yes)
	    return
	self.paramters["buyPrice"] = bp


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
	    self.paramters['isStop'] = False
	    with open(self.fileName, 'a') as f:
		f.write("{}")
		f.close()
	if 'tradeTime' not in self.paramters.keys():
	    self.paramters['tradeTime'] = {}
	self.paramters['isStop'] = False
	self.paramters = self.paramters
	self.saveP()
    def saveP(self):
	d1 = json.dumps(self.paramters,sort_keys=True,indent=4)
	with open(self.fileName, "w") as f:
	    f.write(d1)
	    f.close()
	self.setting['name'] = str(self.strategyName)
	self.setting['className'] = 'theGirdTrading'
	self.setting['vtSymbol'] = self.vtSymbol

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
























