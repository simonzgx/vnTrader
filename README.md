# vnTrader
some changes based on an existing open source projects--VNPY


# 20170405 更新CTP&IB双接口套利策略模板 1.0
详见https://simonzgx.github.io/2017/04/05/CTP-IB%E5%8F%8C%E6%8E%A5%E5%8F%A31.0.0-Beta/


# 20170411 更新CTP&IB双接口套利策略模板 1.0.1

1. 将CTPIB 双接口整合到了原来的tradeTest文件中，即现在创建双合约套利策略可以填任意IB或CTP合约（IB只限期货）

2.修复了原来的CTP接口的BUG

3.tradeTest双合约套利策略增加了限价单选择框，默认限价加滑点，如果选择则是市价（CTP合约不能发市价单）

4.现在的CTP IB 双接口策略暂时保留,待测试完成后会删除
