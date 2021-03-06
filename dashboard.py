import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table  # pip install dash (version 2.0.0 or higher)
from pinotdb import connect, db
import datetime
import querydb
import tabs
import dash_utils
import concurrent.futures

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Crypto Watch Real-Time Dashboard"
app.config.suppress_callback_exceptions=True

connection = connect(
    host="localhost",
    port="8099",
    path="/query/sql",
    scheme=( "http"),
)
cursor = connection.cursor()
all_quotes = querydb.quotes(cursor)
all_bases = querydb.bases(cursor)

app.layout = html.Div([
    html.H1("Crypto Watch Real-Time Dashboard", style={'text-align': 'center'}),
    html.Div(children=[
        html.Div(children=[
            html.Div(children=[
                html.Span("Refresh rate (seconds)", style={"font-weight": "bold"})
            ], className="two columns"),
            html.Div(children=[
                dcc.Slider(min=1, max=10, step=1, value=1, id='interval-refresh'),
            ], className="three columns"),
            html.Div(children=[
                html.Span("Data Recency", style={"font-weight": "bold"})
            ], className="two columns"),
            html.Div(children=[
                dcc.Dropdown(id='data-recency', options=[
                {'label': 'Last 1 minute', 'value': 1},
                {'label': 'Last 2 minutes', 'value': 2},
                {'label': 'Last 5 minutes', 'value': 5},
                {'label': 'Last 10 minutes', 'value':10},
                {'label': 'Last 30 minutes', 'value': 30},
            ],
            value=1),
            ], className="three columns"),        
        ], className="one row", style={"padding": "5px 0"}),
        html.Div(id='latest-timestamp', style={"padding": "5px 0"}),
    ], className="one row", style={"backgroundColor": "#EFEFEF", "padding": "10px", "margin": "10px 0", "borderRadius": "10px"}),

    dcc.Interval(
            id='interval-component',
            interval=1 * 1000,  # in milliseconds
            n_intervals=0
        ),
    dcc.Tabs(id="tabs-example-graph", value='overview', children=[
        dcc.Tab(label='Overview', value='overview', children=[tabs.overview(all_quotes)]),
        dcc.Tab(label='Assets', value='by-asset', children=[tabs.assets(all_bases)]),
        dcc.Tab(label='Latest Trades', value='all-latest-trades', children=[tabs.latest_trades()]),
    ]),
    html.Div(id='tabs-content-example-graph')
])

@app.callback(
    [Output(component_id='interval-component', component_property='interval')],
    [Input('interval-refresh', 'value')])
def update_refresh_rate(value):
    return [value * 1000]

# @app.callback(
#     [Output(component_id='latest-trades-bases', component_property='children'),
#     Output(component_id='prices', component_property='figure'),
#     Output(component_id='markets', component_property='figure'),
#     Output(component_id='assets', component_property='figure'),
#     Output(component_id='order_side', component_property='figure'),
#      ],
#     [Input('bases-dropdown', 'value'), Input('interval-component', 'n_intervals'),  Input('data-recency', 'value')]
# )
@app.callback(
    [Output(component_id='latest-trades-bases', component_property='children'),
     Output(component_id="asset-charts", component_property="children")
     ],
    [Input('bases-dropdown', 'value'), Input('interval-component', 'n_intervals'),  Input('data-recency', 'value')]
)
def assets_page(base_name, n, interval):
    cursor = connection.cursor()

    results = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(querydb.latest_period_prices, cursor, base_name, interval): "now",
            executor.submit(querydb.previous_period_prices, cursor, base_name, interval): "prev",
            executor.submit(querydb.get_pairs, cursor, base_name, interval): "pairs",
            executor.submit(querydb.get_latest_trades, cursor, base_name): "trades",
            executor.submit(querydb.get_assets, cursor, base_name, interval): "assets",
            executor.submit(querydb.get_order_side, cursor, base_name, interval): "order_side",
        }
        for future in concurrent.futures.as_completed(futures):
            results[futures[future]] = future.result()
    cursor.close()

    df_now = results["now"]
    df_prev = results["prev"]
    trades_df = results["trades"]
    
    fig = go.Figure()
    if df_now["count"][0] > 0:
        if df_prev["count"][0] > 0:
            dash_utils.add_delta_trace(fig, "Min Price", df_now["minPrice"][0], df_prev["minPrice"][0], 0, 0)
            dash_utils.add_delta_trace(fig, "Average Price", df_now["avgPrice"][0], df_prev["avgPrice"][0], 0, 1)
            dash_utils.add_delta_trace(fig, "Max Price", df_now["maxPrice"][0], df_prev["maxPrice"][0], 0, 2)
            dash_utils.add_delta_trace(fig, "Transactions", df_now["count"][0], df_prev["count"][0], 1, 0)
            dash_utils.add_delta_trace(fig, "Amount Traded", df_now["amountTraded"][0], df_prev["amountTraded"][0], 1, 1)
        else:
            dash_utils.add_trace(fig, "Min Price", df_now["minPrice"][0], 0, 0)
            dash_utils.add_trace(fig, "Average Price", df_now["avgPrice"][0], 0, 1)
            dash_utils.add_trace(fig, "Max Price", df_now["maxPrice"][0], 0, 2)
            dash_utils.add_trace(fig, "Transactions", df_now["count"][0], 1, 0)
            dash_utils.add_trace(fig, "Amount Traded", df_now["amountTraded"][0], 1, 1)
        fig.update_layout(
            grid = {"rows": 2, "columns": 3,  'pattern': "independent"},
        )       
    else:
        fig.update_layout(
            annotations = [{"text": "No transactions found", "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 28}}]
        )
    
    fig_market = px.bar(results["pairs"], x='market', y='count', title="Top markets", color_discrete_sequence =['blue'])
    fig_asset = px.bar(results["assets"], x='asset', y='count', title="Top assets", color_discrete_sequence =['green'])
    fig_order_side = px.bar(results["order_side"], x='orderSide', y='count', title="Order Side", color_discrete_sequence =['purple'])
    
    latest_trades = dash_utils.as_datatable(trades_df)

    charts = [dcc.Graph(figure=fig), dcc.Graph(figure=fig_market), dcc.Graph(figure=fig_asset), dcc.Graph(figure=fig_order_side)] \
        if results["pairs"].shape[0] > 0  \
        else "No recent trades"

    return latest_trades, charts

@app.callback(
    [Output(component_id='pairs', component_property='children'),
     Output(component_id='overview-assets', component_property='children'),
     Output(component_id='latest-timestamp', component_property='children'),
     Output(component_id='aggregate-trades', component_property='children')
     ],
    [Input('interval-component', 'n_intervals'), Input('data-recency', 'value')]
)
def overview(n, interval):
    cursor = connection.cursor()

    results = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(querydb.get_all_pairs, cursor, interval): "pairs",
            executor.submit(querydb.get_all_assets, cursor, interval): "assets",
            executor.submit(querydb.get_aggregate_trades_current_period, cursor, interval): "trades_now",
            executor.submit(querydb.get_aggregate_trades_previous_period, cursor, interval): "trades_previous"
        }
        for future in concurrent.futures.as_completed(futures):
            results[futures[future]] = future.result()
    cursor.close()

    pairs = dash_utils.as_data_table_or_message(results["pairs"], "No recent trades")
    assets = dash_utils.as_data_table_or_message(results["assets"], "No recent trades")

    aggregate_trades_now = results["trades_now"]
    aggregate_trades_prev = results["trades_previous"]
      

    fig = go.Figure(layout=go.Layout(height=300))
    if aggregate_trades_now["count"][0] > 0:
        if aggregate_trades_prev["count"][0] > 0:
            dash_utils.add_delta_trace(fig, "Transactions", aggregate_trades_now["count"][0], aggregate_trades_prev["count"][0], 0, 0)
            dash_utils.add_delta_trace(fig, "Amount Traded", aggregate_trades_now["amountTraded"][0], aggregate_trades_prev["amountTraded"][0], 0, 1)
            
        else:
            dash_utils.add_trace(fig, "Transactions", aggregate_trades_now["count"][0], 0, 0)
            dash_utils.add_trace(fig, "Amount Traded", aggregate_trades_now["amountTraded"][0], 0, 1)
        fig.update_layout(grid = {"rows": 1, "columns": 2,  'pattern': "independent"},) 
    else:
        fig.update_layout(annotations = [{"text": "No transactions found", "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 28}}])
    

    overview_fig = dcc.Graph(figure=fig) if aggregate_trades_now["count"][0] > 0 else None

    return pairs, assets, [html.Span(f"Last updated: {datetime.datetime.now()}")], overview_fig


@app.callback(
    [Output(component_id='latest-trades', component_property='children')],
    [Input('interval-component', 'n_intervals')]
)
def latest_trades(n):
    latest_trades = dash_utils.as_datatable(querydb.get_all_latest_trades(cursor))
    return latest_trades

@app.callback(
    [Output(component_id='quote-currency', component_property='style'),
     Output(component_id='top-pairs-buy-side', component_property='children'),
     Output(component_id='top-exchange', component_property='children'),
     Output(component_id='top-quote', component_property='children')
     ],
    [Input('interval-component', 'n_intervals'), Input('quotes-dropdown', 'value'),  Input('data-recency', 'value')]
)
def charts(n, value, interval):    
    cursor = connection.cursor()

    results = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(querydb.get_top_pairs_buy_side, cursor, value, interval): "buy_side",
            executor.submit(querydb.get_exchange_buy_side, cursor, interval): "exchange",
            executor.submit(querydb.get_quote_buy_side, cursor, interval): "quote",
        }
        for future in concurrent.futures.as_completed(futures):
            results[futures[future]] = future.result()
    cursor.close()

    df_buy_side = results["buy_side"]
    df_exchange = results["exchange"]
    df_quote = results["quote"]    

    fig_buy = px.bar(df_buy_side, x='baseName', y='totalAmount', log_y=True, color_discrete_sequence =['green'])
    fig_exchange = px.bar(df_exchange, x='exchangeName', y='transactions', log_y=True, color_discrete_sequence =['blue'])
    fig_quote = px.bar(df_quote, x='quoteName', y='transactions', log_y=True, color_discrete_sequence =['purple'])

    quote_currency_styling = {'display': 'block'} if df_buy_side.shape[0] > 0 else {"display": "none"}
    buy = dcc.Graph(figure=fig_buy) if df_buy_side.shape[0] > 0 else "No recent trades"
    exchange = dcc.Graph(figure=fig_exchange) if df_exchange.shape[0] > 0 else "No recent trades"
    quote = dcc.Graph(figure=fig_quote) if df_quote.shape[0] > 0 else "No recent trades"

    return quote_currency_styling, buy, exchange, quote

if __name__ == '__main__':
    app.run_server(debug=True)