"""Downloads daily closing prices from Yahoo Finance with the `yfinance` API (needs internet: pip install yfinance).
Falls back to a synthetic random-walk dataset if the download is unavailable, so the analysis always runs."""
import os, numpy as np, pandas as pd

TICKERS = {"RELIANCE.NS": "Reliance", "TCS.NS": "TCS", "INFY.NS": "Infosys", "HDFCBANK.NS": "HDFC Bank", "^NSEI": "Nifty 50"}

def synthetic(start="2020-01-01", end="2025-12-31", seed=2):
    rng = np.random.default_rng(seed); dates = pd.bdate_range(start, end)
    market = rng.normal(.0004, .011, len(dates)); out = {}
    for (t, name), beta, start_px in zip(TICKERS.items(), [1.1, .8, .9, 1.0, 1.0], [1200, 2000, 700, 1100, 12000]):
        r = beta * market + rng.normal(.0002, .01 if t != "^NSEI" else 0, len(dates))
        out[name] = start_px * np.exp(np.cumsum(r))
    return pd.DataFrame(out, index=dates)

def fetch(path="data/prices.csv", start="2020-01-01", end="2025-12-31"):
    os.makedirs("data", exist_ok=True)
    try:
        import yfinance as yf
        raw = yf.download(list(TICKERS), start=start, end=end, auto_adjust=True, progress=False)["Close"]
        df = raw.rename(columns=TICKERS).dropna(how="all")
        if df.empty: raise ValueError("empty download")
        print("Downloaded live data from Yahoo Finance")
    except Exception as e:
        print(f"Live download not available ({type(e).__name__}) - using synthetic prices")
        df = synthetic(start, end)
    df.index.name = "Date"; df.to_csv(path); return df

if __name__ == "__main__":
    fetch()
