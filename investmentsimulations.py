from __future__ import print_function

import argparse
import random


STOCK = (
    # Name, count, price, dividend
    ("Investor", 1, 200, 7),
    ("Telia", 1, 50, 2.1),
    )

BASE_GROWTH = 1.06
STDDEV = 0.4

YEARS = 20
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

def main():
    results = {}
    print("Calculating...")
    for run in range(RUNS):
        for stock_name, stock_count, stock_price, stock_dividend in STOCK:
            stock_results = results.setdefault(stock_name, {})
            stock_result_cases = results.setdefault(stock_name + "Cases", [])
            case = Case()
            stock_result_cases.append(case)
            start_earning = stock_price / START_PE
            pe = START_PE
            ack_div = 0
            price_list = case.price_list
            dividend_list = case.dividend_list
            earning_list = case.earning_list
            pe_list = case.pe_list
            stock_count_list = case.stock_count_list
            for year in range(YEARS):
                prev_earning = start_earning
                if earning_list:
                    prev_earning = average(earning_list, 1)
                earning_change = random.normalvariate(BASE_GROWTH, STDDEV)
                new_earning = prev_earning * earning_change
                earning_list.append(new_earning)

                stock_count = 1
                if stock_count_list:
                    stock_count = stock_count_list[-1]

                if dividend_list:
                    div = dividend_list[-1]
                else:
                    div = stock_dividend
                avg_earnings = average(earning_list, 3)
                if avg_earnings <= 0:
                    div = 0
                elif avg_earnings * 0.8 < div:
                    div = div / 2
                elif avg_earnings * 0.3 > div:
                    div = avg_earnings * 0.5
                else:
                    div = div * BASE_GROWTH
                div = div * stock_count
                dividend_list.append(div)

                pe = calc_new_pe(pe)

                if avg_earnings > 0:
                    price = avg_earnings * pe
                else:
                    if price_list:
                        price = price_list[-1] / 2
                    else:
                        price = stock_price / 2
#                print("Year %d:\t%d (%g)" % (year + 1, int(price), int(100.0 * price) / stock_price - 100))
                if div:
                    reinvest_buy = (div * 0.7) / price # Assume 30% taxes
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
        for year in range(YEARS):
            def case_final_value(case):
                return case.final_value(year + 1)
            cases_in_order = sorted(stock_result_cases, key=case_final_value)
            case_05 = select_by_percentile(cases_in_order, 0.05)
            case_10 = select_by_percentile(cases_in_order, 0.1)
            case_50 = select_by_percentile(cases_in_order, 0.5)
            case_90 = select_by_percentile(cases_in_order, 0.9)
            case_95 = select_by_percentile(cases_in_order, 0.95)
            print("Year %2d: %6.2f (+%2d) - %3d (+%2d) - %3d (+%2d) - %3d (+%3d) - %3d (+%3d)" % (
                    year + 1,
                    case_05.price_list[year],
                    sum(case_05.dividend_list[:year + 1]),
                    case_10.price_list[year],
                    sum(case_10.dividend_list[:year + 1]),
                    case_50.price_list[year],
                    sum(case_50.dividend_list[:year + 1]),
                    case_90.price_list[year],
                    sum(case_90.dividend_list[:year + 1]),
                    case_95.price_list[year],
                    sum(case_95.dividend_list[:year + 1]),
                    ))

        print("Gain:\t%.2f %.2f %.2f %.2f %.2f" %
              (case_05.final_value(YEARS) / stock_price - 0,
               case_10.final_value(YEARS) / stock_price - 0,
               select_by_percentile(cases_in_order, 0.50).final_value(YEARS) / stock_price - 0,
               case_90.final_value(YEARS) / stock_price - 0,
               case_95.final_value(YEARS) / stock_price - 0
              ))

        print("P/E:\t%2d %2d %2d %2d %2d" %
              (case_05.pe_list[YEARS-1],
               case_10.pe_list[YEARS-1],
               case_50.pe_list[YEARS-1],
               case_90.pe_list[YEARS-1],
               case_95.pe_list[YEARS-1],
              ))

        def earning_list_to_str(earning_list):
            strs = ["%.2f" % x for x in earning_list]
            return "[" + ", ".join(strs) + "]\n"
        print("E:\t%s %s %s %s %s" %
              (earning_list_to_str(case_05.earning_list),
               earning_list_to_str(case_10.earning_list),
               earning_list_to_str(case_50.earning_list),
               earning_list_to_str(case_90.earning_list),
               earning_list_to_str(case_95.earning_list),
              ))

        print("Count:\t%.2f %.2f %.2f %.2f %.2f" %
              (case_05.stock_count_list[YEARS-1],
               case_10.stock_count_list[YEARS-1],
               case_50.stock_count_list[YEARS-1],
               case_90.stock_count_list[YEARS-1],
               case_95.stock_count_list[YEARS-1],
              ))
if __name__ == "__main__":
    main()
