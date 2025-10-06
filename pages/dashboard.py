from dash import html, dcc, dash_table, Input, Output, State, ctx, no_update
from db import get_current_balance,get_balance_for_common, get_balance_per_currency,select_transactions_from_booking,get_bookings
from model_classes.page import Page
import plotly.express as px
import dash
from dash import html, register_page

class DashBoard(Page):
    path = "/"
    def __init__(self, app, db):
        super().__init__(app,db)
        self.current_currency = "HUF"

    def define_layout(self):
        layout = html.Div([
            html.H2("Dashboard"),

            # --- Section: Current Balance ---
            html.Div(id="balance-section"),

            html.Div([
                dcc.Graph(id="dashboard-graph"),
            ], style={"display": "inline-block", "verticalAlign": "top", "width": "420px"}),

            html.Hr(),
        ])
        return layout


    def register_callbacks(self, app):
        @app.callback(
            Output("balance-section", "children"),
             Input("url", "pathname")
        )
        def update_balance(pathname):
            # Only update when on Dashboard
            if pathname != "/":
                return dash.no_update

            balance = get_current_balance(self.current_currency)
            balances_per_currency = get_balance_per_currency()
            return self.layout_header_summary(balance,balances_per_currency)

        # Callback for graph
        @app.callback(
            Output("dashboard-graph", "figure"),
            Input("url", "pathname")
        )
        def update_graph(pathname):
            if pathname != "/":
                return dash.no_update

            rows = get_balance_for_common("HUF")
            if not rows:
                return px.bar(title="No transactions yet")

            currencies = [row[0] for row in rows]
            balances = [row[1] for row in rows]

            # Choose pie or bar
            fig = px.pie(
                names=currencies,
                values=balances,
                title="Balance Distribution by Currency"
            )
            fig.update_traces(textinfo="percent+label")
            return fig


    def layout_header_summary(self,total_balance, balances_per_currency):
        return html.Div(
            style={"display": "flex", "alignItems": "flex-start", "gap": "40px", "margin": "20px"},
            children=[
                # Left: big number
                html.Div(
                    f"{total_balance:,.2f} {self.current_currency}",
                    style={"fontSize": "48px", "fontWeight": "bold"}
                ),

                # Right: list of per-currency balances
                html.Ul(
                    [html.Li(f"{currency}: {balance:,.2f}") for currency, balance in balances_per_currency],
                    style={"listStyleType": "none", "padding": "0", "margin": "0", "fontSize": "18px"}
                )
            ]
        )
