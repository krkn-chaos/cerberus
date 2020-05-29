import logging
import redis


# Initialize redis cli
def initialize(host, port, flush):
    global redis_cli
    logging.info("Initializing redis client")
    try:
        redis_cli = redis.StrictRedis(host=host, port=port, decode_responses=True)
    except Exception as e:
        logging.error("Cannot connect to redis server on %s:%s, please check" % (host, port))
        logging.error(e)
    # Flush all keys
    if flush:
        logging.info("Flushing all keys in redis")
        redis_cli.flushall()
    else:
        logging.info("Using the redis database without flushing the existing keys")


# Insert keys as sets
def insert_sets(key, item):
    redis_cli.sadd(key, item)


# Return the items
def get_set_items(key):
    return list(redis_cli.smembers(key))


# Set expiry date
def set_expiry(key, time):
    redis_cli.expire(key, time)


# Checks if key exists
def check_if_exists(key):
    status = redis_cli.exists(key)
    return status


# Delete key
def delete_key(key):
    redis_cli.delete(key)
