import redis
import logging
from backend.utils import setup_logging


class RedisHashTable:
    """Redis wrapper class for implementing hash table"""

    def __init__(self, redis_handle: redis.Redis, table_name: str):
        self.logger = None
        setup_logging(self, logging.INFO)
        self.redis_handle = redis_handle
        self.table_name = table_name

    def set(self, key, value):
        # self.logger.info("set: " + key + ", " + value)
        self.redis_handle.hset(self.table_name, key, value)

    def get(self, key):
        return self.redis_handle.hget(self.table_name, key)

    def delete(self, key):
        self.logger.info("delete: " + key + ", " + key)
        self.redis_handle.hdel(self.table_name, key)

    def keys(self):
        return self.redis_handle.hkeys(self.table_name)

    def values(self):
        return self.redis_handle.hvals(self.table_name)

    def items(self):
        return self.redis_handle.hgetall(self.table_name)


class RedisQueue:
    """Redis wrapper class for implementing queue"""

    def __init__(self, redis_handle: redis.Redis, queue_name: str):
        self.logger = None
        setup_logging(self, logging.INFO)
        self.redis_handle = redis_handle
        self.queue_name = queue_name

    def enqueue(self, value):
        # self.logger.debug("enqueue: " + self.queue_name + ", " + value)
        self.redis_handle.rpush(self.queue_name, value)

    def dequeue(self):
        value = self.redis_handle.lpop(self.queue_name)
        # self.logger.debug("dequeue: " + self.queue_name)
        return value

    def length(self) -> int:
        qlen = self.redis_handle.llen(self.queue_name)
        self.logger.debug("queue length: " + self.queue_name + ", " + str(qlen))
        return qlen

    def dump_n(self, n: int):
        """Delete n elements from queue"""
        cnt = 0
        while cnt < n:
            cnt = cnt + 1
            self.dequeue()

    def cap_n(self, n: int):
        """Util function for enforcing that the queue have a maximum number of elements

        Args:
            n (int): the maximum number of elements
        """
        qlen = self.length()
        dump_qlen = qlen - n
        self.dump_n(dump_qlen)


def main():
    redis_url = "redis://localhost:6379"
    table_name = "my_hash_table"
    reddit_handle = redis.from_url(redis_url)

    hash_table = RedisHashTable(reddit_handle, table_name)
