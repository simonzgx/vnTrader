# encoding: UTF-8

"""
包含一些开放中常用的函数
"""

import decimal
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
MAX_NUMBER = 10000000000000
MAX_DECIMAL = 4

#----------------------------------------------------------------------
def safeUnicode(value):
    """检查接口数据潜在的错误，保证转化为的字符串正确"""
    # 检查是数字接近0时会出现的浮点数上限
    if type(value) is int or type(value) is float:
        if value > MAX_NUMBER:
            value = 0
    
    # 检查防止小数点位过多
    if type(value) is float:
        d = decimal.Decimal(str(value))
        if abs(d.as_tuple().exponent) > MAX_DECIMAL:
            value = round(value, ndigits=MAX_DECIMAL)
    
    return unicode(value)

#----------------------------------------------------------------------
def loadMongoSetting():
    """载入MongoDB数据库的配置"""
    try:
        f = file("VT_setting.json")
        setting = json.load(f)
        host = setting['mongoHost']
        port = setting['mongoPort']
    except:
        host = 'localhost'
        port = 27017
        
    return host, port

#----------------------------------------------------------------------
def todayDate():
    """获取当前本机电脑时间的日期"""
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)   


def emailSender(receivers,all_text,event_subject):

	# 第三方 SMTP 服务
	mail_host = "smtpdm.aliyun.com"  # 设置服务器
	mail_user = "tb@mail.wokens.com"  # 用户名
	mail_pass = "wokens6666"  # 口令

	sender = 'tb@mail.wokens.com'

	message = MIMEText(all_text, 'plain', 'utf-8')  # 邮件内容
	message['From'] = Header(sender, 'utf-8')  # 发件人


	message['Subject'] = Header(event_subject, 'utf-8')#标题

	try:
		smtpObj = smtplib.SMTP()
		smtpObj.connect(mail_host, 25)
		smtpObj.login(mail_user, mail_pass)
		for receiver in receivers:
			message['To'] = Header(receiver, 'utf-8')  # 收件人
			smtpObj.sendmail(sender, receiver, message.as_string())
		print("邮件发送成功")
	except smtplib.SMTPException:
		print("Error: 无法发送邮件") 

 
