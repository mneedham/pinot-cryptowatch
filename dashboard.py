import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table  # pip install dash (version 2.0.0 or higher)
from pinotdb import connect, db
import datetime
import math

connection = connect(
            host="localhost",
            port="8099",
            path="/query/sql",
            scheme=( "http"),
        )

def quotes():
    cursor  = connection.cursor()
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

def bases():
    cursor  = connection.cursor()
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

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Crypto Watch Dashboard"
app.config.suppress_callback_exceptions=True

# ------------------------------------------------------------------------------
# App layout
all_quotes = quotes()
all_bases = bases()


app.layout = html.Div([
    html.H1("Crypto Watch Dashboard", style={'text-align': 'center'}),
    html.Div(id='latest-timestamp'),
        dcc.Tabs(id="tabs-example-graph", value='overview', children=[
        dcc.Tab(label='Overview', value='overview'),
        dcc.Tab(label='By asset', value='by-asset'),
    ]),
    html.Div(id='tabs-content-example-graph')
])

@app.callback(Output('tabs-content-example-graph', 'children'),
              Input('tabs-example-graph', 'value'))
def render_content(tab):
    if tab == 'overview':
        return html.Div([
        html.Div([
            html.H2('Pairs'),
            html.Div(id='pairs'),
            html.H2('Assets'),
            html.Div(id='assets'),
            html.H2('Latest Trades'),
            html.Div(id='latest-trades'),
        ]),
        html.Div([
            html.H2('Most Traded Coins'),
            html.Label(children=[
                html.Span("Quote currency:", style={"font-weight": "bold"}),
                dcc.Dropdown(all_quotes, all_quotes[0], id='quotes-dropdown'),
            ]),        
            html.H3("Buy Side"),
            dcc.Graph(id='top-pairs-buy-side', figure={}),
            html.H3 ("Sell Side"),
            dcc.Graph(id='top-pairs-sell-side', figure={})
        ]),
        dcc.Interval(
            id='interval-component',
            interval=1 * 1000,  # in milliseconds
            n_intervals=0
        ) 
        ])
    if tab == 'by-asset':
        return html.Div([
            html.H2("By Asset"),
            html.Label(children=[
                dcc.Dropdown(all_bases, all_bases[0], id='bases-dropdown'),
            ]),  
            dcc.Graph(id='prices', figure={}),
            dcc.Graph(id='markets', figure={}),
            dcc.Graph(id='assets', figure={}),
            dcc.Graph(id='order_side', figure={}),
            html.Div([
                html.H4('Latest Trades'),
                html.Div(id='latest-trades-bases')
            ]),
            dcc.Interval(
            id='interval-component-by-asset',
            interval=1 * 1000,  # in milliseconds
            n_intervals=0
        ) 
        ])


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

def add_delta_trace(fig, title, value, last_value, row, column):
    fig.add_trace(go.Indicator(
        mode = "number+delta",
        title= {'text': title},
        value = value,
        delta = {'reference': last_value, 'relative': True},
        domain = {'row': row, 'column': column})
    )

def add_trace(fig, title, value, row, column):
    fig.add_trace(go.Indicator(
        mode = "number",
        title= {'text': title},
        value = value,
        domain = {'row': row, 'column': column})
    )

@app.callback(
    [Output(component_id='latest-trades-bases', component_property='children'),
     Output(component_id='prices', component_property='figure'),
     Output(component_id='markets', component_property='figure'),
     Output(component_id='assets', component_property='figure'),
     Output(component_id='order_side', component_property='figure')
     ],
    [Input('bases-dropdown', 'value'), Input('interval-component-by-asset', 'n_intervals')]
)
def bases(base_name, n):
    style_table = {'overflowX': 'auto'}
    style_cell = {
        'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis',
    }

    cursor = connection.cursor()

    df = get_latest_trades(cursor, base_name)
    latest_trades = [html.Div([dash_table.DataTable(
        df.to_dict('records'), [{"name": i, "id": i} for i in df.columns],
        style_table=style_table,
        style_cell=style_cell
    )])]

    df_now = latest_period_prices(cursor, base_name)
    df_prev = previous_period_prices(cursor, base_name)
    
    fig = go.Figure()
    if df_now["count"][0] > 0:
        if df_prev["count"][0] > 0:
            add_delta_trace(fig, "Min Price", df_now["minPrice"][0], df_prev["minPrice"][0], 0, 0)
            add_delta_trace(fig, "Average Price", df_now["avgPrice"][0], df_prev["avgPrice"][0], 0, 1)
            add_delta_trace(fig, "Max Price", df_now["maxPrice"][0], df_prev["maxPrice"][0], 0, 2)
            add_delta_trace(fig, "Transactions", df_now["count"][0], df_prev["count"][0], 1, 0)
            add_delta_trace(fig, "Amount Traded", df_now["amountTraded"][0], df_prev["amountTraded"][0], 1, 1)
        else:
            add_delta_trace(fig, "Min Price", df_now["minPrice"][0], 0, 0)
            add_delta_trace(fig, "Average Price", df_now["avgPrice"][0], 0, 1)
            add_delta_trace(fig, "Max Price", df_now["maxPrice"][0], 0, 2)
            add_delta_trace(fig, "Transactions", df_now["count"][0], 1, 0)
            add_delta_trace(fig, "Amount Traded", df_now["amountTraded"][0], 1, 1)
        fig.update_layout(
            grid = {"rows": 2, "columns": 3,  'pattern': "independent"},
        )       
    else:
        fig.update_layout(
            annotations = [{"text": "No transactions found", "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 28}}]
        )

    cursor.execute("""
    select lookUp('exchanges', 'name', 'id', exchangeId) AS market, count(*) AS count
    from trades 
    WHERE lookUp('pairs', 'baseName', 'id', currencyPairId) = (%(baseName)s) 
    group by market
	order by count DESC
    """, {"baseName": base_name})
    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
    fig_market = px.bar(df, x='market', y='count', title="Top markets")

    cursor.execute("""
    select lookUp('pairs', 'quoteName', 'id', currencyPairId) AS asset, count(*) AS count
    from trades 
    WHERE lookUp('pairs', 'baseName', 'id', currencyPairId) = (%(baseName)s) 
    group by asset
	order by count DESC
    """, {"baseName": base_name})
    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
    fig_asset = px.bar(df, x='asset', y='count', title="Top assets")

    cursor.execute("""
    select orderSide, count(*) AS count
    from trades 
    WHERE lookUp('pairs', 'baseName', 'id', currencyPairId) = (%(baseName)s) 
    AND orderSide != 'null'
    group by orderSide
	order by count DESC
    """, {"baseName": base_name})
    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
    fig_order_side = px.bar(df, x='orderSide', y='count', title="Order Side")


    return latest_trades, fig, fig_market, fig_asset, fig_order_side

@app.callback(
    [Output(component_id='latest-trades', component_property='children'),
     Output(component_id='pairs', component_property='children'),
     Output(component_id='assets', component_property='children'),
     Output(component_id='latest-timestamp', component_property='children')],
    [Input('interval-component', 'n_intervals')]
)
def latest_trades(n):
    style_table = {'overflowX': 'auto'}
    style_cell = {
        'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis',
        "padding": '10px'
    }

    cursor = connection.cursor()

    cursor.execute("""
    select tsMs, currencyPairId, amount, price,  marketId, orderSide,
           lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName,
           lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quoteName,
           lookUp('markets', 'exchange', 'id', marketId) AS market,
           lookUp('exchanges', 'name', 'id', exchangeId) AS exchange
    from trades 
    order by tsMs DESC
    """)

    df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])    
    df = df[["tsMs", "baseName", "quoteName", "market", "exchange", "amount", "price", "orderSide"]]

    latest_trades = [html.Div([dash_table.DataTable(
        df.to_dict('records'), [{"name": i, "id": i} for i in df.columns],
        style_table=style_table,
        style_cell=style_cell
    )])]

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

    pairs = [html.Div([dash_table.DataTable(
        df.to_dict('records'), [{"name": i, "id": i} for i in df.columns],
        style_table=style_table,
        style_cell=style_cell
    )])]

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

    assets = [html.Div([dash_table.DataTable(
        df.to_dict('records'), [{"name": i, "id": i} for i in df.columns],
        style_table=style_table,
        style_cell=style_cell,
    )])]

    return latest_trades, pairs, assets, [html.Span(f"Last updated: {datetime.datetime.now()}")]


@app.callback(
    [Output(component_id='top-pairs-buy-side', component_property='figure'),
     Output(component_id='top-pairs-sell-side', component_property='figure')],
    [Input('interval-component', 'n_intervals'), Input('quotes-dropdown', 'value')]
)
def top_pairs_buy_side(n, value):    
    cursor = connection.cursor()

    cursor.execute("""
    select sum(amount*price) AS totalAmount,
           lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName,
           lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quoteName
    from trades 
    where quoteName = (%(quoteName)s) AND orderSide = 'BUYSIDE'
    group by baseName, quoteName
    order by totalAmount DESC
    """, {"quoteName": value})
    df_buy_side = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
    fig_buy = px.bar(df_buy_side, x='baseName', y='totalAmount', log_y=True)

    cursor.execute("""
    select sum(amount*price) AS totalAmount,
           lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName,
           lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quoteName
    from trades 
    where quoteName = (%(quoteName)s) AND orderSide = 'SELLSIDE'
    group by baseName, quoteName
    order by totalAmount DESC
    """, {"quoteName": value})
    df_sell_side = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
    fig_sell = px.bar(df_sell_side, x='baseName', y='totalAmount', log_y=True)

    return [fig_buy, fig_sell]

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)