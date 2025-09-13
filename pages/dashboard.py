from dash import html, Input, Output, ctx
from db import get_current_balance
from model_classes.page import Page
import dash
from dash import html, register_page

class DashBoard(Page):
    path = "/"
    def __init__(self, app, db):
        super().__init__(app,db)

    def define_layout(self):
        layout = html.Div([
            html.H2("Dashboard"),
            # Current balance display
            html.Div(id="current-balance", style={"margin": "10px", "fontWeight": "bold"}),
            # dcc.Graph(id="dashboard-graph", figure={}),  # you can add callbacks later
        ])

        return layout


    def register_callbacks(self, app):
        @app.callback(
            Output("current-balance", "children"),
             Input("url", "pathname")
        )
        def update_balance(pathname):
            # Only update when on Dashboard
            if pathname != "/":
                return dash.no_update

            balance = get_current_balance()
            return f"Balance: {balance:.2f}"
