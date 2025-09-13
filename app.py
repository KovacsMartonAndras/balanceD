from dash import Dash, html, dcc
import dash
app = Dash(__name__, use_pages=True)  # enable Dash Pages

app.layout = html.Div([
    html.H1("Personal Finance Tracker"),

    # Navigation menu
    html.Div([
        dcc.Link("Dashboard | ", href="/"),
        dcc.Link("Bookkeeper | ", href="/bookkeeper"),
        dcc.Link("Debug", href="/debug"),
    ]),

    dash.page_container  # where each page’s layout gets displayed
])
from pages import bookkeeper
bookkeeper.register_callbacks(app)
if __name__ == "__main__":
    app.run(debug=True)
