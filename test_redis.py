import redis

# RedisのURLを設定
redis_url = "redis://default:nm1Ok7WLMwEPxlWNhE5Al3EGJ1aMSLRo@redis-14909.c278.us-east-1-4.ec2.redns.redis-cloud.com:14909/0"
redis_client = redis.StrictRedis.from_url(redis_url)

# テストで値を設定・取得
redis_client.set('test_key', 'test_value')
value = redis_client.get('test_key')

print(f"取得した値: {value.decode('utf-8')}")
