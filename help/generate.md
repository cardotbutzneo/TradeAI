===================================================================
 HELP: --generate
===================================================================
Usage:
  ./run.sh --generate [file=...] [fdate=...] [dur=...]

Arguments:
  file  : Filepath of the generated output CSV. 
          (Default: "data/historic.csv")
  fdate : First date of the historical data (Format: YYYY-MM-DD).
          (Default: Today at 9:00 AM)
  dur   : Duration of the simulation in days. 
          (Default: 7 days)

Notes:
  * The end date is automatically calculated as: fdate + dur.
  * Opening and closing times are fixed to the Paris Stock Market 
    hours: from 9:00 AM to 5:30 PM.
  * The program generates a price tick every 5 seconds.
  * Total data points generated per day formula:
    Total = duration * (closing_hour_in_sec - opening_hour_in_sec) / 5
===================================================================