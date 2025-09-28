from dash import Dash, html, dcc, Input, Output
import dash
from db import init_db
from pages.dashboard import DashBoard
from pages.bookkeeper import Bookkeeper
import dash_bootstrap_components as dbc
from column_names_db import init_columns_db

class App:
    def __init__(self):
        self.app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)  # enable Dash Pages
        self.layout = self.init_layout()
        self.app.layout = self.layout

        # Setup database
        init_db()  # Always init the database, does not overwrite if it exists
        init_columns_db()
        self.db = None

        self.pages = None
        self.page_instances = []
        self.page_map = {}
        self.init_pages()
        self.register_callbacks()

    def init_pages(self):
        print("Instance off app is created")
        self.pages = [DashBoard(self.app,None), Bookkeeper(self.app,None)]
        # Map paths -> page instance

        for page in self.pages:
            print(page.path)
            self.page_map[page.path] = page


    def init_layout(self):
        layout = html.Div([
        dcc.Location(id="url", refresh=False),
        html.H1("Personal Finance Tracker"),
        # Navigation menu
        html.Div([
            dcc.Link("Dashboard | ", href="/"),
            dcc.Link("Bookkeeper | ", href="/bookkeeper"),
            dcc.Link("Debug", href="/debug"),
        ]),
        html.Div(id="page-content")
        ])
        return layout

    def register_callbacks(self):
        print("Registering display_page callback")  # <-- confirm registration
        @self.app.callback(
            Output("page-content", "children"),
            Input("url", "pathname")
        )
        def display_page(pathname):
            page = self.page_map.get(pathname)
            if page:
                return page.layout
            else:
                return html.Div([html.H2("404 - Page not found")])


    def run(self):
        self.app.run(debug=True)

import os
app = App()

if __name__ == "__main__":

    app.run()
