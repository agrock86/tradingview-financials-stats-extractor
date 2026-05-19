import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
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
    with build_driver() as driver:
        target_stats = {
            "pe_ratio": "Price to earnings ratio",
            "roic": "Return on invested capital %",
            "fcf_share": "Free cash flow per share",
            "operating_margin": "Operating margin %",
            "de_ratio": "Debt to equity ratio",
            "shares_outstanding": "Total common shares outstanding"
        }
        finantial_stats = {}

        for stock in stock_list[:1]:
            finantial_stats_url = f"https://www.tradingview.com/symbols/{stock["exchange"]}-{stock["ticker"]}/financials-statistics-and-ratios/"

            driver.get(finantial_stats_url)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            for stat_name in target_stats.values():
                stat_list = (soup
                    .select_one(f'div[data-name="{stat_name}"]')
                    .select_one('div[class*="values-"]')
                    .select('div[class*="value-"]')
                )

                stat_values = []
                for value_text in stat_list:
                    value_clean = re.sub(r"[^\d.-]", "", value_text.text)
                    
                    if value_clean:
                        stat_values.append(float(value_clean))
                        
                finantial_stats[stat_name] = stat_values
            
        return finantial_stats
def get_finantial_income_statement(stock_list: list) -> list:
    with build_driver() as driver:
        target_stats = {
            "total_revenue": "Total revenue",
        }
        stats = {}

        for stock in stock_list[:1]:
            stats_url = f"https://www.tradingview.com/symbols/{stock["exchange"]}-{stock["ticker"]}/financials-income-statement/"

            driver.get(stats_url)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            for stat_name in target_stats.values():
                stat_list = (soup
                    .select_one(f'div[data-name="{stat_name}"]')
                    .select_one('div[class*="values-"]')
                    .select('div[class*="value-"]')
                )

                stat_values = []
                for value_text in stat_list:
                    value_clean = re.sub(r"[^\d.-]", "", value_text.text)
                    
                    if value_clean:
                        stat_values.append(float(value_clean))
                        
                stats[stat_name] = stat_values
            
        return stats

stock_list = get_stock_list()
finantial_stats = get_finantial_stats(stock_list)
finantial_income_statement = get_finantial_income_statement(stock_list)



