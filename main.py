"""Extract fundamental stats for a uninverse of stocks."""

import logging
import re
import time

from pathlib import Path

import numpy as np
import pandas as pd

from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


logger = logging.getLogger(__name__)

chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.page_load_strategy = "normal"

STOCK_INDEXES = {"idx_ndx": "NASDAQ 100", "idx_sp500": "S&P 500"}
LOAD_WAIT_TIME = 3


def build_driver() -> Chrome:
    """Build Chrome driver for web-scrapping.

    :return: Chrome driver.
    :rtype: list[dict]
    """
    driver = Chrome(options=chrome_options)
    driver.set_page_load_timeout(500)
    driver.set_script_timeout(500)

    return driver


def wait_for_data_element(selector: str, timeout: int = 15) -> bool:
    """Wait until the given CSS selector element exists and has non-empty text.

    :param selector: CSS selector.
    :type selector: str
    :param timeout: Max time to wait for the element.
    :type timeout: int
    :return: True if the element was found and has non-empty text. False otherwise.
    :rtype: bool
    """
    """"""
    try:
        WebDriverWait(driver, timeout).until(lambda d: len(d.find_element(By.CSS_SELECTOR, selector).text.strip()) > 0)
    except Exception:
        logger.exception("Data element not found")
    else:
        return True

    return False


def get_stock_universe() -> list[dict]:
    """Get universe of stocks.

    :return: Universe of stocks.
    :rtype: list[dict]
    """
    with build_driver() as driver:
        file_name = "stock_universe.csv"
        stock_universe = []

        if Path(file_name).is_file():
            df = pd.read_csv(file_name)
            stock_universe = df.to_dict(orient="records")

            return stock_universe

        for stock_index_code, stock_index_name in STOCK_INDEXES.items():
            for page_index in range(3):
                stock_list_url = (
                    f"https://finviz.com/screener?v=111&f=cap_mega,{stock_index_code}&r={20 * page_index + 1}"
                )

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
                            "ticker": ticker.replace("-", "."),
                            "company": company,
                            "industry": industry,
                            "country": country,
                            "exchange": "NASDAQ" if "NASDAQ" in stock_index_name else "NYSE",
                        })

        if stock_universe:
            df = pd.DataFrame(data=stock_universe)
            df.to_csv(file_name, index=False)

        return stock_universe


def get_finantial_stats(stock_list: list) -> list[dict]:
    """Get finantial stats for the given stocks.

    :param stock_list: Stocks to get stats for.
    :type stock_list: list
    :return: Stats for the given stocks.
    :rtype: list[dict]
    """
    target_stats = {
        "pe_ratio": "Price to earnings ratio",
        "roic": "Return on invested capital %",
        "fcf_share": "Free cash flow per share",
        "operating_margin": "Operating margin %",
        "de_ratio": "Debt to equity ratio",
        "shares_outstanding": "Total common shares outstanding",
    }

    all_stats = []

    for stock in stock_list:
        logger.info(f"Processing stock: {stock['ticker']}")

        stock_stats = {}
        stock_stats["ticker"] = stock["ticker"]

        stock_stats_url = (
            f"https://www.tradingview.com/symbols/{stock['exchange']}-{stock['ticker']}"
            "/financials-statistics-and-ratios/"
        )
        driver.get(stock_stats_url)

        # Wait for first stat to load.
        time.sleep(LOAD_WAIT_TIME)
        wait_for_data_element(selector=f'div[data-name="{target_stats["pe_ratio"]}"]')

        soup = BeautifulSoup(driver.page_source, "html.parser")

        for stat_key, stat_name in target_stats.items():
            stats_list = (
                soup
                .select_one(f'div[data-name="{stat_name}"]')
                .select_one('div[class*="values-"]')
                .select('div[class*="value-"]')
            )

            stat_values = []
            for stat_text in stats_list:
                stat_value = re.sub(r"[^\d.-]", "", stat_text.text)

                if stat_value:
                    stat_value = float(stat_value)
                    if stat_key in ("roic", "operating_margin"):
                        stat_value = stat_value / 100
                    stat_values.append(stat_value)
            stat_values = stat_values[:-1]
            for i, stat_value in enumerate(stat_values):
                stock_stats[f"{stat_key}_{len(stat_values) - i}"] = stat_value

        all_stats.append(stock_stats)

    return all_stats


def get_finantial_income_statement(stock_list: list) -> list[dict]:
    """Get finantial income statement stats for the given stocks.

    :param stock_list: Stocks to get stats for.
    :type stock_list: list
    :return: Stats for the given stocks.
    :rtype: list[dict]
    """
    target_stats = {
        "total_revenue": "Total revenue",
    }

    all_stats = []

    for stock in stock_list:
        stock_stats = {}
        stock_stats["ticker"] = stock["ticker"]

        stock_stats_url = (
            f"https://www.tradingview.com/symbols/{stock['exchange']}-{stock['ticker']}/financials-income-statement/"
        )
        driver.get(stock_stats_url)

        # Wait for first stat to load.
        time.sleep(LOAD_WAIT_TIME)
        wait_for_data_element(selector=f'div[data-name="{target_stats["total_revenue"]}"]')

        soup = BeautifulSoup(driver.page_source, "html.parser")

        for stat_key, stat_name in target_stats.items():
            stats_list = (
                soup
                .select_one(f'div[data-name="{stat_name}"]')
                .select_one('div[class*="values-"]')
                .select('div[class*="value-"]')
            )

            stat_values = []
            for stat_text in stats_list:
                stat_value = re.sub(r"[^\d.-]", "", stat_text.text)

                if stat_value:
                    stat_values.append(float(stat_value))
            stat_values = stat_values[:-1]
            for i, stat_value in enumerate(stat_values):
                stock_stats[f"{stat_key}_{len(stat_values) - i}"] = stat_value

        all_stats.append(stock_stats)

    return all_stats


def get_finantial_earnings(stock_list: list) -> list:
    """Get finantial earnings stats for the given stocks.

    :param stock_list: Stocks to get stats for.
    :type stock_list: list
    :return: Stats for the given stocks.
    :rtype: list[dict]
    """
    target_stats = {
        "eps": "Reported",
    }

    all_stats = []

    for stock in stock_list:
        stock_stats = {}
        stock_stats["ticker"] = stock["ticker"]

        stock_stats_url = (
            f"https://www.tradingview.com/symbols/{stock['exchange']}-{stock['ticker']}"
            "/financials-earnings/?earnings-period=FY&revenues-period=FY"
        )
        driver.get(stock_stats_url)

        # Wait for first stat to load.
        time.sleep(LOAD_WAIT_TIME)
        wait_for_data_element(selector=f'div[data-name="{target_stats["eps"]}"]')

        soup = BeautifulSoup(driver.page_source, "html.parser")

        for stat_key, stat_name in target_stats.items():
            stats_list = (
                soup
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


driver = build_driver()

stock_list = get_stock_universe()
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
pe_ratio_cols = [f"pe_ratio_{i}" for i in range(1, 6) if f"pe_ratio_{i}" in df.columns]
df["pe_ratio_score"] = 1 - (df["pe_ratio_1"] / df[pe_ratio_cols].median(axis=1))

# --------------
# FCF/share
# --------------
df["fcf_share_cagr"] = np.where(
    (df["fcf_share_1"] > 0) & (df["fcf_share_5"] > 0), (df["fcf_share_1"] / df["fcf_share_5"]) ** (1 / 4) - 1, np.nan
)
df["eps_cagr"] = np.where((df["eps_1"] > 0) & (df["eps_5"] > 0), (df["eps_1"] / df["eps_5"]) ** (1 / 4) - 1, np.nan)
# Relative growth velocity (rgv) of FCF per shar in relation to EPS.
df["fcf_share_rgw"] = np.where(
    df["eps_cagr"] > 0, df["fcf_share_cagr"] / df["eps_cagr"], np.where(df["fcf_share_cagr"] > 0, 1.2, 0.0)
)
df["fcf_share_rgw"] = df["fcf_share_rgw"].clip(lower=0.0, upper=1.2)
# FCF per share growth consistency.
df["fcf_share_trend"] = (
    (df["fcf_share_4"] > df["fcf_share_5"])
    + (df["fcf_share_3"] > df["fcf_share_4"])
    + (df["fcf_share_2"] > df["fcf_share_3"])
    + (df["fcf_share_1"] > df["fcf_share_2"])
) / 4
# Use 10% as target yield to normailize.
df["fcf_yield"] = (df["fcf_share_1"] / (df["pe_ratio_1"] * df["eps_1"])) / 0.1
df["fcf_yield"] = df["fcf_yield"].clip(lower=0.0, upper=1.5)
df["fcf_share_score"] = df["fcf_share_trend"] * df["fcf_share_rgw"] * df["fcf_yield"]

# --------------
# Total revenue
# --------------
df["total_revenue_cagr"] = np.where(
    (df["total_revenue_1"] > 0) & (df["total_revenue_5"] > 0),
    (df["total_revenue_1"] / df["total_revenue_5"]) ** (1 / 4) - 1,
    np.nan,
)
df["total_revenue_trend"] = (
    (df["total_revenue_4"] > df["total_revenue_5"])
    + (df["total_revenue_3"] > df["total_revenue_4"])
    + (df["total_revenue_2"] > df["total_revenue_3"])
    + (df["total_revenue_1"] > df["total_revenue_2"])
) / 4
df["total_revenue_score"] = df["total_revenue_trend"] * df["total_revenue_cagr"].rank(pct=True)

# --------------
# Operating margin
# --------------
df["operating_margin_strength"] = (df["operating_margin_1"] / 0.25).clip(lower=0.0, upper=1.0)
df["operating_margin_trend"] = (
    (df["operating_margin_4"] >= df["operating_margin_5"] * 0.98)
    + (df["operating_margin_3"] >= df["operating_margin_4"] * 0.98)
    + (df["operating_margin_2"] >= df["operating_margin_3"] * 0.98)
    + (df["operating_margin_1"] >= df["operating_margin_2"] * 0.98)
) / 4
df["operating_margin_score"] = df["operating_margin_trend"] * df["operating_margin_strength"]

# --------------
# ROIC
# --------------
df["roic_strength"] = (df["roic_1"] / 0.25).clip(lower=0.0, upper=1.0)
df["roic_trend"] = (
    (df["roic_4"] >= df["roic_5"] * 0.98)
    + (df["roic_3"] >= df["roic_4"] * 0.98)
    + (df["roic_2"] >= df["roic_3"] * 0.98)
    + (df["roic_1"] >= df["roic_2"] * 0.98)
) / 4
df["roic_score"] = df["roic_trend"] * df["roic_strength"]

# --------------
# Debt to equity
# --------------
df["de_ratio_score"] = 1 / (1 + df["de_ratio_1"])

# --------------
# Buyback yield
# --------------
df["buyback_yield"] = (
    (df["shares_outstanding_2"] - df["shares_outstanding_1"]) / df["shares_outstanding_2"] / 0.02
).clip(lower=0.0, upper=1.0)
df["buyback_trend"] = (
    (df["shares_outstanding_4"] < df["shares_outstanding_5"])
    + (df["shares_outstanding_3"] < df["shares_outstanding_4"])
    + (df["shares_outstanding_2"] < df["shares_outstanding_3"])
    + (df["shares_outstanding_1"] < df["shares_outstanding_2"])
) / 4
df["buyback_score"] = df["buyback_trend"] * df["buyback_yield"]

df["ranking_score"] = (
    (df["pe_ratio_score"] * 0.10)
    + (df["fcf_share_score"] * 0.15)
    + (df["total_revenue_score"] * 0.15)
    + (df["operating_margin_score"] * 0.15)
    + (df["roic_score"] * 0.25)
    + (df["de_ratio_score"] * 0.10)
    + (df["buyback_score"] * 0.10)
)
df["has_incomplete_data"] = df.isna().any(axis=1)
df = df.round(4)

df_ranking = df.sort_values(by="ranking_score", ascending=False)
df_ranking.to_csv("stock_ranking.csv", index=False)
