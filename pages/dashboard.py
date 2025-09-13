from dash import html, dcc, register_page

register_page(__name__, path="/")  # homepage

layout = html.Div([
    html.H2("Dashboard"),
    dcc.Graph(id="dashboard-graph", figure={}),  # you can add callbacks later
])