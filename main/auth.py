import webbrowser
import requests
from private import credentials
import os

API_KEY = credentials.API_KEY
API_SECRET = credentials.API_SECRET
REDIRECT_URL = credentials.REDIRECT_URL
ACCESS_TOKEN = getattr(credentials, "ACCESS_TOKEN", "")  # in case not set yet

# Step 1: Generate login URL (v2)
login_url = (
    f"https://api.upstox.com/v2/login/authorization/dialog?"
    f"response_type=code&client_id={API_KEY}&redirect_uri={REDIRECT_URL}"
)

print("Opening Upstox v2 login page in browser...")
webbrowser.open(login_url)

# Step 2: Get authorization code from browser
auth_code = input("Enter the 'code' parameter from redirected URL: ").strip()

# Step 3: Exchange code for access token (v2)
token_url = "https://api.upstox.com/v2/login/authorization/token"
data = {
    "grant_type": "authorization_code",
    "code": auth_code,
    "client_id": API_KEY,
    "client_secret": API_SECRET,
    "redirect_uri": REDIRECT_URL
}

try:
    response = requests.post(token_url, data=data)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print("HTTP request failed:", e)
    exit()

token_data = response.json()
print("Access Token Data:", token_data)

# Step 4: Save ACCESS_TOKEN in credentials.py
access_token = token_data.get("access_token")
if access_token:
    credentials_file = os.path.join(os.path.dirname(__file__), "../private/credentials.py")
    with open(credentials_file, "a") as f:
        f.write(f"\nACCESS_TOKEN = '{access_token}'\n")
    print("Access token saved in private/credentials.py")
else:
    print("Failed to get access token. Check auth code, redirect URL, and credentials.")
