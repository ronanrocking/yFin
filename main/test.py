import yfinance as yf

nifty = "ACC.NS"
df = yf.download(
    nifty, 
    start = "2025-01-01",
    end = "2025-09-19",
    interval = "1h"
)
df = df.tz_convert("Asia/Kolkata")
print(df.between_time("09:15", "15:30"))
df = df[df["Volume"] > 0]


print(df)