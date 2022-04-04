import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table  # pip install dash (version 2.0.0 or higher)
from pinotdb import connect, db
import datetime

connection = connect(
            host="localhost",
            port="8099",
            path="/query/sql",
            scheme=( "http"),
        )

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)

# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div([
    html.H1("Crypto Watch Dashboard", style={'text-align': 'center'}),
    html.Div(id='latest-timestamp'),
    html.Div([
        html.H4('Latest Trades'),
        html.Div(id='latest-trades')
    ]),
    html.Div([
        html.H4('Most Traded Coins in USD - Buy Side'),
        dcc.Graph(id='top-pairs-buy-side', figure={})
    ]),
    html.Div([
        html.H4('Most Traded Coins in USD - Sell Side'),
        dcc.Graph(id='top-pairs-sell-side', figure={})
    ]),
    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,  # in milliseconds
        n_intervals=0
    )
])



@app.callback(
    [Output(component_id='latest-trades', component_property='children'),
     Output(component_id='latest-timestamp', component_property='children')],
    [Input('interval-component', 'n_intervals')]
)
def latest_trades(n):
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

    return [html.Div([dash_table.DataTable(
        df.to_dict('records'), [{"name": i, "id": i} for i in df.columns],
        style_table={'overflowX': 'auto'},
        style_cell={
            'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
        }
    )])], [html.Span(f"Last updated: {datetime.datetime.now()}")]


@app.callback(
    [Output(component_id='top-pairs-buy-side', component_property='figure'),
     Output(component_id='top-pairs-sell-side', component_property='figure')],
    [Input('interval-component', 'n_intervals')]
)
def top_pairs_buy_side(n):
    cursor = connection.cursor()

    cursor.execute("""
    select sum(amount*price) AS totalAmount,
           lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName,
           lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quoteName
    from trades 
    where quoteName = 'United States Dollar' AND orderSide = 'BUYSIDE'
    group by baseName, quoteName
    order by totalAmount DESC
    """)
    df_buy_side = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
    fig_buy = px.bar(df_buy_side, x='baseName', y='totalAmount', log_y=True)

    cursor.execute("""
    select sum(amount*price) AS totalAmount,
           lookUp('pairs', 'baseName', 'id', currencyPairId) AS baseName,
           lookUp('pairs', 'quoteName', 'id', currencyPairId) AS quoteName
    from trades 
    where quoteName = 'United States Dollar' AND orderSide = 'SELLSIDE'
    group by baseName, quoteName
    order by totalAmount DESC
    """)
    df_sell_side = pd.DataFrame(cursor, columns=[item[0] for item in cursor.description])
    fig_sell = px.bar(df_sell_side, x='baseName', y='totalAmount', log_y=True)

    return [fig_buy, fig_sell]

    # return [html.Div([dash_table.DataTable(
    #     df.to_dict('records'), [{"name": i, "id": i} for i in df.columns],
    #     style_table={'overflowX': 'auto'},
    #     style_cell={
    #         'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
    #         'overflow': 'hidden',
    #         'textOverflow': 'ellipsis',
    #     }
    # )])]

# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
# @app.callback(
#     [Output(component_id='output_container', component_property='children'),
#      Output(component_id='my_bee_map', component_property='figure')],
#     [Input(component_id='slct_year', component_property='value')]
# )
# def update_graph(option_slctd):
#     print(option_slctd)
#     print(type(option_slctd))
# 
#     container = "The year chosen by user was: {}".format(option_slctd)
# 
#     dff = df.copy()
#     dff = dff[dff["Year"] == option_slctd]
#     dff = dff[dff["Affected by"] == "Varroa_mites"]
# 
#     # Plotly Express
#     fig = px.choropleth(
#         data_frame=dff,
#         locationmode='USA-states',
#         locations='state_code',
#         scope="usa",
#         color='Pct of Colonies Impacted',
#         hover_data=['State', 'Pct of Colonies Impacted'],
#         color_continuous_scale=px.colors.sequential.YlOrRd,
#         labels={'Pct of Colonies Impacted': '% of Bee Colonies'},
#         template='plotly_dark'
#     )
# 
#     # Plotly Graph Objects (GO)
#     # fig = go.Figure(
#     #     data=[go.Choropleth(
#     #         locationmode='USA-states',
#     #         locations=dff['state_code'],
#     #         z=dff["Pct of Colonies Impacted"].astype(float),
#     #         colorscale='Reds',
#     #     )]
#     # )
#     #
#     # fig.update_layout(
#     #     title_text="Bees Affected by Mites in the USA",
#     #     title_xanchor="center",
#     #     title_font=dict(size=24),
#     #     title_x=0.5,
#     #     geo=dict(scope='usa'),
#     # )
# 
#     return container, fig


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)