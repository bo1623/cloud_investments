import requests
import pandas as pd
import logging
import pandas_datareader.data as web
import datetime
import sys
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(verbose=True)
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)


def update_historical_prices(env):
    constituents = pd.read_csv('bvp_emcloud_fundamentals.csv')
    prices = pd.read_csv('Historical_Prices_updated.csv')
    latest = prices['date'].iloc[-1]
    day, month, year = latest.split('/')
    tickers = list(constituents['Symbol'])
    start = datetime.date(int(year), int(month), int(day))
    end = datetime.date.today()

    if start == end:
        LOG.info('Prices are already up to date')
        return

    token = os.getenv("IEX_KEY") if env == 'prod' else os.getenv("SANDBOX_KEY")
    if env=='prod':
        url = 'https://cloud.iexapis.com/stable/stock/market/batch?symbols={}&types=chart&chartCloseOnly=True' \
              '&token={}&range=5d&includeToday=True'.format(tickers, token)
    else:
        url = 'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={}&types=chart&chartCloseOnly=True' \
              '&token={}&range=5d&includeToday=True'.format(tickers, token)
    resp = requests.get(url)
    new_prices = pd.DataFrame(resp.json())
    new_prices = new_prices.T
    n, _ = prices.shape
    for idx, row in new_prices.iterrows():
        ticker = idx
        data = row['chart']
        for day in data:
            date = day['date']
            y, m, d = date.split('-')
            new_date = '{}/{}/{}'.format(int(d), int(m), y)
            prices.loc[n] = [ticker, new_date, day['close'], day['volume']]
            n += 1
    prices = prices.drop_duplicates(['ticker', 'date'], keep='last')
    prices.to_csv('Historical_Prices_updated.csv', index=False)
    LOG.info('Price update complete for {}'.format(end))


def update_fundamentals():
    LOG.info('Downloading fundamentals from https://cloud-index-data.bvp.com/BVP-Nasdaq-Emerging-Cloud-Index.xlsx\n')
    dls = "https://cloud-index-data.bvp.com/BVP-Nasdaq-Emerging-Cloud-Index.xlsx"
    resp = requests.get(dls)
    output = open('BVP-Nasdaq-Emerging-Cloud-Index.xlsx', 'wb')
    output.write(resp.content)
    output.close()

    fndmntls_df = pd.read_excel('BVP-Nasdaq-Emerging-Cloud-Index.xlsx', sheet_name='Index Constituents')
    fndmntls_df.columns = fndmntls_df.iloc[6]
    fndmntls_df = fndmntls_df.iloc[9:, 1:-1]
    fndmntls_df.dropna(subset=['Symbol'], inplace=True)
    print(fndmntls_df.head())

    hist_df = pd.read_csv('bvp_emcloud_fundamentals.csv')
    hist_tickers = hist_df['Symbol']
    current_tickers = fndmntls_df['Symbol']
    new_names = list(set(current_tickers)-set(hist_tickers))
    removed_names = list(set(hist_tickers)-set(current_tickers))
    if len(new_names) != 0 or len(removed_names) != 0:
        idx_chg = pd.read_csv('index_changes.csv')
        rows, _ = idx_chg.shape
        today = datetime.date.today().strftime('%Y%m%d')
        for n in range(len(new_names)):
            idx_chg.loc[rows+n] = [new_names[n],1,today]
            LOG.info('Added {} to index'.format(new_names[n]))
        rows, _ = idx_chg.shape
        for m in range(len(removed_names)):
            idx_chg.loc[rows+m] = [removed_names[m],-1,today]
            LOG.info('Dropped {} from index'.format(removed_names[m]))
        idx_chg.to_csv('index_changes.csv', index=False)
    fndmntls_df.to_csv('bvp_emcloud_fundamentals.csv', index=False)
    os.remove('BVP-Nasdaq-Emerging-Cloud-Index.xlsx')


if __name__ == '__main__':
    update_fundamentals()
    update_historical_prices('prod')









