from abc import ABC, abstractmethod
from bs4 import BeautifulSoup as bs
import FinanceDataReader as fdr
import finnhub
import pandas as pd
import pyqtgraph as pg
import requests
import yaml
from pyqt.date import get_timestamp
from pyqt.date import get_n_days_ago
from pyqt.util import resource_path


class Stock(ABC):

    def __init__(self, symbol):
        self.symbol = symbol
        self.finnhub_client = finnhub.Client(api_key=self.get_api_key())
        self.daily = 'D'
        one_year_ago = get_n_days_ago(365)
        today = pd.Timestamp.today().normalize()
        self.start = get_timestamp(one_year_ago)
        self.end = get_timestamp(today)

    def get_api_key(self):
        path = resource_path('api.yaml')
        with open(path) as f:
            yml = yaml.load(f, Loader=yaml.FullLoader)
            api_key = yml['FINNHUB_APIKEY']
        return api_key

    @abstractmethod
    def get_price(self):
        pass

    def get_price_now(self):
        return self.finnhub_client.quote(self.symbol)

    def draw_chart(self):
        pg.setConfigOption('background', 'w')
        price = self.get_price()
        close = price['c']
        date = price['t']
        plt = pg.PlotWidget()
        plt.plot(date, close, pen=pg.mkPen('b', width=5))
        plt.setAxisItems({'bottom': pg.DateAxisItem()})
        plt.showGrid(x=True, y=True)
        plt.setMouseEnabled(x=False, y=False)

        return plt


class UsStock(Stock):

    def __init__(self, symbol):
        super().__init__(symbol)

    def get_price(self):
        res = self.finnhub_client.stock_candles(
                self.symbol,
                self.daily,
                self.start,
                self.end
            )
        return res


class Crypto(Stock):

    def __init__(self, symbol):
        super().__init__(symbol)

    def get_price(self):
        res = self.finnhub_client.crypto_candles(
                self.symbol,
                self.daily,
                self.start,
                self.end
            )
        return res


class KorStock(Stock):

    def __init__(self, symbol):
        self.symbol = symbol

    def get_price(self):
        one_year_ago = get_n_days_ago(365)
        date = one_year_ago.strftime('%Y-%m-%d')
        price = fdr.DataReader(self.symbol, date)
        price = price.reset_index(level=0)
        price = self.change_col_name(price)
        price['t'] = [get_timestamp(x) for x in price['t']]
        return price

    def scrape_from_naver_finance(self):
        url = f'https://finance.naver.com/item/main.nhn?code={self.symbol}'
        res = requests.get(url)
        res.raise_for_status()
        html = res.text
        soup = bs(html, 'html.parser')
        today = soup.select_one('#chart_area > div.rate_info > div')
        tags = today.find_all('span', class_='blind')
        return tags

    def get_price_now(self):
        tags = self.scrape_from_naver_finance()
        info = []
        for tag in tags:
            item = tag.get_text()
            item = item.replace(',', '')
            info.append(item)
        label = ['c', 'd', 'dp']
        price_now = {k: v for k, v in zip(label, info)}
        return price_now

    def change_col_name(self, price):
        new_col_name = ['t', 'o', 'h', 'l', 'c', 'v', 'pct']
        price.columns = new_col_name
        return price
