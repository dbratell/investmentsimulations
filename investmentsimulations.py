from __future__ import print_function

import argparse
import random


STOCK = (
    # Name, count, price, dividend
    ("Investment firm", 1, 100, 3.5),
    ("Telecom", 1, 100, 4.1),
    )

REV_GROWTH = 1.06
REV_STDDEV = 0.1
COST_GROWTH = REV_GROWTH + 0.04
COST_STDDEV = REV_STDDEV / 2

YEARS = 5
RUNS = 10000

def average(lst, count):
    assert len(lst), "Empty list"
    assert count > 0
    smaller_list = lst[-count:]
    return sum(smaller_list) / len(smaller_list)

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

def select_by_percentile(lst, percentile):
    assert len(lst), "Empty list"
    pos = int(percentile * (len(lst) - 1) + 0.5)
    return lst[pos]

class Case(object):
    def __init__(self):
        self.price_list = []
        self.pe_list = []
        self.earning_list = []
        self.dividend_list = []
        self.stock_count_list = []
        self.cost_list = []
        self.revenue_list = []

    def final_value(self, year):
        return self.price_list[year - 1] * self.stock_count_list[year - 1] + sum(self.dividend_list[:year])

START_PE = 20
BASE_PE = 14
BOTTOM_PE = 7
MAX_PE = 30
def calc_new_pe(pe):
    # So P/E drops quickly but increases slowly. How to model that?
    if pe > BASE_PE:
        pe_change = random.choice([-4, -2, 0, 1, 1, 1, 2])
    else:
        pe_change = random.choice([-3, -1, 0, 1, 1, 2])
    pe = pe + pe_change

    if pe < BOTTOM_PE:
        pe = BOTTOM_PE
    if pe > MAX_PE:
        pe = MAX_PE

    return pe

def simulate_new_rev_cost_year(revenue_list, cost_list, start_stock_price):
    if cost_list:
        prev_cost = cost_list[-1]
        prev_revenue = revenue_list[-1]
        prev_earning = prev_revenue - prev_cost
    else:
        prev_earning = float(start_stock_price) / START_PE
        prev_revenue = (float(start_stock_price) / START_PE) / 0.1 # Assuming 10% margin
        prev_cost = 9.0 * start_stock_price / START_PE

    if prev_earning < 0:
        # Losses -> Cost cuts.
        cost_change = random.normalvariate(0.4 + COST_GROWTH / 2, COST_STDDEV)
        rev_change = random.normalvariate(0.5 + REV_GROWTH / 2, REV_STDDEV)
    else:
        cost_change = random.normalvariate(COST_GROWTH, COST_STDDEV)
        rev_change = random.normalvariate(REV_GROWTH, REV_STDDEV)
        if cost_change < 0:
            cost_change = 0
        if rev_change < 0:
            rev_change = 0
    new_cost = prev_cost * cost_change
    new_revenue = prev_revenue * rev_change
    new_earning = new_revenue - new_cost

    return (new_earning, new_revenue, new_cost)

def main():
    results = {}
    print("Calculating...")
    for run in range(RUNS):
        for stock_name, stock_count, stock_price, stock_dividend in STOCK:
            stock_results = results.setdefault(stock_name, {})
            stock_result_cases = results.setdefault(stock_name + "Cases", [])
            case = Case()
            stock_result_cases.append(case)
            pe = START_PE
            price_list = case.price_list
            dividend_list = case.dividend_list
            earning_list = case.earning_list
            revenue_list = case.revenue_list
            cost_list = case.cost_list
            pe_list = case.pe_list
            stock_count_list = case.stock_count_list
            for year in range(YEARS):
                new_earning, new_revenue, new_cost = simulate_new_rev_cost_year(revenue_list, cost_list, stock_price)
                earning_list.append(new_earning)
                cost_list.append(new_cost)
                revenue_list.append(new_revenue)

                stock_count = 1
                if stock_count_list:
                    stock_count = stock_count_list[-1]

                if dividend_list:
                    last_div_per_share = dividend_list[-1] / stock_count_list[-1]
                else:
                    last_div_per_share = stock_dividend / stock_count
                avg_earnings_per_share = average([stock_price / START_PE] * 5 + earning_list, 5)
                if avg_earnings_per_share <= 0:
                    new_div_per_share = 0
                elif avg_earnings_per_share * 0.8 < last_div_per_share:
                    new_div_per_share = last_div_per_share / 2
                elif avg_earnings_per_share * 0.3 > last_div_per_share:
                    new_div_per_share = avg_earnings_per_share * 0.5
                else:
                    new_div_per_share = last_div_per_share * REV_GROWTH
                new_div = new_div_per_share * stock_count
                dividend_list.append(new_div)

                pe = calc_new_pe(pe)

                if avg_earnings_per_share > 0:
                    pe_price = avg_earnings_per_share * pe
                    sale_price = average(revenue_list, 5)
                    price = max((pe_price, sale_price))
                else:
                    sale_price = average(revenue_list, 5)
                    price = sale_price
#                print("Year %d:\t%d (%g)" % (year + 1, int(price), int(100.0 * price) / stock_price - 100))
                if new_div:
                    reinvest_buy = (new_div * 0.7) / price # Assume 30% taxes
                    stock_count = stock_count + reinvest_buy
                price_list.append(price)
                pe_list.append(pe)
                stock_count_list.append(stock_count)
            stock_results.setdefault("pe_lists", []).append(pe_list)
            stock_results.setdefault("price_lists", []).append(price_list)
            stock_results.setdefault("earning_lists", []).append(earning_list)

    report(results)

def report(results):
    for stock_name, stock_count, stock_price, stock_dividend in STOCK:
        stock_results = results[stock_name]
        stock_result_cases = results[stock_name + "Cases"]
        print("%s" % stock_name)
        print("=" * len(stock_name))
        print("Year  0: %d" % stock_price)
        year = YEARS - 1
        def case_final_value(case):
            return case.final_value(year + 1)
        cases_in_order = sorted(stock_result_cases, key=case_final_value)
        percentiles = (0.05, 0.1, 0.5, 0.9, 0.95)
        case_list = tuple([select_by_percentile(cases_in_order, x) for x in percentiles])
        def case_to_str(case, year):
            return "%3d (+%2d)" % (case.price_list[year],
                                   sum(case.dividend_list[:year + 1]),
                                   )

        for year in range(YEARS):
            print("Year %2d: %s" % (
                    year + 1,
                    " - ".join([case_to_str(x, year) for x in case_list])
                    ))

        def per_year(val):
            return val ** (1.0 / YEARS)
        print("Gain/year:\t%s" %
              " ".join(["%.2f" % per_year(x.final_value(YEARS) / stock_price) for x in case_list]))

        print("P/E:\t%s" %
              " ".join(["%2d" % x.pe_list[YEARS - 1] for x in case_list]))

        if False:
            def earning_list_to_str(earning_list):
                strs = ["%.2f" % x for x in earning_list]
                return "[" + ", ".join(strs) + "]\n"
            print("E:\t%s" %
                  " ".join([earning_list_to_str(x.earning_list) for x in case_list]))
        print("Count:\t%s" %
              " ".join(["%.2f" % x.stock_count_list[YEARS-1] for x in case_list]))
if __name__ == "__main__":
    main()
