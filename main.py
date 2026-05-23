import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import numpy as np
from pathlib import Path
import re

# Configure Chrome Options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# chrome_options.page_load_strategy = "eager"

stock_indexes = {
    "idx_ndx": "NASDAQ 100",
    "idx_sp500": "S&P 500"
}

def build_driver():
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(500)
    driver.set_script_timeout(500)

    return driver

def get_stock_list():
    with build_driver() as driver:
        file_name =  "stock_universe.csv"
        stock_universe = []

        if Path(file_name).is_file():
            df = pd.read_csv(file_name)
            stock_universe = df.to_dict(orient="records")

            return stock_universe
            
        for stock_index_code, stock_index_name in stock_indexes.items():
            for page_index in range(0, 3):
                stock_list_url = f"https://finviz.com/screener?v=111&f=cap_mega,{stock_index_code}&r={20 * page_index + 1}"
                
                driver.get(stock_list_url)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                
                stock_list = soup.select("td[data-boxover-ticker]")
                    
                for stock in stock_list:
                    ticker = stock["data-boxover-ticker"]
                    company = stock["data-boxover-company"]
                    industry = stock["data-boxover-industry"]
                    country = stock["data-boxover-country"]
                    
                    if not any(stock["ticker"] == ticker for stock in stock_universe):
                        stock_universe.append({
                            "ticker": ticker,
                            "company": company,
                            "industry": industry,
                            "country": country,
                            "exchange": "NASDAQ" if "NASDAQ" in stock_index_name else "NYSE"
                        })

        if stock_universe:
            df = pd.DataFrame(data=stock_universe)
            df.to_csv(file_name, index=False)

        return stock_universe

def get_finantial_stats(stock_list: list) -> list:
    target_stats = {
        "pe_ratio": "Price to earnings ratio",
        "roic": "Return on invested capital %",
        "fcf_share": "Free cash flow per share",
        "operating_margin": "Operating margin %",
        "de_ratio": "Debt to equity ratio",
        "shares_outstanding": "Total common shares outstanding"
    }
    
    all_stats = []

    for stock in stock_list[:1]:
        stock_stats = {}
        stock_stats["ticker"] = stock["ticker"]

        stock_stats_url = f"https://www.tradingview.com/symbols/{stock["exchange"]}-{stock["ticker"]}/financials-statistics-and-ratios/"
        with build_driver() as driver:
            driver.get(stock_stats_url)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            last_price = soup.select_one('span[data-qa-id="symbol-last-value"] span')
            last_price = re.sub(r"[^\d.-]", "", last_price.text)
            if last_price:
                stock_stats[f"last_price"] = float(last_price)

            for stat_key, stat_name in target_stats.items():
                stats_list = (soup
                    .select_one(f'div[data-name="{stat_name}"]')
                    .select_one('div[class*="values-"]')
                    .select('div[class*="value-"]')
                )

                stat_values = []
                for stat_text in stats_list:
                    stat_value = re.sub(r"[^\d.-]", "", stat_text.text)
                    
                    if stat_value:
                        stat_values.append(float(stat_value))
                
                for i, stat_value in enumerate(stat_values):
                    stock_stats[f"{stat_key}_{len(stat_values) - i}"] = stat_value
            
            all_stats.append(stock_stats)
    
    return all_stats
def get_finantial_income_statement(stock_list: list) -> list:
    target_stats = {
        "total_revenue": "Total revenue",
    }

    all_stats = []

    for stock in stock_list[:1]:
        stock_stats = {}
        stock_stats["ticker"] = stock["ticker"]
        
        stock_stats_url = f"https://www.tradingview.com/symbols/{stock["exchange"]}-{stock["ticker"]}/financials-income-statement/"
        
        with build_driver() as driver:
            driver.get(stock_stats_url)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            for stat_key, stat_name in target_stats.items():
                stats_list = (soup
                    .select_one(f'div[data-name="{stat_name}"]')
                    .select_one('div[class*="values-"]')
                    .select('div[class*="value-"]')
                )

                stat_values = []
                for stat_text in stats_list:
                    stat_value = re.sub(r"[^\d.-]", "", stat_text.text)
                    
                    if stat_value:
                        stat_values.append(float(stat_value))
                
                for i, stat_value in enumerate(stat_values):
                    stock_stats[f"{stat_key}_{len(stat_values) - i}"] = stat_value
            
            all_stats.append(stock_stats)

    return all_stats

def get_finantial_earnings(stock_list: list) -> list:
    target_stats = {
        "eps": "Reported",
    }

    all_stats = []

    for stock in stock_list[:1]:
        stock_stats = {}
        stock_stats["ticker"] = stock["ticker"]
        
        stock_stats_url = f"https://www.tradingview.com/symbols/{stock["exchange"]}-{stock["ticker"]}/financials-earnings/?earnings-period=FY&revenues-period=FY"
        
        with build_driver() as driver:
            driver.get(stock_stats_url)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            for stat_key, stat_name in target_stats.items():
                stats_list = (soup
                    .select_one(f'div[data-name="{stat_name}"]')
                    .select_one('div[class*="values-"]')
                    .select('div[class*="value-"]')
                )

                stat_values = []
                for stat_text in stats_list:
                    stat_value = re.sub(r"[^\d.-]", "", stat_text.text)
                    
                    if stat_value:
                        stat_values.append(float(stat_value))
                
                for i, stat_value in enumerate(stat_values):
                    stock_stats[f"{stat_key}_{len(stat_values) - i}"] = stat_value
            
            all_stats.append(stock_stats)
    
    return all_stats

stock_list = get_stock_list()
finantial_stats = get_finantial_stats(stock_list)
finantial_income_statement = get_finantial_income_statement(stock_list)
finantial_earnings = get_finantial_earnings(stock_list)

df_stock_list = pd.DataFrame(data=stock_list)
df_finantial_stats = pd.DataFrame(data=finantial_stats)
df_finantial_income_statement = pd.DataFrame(data=finantial_income_statement)
df_finantial_earnings = pd.DataFrame(data=finantial_earnings)

df = pd.merge(df_stock_list, df_finantial_stats, on="ticker")
df = pd.merge(df, df_finantial_income_statement, on="ticker")
df = pd.merge(df, df_finantial_earnings, on="ticker")

# --------------
# PE Ratio
# --------------
# Score centered on mean.
df["pe_ratio_score"] = df["pe_ratio_1"] / df.filter(like="pe_ratio_").mean(axis=1) - 1

# --------------
# FCF/share
# --------------
df["fcf_share_cagr"] = np.where(df["fcf_share_5"] > 0, (df["fcf_share_1"] / df["fcf_share_5"]) ** (1 / 5) - 1, np.nan)
df["eps_cagr"] = np.where(df["eps_5"] > 0, (df["eps_1"] / df["eps_5"]) ** (1 / 5) - 1, np.nan)
# Relative growth velocity (rgv) of FCF per share in relation to EPS.
df["fcf_share_rgw"] = df["fcf_share_cagr"] / df["eps_cagr"]
# FCF per share growth consistency.
df["fcf_share_trend"] = (
    (df["fcf_share_4"] > df["fcf_share_5"]) +
    (df["fcf_share_3"] > df["fcf_share_4"]) +
    (df["fcf_share_2"] > df["fcf_share_3"]) +
    (df["fcf_share_1"] > df["fcf_share_2"])
) / 4
# Use 10% as target yield to normailize.
df["fcf_yield"] = (df["fcf_share_1"] / df["last_price"]) / 0.1
df["fcf_share_score"] = df["fcf_share_trend"] * df["fcf_share_rgw"] * df["fcf_yield"]

# --------------
# Total revenue
# --------------
df["total_revenue_cagr"] = np.where(
    df["total_revenue_5"] > 0, (df["total_revenue_1"] / df["total_revenue_5"]) ** (1 / 5) - 1, np.nan
)
df["total_revenue_trend"] = (
    (df["total_revenue_4"] > df["total_revenue_5"]) +
    (df["total_revenue_3"] > df["total_revenue_4"]) +
    (df["total_revenue_2"] > df["total_revenue_3"]) +
    (df["total_revenue_1"] > df["total_revenue_2"])
) / 4
df["total_revenue_score"] = df["total_revenue_trend"] * df["total_revenue_cagr"]

# --------------
# Operating margin
# --------------
df["operating_margin_strength"] = df["operating_margin_1"] / 0.25
df["operating_margin_trend"] = (
    (df["operating_margin_4"] >= df["operating_margin_5"] * 0.98) +
    (df["operating_margin_3"] >= df["operating_margin_4"] * 0.98) +
    (df["operating_margin_2"] >= df["operating_margin_3"] * 0.98) +
    (df["operating_margin_1"] >= df["operating_margin_2"] * 0.98)
) / 4
df["operating_margin_score"] = df["operating_margin_trend"] * df["operating_margin_strength"]

# --------------
# ROIC
# --------------
df["roic_strength"] = df["roic_1"] / 0.25
df["roic_trend"] = (
    (df["roic_4"] >= df["roic_5"] * 0.98) +
    (df["roic_3"] >= df["roic_4"] * 0.98) +
    (df["roic_2"] >= df["roic_3"] * 0.98) +
    (df["roic_1"] >= df["roic_2"] * 0.98)
) / 4
df["roic_score"] = df["roic_trend"] * df["roic_strength"]


# print(df[["fcf_share_1", "fcf_share_5"]])
# print(df[["eps_1", "eps_5"]])
# print(df[["fcf_share_cagr", "eps_cagr", "fcf_share_rgw", "fcf_share_trend", "fcf_share_score"]])



