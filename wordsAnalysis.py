import json
from jieba_fast import analyse
import numpy as np
import pandas as pd
from pymongo import MongoClient
from api import *


# 提取带有权重的关键字
def getRecordWithWeight(weibo):
    record = {}
    for content in weibo['tweet']:
        sentense = content['content']
        words = analyse.textrank(sentense, withWeight = True, allowPOS=('ns', 'n', 'vn', 'an', 'nr', 'nt'))
        # words = analyse.extract_tags(sentense, withWeight = True)
        for word in words:
            word, weight = word
            if word in record:
                record[word][0] += weight
                record[word][1] += 1
            else:
                record[word] = [0, 0]
                record[word][0] = weight
                record[word][1] = 1
    return record


# 对关键字排序
def recordSort(record):
    if len(record) == 0:return[]
    values = np.array(list(record.values()))
    df = pd.DataFrame()
    df.insert(0, 0, record.keys())
    df.insert(1, 1, values[:, 0])
    df.insert(2, 2, values[:, 1])
    df = df.sort_values(by=1 , ascending=False)
    df = df.sort_values(by=2 , ascending=False)
    return df[0].tolist()


# 删除字母和数字
def removeNumAndEngStopWords(words):
    newWords = []
    for word in words:
        if not (word.isdigit() or word.encode('UTF-8').isalpha() or word.encode('UTF-8').isalnum()):
            newWords.append(word)
    return newWords


# 获取一名微博用户对应的关键字列表
def getKeyWordsByUserID(userID, key_num=20):
    weibo = json.loads(getAllByIdJson(userID))
    record = getRecordWithWeight(weibo)
    words = recordSort(record)
    return weibo['nick_name'], removeNumAndEngStopWords(words)[:key_num]


# 已处理的微博数量
def getAllCount():
    count = 0
    for line in open('config/count.txt'):
        count = int(line)
    return count


# 处理完一批后修正数量
def resetAllCount(nums):
    with open('config/count.txt', 'w') as f:
        f.write(str(nums))


if __name__ == '__main__':

    # mongo
    client = MongoClient('47.107.130.215', 27017)
    db = client['local']
    collection = db['weibo']

    # 加载停用词
    analyse.set_stop_words('config/stopWords.txt')

    # 起始索引
    beginNum = getAllCount()

    # 获取微博ID
    ids = json.loads(getAllIdJson())

    # 结束索引
    endNum = len(ids)

    for index, id in enumerate(ids[beginNum:endNum]):
        name, vector = getKeyWordsByUserID(id)
        collection.insert_one({'name': name, 'words': vector})
        resetAllCount(beginNum+1+index)

