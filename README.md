~~ASCII 字符最大值`0111 1111`, 则文件的每一字节可以存储7个有效数据, 以此来模拟bitArray节省内存空间.~~

可以拆分记录文件来提升速度

待做:
  ~~1. 修改文件写入方式, 直接写二进制取代写ASCII码: `f.write(b"\xff")`
  
  2. 过大去重文件拆分, 多线程处理各个文件子文件以提速
