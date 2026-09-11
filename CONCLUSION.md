# Project 2 Results & Conclusion

## Target Asset & Contract Parameters
* **Asset**: Apple Inc. (`AAPL`)
* **Spot Price ($S$)**: $326.57
* **Expirations Evaluated**: 
  * Near-Term: October 16, 2026 ($T pprox 0.1$ yrs)
  * Long-Term (LEAP): December 15, 2028 ($T = 2.26$ yrs)
* **Risk-Free Rate ($r$)**: 5.0%

---

## Key Observations & Market Dynamics

### 1. ATM & OTM Skew Convergence (Short-Dated Expiry)
* **Alignment**: At-the-money (ATM) and out-of-the-money (OTM) call options for short-dated contracts exhibited tight alignment between our self-built Black-Scholes solver (`my_iv`) and Yahoo Finance's quoted `impliedVolatility`. Differences ranged between **0.20 and 1.74 percentage points**.
* **Vol Shape**: The curve displays a classic equity volatility skew, starting near **~27%** around ATM ($325) and dropping to a minimum of **~25.17%** at strike $360 before slightly curling upward at far OTM strikes.
* **Driver**: High Vega in the ATM regime ensures stable numerical convergence, where market mid-prices accurately reflect extrinsic time value.

### 2. Deep ITM Call Discrepancy & Put-Call Parity (Short-Dated Expiry)
* **Observed Divergence**: For deep in-the-money (ITM) calls ($280 strike), Yahoo reports an IV of **42.95%**, whereas our direct Black-Scholes call solver computed **27.35%** (a **15.60 percentage point** divergence).
* **Cause 1: Vega Collapse**: As calls move deep ITM, extrinsic (time) value collapses. For instance, at strike $280, the intrinsic value is $46.57 ($326.57 - $280.00) relative to a $48.15 mid-price, leaving only ~$1.58 in time value. Vega approaches zero, making $\Delta \sigma = \frac{\Delta C}{\text{Vega}}$ hypersensitive to bid-ask noise or minor interest rate/dividend mismatches.
* **Cause 2: Market Vendor Methodology (Put-Call Parity)**: Financial data providers do not solve deep ITM call IVs directly from call prices due to low liquidity and wide spreads. Instead, they infer ITM Call IV using **Put-Call Parity** ($C - P = S - K e^{-rT}$) from the corresponding OTM Put contract. Equity OTM puts trade at a structural volatility premium due to institutional downside hedging demand, driving Yahoo's reported IV up to **~43%**.

### 3. Systematic Parallel Shift on Long-Dated LEAPs ($T = 2.26$ Years)
* **Observed Divergence**: For the long-dated December 15, 2028 expiration ($T = 2.26$ years), `my_iv` sits consistently **8 to 11 percentage points below** Yahoo Finance's quoted IV across **all strikes** (e.g., $28.02\%$ vs $37.09\%$ at the $330 strike).
* **Cause: Unmodeled Continuous Dividend Yield ($q$)**:
  * Real market prices account for future quarterly dividend payouts over the 2.26-year horizon. Dividends reduce the expected future stock price ($S_{\text{eff}} = S e^{-q T}$), which lowers real market call prices.
  * Our solver assumed $q = 0$ (zero dividends), expecting calls to be more expensive ($S = 326.57$).
  * When inputting the cheaper market price into a $q = 0$ Black-Scholes formula, the solver compensates for the "missing" dividend price drag by artificially suppressing calculated volatility ($\sigma$).
* **Mathematical Mechanism**:
  $$\text{Call}_{\text{BS}} = S e^{-q T} N(d_1) - K e^{-r T} N(d_2)$$
  To match the market price when $q=0$ is wrongly assumed, $\sigma$ must decrease to offset the unadjusted $S$.

---

## Practical Takeaways for Quantitative Modeling

1. **Filtering Strategy**: Always drop `bid == 0` rows and restrict IV extraction to options with meaningful Vega (typically $K \in [0.85 S, 1.15 S]$) when using direct Black-Scholes solvers.
2. **Synthetic Data Substitution**: To price deep ITM contracts accurately in production, derive IVs from liquid OTM options using Put-Call Parity rather than directly inverting illiquid ITM mid-prices.
3. **Merton Model Extension for LEAPs**: Standard Black-Scholes ($q=0$) is sufficient for short-dated options ($T < 60$ days). For long-dated LEAPs, continuous dividend yield ($q$) and yield-curve rate adjustments ($r(T)$) are strictly required to avoid multi-point IV underestimation.
