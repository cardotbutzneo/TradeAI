===================================================================
 HELP: --generate
===================================================================
Usage:
  ./run.sh --generate [--file=PATH] [--fdate=YYYY-MM-DD] [--dur=DAYS]

Arguments:
  --file  : Filepath of the generated output CSV.
            (Default: "data/historic.csv")
  --fdate : First date of the historical data (Format: YYYY-MM-DD).
            (Default: today at 9:30 AM)
  --dur   : Duration of the simulation in days.
            (Default: 7 days)

Notes:
  * Two tickers are generated on every run: GOOG (starting at 142.05)
    and APPL (starting at 41.02), each following a Geometric Brownian
    Motion (10%/year drift, 25%/year volatility).
  * Opening and closing times are fixed to Paris Stock Market hours:
    9:30 AM to 5:00 PM, Monday to Friday (no weekend data).
  * The generator emits one price tick every 5 simulated minutes.
  * Points per ticker per day: 102 (one every 5 minutes over the
    9:30-17:00 window).
  * Output format (CSV, one line per tick):
      date,ticker,price,volume,currency,hash
===================================================================
