#!/usr/bin/python3

import redis
from my_conf import REDIS_HOST,REDIS_PORT,REDIS_PASS


class Redis(object):
    r = ''

    def __init__(self):
        self._con()

    """ 连接redis """

    def _con(self, db=0):
        if self.r == '':
            pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=db, 
                                            password=REDIS_PASS,decode_responses=True)
            self.r = redis.StrictRedis(connection_pool=pool,)

    def set(self, key, value, ex=None):
        return self.r.set(key, value, ex)

    def get(self, key):
        return self.r.get(key)

    def keys(self, key):
        return self.r.keys(key)

    def delete(self, key):
        return self.r.delete(key)

    def incr(self,key):
        return self.r.incr(key)

    def lpush(self,key,val):
        return self.r.lpush(key,val)

    def rpop(self,list_name):
        return self.r.rpop(list_name)

    def llen(self,key,):
        return self.r.llen(key)

    def ltrim(self,key,start=0,end=None):
        return self.r.ltrim(key,start,end)

    def lrange(self,key,start=0,end=None):
        return self.r.lrange(key,start,end)

    def mget(self, keys):
        return self.r.mget(keys)

    def expire(self,key,expire_time):
        return self.r.expire(key,expire_time)

    """ 有序集合添加 data_dict={data1: score1, data2: score2}"""
    def zadd(self, key, data_dict):
        return self.r.zadd(key, data_dict)

    """ 有序集合查询 """
    def zrange(self, key, start=0, end=-1):
        return self.r.zrange(key, start, end)

    """ 返回有序集 key 中，所有 score 值介于 min 和 max 之间 从小到大 """
    def zrangebyscore(self, key, sScore, eScore):
        return self.r.zrangebyscore(key, sScore, eScore)

    """ 返回有序集 key 中，指定区间内的成员 从大到小 """
    def zrevrange(self, key, start=0, end=-1):
        return self.r.zrevrange(key, start, end)

    """ 返回有序集 key 中， score 值介于 max 和 min 之间 从大到小 """
    def zrevrangebyscore(self, key, sScore, eScore):
        return self.r.zrevrangebyscore(key, sScore, eScore)

    """ 设置 string 值,原子操作 """
    def setex(self, key, value, time=1):
        return self.r.setex(key, time, value)

    def setnx(self, key, value, time=1):
        return self.r.setnx(key, value)

    """ 将哈希表 key 中的域 field 的值设为 value """
    def hset(self, key, field, value):
        return self.r.hset(key, field, value)

    """ 返回哈希表 key 中给定域 field 的值 """
    def hget(self, key, field):
        return self.r.hget(key, field)

    def hgetall(self,key):
        return self.r.hgetall(key)

    def hvals(self,key):
        return self.r.hvals(key)      

    """ 将哈希表 key 中的域 field 的值设置为 value ，当且仅当域 field 不存在 """
    def hsetnx(self, key, field, value):
        return self.r.hsetnx(key, field, value)

    """ 移除有序集 key 中，所有 score 值介于 min 和 max 之间(包括等于 min 或 max )的成员 """
    def zremrangebyscore(self, key, min, max):
        return self.r.zremrangebyscore(key, min, max)

    """ 移除有序集 key 中，指定排名(rank)区间内的所有成员 """
    def zremrangebyrank(self, key, start, stop):
        return self.r.zremrangebyrank(key, start, stop)

    """ 返回有序集 key 的基数 """
    def zcard(self, key):
        return self.r.zcard(key)

    """ 删除哈希表 key 中的一个或多个指定域，不存在的域将被忽略 """
    def hdel(self, key, field):
        return self.r.hdel(key, field)
    
    """ 将 key 所储存的值加上增量 increment """
    def incrby(self, key, increment):
        return self.r.incrby(key, increment)