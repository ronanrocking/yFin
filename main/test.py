import requests
from private import credentials

# ❌ Wrong
# BASE_URL = "https://api.upstock.com/v2"
# The domain "api.upstock.com" doesn’t exist → DNS error

# ✅ Correct
BASE_URL = "https://api-v2.upstox.com/v2"

headers = {"Authorization": f"Bearer {credentials.ACCESS_TOKEN}"}

# Example: getting user profile
resp = requests.get(f"{BASE_URL}/user/profile", headers=headers)
print(resp.json())
