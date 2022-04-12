import pandas as pd

def get_latest_trades(cursor, base_name):
    cursor.execute(f"""
    select tsMs, currencyPairId, amount, price,  marketId, orderSide,
           lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName,
           lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quoteName,
           lookUp('markets', 'exchange', 'id', marketId) AS market,
           lookUp('exchanges', 'name', 'id', exchangeId) AS exchange
    from trades 
    WHERE IN_SUBQUERY(
        currencyPairId, 
        'SELECT ID_SET(id) FROM pairs WHERE baseName = ''{base_name}'''
        ) = 1
    order by tsMs DESC
    """, {"baseName": base_name})

    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])    
    return df[["tsMs", "quoteName", "market", "exchange", "amount", "price", "orderSide"]]

def latest_period_prices(cursor, base_name, interval):
    cursor.execute(f"""
    select avg(price) AS avgPrice, max(price) as maxPrice, min(price) AS minPrice, 
           count(*) AS count, sum(amount) AS amountTraded
    from trades 
    WHERE IN_SUBQUERY(
        currencyPairId, 
        'SELECT ID_SET(id) FROM pairs WHERE baseName = ''{base_name}'' AND quoteName = ''United States Dollar'''
        ) = 1
    AND tsMs > cast(ago((%(intervalString)s)) as long)
    """, {"baseName": base_name, "intervalString": f"PT{interval}M"})
    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
    return df

def previous_period_prices(cursor, base_name, interval):

    cursor.execute(f"""
    select avg(price) AS avgPrice, max(price) as maxPrice, min(price) AS minPrice, 
           count(*) AS count, sum(amount) AS amountTraded
    from trades 
    WHERE IN_SUBQUERY(
        currencyPairId, 
        'SELECT ID_SET(id) FROM pairs WHERE baseName = ''{base_name}'' AND quoteName = ''United States Dollar'''
        ) = 1
    AND tsMs < cast(ago((%(intervalString)s)) as long)
    AND tsMs > cast(ago((%(previousIntervalString)s)) as long)
    """, {"baseName": base_name, "intervalString": f"PT{interval}M", "previousIntervalString": f"PT{interval*2}M"})
    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
    
    return df

def all_prices(cursor, base_name, interval):
    cursor.execute(f"""
    select tsMs, price
    from trades 
    WHERE IN_SUBQUERY(
        currencyPairId, 
        'SELECT ID_SET(id) FROM pairs WHERE baseName = ''{base_name}'' AND quoteName = ''United States Dollar'''
        ) = 1
    AND tsMs > cast(ago((%(intervalString)s)) as long)
    ORDER BY tsMs DESC
    LIMIT 10000
    """, {"baseName": base_name,"intervalString": f"PT{interval}M"})
    return pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

def get_pairs(cursor, base_name, interval):
    cursor.execute(f"""
    select lookUp('exchanges', 'name', 'id', exchangeId) AS market, count(*) AS count
    from trades     
    WHERE IN_SUBQUERY(
        currencyPairId, 
        'SELECT ID_SET(id) FROM pairs WHERE baseName = ''{base_name}'''
        ) = 1
    AND tsMs > cast(ago((%(intervalString)s)) as long)
    group by market
	order by count DESC
    """, {"baseName": base_name, "intervalString": f"PT{interval}M"})
    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
    return df

def get_assets(cursor, base_name, interval):
    cursor.execute(f"""
    select lookUp('pairs', 'quoteName', 'id', currencyPairId) AS asset, count(*) AS count
    from trades 
    WHERE IN_SUBQUERY(
        currencyPairId, 
        'SELECT ID_SET(id) FROM pairs WHERE baseName = ''{base_name}'''
        ) = 1
    AND tsMs > cast(ago((%(intervalString)s)) as long) 
    group by asset
	order by count DESC
    """, {"baseName": base_name, "intervalString": f"PT{interval}M"})
    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
    return df

def get_order_side(cursor, base_name, interval):
    cursor.execute(f"""
    select orderSide, count(*) AS count
    from trades 
    WHERE IN_SUBQUERY(
        currencyPairId, 
        'SELECT ID_SET(id) FROM pairs WHERE baseName = ''{base_name}'''
        ) = 1
    AND orderSide != 'null'
    AND tsMs > cast(ago((%(intervalString)s)) as long) 
    group by orderSide
	order by count DESC
    """, {"baseName": base_name, "intervalString": f"PT{interval}M"})
    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
    return df

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

def get_all_pairs(cursor, interval):
    cursor.execute("""
    select lookUp('pairs', 'baseName', 'id', currencyPairId) AS base,
       lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quote, 
	   count(*) AS transactions,	   
       max(amount) as biggestTrade,
       avg(amount) as averageTrade,
       sum(amount) AS amountTraded
    from trades 
    where tsMs > cast(ago((%(intervalString)s)) as long)
    group by quote, base
    order by transactions DESC
    limit 10
    """, {"intervalString": f"PT{interval}M"})

    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
    for column in ["transactions", "amountTraded", "biggestTrade", "averageTrade"]:
        df[column]=df[column].map('{:,.3f}'.format)
    return df

def get_all_assets(cursor, interval):
    cursor.execute("""
    select lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName, 
           min(price) AS minPrice, avg(price) AS avgPrice, max(price) as maxPrice,  
           count(*) AS count, sum(amount) AS amountTraded		   
    from trades 
    WHERE lookUp('pairs', 'quoteName', 'id', currencyPairId) = 'United States Dollar'
    AND tsMs > cast(ago((%(intervalString)s)) as long)
	group by baseName
	order by count DESC
    """, {"intervalString": f"PT{interval}M"})

    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

    for column in ["avgPrice", "minPrice", "maxPrice", "amountTraded", "count"]:
        df[column]=df[column].map('{:,.3f}'.format)
    return df

def get_aggregate_trades_current_period(cursor, interval):
    cursor.execute("""
    select count(*) AS count, sum(amount) AS amountTraded	   
    from trades 
    WHERE tsMs > cast(ago((%(intervalString)s)) as long)
	order by count DESC
    """, {"intervalString": f"PT{interval}M"})

    return pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

def get_aggregate_trades_previous_period(cursor, interval):
    cursor.execute("""
    select count(*) AS count, sum(amount) AS amountTraded	   
    from trades 
    WHERE tsMs < cast(ago((%(intervalString)s)) as long)
    AND tsMs > cast(ago((%(previousIntervalString)s)) as long)
	order by count DESC
    """, {"intervalString": f"PT{interval}M", "previousIntervalString": f"PT{interval*2}M"})

    return pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

def get_exchange_buy_side(cursor, interval):
    cursor.execute("""
    select lookUp('exchanges', 'name', 'id', exchangeId) AS exchangeName, count(*) AS transactions
    from trades
    where orderSide = 'BUYSIDE'
    AND tsMs > cast(ago((%(intervalString)s)) as long)
    group by exchangeName
    order by transactions DESC
    """, {"intervalString": f"PT{interval}M"})
    return pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

def get_quote_buy_side(cursor, interval):
    cursor.execute("""
    select lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quoteName, count(*) AS transactions
    from trades
    where orderSide = 'BUYSIDE'
    AND tsMs > cast(ago((%(intervalString)s)) as long)
    group by quoteName
    order by transactions DESC
    """, {"intervalString": f"PT{interval}M"})
    return pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

def get_top_pairs_buy_side(cursor, quote_name, interval):
    cursor.execute("""
    select sum(amount*price) AS totalAmount,
           lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName,
           lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quoteName
    from trades 
    where quoteName = (%(quoteName)s) AND orderSide = 'BUYSIDE'
    AND tsMs > cast(ago((%(intervalString)s)) as long)
    group by baseName, quoteName
    order by totalAmount DESC
    """, {"quoteName": quote_name, "intervalString": f"PT{interval}M"})
    return pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

def get_top_pairs_sell_side(cursor, quote_name, interval):
    cursor.execute("""
    select sum(amount*price) AS totalAmount,
           lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName,
           lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quoteName
    from trades 
    where quoteName = (%(quoteName)s) AND orderSide = 'SELLSIDE'
    AND tsMs > cast(ago((%(intervalString)s)) as long)
    group by baseName, quoteName
    order by totalAmount DESC
    """, {"quoteName": quote_name, "intervalString": f"PT{interval}M"})
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