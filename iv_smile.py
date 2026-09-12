"""
Implied Volatility Smile / Skew Visualizer & Validation Engine.
Extracts live option chains, calculates Black-Scholes implied volatilities
using a custom root-finding solver (from P1), and validates against Yahoo Finance's quoted IV.
"""

import sys
from pathlib import Path
import datetime as dt

import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

sys.path.append(str(Path(__file__).resolve().parent.parent))
from P1.pricer import implied_volatility

pd.set_option("display.max_columns", None)


def fetch_option_chain(ticker: str, expiry: str) -> tuple[pd.DataFrame, float, float]:
    """Fetch option chain, spot price, and time-to-expiry (T) for a given ticker and expiration date."""
    stock = yf.Ticker(ticker)
    chain = stock.option_chain(expiry)
    
    expiry_date = dt.datetime.strptime(expiry, "%Y-%m-%d")
    today = dt.datetime.now()
    days_to_expiry = (expiry_date - today).days

    # Ensure time-to-expiry T is strictly positive to prevent ZeroDivisionError in Black-Scholes (d1/d2)
    T = max(days_to_expiry, 0.5) / 365.0

    current_price = stock.history(period="1d")["Close"].iloc[-1]
    return chain.calls, current_price, T


def filter_near_the_money_calls(calls: pd.DataFrame, current_price: float, lower_pct: float = 0.85, upper_pct: float = 1.15) -> pd.DataFrame:
    """Filter call options to near-the-money strikes (default +/- 15%) and compute mid price."""
    lower_bound = current_price * lower_pct
    upper_bound = current_price * upper_pct
    
    near_money_calls = calls[(calls["strike"] >= lower_bound) & (calls["strike"] <= upper_bound)].copy()
    near_money_calls["mid"] = (near_money_calls["bid"] + near_money_calls["ask"]) / 2.0
    
    # Exclude options with non-positive mid prices (which break IV solver bounds)
    near_money_calls = near_money_calls[near_money_calls["mid"] > 0]
    return near_money_calls


def compute_implied_volatilities(near_money_calls: pd.DataFrame, S: float, T: float, r: float = 0.05) -> pd.DataFrame:
    """Calculate Black-Scholes implied volatility for each strike using custom pricer module."""
    my_ivs = []
    for _, row in near_money_calls.iterrows():
        try:
            iv = implied_volatility(
                market_price=row["mid"],
                S=S,
                K=row["strike"],
                T=T,
                r=r,
                option_type="call"
            )
            my_ivs.append(iv)
        except (ValueError, ZeroDivisionError):
            my_ivs.append(None)  # solver failed to converge or hit zero boundary

    df = near_money_calls.copy()
    df["my_iv"] = my_ivs
    df_plot = df.dropna(subset=["my_iv"]).copy()
    return df_plot


def format_iv_comparison(df_plot: pd.DataFrame) -> pd.DataFrame:
    """Format and compare calculated IVs against market-quoted IVs."""
    comparison_df = df_plot[["strike", "bid", "ask", "mid", "impliedVolatility", "my_iv"]].copy()
    comparison_df["impliedVolatility"] = (comparison_df["impliedVolatility"] * 100).round(2)
    comparison_df["my_iv"] = (comparison_df["my_iv"] * 100).round(2)
    comparison_df["diff_pct_pts"] = (comparison_df["my_iv"] - comparison_df["impliedVolatility"]).round(2)
    return comparison_df


def plot_volatility_smile(comparison_df: pd.DataFrame, ticker: str, expiry: str, current_price: float, save_path: str = None) -> str:
    """Plot custom BS solver IV curve vs Yahoo Finance quoted IV curve."""
    if save_path is None:
        save_path = f"{ticker}_iv_comparison.png"

    plt.figure(figsize=(10, 6))

    plt.plot(
        comparison_df["strike"],
        comparison_df["my_iv"],
        marker="o",
        linestyle="-",
        color="#1f77b4",
        linewidth=2,
        label="Self-Built BS Solver (my_iv)"
    )

    plt.plot(
        comparison_df["strike"],
        comparison_df["impliedVolatility"],
        marker="s",
        linestyle="--",
        color="#ff7f0e",
        alpha=0.75,
        label="Yahoo Quoted IV"
    )

    plt.axvline(x=current_price, color="red", linestyle=":", label=f"Spot Price (${current_price:.2f})")

    plt.title(f"{ticker} Volatility Skew (Expiry: {expiry})", fontsize=14, pad=12)
    plt.xlabel("Strike Price ($)", fontsize=12)
    plt.ylabel("Implied Volatility (%)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.show()

    return save_path


def iv_comparator(ticker: str, expiry: str, r: float = 0.05) -> tuple[pd.DataFrame, str]:
    """Execute end-to-end IV calculation, table comparison output, and plot generation."""
    calls, current_price, T = fetch_option_chain(ticker, expiry)
    print(f"Current {ticker} price: ${current_price:.2f}")
    
    expiry_date = dt.datetime.strptime(expiry, "%Y-%m-%d")
    days_left = max((expiry_date - dt.datetime.now()).days, 0)
    print(f"Time to expiry: {T:.4f} years ({days_left} days)")

    near_money_calls = filter_near_the_money_calls(calls, current_price)
    df_plot = compute_implied_volatilities(near_money_calls, S=current_price, T=T, r=r)
    
    if df_plot.empty:
        print("No valid implied volatilities could be calculated for this chain.")
        return pd.DataFrame(), ""

    comparison_df = format_iv_comparison(df_plot)

    print(f"{ticker} Options IV Validation (Expiry: {expiry} | Spot: ${current_price:.2f}) ---")
    print(comparison_df.to_string(index=False))

    save_path = plot_volatility_smile(comparison_df, ticker, expiry, current_price)
    return comparison_df, save_path


def valid_ticker(ticker: str) -> bool:
    """Validate whether the ticker symbol has available option chains in yfinance."""
    try:
        data = yf.Ticker(ticker)
        return len(data.options) > 0
    except Exception:
        return False


def main():

    stock = yf.Ticker(ticker)
    expiries = stock.options

    print("Available Expiries:")
    print(expiries)
    expiry = input("Enter an expiry date from the above given dates: ").strip()

    while expiry not in expiries:
        print("Given Expiry Date is Invalid. Please choose from the available dates. To exit the program, type 'EXIT'.")
        print(expiries)
        expiry = input("Enter an expiry date from the given dates: ").strip()
        if expiry.lower() == "exit":
            sys.exit()

    iv_comparator(ticker, expiry)


if __name__ == "__main__":
    ticker = input("Enter ticker symbol (e.g. AAPL, MSFT, TSLA): ").strip().upper()
    
    if not valid_ticker(ticker):
        print("Invalid ticker or no option chains available.")
        sys.exit()
    main()
