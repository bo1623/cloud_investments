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
    prices = pd.read_csv('bvp_historical_prices_2020.csv')
    latest = prices['Date'].iloc[-1]
    day, month, year = latest.split('/')

    tickers = list(prices.columns)
    tickers.remove('Date')
    ls_key = 'Adj Close'
    start = datetime.date(int(year), int(month), int(day))
    end = datetime.date.today()

    if start == end:
        LOG.info('Prices are already up to date')
        return

    LOG.info('Downloading historical prices from Yahoo from {} to {}'.format(start, end))
    try:
        f = web.DataReader(tickers, 'yahoo', start, end)
    except ValueError:
        LOG.info('{} Yahoo prices not available for download yet'.format(end))
        sys.exit(0)
    close_data = f[ls_key]
    px = pd.DataFrame(close_data)
    print(px.head())

    missing_prices = px.isna().any()
    missing_prices = list(missing_prices.where(missing_prices == True).dropna().index)
    token = os.getenv("IEX_KEY") if env=='prod' else os.getenv("SANDBOX_KEY")
    count = 0
    missing_df = pd.DataFrame()
    LOG.info('Downloading historical prices for missing tickers {} for {} to {}'.format(
        missing_prices, start, end))
    for ticker in missing_prices:
        if env=='prod':
            url = 'https://cloud.iexapis.com/stable/stock/{ticker}/chart/5d?chartCloseOnly=True' \
                  '&includeToday=True&token={token}'.format(ticker=ticker, token=token)
        else:
            url = 'https://sandbox.iexapis.com/stable/stock/{ticker}/chart/5d?chartCloseOnly=True' \
                  '&includeToday=True&token={token}'.format(ticker=ticker, token=token)
        resp = requests.get(url)
        d = pd.DataFrame(resp.json())
        while count == 0:
            missing_df['date'] = d['date']
            count += 1
        missing_df[ticker] = d['close']

    missing_df['date'] = pd.to_datetime(missing_df['date']).apply(lambda x: x.strftime('%#d/%#m/%Y'))
    missing_df.index = missing_df['date']
    missing_df.drop(columns=['date'], inplace=True)
    LOG.info('Missing ticker prices: \n')
    print(missing_df.head())
    print('\n')

    px.drop(columns=missing_prices, inplace=True)
    px.index = px.index.to_series().apply(lambda x: x.strftime('%#d/%#m/%Y'))
    new_prices = pd.merge(px, missing_df, how='left', left_index=True, right_index=True)

    prices.index = prices['Date']
    prices.drop(columns=['Date'], inplace=True)
    initial_columns = list(prices.columns)
    new_prices = new_prices[initial_columns]
    updated_prices = pd.concat([prices, new_prices])
    updated_prices = updated_prices.loc[~updated_prices.index.duplicated(keep='last')]
    updated_prices.to_csv('bvp_historical_prices_2020.csv')
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
    fndmntls_df.to_csv('bvp_emcloud_fundamentals.csv', index=False)
    os.remove('BVP-Nasdaq-Emerging-Cloud-Index.xlsx')


if __name__ == '__main__':
    update_fundamentals()
    update_historical_prices('test')









