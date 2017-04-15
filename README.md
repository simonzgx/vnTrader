# vnTrader
some changes based on an existing open source projects--VNPY


# 20170405 更新CTP&IB双接口套利策略模板 1.0
详见https://simonzgx.github.io/2017/04/05/CTP-IB%E5%8F%8C%E6%8E%A5%E5%8F%A31.0.0-Beta/


# 20170411 更新CTP&IB双接口套利策略模板 1.0.1


  1.将CTPIB 双接口整合到了原来的tradeTest文件中，即现在创建双合约套利策略可以填任意IB或CTP合约（IB只限期货）
  
  2.修复了原来的CTP接口的BUG
  
  3.tradeTest双合约套利策略增加了限价单选择框，默认限价加滑点，如果选择则是市价（CTP合约不能发市价单）
  
  4.现在的CTP IB 双接口策略暂时保留,待测试完成后会删除
  
# 20170411 更新CTP&IB双接口套利策略模板 1.0.1

  1.重做了策略参数界面，由原来的固定位置改为GirdLayout
  
  2.修复了策略内一些参数不能填写小数的BUG（注意一些合约的最小交易单位)
  
  3.修复了策略不开始看不到参数的BUG
  
  4.对于CTP IB策略，删除了原来的滑点参数，增加了两个对应合约的滑点参数
  
  5.对于但合约策略增加了9.02分才开始的判断
  
  6.对于CTPgateway 修改了持仓查询，报单查询，委托查询等代码的实现方法
