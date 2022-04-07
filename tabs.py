from dash import Dash, dcc, html

def overview(all_quotes):
    return html.Div([
        html.Div([
            html.Div(id='aggregate-trades'),
            html.H2('Pairs'),
            html.Div(id='pairs'),
            html.H2('Assets'),
            html.Div(id='overview-assets'),
        ]),
        html.Div([
            html.H2('Most Traded Assets'),
            html.Label(children=[
                html.Span("Quote currency:", style={"font-weight": "bold"}),
                dcc.Dropdown(all_quotes, all_quotes[0], id='quotes-dropdown'),
            ]),
            html.Div([
                html.Div([
                    html.H3("Buy Side"),
                    html.Div(id="top-pairs-buy-side"),
                    # dcc.Graph(id='top-pairs-buy-side', figure={}),
                ], className="six columns"),
                html.Div([
                    html.H3("Sell Side"),
                    html.Div(id="top-pairs-sell-side"),
                    # dcc.Graph(id='top-pairs-sell-side', figure={}),
                ], className="six columns"),
            
            ], className="one row"),
            
        ]),         
    ])    

def assets(all_bases):
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
            ])
        ])

def latest_trades():
    return html.Div([
        html.Div([
            html.H2('Latest Trades'),
            html.Div(id='latest-trades'),
        ])     
    ])    
