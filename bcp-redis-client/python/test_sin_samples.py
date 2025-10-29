from bcp_redis_client.sample import set_sample_primitive
import time
import math
import redis

r = redis.Redis(host="localhost", port=6379, db=0)

while True:
    value = math.sin(time.time())
    set_sample_primitive(r, "test-sin", value)
    time.sleep(0.2)