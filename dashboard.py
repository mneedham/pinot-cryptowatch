import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table  # pip install dash (version 2.0.0 or higher)
from pinotdb import connect, db
import datetime
import math
import querydb

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

    df = querydb.get_latest_trades(cursor, base_name)
    latest_trades = [html.Div([dash_table.DataTable(
        df.to_dict('records'), [{"name": i, "id": i} for i in df.columns],
        style_table=style_table,
        style_cell=style_cell
    )])]

    df_now = querydb.latest_period_prices(cursor, base_name)
    df_prev = querydb.previous_period_prices(cursor, base_name)
    
    fig = go.Figure()
    if df_now["count"][0] > 0:
        if df_prev["count"][0] > 0:
            add_delta_trace(fig, "Min Price", df_now["minPrice"][0], df_prev["minPrice"][0], 0, 0)
            add_delta_trace(fig, "Average Price", df_now["avgPrice"][0], df_prev["avgPrice"][0], 0, 1)
            add_delta_trace(fig, "Max Price", df_now["maxPrice"][0], df_prev["maxPrice"][0], 0, 2)
            add_delta_trace(fig, "Transactions", df_now["count"][0], df_prev["count"][0], 1, 0)
            add_delta_trace(fig, "Amount Traded", df_now["amountTraded"][0], df_prev["amountTraded"][0], 1, 1)
        else:
            add_trace(fig, "Min Price", df_now["minPrice"][0], 0, 0)
            add_trace(fig, "Average Price", df_now["avgPrice"][0], 0, 1)
            add_trace(fig, "Max Price", df_now["maxPrice"][0], 0, 2)
            add_trace(fig, "Transactions", df_now["count"][0], 1, 0)
            add_trace(fig, "Amount Traded", df_now["amountTraded"][0], 1, 1)
        fig.update_layout(
            grid = {"rows": 2, "columns": 3,  'pattern': "independent"},
        )       
    else:
        fig.update_layout(
            annotations = [{"text": "No transactions found", "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 28}}]
        )

    fig_market = px.bar(querydb.get_pairs(cursor, base_name), x='market', y='count', title="Top markets")
    fig_asset = px.bar(querydb.get_assets(cursor, base_name), x='asset', y='count', title="Top assets")
    fig_order_side = px.bar(querydb.get_order_side(cursor, base_name), x='orderSide', y='count', title="Order Side")

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

    df = querydb.get_all_latest_trades(cursor)
    latest_trades = [html.Div([dash_table.DataTable(
        df.to_dict('records'), [{"name": i, "id": i} for i in df.columns],
        style_table=style_table,
        style_cell=style_cell
    )])]

    df = querydb.get_all_pairs(cursor)
    pairs = [html.Div([dash_table.DataTable(
        df.to_dict('records'), [{"name": i, "id": i} for i in df.columns],
        style_table=style_table,
        style_cell=style_cell
    )])]

    df = querydb.get_all_assets(cursor)
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

    df_buy_side = querydb.get_top_pairs_buy_side(cursor, value)
    fig_buy = px.bar(df_buy_side, x='baseName', y='totalAmount', log_y=True)

    df_sell_side = querydb.get_top_pairs_sell_side(cursor, value)
    fig_sell = px.bar(df_sell_side, x='baseName', y='totalAmount', log_y=True)

    return [fig_buy, fig_sell]

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)