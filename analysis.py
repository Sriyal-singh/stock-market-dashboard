# %%
# # Stock Market Dashboard - Time-Series Analysis
# Moving averages, daily returns, volatility and correlation for NSE stocks, via the Yahoo Finance API (`yfinance`).
# If you are offline (or yfinance is not installed) a synthetic price series is used so everything still runs.

# %%
import os
import pandas as pd, numpy as np
import matplotlib.pyplot as plt, seaborn as sns
sns.set_theme(style="whitegrid")
os.makedirs("images", exist_ok=True)
if not os.path.exists("data/prices.csv"):
    from fetch_data import fetch
    fetch()
prices = pd.read_csv("data/prices.csv", index_col="Date", parse_dates=True).sort_index().ffill().dropna()
prices.tail()

# %%
# ## 1. Daily returns and cleaning
returns = prices.pct_change().dropna()
prices.to_csv("cleaned_dataset.csv")
print(returns.describe().round(4).loc[["mean", "std", "min", "max"]])

# %%
# ## 2. Moving averages (20 / 50 / 200 day) and golden/death cross signals
stock = prices.columns[0]
p = prices[stock].to_frame("Close")
for w in (20, 50, 200): p[f"MA{w}"] = p["Close"].rolling(w).mean()
cross = np.sign(p["MA50"] - p["MA200"]).diff()
golden, death = p.index[cross > 1], p.index[cross < -1]
fig, ax = plt.subplots(figsize=(13, 5.5))
p[["Close", "MA20", "MA50", "MA200"]].plot(ax=ax, lw=1.2, color=["#444", "#1f77b4", "#ff7f0e", "#d62728"])
ax.scatter(golden, p.loc[golden, "Close"], marker="^", color="green", s=90, label="Golden cross", zorder=5)
ax.scatter(death, p.loc[death, "Close"], marker="v", color="red", s=90, label="Death cross", zorder=5)
ax.set_title(f"{stock}: price and moving averages"); ax.legend(); plt.tight_layout(); plt.savefig("images/moving_averages.png", dpi=150); plt.show()

# %%
# ## 3. Daily return distribution
fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
sns.histplot(returns[stock] * 100, bins=60, kde=True, ax=ax[0], color="#1f77b4"); ax[0].set_title(f"{stock}: daily returns (%)"); ax[0].axvline(0, color="k")
sns.boxplot(data=returns * 100, ax=ax[1], orient="h"); ax[1].set_title("Daily returns by stock (%)")
plt.tight_layout(); plt.savefig("images/daily_returns.png", dpi=150); plt.show()

# %%
# ## 4. Volatility (30-day rolling, annualised)
vol = returns.rolling(30).std() * np.sqrt(252) * 100
ax = vol.plot(figsize=(13, 4.8), lw=1); ax.set_title("30-day rolling volatility (annualised, %)"); ax.set_ylabel("%")
plt.tight_layout(); plt.savefig("images/volatility.png", dpi=150); plt.show()

# %%
# ## 5. Correlation
corr = returns.corr()
plt.figure(figsize=(6.5, 5.2)); sns.heatmap(corr, annot=True, cmap="coolwarm", vmin=-1, vmax=1); plt.title("Correlation of daily returns")
plt.tight_layout(); plt.savefig("images/correlation.png", dpi=150); plt.show()

# %%
# ## 6. Cumulative growth of Rs 100 and maximum drawdown
growth = (1 + returns).cumprod() * 100
drawdown = growth / growth.cummax() - 1
fig, ax = plt.subplots(1, 2, figsize=(14, 4.8))
growth.plot(ax=ax[0]).set_title("Growth of Rs 100 invested"); (drawdown * 100).plot(ax=ax[1]).set_title("Drawdown (%)")
plt.tight_layout(); plt.savefig("images/growth_drawdown.png", dpi=150); plt.show()

# %%
# ## 7. Risk-return summary (annualised)
summary = pd.DataFrame({"annual_return_%": returns.mean() * 252 * 100, "volatility_%": returns.std() * np.sqrt(252) * 100,
                        "sharpe (rf=0)": returns.mean() / returns.std() * np.sqrt(252), "max_drawdown_%": drawdown.min() * 100}).round(2)
summary.to_csv("risk_return_summary.csv"); summary

# %%
# ## 8. Interactive candlestick-style chart (optional: `pip install plotly`)
try:
    import plotly.express as px
    px.line(growth.reset_index().melt("Date", var_name="Stock", value_name="Value"), x="Date", y="Value", color="Stock", title="Growth of Rs 100").write_html("images/growth_interactive.html")
    print("Saved images/growth_interactive.html")
except ImportError:
    print("plotly not installed - skipping interactive chart")

# %%
# ## 9. Insights
print("Insights:")
print(f"1. Best risk-adjusted performer: {summary['sharpe (rf=0)'].idxmax()} (Sharpe {summary['sharpe (rf=0)'].max():.2f})")
print(f"2. Most volatile: {summary['volatility_%'].idxmax()} ({summary['volatility_%'].max():.0f}% annualised)")
print(f"3. Deepest drawdown: {summary['max_drawdown_%'].idxmin()} ({summary['max_drawdown_%'].min():.0f}%)")
pairs = corr.where(np.triu(np.ones(corr.shape), 1).astype(bool)).stack()
print(f"4. Most correlated pair: {pairs.idxmax()[0]} & {pairs.idxmax()[1]} ({pairs.max():.2f})")
print(f"5. {stock} had {len(golden)} golden cross(es) and {len(death)} death cross(es) in the period")
