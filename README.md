# Cloud Investments

We're in an age where the importance of data services and all things related are starting to gain momentum. I was looking for ideas on how to monetize this view when I came across this index called the The BVP (Bessemer Venture Partners) Nasdaq Emerging Cloud Index.

This index has consistently outperformed the NASDAQ and S&P500 by multiples since its inception. The index has 50+ names and I thought not all constituents must have posted strong gains this year, surely there must be some losers here that could make good value plays. 

So I set out to conduct some research on this, but being the data engineer that I am, I wanted to create a decent pipeline that would update the prices and fundamentals data on a daily basis, which is what my Python script serves. I wanted to do this because I wanted to track any changes in constituents to the index and any significant changes in the fundamentals of the constituents. Once my script was ready, I created a bat file which I could then run with Windows task scheduler.

Just so you know what I'm referring to, I obtain the fundamentals data from the Bessemer Venture Partners website: https://www.bvp.com/bvp-nasdaq-emerging-cloud-index and is of the form: 

![fundamentals](https://i.imgur.com/tlwpWbi.png)

I had to download the prices myself since they're not readily available on BVP's website. I got this via a combination of Yahoo and my IEX Cloud API. I do this because Yahoo is free and I am stingy with my limited IEX Cloud API messages. 

**Yahoo via pandas_datareader**
```
import pandas_datareader.data as web
f = web.DataReader(tickers, 'yahoo', start, end)
```

**IEX Cloud API**
```
url = 'https://cloud.iexapis.com/stable/stock/{ticker}/chart/5d?chartCloseOnly=True' \
              '&includeToday=True&token={token}'.format(ticker=ticker, token=token)
        resp = requests.get(url)
        d = pd.DataFrame(resp.json())
```

Once my quick and easy pipeline was set up, I then got to work on my jupyter notebooks, and came up with a scatter plot comparing each stock's YTD% against its EV/Annualized Revenue.

<p align='right'>
  <img src="https://i.imgur.com/5cU3MgJ.gif" width="900">
</p>

From here we're able to see that there were only 6 names that are down YTD, while the rest are all up with some names even posting >300% gains. (Well done BVP). Now the scatter points on the bottom left look interesting because they've remained in loss territory while most of the stock market has recovered from the initial COVID slump and secondly because they have low EV/Annualized Revenue, which is an indicator of value.

This gives me a good starting point, next step would be to look further into these names to understand why they've done more poorly than their peers and whether that's justified. 
