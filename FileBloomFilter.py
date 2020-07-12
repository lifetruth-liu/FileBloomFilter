from hashlib import md5
from math import ceil, log, fabs

import hashlib
import os
import time

from struct import unpack, pack

# 写入换行符 0000 1010 会导致换行位置的下一位被强制替换成换行, 原因 win换行位 \r\n


def make_hashfuncs(num_slices, num_bits):
    if num_bits >= (1 << 31):
        fmt_code, chunk_size = 'Q', 8
    elif num_bits >= (1 << 15):
        fmt_code, chunk_size = 'I', 4
    else:
        fmt_code, chunk_size = 'H', 2
    total_hash_bits = 8 * num_slices * chunk_size
    if total_hash_bits > 384:
        hashfn = hashlib.sha512
    elif total_hash_bits > 256:
        hashfn = hashlib.sha384
    elif total_hash_bits > 160:
        hashfn = hashlib.sha256
    elif total_hash_bits > 128:
        hashfn = hashlib.sha1
    else:
        hashfn = hashlib.md5

    fmt = fmt_code * (hashfn().digest_size // chunk_size)
    num_salts, extra = divmod(num_slices, len(fmt))
    if extra:
        num_salts += 1
    salts = tuple(hashfn(hashfn(pack('I', i)).digest()) for i in range(0, num_salts))

    def _hash_maker(key):
        if isinstance(key, str):
            key = key.encode('utf-8')
        else:
            key = str(key).encode('utf-8')
        i = 0
        for salt in salts:
            h = salt.copy()
            h.update(key)
            for uint in unpack(fmt, h.digest()):
                yield uint % num_bits
                i += 1
                if i >= num_slices:
                    return

    return _hash_maker, hashfn

class BloomFilterWithFile:
    def __init__(self, key, capacity, error_rate=0.001, encoding="utf-8", cFile=True, maxExtend=8):
        """

        :param key:
        :param capacity: 数据容量
        :param error_rate: 错误率,单位%
        :param encoding:
        :param cFile:
        :param maxExtend: 去重文件最大延伸倍率

        m = fabs(capacity * log(error_rate/100) / (log(2) ** 2))
        k = log(2) * m
        """
        self.key = key
        self.encoding = encoding

        self.m, self.hash_count, self.preSize, self.size, self.fileSize = \
            self.calculator(capacity, error_rate, maxExtend)
        if cFile:
            self.createBFFile(self.key, self.size)
        self.BFFileObj = self.loadBFFileObj(self.key)
        self.make_hashes, self.hashfn = make_hashfuncs(self.hash_count, self.preSize)

    def calculator(self, capacity, error_rate, maxExtend):
        m = ceil(fabs(capacity * log(error_rate / 100) / (log(2) ** 2)))
        k = max([min([ceil(log(2) * m / capacity / 4), maxExtend]), 3])
        preSize = m
        fileSize = ceil(m * k / 7)
        size = fileSize * 7
        fileMemTypeSize, memType = self.calculatorFileSize(size)
        print("所需磁盘容量:", "%s%s"%(fileMemTypeSize, memType))

        return m, k, preSize, size, fileSize

    def calculatorFileSize(self, size):
        fileSize = ceil(size / 1024 / 1024 / 7)
        if fileSize >= 1024:
            fileSize = ceil(fileSize / 1024)
            return fileSize, "G"
        return fileSize, "M"

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
        offset = 0
        hashes = self.make_hashes(item)
        for k in hashes:
            self._add(self.BFFileObj, k + self.preSize)
            offset += self.preSize
            # offset += k

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
        offset = 0
        hashes = self.make_hashes(item)
        for k in hashes:
            if not self._contains(self.BFFileObj, k + self.preSize): return
            offset += self.preSize
            # offset += k

        return True


def timeTest():
    bloom = BloomFilterWithFile("test", 10000*1000, 0.01)
    s = time.time()
    for i in range(150000):
        bloom.add(i)
    print("插入耗时:", time.time() - s)

    s = time.time()
    count = 0
    for i in range(10000*80, 10000*100):
        if i in bloom:
            count += 1
    print("查询耗时:", time.time() - s)
    print("存在个数:", count)



if __name__ == '__main__':
    timeTest()
