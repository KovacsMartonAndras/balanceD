from dash import html, register_page

register_page(__name__, path="/debug")

layout = html.Div([
    html.H2("Debug page"),
    html.P("This is a personal finance tracker built with Dash and Plotly."),
])