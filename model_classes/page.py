from dash import Dash, html, dcc
import dash


class Page:
    def __init__(self, app, db):
        self.app = app
        self.db = db
        self.layout = self.define_layout()
        self.register_callbacks(self.app)

    def define_layout(self):
        raise NotImplementedError("Subclasses must implement define_layout()")

    def register_callbacks(self, app):
        raise NotImplementedError("Subclasses must implement register_callbacks()")