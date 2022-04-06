import pandas as pd

def get_latest_trades(cursor, base_name):    
    cursor.execute("""
    select tsMs, currencyPairId, amount, price,  marketId, orderSide,
           lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName,
           lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quoteName,
           lookUp('markets', 'exchange', 'id', marketId) AS market,
           lookUp('exchanges', 'name', 'id', exchangeId) AS exchange
    from trades 
    where baseName = (%(baseName)s) 
    order by tsMs DESC
    """, {"baseName": base_name})

    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])    
    return df[["tsMs", "quoteName", "market", "exchange", "amount", "price", "orderSide"]]

def latest_period_prices(cursor, base_name):
    cursor.execute("""
    select avg(price) AS avgPrice, max(price) as maxPrice, min(price) AS minPrice, 
           count(*) AS count, sum(amount) AS amountTraded
    from trades 
    WHERE lookUp('pairs', 'baseName', 'id', currencyPairId) = (%(baseName)s) 
    AND lookUp('pairs', 'quoteName', 'id', currencyPairId) = 'United States Dollar'
    AND tsMs > cast(ago('PT1M') as long)
    """, {"baseName": base_name})

    return pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

def previous_period_prices(cursor, base_name):
    cursor.execute("""
    select avg(price) AS avgPrice, max(price) as maxPrice, min(price) AS minPrice, 
           count(*) AS count, sum(amount) AS amountTraded
    from trades 
    WHERE lookUp('pairs', 'baseName', 'id', currencyPairId) = (%(baseName)s) 
    AND lookUp('pairs', 'quoteName', 'id', currencyPairId) = 'United States Dollar'
    AND tsMs > cast(ago('PT2M') as long) 
    AND tsMs < cast(ago('PT1M') as long)
    """, {"baseName": base_name})
    return pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

def get_pairs(cursor, base_name):
    cursor.execute("""
    select lookUp('exchanges', 'name', 'id', exchangeId) AS market, count(*) AS count
    from trades 
    WHERE lookUp('pairs', 'baseName', 'id', currencyPairId) = (%(baseName)s) 
    group by market
	order by count DESC
    """, {"baseName": base_name})
    return pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

def get_assets(cursor, base_name):
    cursor.execute("""
    select lookUp('pairs', 'quoteName', 'id', currencyPairId) AS asset, count(*) AS count
    from trades 
    WHERE lookUp('pairs', 'baseName', 'id', currencyPairId) = (%(baseName)s) 
    group by asset
	order by count DESC
    """, {"baseName": base_name})
    return pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

def get_order_side(cursor, base_name):
    cursor.execute("""
    select orderSide, count(*) AS count
    from trades 
    WHERE lookUp('pairs', 'baseName', 'id', currencyPairId) = (%(baseName)s) 
    AND orderSide != 'null'
    group by orderSide
	order by count DESC
    """, {"baseName": base_name})
    return pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

def get_all_latest_trades(cursor):
    cursor.execute("""
    select tsMs, currencyPairId, amount, price,  marketId, orderSide,
           lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName,
           lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quoteName,
           lookUp('markets', 'exchange', 'id', marketId) AS market,
           lookUp('exchanges', 'name', 'id', exchangeId) AS exchange
    from trades 
    order by tsMs DESC
    LIMIT 50
    """)

    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])    
    return df[["tsMs", "baseName", "quoteName", "market", "exchange", "amount", "price", "orderSide"]]

def get_all_pairs(cursor):
    cursor.execute("""
    select lookUp('pairs', 'baseName', 'id', currencyPairId) AS base,
       lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quote, 
	   count(*) AS transactions,
	   sum(amount) AS amountTraded,
       max(amount) as biggestTrade,
       avg(amount) as averageTrade
    from trades 
    group by quote, base
    order by transactions DESC
    limit 10
    """)

    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
    for column in ["transactions", "amountTraded", "biggestTrade", "averageTrade"]:
        df[column]=df[column].map('{:,.3f}'.format)
    return df

def get_all_assets(cursor):
    cursor.execute("""
    select lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName, 
           min(price) AS minPrice, avg(price) AS avgPrice, max(price) as maxPrice,  
           count(*) AS count, sum(amount) AS amountTraded		   
    from trades 
    WHERE lookUp('pairs', 'quoteName', 'id', currencyPairId) = 'United States Dollar'
    --AND tsMs > cast(ago('PT2M') as long) 
    --AND tsMs < cast(ago('PT1M') as long)
	group by baseName
	order by count DESC
    """)

    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

    for column in ["avgPrice", "minPrice", "maxPrice", "amountTraded", "count"]:
        df[column]=df[column].map('{:,.3f}'.format)
    return df


def get_top_pairs_buy_side(cursor, quote_name):
    cursor.execute("""
    select sum(amount*price) AS totalAmount,
           lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName,
           lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quoteName
    from trades 
    where quoteName = (%(quoteName)s) AND orderSide = 'BUYSIDE'
    group by baseName, quoteName
    order by totalAmount DESC
    """, {"quoteName": quote_name})
    return pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

def get_top_pairs_sell_side(cursor, quote_name):
    cursor.execute("""
    select sum(amount*price) AS totalAmount,
           lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName,
           lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quoteName
    from trades 
    where quoteName = (%(quoteName)s) AND orderSide = 'SELLSIDE'
    group by baseName, quoteName
    order by totalAmount DESC
    """, {"quoteName": quote_name})
    return pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

def quotes(cursor):
    cursor.execute("""
    select count(*) AS count,
       lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quoteName
    from trades 
    where quoteName != 'null'
    group by quoteName
    order by count desc
    limit 20
    """)
    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description]) 

    return df["quoteName"].values

def bases(cursor):
    cursor.execute("""
    select count(*) AS count,
       lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName
    from trades 
    where baseName != 'null'
    group by baseName
    order by count desc
    limit 20
    """)
    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description]) 

    return df["baseName"].values