import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table  # pip install dash (version 2.0.0 or higher)
from pinotdb import connect, db
import datetime
import querydb
import tabs
import dash_utils

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Crypto Watch Dashboard"
app.config.suppress_callback_exceptions=True

connection = connect(
    host="localhost",
    port="8099",
    path="/query/sql",
    scheme=( "http"),
)
cursor = connection.cursor()
all_quotes = querydb.quotes(connection)
all_bases = querydb.bases(connection)

app.layout = html.Div([
    html.H1("Crypto Watch Dashboard", style={'text-align': 'center'}),
    # html.Div(children=[
    #     html.Div(children=[
    #         html.Span("Refresh rate (seconds)", style={"font-weight": "bold"})
    #     ], className="two columns"),
    #     html.Div(children=[
    #         dcc.Slider(min=1, max=10, step=1, value=1, id='interval-refresh'),
    #     ], className="three columns"),
    #     html.Div(id='latest-timestamp', className="three columns"),    
    # ], className="one row"),

    html.Label(children=[
        html.Span("Data Recency:", style={"font-weight": "bold"}),
        dcc.Dropdown(id='data-recency', options=[
            {'label': 'Last 1 minute', 'value': 'PT1M'},
            {'label': 'Last 2 minutes', 'value': 'PT2M'},
            {'label': 'Last 5 minutes', 'value': 'PT5M'},
            {'label': 'Last 10 minutes', 'value': 'PT10M'},
            {'label': 'Last 30 minutes', 'value': 'PT30M'},
        ],
        value='PT1M'
    ),
    ]), 
    html.Div(id='latest-timestamp'),  
    dcc.Interval(
            id='interval-component',
            interval=1 * 1000,  # in milliseconds
            n_intervals=0
        ),
    dcc.Tabs(id="tabs-example-graph", value='overview', children=[
        dcc.Tab(label='Overview', value='overview', children=[tabs.overview(all_quotes)]),
        # dcc.Tab(label='Assets', value='by-asset', children=[tabs.assets(all_bases)]),
        # dcc.Tab(label='Latest Trades', value='all-latest-trades', children=[tabs.latest_trades()]),
    ]),
    html.Div(id='tabs-content-example-graph')
])

# @app.callback(
#     [Output(component_id='interval-component', component_property='interval')],
#     [Input('interval-refresh', 'value')])
# def update_refresh_rate(value):
#     return [value * 1000]

# @app.callback(
#     [Output(component_id='latest-trades-bases', component_property='children'),
#      Output(component_id='prices', component_property='figure'),
#      Output(component_id='markets', component_property='figure'),
#      Output(component_id='overview-assets', component_property='children'),
#      Output(component_id='order_side', component_property='figure'),
#      ],
#     [Input('bases-dropdown', 'value'), Input('interval-component', 'n_intervals')]
# )
# def bases(base_name, n):
#     latest_trades = dash_utils.as_datatable(querydb.get_latest_trades(connection, base_name))

#     df_now = querydb.latest_period_prices(connection, base_name)
#     df_prev = querydb.previous_period_prices(connection, base_name)
    
#     fig = go.Figure()
#     if df_now["count"][0] > 0:
#         if df_prev["count"][0] > 0:
#             dash_utils.add_delta_trace(fig, "Min Price", df_now["minPrice"][0], df_prev["minPrice"][0], 0, 0)
#             dash_utils.add_delta_trace(fig, "Average Price", df_now["avgPrice"][0], df_prev["avgPrice"][0], 0, 1)
#             dash_utils.add_delta_trace(fig, "Max Price", df_now["maxPrice"][0], df_prev["maxPrice"][0], 0, 2)
#             dash_utils.add_delta_trace(fig, "Transactions", df_now["count"][0], df_prev["count"][0], 1, 0)
#             dash_utils.add_delta_trace(fig, "Amount Traded", df_now["amountTraded"][0], df_prev["amountTraded"][0], 1, 1)
#         else:
#             dash_utils.add_trace(fig, "Min Price", df_now["minPrice"][0], 0, 0)
#             dash_utils.add_trace(fig, "Average Price", df_now["avgPrice"][0], 0, 1)
#             dash_utils.add_trace(fig, "Max Price", df_now["maxPrice"][0], 0, 2)
#             dash_utils.add_trace(fig, "Transactions", df_now["count"][0], 1, 0)
#             dash_utils.add_trace(fig, "Amount Traded", df_now["amountTraded"][0], 1, 1)
#         fig.update_layout(
#             grid = {"rows": 2, "columns": 3,  'pattern': "independent"},
#         )       
#     else:
#         fig.update_layout(
#             annotations = [{"text": "No transactions found", "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 28}}]
#         )

#     fig_prices = px.line(querydb.all_prices(connection, base_name), x="tsMs", y="price", title='Price over time')
#     fig_market = px.bar(querydb.get_pairs(connection, base_name), x='market', y='count', title="Top markets")
#     fig_asset = px.bar(querydb.get_assets(connection, base_name), x='asset', y='count', title="Top assets")
#     fig_order_side = px.bar(querydb.get_order_side(connection, base_name), x='orderSide', y='count', title="Order Side")

#     return latest_trades, fig, fig_market, fig_asset, fig_order_side

@app.callback(
    [Output(component_id='pairs', component_property='children'),
    Output(component_id='overview-assets', component_property='children'),
     Output(component_id='latest-timestamp', component_property='children')],
    [Input('interval-component', 'n_intervals'), Input('data-recency', 'value')]
)
def overview(n, interval):
    cursor = connection.cursor()
    pairs = dash_utils.as_datatable(querydb.get_all_pairs(cursor, interval))
    assets = dash_utils.as_datatable(querydb.get_all_assets(cursor, interval))

    cursor.close()
    return pairs, assets, [html.Span(f"Last updated: {datetime.datetime.now()}")]


@app.callback(
    [Output(component_id='latest-trades', component_property='children')],
    [Input('interval-component', 'n_intervals')]
)
def latest_trades(n):
    latest_trades = dash_utils.as_datatable(querydb.get_all_latest_trades(cursor))
    return latest_trades

@app.callback(
    [Output(component_id='top-pairs-buy-side', component_property='figure'),
     Output(component_id='top-pairs-sell-side', component_property='figure')],
    [Input('interval-component', 'n_intervals'), Input('quotes-dropdown', 'value'),  Input('data-recency', 'value')]
)
def top_pairs_buy_side(n, value, interval):    
    df_buy_side = querydb.get_top_pairs_buy_side(cursor, value, interval)
    fig_buy = px.bar(df_buy_side, x='baseName', y='totalAmount', log_y=True)

    df_sell_side = querydb.get_top_pairs_sell_side(cursor, value, interval)
    fig_sell = px.bar(df_sell_side, x='baseName', y='totalAmount', log_y=True)

    return [fig_buy, fig_sell]

if __name__ == '__main__':
    app.run_server(debug=True)