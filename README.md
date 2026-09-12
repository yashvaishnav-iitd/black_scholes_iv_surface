# Implied Volatility Surface & Skew Analysis

## Overview
This project extracts real-time option chain data from Yahoo Finance via `yfinance`, cleans and filters the bid-ask quotes, and numerically extracts Black-Scholes Implied Volatility (IV) across various strike prices for a given expiration. The calculated IVs are compared directly against Yahoo's reported implied volatility to analyze pricing dynamics, model limitations, and market skew/smile behaviors.

---

## Dependencies & Installation

Ensure you have Python 3.8+ installed along with the following required libraries:

```bash
pip install numpy pandas matplotlib yfinance scipy
```

### Key Modules:
* **`yfinance`**: Fetches option chains, market quotes, and underlying asset prices.
* **`numpy` / `pandas`**: Handles vector calculations and tabular data manipulation.
* **`matplotlib`**: Renders 2D visual comparisons of implied volatility skew.
* **`scipy`**: Supplies cumulative distribution (`norm.cdf`) and probability density (`norm.pdf`) functions for Black-Scholes pricing.

---

## Code Architecture & Methodology

The pipeline follows a structured mathematical and data processing flow:

1. **Option Chain Retrieval & Spot Determination**:
   * Pulls current options chain (`yf.Ticker.option_chain`) for target expiration.
   * Pulls current spot price ($S$) via 1-day historical close (`stock.history(period="1d")['Close']`) to avoid missing/incomplete real-time rows.

2. **Data Clean-Up & Filtering**:
   * **Near-The-Money (NTM) Window**: Restricts strikes within $\pm 15\%$ of spot price ($0.85 S \le K \le 1.15 S$) to focus on liquid, informative options.
   * **Zero-Bid Removal**: Removes stale quotes where `bid == 0` to prevent distorted mid-prices (`mid = (bid + ask) / 2`).

3. **Newton-Raphson IV Solver**:
   * Implements Newton-Raphson root finding:
     $$\sigma_{n+1} = \sigma_n - rac{C_{	ext{BS}}(\sigma_n) - C_{	ext{market}}}{	ext{Vega}(\sigma_n)}$$
   * **Vega Guard**: Prevents division by near-zero vega ($	ext{Vega} < 1e-8$) when options move far in/out-of-the-money.
   * **Bisection Fallback**: Provides a secondary search mechanism if Newton-Raphson oscillates or strays into non-physical ($\sigma \le 0$) regimes.

4. **Validation & Plotting**:
   * Aligns self-built `my_iv` against Yahoo's `impliedVolatility`.
   * Generates `strike` vs `IV` curves to visualizes the volatility skew and identify pricing discrepancies.

---

## How to Run

1. Ensure `pricer.py` (from Project 1) is in the same directory or import paths.
2. Run the main execution script:
   ```bash
   python main.py
   ```
3. Inspect output validation tables and the generated `matplotlib` skew chart.
