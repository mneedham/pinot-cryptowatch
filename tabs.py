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
            html.Div(id="quote-currency", children=[
                html.Div(children=[
                    html.Span("Purchase currency", style={"font-weight": "bold"})
                ], className="two columns"),
                html.Div(children=[
                    dcc.Dropdown(all_quotes, all_quotes[0], id='quotes-dropdown'),
                ], className="three columns"),                
            ], className="one row"),
            html.Div([
                html.Div([
                    html.Div(id="top-pairs-buy-side"),
                ], className="six columns"),
            
            ], className="one row"),
            html.Div([
                html.Div([
                    html.H2("Top Exchanges"),
                    html.Div(id="top-exchange"),
                ], className="six columns"),
                html.Div([
                    html.H2("Assets used to make purchases"),
                    html.Div(id="top-quote"),
                ], className="six columns"),
            ], className="one row"),
            
        ]),         
    ])    

def assets(all_bases):
    return html.Div([
            html.H2("Assets"),
            html.Div(children=[
                html.Div(children=[
                    html.Span("Select asset", style={"font-weight": "bold"})
                ], className="two columns"),
                html.Div(children=[
                    dcc.Dropdown(all_bases, all_bases[0], id='bases-dropdown'),
                ], className="three columns"),                
            ], className="one row"),
 
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
