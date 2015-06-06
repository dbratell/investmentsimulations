from __future__ import print_function

import argparse
import random


STOCK = (
    # Name, count, price, dividend
    ("Investor", 100, 200, 7),
    ("Telia", 100, 50, 2.1),
    )

BASE = 1.06
STDDEV = 0.2

YEARS = 15
RUNS = 10000

def nth_percentile(lst, percentile):
    assert len(lst), "Empty list"
    pos = percentile * (len(lst) - 1)
    lower_index = int(pos)
    lower_share = 1 - (pos - lower_index)
    upper_index = lower_index + 1
    upper_share = 1 - lower_share
    sorted_lst = sorted(lst)
#    print("%g -> %d (%g) + %d (%g)" %(percentile, lower_index, lower_share,
#          upper_index, upper_share))
    if upper_share > 0:
        return upper_share * sorted_lst[upper_index] + lower_share * sorted_lst[lower_index]
    return sorted_lst[lower_index]

def main():
    results = {}
    print("Calculating...")
    BASE_PE = 20
    for run in range(RUNS):
        for stock_name, stock_count, stock_price, stock_dividend in STOCK:
            stock_results = results.setdefault(stock_name, {})
 #           print("%s" % stock_name)
 #           print("=" * len(stock_name))
            earning = stock_price / BASE_PE
#            price = stock_price
 #           print("Year 0:\t%d" % price)
            pe = BASE_PE
            ack_div = 0
            for year in range(YEARS):
                stock_year_results = stock_results.setdefault("price%d" % year, [])
                stock_year_dividends = stock_results.setdefault("dividend%d" % year, [])
                change = random.normalvariate(BASE, STDDEV)
                if change < 0:
                    change = 0
                earning = earning * change
                if earning > 0:
                    ack_div += 0.5 * earning
                pe_change = random.choice([-1, 0, 1])
                pe = pe + pe_change
                if pe < 7:
                    pe = 7
                if pe > 30:
                    pe = 30
                
#                print("Year %d:\t%d (%g)" % (year + 1, int(price), int(100.0 * price) / stock_price - 100))
                stock_year_results.append(earning * pe)
                stock_year_dividends.append(ack_div)

    for stock_name, stock_count, stock_price, stock_dividend in STOCK:
        stock_results = results[stock_name]
        print("%s" % stock_name)
        print("=" * len(stock_name))
        print("Year  0: %d" % stock_price)
        for year in range(YEARS):
            stock_year_results = stock_results["price%d" % year]
            stock_year_dividends = stock_results["dividend%d" % year]
            print("Year %2d: %6.2f (+%2d) - %3d (+%2d) - %3d (+%2d) - %3d (+%3d) - %3d (+%3d)" % (
                    year + 1,
#                    min(stock_year_results),
                    nth_percentile(stock_year_results, 0.05),
                    nth_percentile(stock_year_dividends, 0.05),
                    nth_percentile(stock_year_results, 0.1),
                    nth_percentile(stock_year_dividends, 0.1),
                    nth_percentile(stock_year_results, 0.5),
                    nth_percentile(stock_year_dividends, 0.5),
                    nth_percentile(stock_year_results, 0.9),
                    nth_percentile(stock_year_dividends, 0.9),
                    nth_percentile(stock_year_results, 0.95),
                    nth_percentile(stock_year_dividends, 0.95),
#                    max(stock_year_results)
                    ))
            
        print("Gain:\t%.2f %.2f %.2f %.2f %.2f" %
              ((nth_percentile(stock_year_results, 0.05) +
               nth_percentile(stock_year_dividends, 0.05)) / stock_price - 0,
              (nth_percentile(stock_year_results, 0.1) +
               nth_percentile(stock_year_dividends, 0.1)) / stock_price - 0,
              (nth_percentile(stock_year_results, 0.5) +
               nth_percentile(stock_year_dividends, 0.5)) / stock_price - 0,
              (nth_percentile(stock_year_results, 0.9) +
               nth_percentile(stock_year_dividends, 0.9)) / stock_price - 0,
              (nth_percentile(stock_year_results, 0.95) +
               nth_percentile(stock_year_dividends, 0.95)) / stock_price - 0,
              ))

if __name__ == "__main__":
    main()
	
