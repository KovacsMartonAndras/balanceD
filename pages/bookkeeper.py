import base64
import io
import pandas as pd
from dash import html, dcc, Input, Output, State, dash_table
from dash.exceptions import PreventUpdate
from model_classes.page import Page
import constants as const
from db import insert_transaction, create_booking, get_available_booking_id, fetch_transactions


class Bookkeeper(Page):
    path = "/bookkeeper"
    def __init__(self, app, db):
        super().__init__(app,db)
        self.current_accounting_df = None
        self.current_csv_source = None
        self.current_booking_id = None

    def define_layout(self):
        layout = html.Div([
            html.H2("Bookkeeper"),
            # Button to create a new booking
            html.Button("Create New Booking", id="create-booking-btn"),
            html.Div(id="current-booking-label", style={"margin": "10px"}),

            # File upload component
            dcc.Upload(
                id="upload-data",
                children=html.Div([
                    "Drag and Drop or ",
                    html.A("Select a CSV File")
                ]),
                style={
                    "width": "300px",
                    "height": "40px",
                    "lineHeight": "40px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "5px",
                    "textAlign": "center",
                    "margin": "10px auto"
                },
                multiple=False,
                disabled=True
            ),

            # Preview transactions
            html.Div(id="transactions-preview"),

            # Button to save transactions
            html.Button("Save Transactions", id="save-transactions-btn"),
            html.Div(id="save-result")
        ])

        return layout

    def register_callbacks(self,app):

        @app.callback( [Output("upload-data", "disabled"),
            Output("current-booking-label", "children")],
            Input("create-booking-btn", "n_clicks"),
            prevent_initial_call=True
        )
        def create_booking_callback(n_clicks):
            if not n_clicks:
                raise PreventUpdate
            self.current_booking_id = get_available_booking_id()  # <- must be implemented in db.py
            return False,f"Active Booking ID: {self.current_booking_id}"


        # Upload CSV and preview
        @app.callback(
            Output("transactions-preview", "children"),
            Input("upload-data", "contents"),
            State("upload-data", "filename"),
            prevent_initial_call=True
        )
        def upload_csv(contents, filename):
            if contents is None or self.current_booking_id is None:
                raise PreventUpdate

            content_type, content_string = contents.split(",")
            decoded = base64.b64decode(content_string)
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))

            # Add excluded column (default False)
            df["Excluded"] = False
            self.current_accounting_df = df

            table = dash_table.DataTable(
                id="transactions-datatable",
                columns=[{"name": i, "id": i, "editable": (i == "excluded")}
                         for i in df.columns],
                data=df.to_dict("records"),
                editable=True,
                row_selectable="multi",
                selected_rows=[],
                style_table={"overflowX": "auto",
                             "overflowY": "auto"},
                fixed_rows={"headers": True}
            )

            self.current_csv_source = filename
            return table

        @app.callback(
            Output("save-result", "children"),
            Input("save-transactions-btn", "n_clicks"),
            State("transactions-datatable", "selected_rows"),
            State("transactions-datatable", "data"),
            prevent_initial_call=True
        )
        def save_transactions(n_clicks, selected_rows, rows):
            if not n_clicks or self.current_accounting_df is None or self.current_booking_id is None:
                raise PreventUpdate

            df = pd.DataFrame(rows)

            if selected_rows:
                for i in selected_rows:
                    df.at[i, "excluded"] = True

            self.insert_transactions_into_database(df)

            # TODO: Same transaction with a different flag may be added twice under different booking_id-s
            create_booking()  # Adds new booking to bookings database
            booking_id = self.current_booking_id
            self.current_booking_id = None
            return True,f"Saved {len(df)} transactions into booking {booking_id}"

    def insert_transactions_into_database(self,df):
        date_column_name = self.handle_date(df)

        # Find amount column
        # TODO: possibly better solution for supporting different column names
        for header in df.columns:
            if header in const.AMOUNT_HEADER_NAMES:
                amount_column_name = header
            elif header in const.CATEGORY_HEADER_NAMES:
                category_column_name = header
            elif header in const.CURRENCY_HEADER_NAMES:
                currency_column_name = header
            elif header in const.TYPE_HEADER_NAMES:
                type_column_name = header
            elif header in const.FLAGS:
                flag_column_name = header

        # Insert rows into database
        for _, row in df.iterrows():
            val = row[date_column_name]
            if pd.isna(val) or row[type_column_name] in const.EXCLUDED_TYPES:
                continue  # or decide how you want to handle missing dates
            insert_transaction(
                date=val.strftime("%Y-%m-%d %H:%M:%S"),
                recipient=row[category_column_name],
                currency=row[currency_column_name],
                amount=row[amount_column_name],
                source_csv=self.current_csv_source,
                booking_id=self.current_booking_id,
                excluded=row[flag_column_name]
            )

    def handle_date(self,df):
        date_column_name = None
        # Find date column
        for header in df.columns:
            print(f"{header}")
            if header in const.DATE_HEADER_NAMES:
                date_column_name = header
                break
        if date_column_name is None:
            raise ValueError("No date column found")

        # Convert to datetime (NaT if parsing fails)
        df[date_column_name] = pd.to_datetime(df[date_column_name], errors="coerce")

        return date_column_name

    def clear_current_accounting(self):
        self.current_accounting_df = None