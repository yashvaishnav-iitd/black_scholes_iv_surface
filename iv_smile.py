import yfinance as yf
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from P1.pricer import implied_volatility


pd.set_option('display.max_columns', None)


def iv_comparator(stock,expiry):
    stock = yf.Ticker("AAPL")

    expiries = stock.options
        
    
    chain = stock.option_chain(expiry)
    expiry_date = dt.datetime.strptime(expiry, "%Y-%m-%d")
    today = dt.datetime.now()
    T= (expiry_date-today).days /365

    calls = chain.calls
    puts = chain.puts

    current_price = stock.history(period="1d")['Close'].iloc[-1]
    print (f"Current AAPL price: {current_price:.2f}")

    lower_bound = current_price*0.85
    upper_bound = current_price*1.15
    near_money_calls = calls[(calls['strike']>=lower_bound) & (calls['strike']<=upper_bound)]
    near_money_calls = near_money_calls.copy()
    near_money_calls['mid']= (near_money_calls['bid'] + near_money_calls['ask'])/2

    print(f"Time to expiry: {T:.4f} years ({(expiry_date - today).days} days)")

    S = current_price
    r=0.05          # risk-free rate assumption

    my_ivs = []

    for _, row in near_money_calls.iterrows():
        try:
            iv = implied_volatility(
                market_price=row['mid'],
                S=S,
                K = row['strike'],
                T=T,
                r=r,
                option_type="call"
            )
            my_ivs.append(iv)

        except ValueError:
            my_ivs.append(None)     # solver failed to converge for this strike

    near_money_calls['my_iv'] = my_ivs


    # Filter out rows where IV calculation failed
    df_plot = near_money_calls.dropna(subset=['my_iv']).copy()

    # Format comparison view
    comparison_df = df_plot[['strike', 'bid', 'ask', 'mid', 'impliedVolatility', 'my_iv']].copy()
    comparison_df['impliedVolatility'] = (comparison_df['impliedVolatility'] * 100).round(2)
    comparison_df['my_iv'] = (comparison_df['my_iv'] * 100).round(2)
    comparison_df['diff_pct_pts'] = (comparison_df['my_iv'] - comparison_df['impliedVolatility']).round(2)

    print(f"\n--- AAPL Options IV Validation (Expiry: {expiry} | Spot: ${current_price:.2f}) ---")
    print(comparison_df.to_string(index=False))


    plt.figure(figsize=(10, 6))

    # Plot calculated Black-Scholes IVs
    plt.plot(
        comparison_df['strike'], 
        comparison_df['my_iv'], 
        marker='o', 
        linestyle='-', 
        color='#1f77b4', 
        linewidth=2, 
        label='Self-Built BS Solver (my_iv)'
    )

    # Plot Yahoo Finance's Quoted IV
    plt.plot(
        comparison_df['strike'], 
        comparison_df['impliedVolatility'], 
        marker='s', 
        linestyle='--', 
        color='#ff7f0e', 
        alpha=0.75, 
        label='Yahoo Quoted IV'
    )

    # Add reference line for spot price
    plt.axvline(x=current_price, color='red', linestyle=':', label=f'Spot Price (${current_price:.2f})')

    plt.title(f"{ticker} Volatility Skew (Expiry: {expiry})", fontsize=14, pad=12)
    plt.xlabel("Strike Price ($)", fontsize=12)
    plt.ylabel("Implied Volatility (%)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(f"{ticker}_iv_comparison.png", dpi=150)
    plt.show()




def valid_ticker(ticker):
    data = yf.Ticker(ticker)
    df = data.options

    return len(df)>0

if __name__ == "__main__":

    ticker = input("Enter ticker symbol (e.g. AAPL, MSFT, TSLA): ").strip().upper()

    if valid_ticker(ticker):
        print("Valid ticker")
        data = yf.Ticker(ticker)
    else:
        print("Invalid ticker")
        exit()



    expiries = data.options

    print(expiries)
    expiry = input("Enter an expiry date from the above given dates: ")
    while expiry not in expiries:
        print("Given Expiry Date is Invalid. Please choose from the following dates. To exit the program, type 'EXIT' ")
        print(expiries)
        expiry = input("Enter an expiry date from the given dates: ")
        if expiry.lower()=="exit":
            exit()

    iv_comparator(data,expiry)

    
