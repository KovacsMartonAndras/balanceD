import base64
import io
import pandas as pd
from dash import html, dcc, Input, Output, State, dash_table,ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from model_classes.page import Page
import constants as const
from db import insert_transaction, create_booking, get_available_booking_id, select_transactions_from_booking,get_bookings
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
        layout = dbc.Container([

            # Header
            dbc.Row(
                dbc.Col(
                    html.H2("Bookkeeper", className="text-center my-4"),
                )
            ),

            dbc.Row([
                # Bookings Table (Left)
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Bookings", className="card-title"),
                            dash_table.DataTable(
                                id="bookings-table",
                                columns=[
                                    {"name": "Booking ID", "id": "booking_id"},
                                    {"name": "Date", "id": "date"},
                                ],
                                data=[],  # filled by callback
                                row_selectable="single",
                                style_table={"overflowX": "auto", "maxHeight": "300px", "overflowY": "auto"},
                            ),
                        ]),
                        className="mb-4 shadow-sm"
                    ),
                    width=6
                ),
                # Transactions Table (Right)
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Transactions for Selected Booking", className="card-title"),
                            dash_table.DataTable(
                                id="transactions-table",
                                columns=[
                                    {"name": "Transaction ID", "id": "transaction_id"},
                                    {"name": "Date", "id": "date"},
                                    {"name": "Amount", "id": "amount"},
                                    {"name": "Currency", "id": "currency"},
                                ],
                                data=[],  # filled dynamically
                                style_table={"overflowX": "auto", "maxHeight": "400px", "overflowY": "auto"},
                            ),
                        ]),
                        className="mb-4 shadow-sm"
                    ),
                    width=6
                ),
            ], className="mb-4"),

            # File upload in a card
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Upload CSV File", className="card-title"),
                            dcc.Upload(
                                id="upload-data",
                                children=html.Div([
                                    "Drag and Drop or ",
                                    html.A("Select a CSV File")
                                ]),
                                style={
                                    "width": "100%",
                                    "height": "60px",
                                    "lineHeight": "60px",
                                    "borderWidth": "2px",
                                    "borderStyle": "dashed",
                                    "borderRadius": "8px",
                                    "textAlign": "center",
                                    "margin": "10px 0",
                                    "backgroundColor": "#f8f9fa",
                                    "cursor": "pointer"
                                },
                                multiple=False
                            ),
                            dcc.Store(id="csv-store"),
                        ]),
                        className="mb-4 shadow-sm"
                    )
                ),
                justify="center"
            ),

            # Hidden content (buttons and preview)
            dbc.Row(
                dbc.Col(
                    html.Div([
                        dbc.Button("Save Column Mapping", id="save-column-btn", color="primary", className="me-2 mb-3"),
                        html.Div(id="transactions-preview", className="mb-3"),
                        dbc.Button("Save Transactions", id="save-transactions-btn", color="success"),
                        html.Div(id="save-result", className="mt-3")
                    ], id="hidden-content", style={"display": "none"})
                )
            )
        ], fluid=True)

        return layout

    def register_callbacks(self,app):
        @app.callback(
            Output("csv-store", "data", allow_duplicate = True),
            Input("upload-data", "contents"),
            State("upload-data", "filename"),
            prevent_initial_call=True
        )

        def upload_csv(contents, filename):
            if contents is None:
                raise PreventUpdate

            content_type, content_string = contents.split(",")
            decoded = base64.b64decode(content_string)
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))

            # Add excluded column (default False)
            df["Excluded"] = False
            self.current_accounting_df = df
            self.current_csv_source = filename

            #Detect columns
            missing_columns = const.REQUIRED_COLUMNS.copy()
            # Search for appropriate columns names
            self.cols = {}
            for column_name in const.REQUIRED_COLUMNS:
                for header in df.columns:
                    if header in fetch_names(column_name):
                        self.cols[column_name] = header
                        missing_columns.remove(column_name)
                        break

            self.current_booking_id = get_available_booking_id()
            return {
                "data": df.to_dict("records"),
                "columns": list(df.columns),
                "missing": missing_columns,
                "source": filename
            }

        @app.callback(
            Output("hidden-content", "style"),
            Input("upload-data", "contents")
        )
        def show_buttons_on_upload(contents):
            if contents is None:
                return {"display": "none"}  # Keep hidden
            return {"display": "block"}  # Show after upload


        @app.callback(
            Output("transactions-preview", "children"),
            Input("csv-store", "data"),
            Input("save-column-btn","n_clicks"),
            prevent_initial_call=True
        )

        def check_for_columns(data, n_clicks):
            if data is not None:
                if len(data.get("missing", [])) != 0:
                    return render_preview(data)
                else:
                    df  = pd.DataFrame(data['data'])
                    return render_table(df)
            else:
                raise PreventUpdate

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
                            id={"type": "map-column_name", "index": col},
                            options=[{"label": c, "value": c} for c in df.columns],
                            placeholder="Select the column..."
                        )
                    ]))
                return html.Div(mapping_ui)

        @app.callback(
            Output("bookings-table", "data"),
            Input("url", "pathname"),
        )
        def load_bookings(pathname):
            print("loading bookings")
            if pathname != Bookkeeper.path:
                return []
            rows = get_bookings()
            if rows is None:
                return []
            return [{"booking_id": r[0], "date": r[1]} for r in rows]

        # --- New: Load transactions for selected booking ---
        @app.callback(
            Output("transactions-table", "data"),
            Input("bookings-table", "selected_rows"),
            State("bookings-table", "data"),
        )
        def load_transactions(selected_rows, bookings_data):
            if not selected_rows or not bookings_data:
                return []

            selected_booking_id = bookings_data[selected_rows[0]]["booking_id"]

            transactions = select_transactions_from_booking(selected_booking_id)
            return [{
                "transaction_id": r[0],
                "date": r[1],
                "amount": r[2],
                "currency": r[3],
                "recipient": r[4],
                "type": r[5],
                "excluded": bool(r[6]), } for r in transactions]


        @app.callback(
            Output("csv-store", "data"),
            Input("csv-store", "data"),
            State({"type": "map-column_name", "index": ALL}, "id"),
            State({"type": "map-column_name", "index": ALL}, "value"),
            Input("save-column-btn", "n_clicks"),
            prevent_initial_call=True
        )
        def save_column(data, ids, values, n_clicks):
            if not n_clicks or data is None or (data is not None and len(data.get("missing", [])) == 0):
                raise PreventUpdate

            if data is not None:
                df = pd.DataFrame(data["data"])
                mapping = dict(zip([i["index"] for i in ids], values))
                missing = data.get("missing", [])
                for missing_column_name in missing:
                    insert_column_name(missing_column_name,mapping[missing_column_name])

                # UPDATE DATA
                # Detect columns
                missing_columns = const.REQUIRED_COLUMNS.copy()

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
                    "missing": missing_columns
                }


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

            new_transaction_added = self.insert_transactions_into_database(df)

            # TODO: Different booking_id-s ?
            if new_transaction_added:
                create_booking()  # Adds new booking to bookings database
                booking_id = self.current_booking_id
                self.current_booking_id = None
                return True,f"Saved {len(df)} transactions into booking {booking_id}"
            else:
                return False, f"No new transactions were booked."



    def insert_transactions_into_database(self,df) -> bool:
        """
        :param df: holds uploaded csv data
        :param cols: dictionary that holds column names for each required field for transactions
        :return: Returns True if a new transaction was added to the database, otherwise False
        """
        date_column_name = self.handle_date(df)
        new_transaction_added = False

        # TODO: possibly better solution for supporting different column names

        # Find the flag column
        for header in df.columns:
            if header in const.FLAGS:
                flag_column_name = header
                break

        # Insert rows into database
        for _, row in df.iterrows():
            val = row[date_column_name]
            if pd.isna(val):
                continue  # or decide how you want to handle missing dates
            transaction_state = insert_transaction(
                date=val.strftime("%Y-%m-%d %H:%M:%S"),
                recipient=row[self.cols["recipient"]],
                currency=row[self.cols["currency"]],
                amount=row[self.cols["amount"]],
                type=row[self.cols["type"]],
                source_csv=self.current_csv_source,
                booking_id=self.current_booking_id,
                excluded=row[flag_column_name]
            )
            new_transaction_added = transaction_state or new_transaction_added
        return new_transaction_added

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