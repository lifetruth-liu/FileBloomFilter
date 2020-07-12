
from hashlib import md5
from math import ceil

import os
import time

class BloomFilterWithFile:
    def __init__(self, key, size, hash_count, encoding="utf-8", cFile=True):
        self.key = key
        self.encoding = encoding
        self.size = int(100 * 2 ** 20 * 8)
        self.fileSize = ceil(self.size / 8)
        self.hash_count = hash_count
        if cFile:
            self.createBFFile(self.key, self.size)
        self.BFFileObj = self.loadBFFileObj(self.key)

    def createBFFile(self, BFKey, size):
        if os.path.isfile(self.key):
            os.remove(self.key)
        f = open(BFKey, "w+b")
        f.truncate(self.fileSize)
        f.close()

    def loadBFFileObj(self, key, mode="r+b"):
        if "b" in mode:
            f = open(key, mode)
        else:
            f = open(key, mode, encoding=self.encoding)
        return f

    def closeBFFileObj(self, f):
        f.close()

    def hashIndex(self, item, hashFuncIndex):
        key = "%s-*-*-*-*-%s"%(item, hashFuncIndex)
        return int(md5(key.encode("utf-8")).hexdigest(), 16)

    def _add(self, f, hashIndex):
        try:
            # 计算偏移
            offset = hashIndex // 7
            index = hashIndex % 7

            # 计算BF位数据
            f.seek(offset)
            d = f.read(1)
            bin = '{:07b}'.format(0 if not d else ord(d))
            bin = "0" + bin[:index] + "1" + bin[index + 1:]

            # 修改BF位数据
            if bin == "00001010":
                charData = "\n".encode(encoding=self.encoding)
            else:
                charData = chr(int(bin, 2)).encode(encoding=self.encoding)
            f.seek(offset)
            f.write(charData)
            f.flush()

        except Exception as e:
            print("0")

    def add(self, item):
        for i in range(self.hash_count):
            index = self.hashIndex(item, i) % self.size
            self._add(self.BFFileObj, index)
        return self

    def _contains(self, f, hashIndex):
        # 计算偏移
        offset = hashIndex // 7
        index = hashIndex % 7

        # 计算BF位数据
        f.seek(offset)
        d = f.read(1)
        bin = '{:07b}'.format(0 if not d else ord(d))
        res = False if bin[index] == "0" else True
        return res

    def __contains__(self, item):
        out = True
        for i in range(self.hash_count):
            index = self.hashIndex(item, i) % self.size
            out = self._contains(self.BFFileObj, index)
        return out
 
 
def timeTest():
    bloom = BloomFilterWithFile("test", 10, 14)
    s = time.time()
    for i in range(100000):
        bloom.add(i)
    print("插入耗时:", time.time() - s)

    s = time.time()
    count = 0
    for i in range(100000):
        if i in bloom:
            count += 1

    print("查询耗时:", time.time() - s)
    print("存在个数:", count)
   
   
if __name__ == '__main__':
    timeTest()
