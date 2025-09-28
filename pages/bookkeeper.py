import base64
import io
import pandas as pd
from dash import html, dcc, Input, Output, State, dash_table,ALL
from dash.exceptions import PreventUpdate
from model_classes.page import Page
import constants as const
from db import insert_transaction, create_booking, get_available_booking_id, fetch_transactions
from column_names_db import fetch_names, insert_column_name


class Bookkeeper(Page):
    path = "/bookkeeper"
    def __init__(self, app, db):
        super().__init__(app,db)
        self.current_accounting_df = None
        self.current_csv_source = None
        self.current_booking_id = None
        self.cols = None

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

            dcc.Store(id="csv-store"),
            html.Button("Save Column Mapping", id="save-column-btn"),
            # Preview transactions
            html.Div(id="transactions-preview"),


            # Button to save transactions
            html.Button("Save Transactions", id="save-transactions-btn"),
            html.Div(id="save-result"),
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


        @app.callback(
            Output("csv-store", "data", allow_duplicate = True),
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
            self.current_csv_source = filename

            #Detect columns
            missing_columns = const.REQUIRED_COLUMNS

            # Search for appropriate columns names
            self.cols = {}
            for column_name in const.REQUIRED_COLUMNS:
                for header in df.columns:
                    if header in fetch_names(column_name):
                        self.cols[column_name] = header
                        missing_columns.remove(column_name)
                        break
            return {
                "data": df.to_dict("records"),
                "columns": list(df.columns),
                "missing": missing_columns,
                "cols": self.cols,
                "source": filename
            }

        @app.callback(
            Output("transactions-preview", "children"),
            Input("csv-store", "data"),
            Input("save-column-btn","n_clicks"),
            prevent_initial_call=True
        )

        def check_for_columns(data, n_clicks):
            if data.get("missing", []):
                return render_preview(data)
            else:
                return render_table(data["data"])

        def render_table(df):
            return dash_table.DataTable(
                id="transactions-datatable",
                columns=[{"name": i, "id": i, "editable": (i == "excluded")} for i in df.columns],
                data=df.to_dict("records"),
                editable=True,
                row_selectable="multi",
                selected_rows=[],
                style_table={"overflowX": "auto", "overflowY": "auto"},
                fixed_rows={"headers": True}
            )


        def render_preview(data):
            if data is None:
                raise PreventUpdate
            df = pd.DataFrame(data["data"])
            missing = data.get("missing", [])

            if missing:
                mapping_ui = []
                for col in missing:
                    mapping_ui.append(html.Div([
                        html.Label(f"Select CSV column for '{col}'"),
                        dcc.Dropdown(
                            id={"type": "map-column_name", "index": f"map-{col}-dropdown"},
                            options=[{"label": c, "value": c} for c in df.columns],
                            placeholder="Select the column..."
                        )
                    ]))
                return html.Div(mapping_ui)

        @app.callback(
            Output("csv-store", "data"),
            Input("csv-store", "data"),
            Input({"type": "map-column_name", "index": ALL}, "value"),
            Input("save-column-btn", "n_clicks"),
            prevent_initial_call=True
        )
        def save_column(n_clicks, data, values):
            if not n_clicks:
                raise PreventUpdate
            print(values)

            print(data)
            df = pd.DataFrame(data["data"])
            missing_columns = const.REQUIRED_COLUMNS


            # Search for appropriate columns name
            self.cols.append(values)

            return {
                "data": df.to_dict("records"),
                "columns": list(df.columns),
                "missing": missing_columns
            }

    #     @app.callback(
    #         Output("transactions-preview", "children"),
    #         Input("csv-store", "data"),
    #         prevent_initial_call=True
    #     )
    #

    #

    #
    #
    #
    #     @app.callback(
    #         Output("csv-store", "data", allow_duplicate=True),
    #         Input("save-column-btn", "n_clicks"),
    #         [State(f"map-{col}-dropdown", "value") for col in const.REQUIRED_COLUMNS],
    #         State("csv-store", "data"),
    #         prevent_initial_call=True
    #     )
    #
    #     @app.callback(
    #         Input("save-column-btn", "n_clicks"),
    #         [State(f"map-{col}-dropdown", "value") for col in const.REQUIRED_COLUMNS],
    #         State("uploaded-csv-store", "data"),
    #         prevent_initial_call=True
    #     )
    #
    #
    #     # Upload CSV and preview
    #     @app.callback(
    #         Output("transactions-preview", "children"),
    #         Input("upload-data", "contents"),
    #         State("upload-data", "filename"),
    #         prevent_initial_call=True
    #     )
    #
    #     @app.callback(
    #         Output("save-result", "children"),
    #         [Input("save-transactions-btn", "n_clicks"),
    #          Input("save-column-btn", "n_clicks")],
    #         State("transactions-datatable", "selected_rows"),
    #         State("transactions-datatable", "column"),
    #         State("transactions-datatable", "data"),
    #         [State(f"map-{column}-dropdown", "value") for column in const.REQUIRED_COLUMNS],
    #         prevent_initial_call=True
    #     )
    #
    #     # @app.callback(
    #     #     Input("save-column-btn", "n_clicks"),
    #     #     [State(f"map-{column}-dropdown", "value") for column in const.REQUIRED_COLUMNS],
    #     #     prevent_initial_call=True
    #     # )
    #
    #     def save_transactions(n_clicks, selected_rows, rows):
    #         if not n_clicks or self.current_accounting_df is None or self.current_booking_id is None:
    #             raise PreventUpdate
    #
    #         df = pd.DataFrame(rows)
    #
    #         if selected_rows:
    #             for i in selected_rows:
    #                 df.at[i, "excluded"] = True
    #
    #         new_transaction_added = self.insert_transactions_into_database(df)
    #
    #         # TODO: Different booking_id-s ?
    #         if new_transaction_added:
    #             create_booking()  # Adds new booking to bookings database
    #             booking_id = self.current_booking_id
    #             self.current_booking_id = None
    #             return True,f"Saved {len(df)} transactions into booking {booking_id}"
    #         else:
    #             return False, f"No new transactions were booked."
    #
    #
    #
    # def insert_transactions_into_database(self,df) -> bool:
    #     """
    #     :param df: holds uploaded csv data
    #     :param cols: dictionary that holds column names for each required field for transactions
    #     :return: Returns True if a new transaction was added to the database, otherwise False
    #     """
    #     date_column_name = self.handle_date(df)
    #     new_transaction_added = False
    #     # Find amount column
    #     # TODO: possibly better solution for supporting different column names
    #     for header in df.columns:
    #         if header in const.FLAGS:
    #             flag_column_name = header
    #             break
    #
    #     # Insert rows into database
    #     for _, row in df.iterrows():
    #         val = row[date_column_name]
    #         if pd.isna(val):
    #             continue  # or decide how you want to handle missing dates
    #         transaction_state = insert_transaction(
    #             date=val.strftime("%Y-%m-%d %H:%M:%S"),
    #             recipient=row[self.cols["recipient"]],
    #             currency=row[self.cols["currency"]],
    #             amount=row[self.cols["amount"]],
    #             type=row[self.cols["type"]],
    #             source_csv=self.current_csv_source,
    #             booking_id=self.current_booking_id,
    #             excluded=row[flag_column_name]
    #         )
    #         new_transaction_added = transaction_state or new_transaction_added
    #
    #     return new_transaction_added

    def handle_date(self,df):
        date_column_name = None
        # Find date column
        for header in df.columns:
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