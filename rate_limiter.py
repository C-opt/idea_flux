from backend.utils import setup_logging
from backend.redis_wrapper import RedisHashTable, RedisQueue
from redis import Redis
from threading import Thread
from multiprocessing import Process
import time
import logging


class RateLimiter:
    def __init__(self, redis_handle: Redis):
        self.logger = None
        setup_logging(self, logging.INFO)

        self.redis_handle: Redis = redis_handle
        self.rate_limiter_queues: dict[RedisQueue] = dict()
        self.threads: list[Process] = list()

    def add_limiter(self, limiter_name: str, rate: int, lim_max_token: int = 1200):
        """add limiter configs

        Args:
            limiter_name (str): _description_
            rate (int): _description_
            lim_max_token (int, optional): _description_. Defaults to 1200.
        """
        _queue = RedisQueue(self.redis_handle, limiter_name)
        self.rate_limiter_queues[limiter_name] = _queue

        t = Thread(
            target=self.drip_token,
            args=(
                limiter_name,
                rate,
                lim_max_token,
            ),
            daemon=True,
        )
        self.threads.append(t)

    def init_limiters(self):
        for t in self.threads:
            t.start()

    def drip_token(self, limiter_name: str, rate: int, lim_max_token: int = 1200):
        """drip token to queue

        Args:
            limiter_name (str): _description_
            rate (int): _description_
            lim_max_token (int, optional): _description_. Defaults to 1200.
        """
        api_limiter_queue: RedisQueue = self.get_limiter_queue(limiter_name)
        api_token = "dummy"
        while True:
            if api_limiter_queue.length() < lim_max_token:
                api_limiter_queue.enqueue(api_token)
            time.sleep(rate)

    def have_token(self, limiter_name: str) -> bool:
        """retrieve token from queue

        Args:
            limiter_name (str): _description_

        Returns:
            bool: _description_
        """
        api_limiter_queue: RedisQueue = self.get_limiter_queue(limiter_name)
        qlen = api_limiter_queue.length()
        self.logger.info(qlen)
        if qlen > 0:
            api_limiter_queue.dequeue()
            return True
        else:
            return False

    def get_limiter_queue(self, limiter_name: str):
        return self.rate_limiter_queues[limiter_name]
