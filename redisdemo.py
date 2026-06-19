import redis

REDIS_URL = "redis://127.0.0.1:6379/0"

redis_client = redis.from_url(REDIS_URL, decode_responses=True, encoding="utf-8")

redis_client.set("username", "admin")
redis_client.set("password", "123456")

username = redis_client.get("username")

print(username)
print(redis_client.exists("username"))
print(redis_client.exists("aaa"))

redis_client.delete("username")
print(redis_client.exists("username"))