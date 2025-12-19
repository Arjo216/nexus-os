import redis
r = redis.Redis(host='localhost', port=6379)

def daily_cleanup():
    print("🧹 NEXUS Maintenance: Trimming city memory...")
    keys = r.keys("history:*")
    for key in keys:
        r.delete(key) # Clear historical logs to keep system lean
    print(f"✅ Success: {len(keys)} records cleared.")

if __name__ == "__main__":
    daily_cleanup()