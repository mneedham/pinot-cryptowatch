import pandas as pd
from dash import Dash, html, dash_table 
from pinotdb import connect

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

cursor.close()

app.layout = html.Div([
    html.H1("Crypto Watch Real-Time Dashboard", style={'text-align': 'center'}),
    html.Div(id='content', children=[
        html.H2("Pairs"),
        pairs, 
        html.H2("Assets"),
        assets
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True)
