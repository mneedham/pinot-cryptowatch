from dash import Dash, html, dash_table, dcc
import plotly.graph_objects as go

from pinotdb import connect
import pandas as pd


def as_data_table_or_message(df, message):
    return as_datatable(df) if df.shape[0] > 0 else message

def as_datatable(df):
    style_table = {'overflowX': 'auto'}
    style_cell = {
        'minWidth': '50px', 'width': '150px', 'maxWidth': '18   0px',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis',
        'padding': '10px'
    }

    return dash_table.DataTable(
        df.to_dict('records'), [{"name": i, "id": i} for i in df.columns],
        style_table=style_table,
        style_cell=style_cell
    )


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

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Crypto Watch Real-Time Dashboard"

connection = connect(host="localhost", port="8099", path="/query/sql", scheme=( "http"))
cursor = connection.cursor()

cursor.execute("""
    select lookUp('pairs', 'baseName', 'id', currencyPairId) AS base,
           lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quote, 
           count(*) AS transactions, max(amount) as biggestTrade,
           avg(amount) as averageTrade, sum(amount) AS amountTraded
    from trades 
    where tsMs > ago(%(intervalString)s)
    group by quote, base
    order by transactions DESC
    limit 10
    """, {"intervalString": f"PT60M"})

pairs_df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
pairs = as_data_table_or_message(pairs_df, "No recent trades")

cursor.execute("""
select lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName, 
        min(price) AS minPrice, avg(price) AS avgPrice, max(price) as maxPrice,  
        count(*) AS count, sum(amount) AS amountTraded		   
from trades 
WHERE lookUp('pairs', 'quoteName', 'id', currencyPairId) = 'United States Dollar'
AND tsMs > ago(%(intervalString)s)
group by baseName
order by count DESC
""", {"intervalString": f"PT60M"})

assets_df = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
assets = as_data_table_or_message(assets_df, "No recent trades") 

interval = 1  

cursor.execute("""
select count(*) AS count, sum(amount) AS amountTraded	   
from trades 
WHERE tsMs > ago(%(intervalString)s)
order by count DESC
""", {"intervalString": f"PT{interval}M"})
aggregate_trades_now =  pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

cursor.execute("""
select count(*) AS count, sum(amount) AS amountTraded	   
from trades 
WHERE tsMs < ago(%(intervalString)s)
AND tsMs > ago(%(previousIntervalString)s)
order by count DESC
""", {"intervalString": f"PT{interval}M", "previousIntervalString": f"PT{interval*2}M"})
aggregate_trades_prev =  pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])

fig = go.Figure(layout=go.Layout(height=300))
if aggregate_trades_now["count"][0] > 0:
    if aggregate_trades_prev["count"][0] > 0:
        add_delta_trace(fig, "Transactions", aggregate_trades_now["count"][0], aggregate_trades_prev["count"][0], 0, 0)
        add_delta_trace(fig, "Amount Traded", aggregate_trades_now["amountTraded"][0], aggregate_trades_prev["amountTraded"][0], 0, 1)
        
    else:
        add_trace(fig, "Transactions", aggregate_trades_now["count"][0], 0, 0)
        add_trace(fig, "Amount Traded", aggregate_trades_now["amountTraded"][0], 0, 1)
    fig.update_layout(grid = {"rows": 1, "columns": 2,  'pattern': "independent"},) 
else:
    fig.update_layout(annotations = [{"text": "No transactions found", "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 28}}])

cursor.close()

app.layout = html.Div([
    html.H1("Crypto Watch Real-Time Dashboard", style={'text-align': 'center'}),
    html.Div(id='content', children=[
        html.H2("Overview"),
        dcc.Graph(figure=fig),
        html.H2("Pairs"),
        pairs, 
        html.H2("Assets"),
        assets
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True)
