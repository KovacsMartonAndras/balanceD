import base64
import io
import pandas as pd
import plotly.express as px
from dash import html, dcc, register_page, Input, Output, State, dash_table
import constants as const
from db import insert_transaction

register_page(__name__, path="/bookkeeper")

layout = html.Div([
    html.H2("Bookkeeper"),
    # File upload component
    dcc.Upload(
        id="upload-data",
        children=html.Div([
            "Drag and Drop or ",
            html.A("Select a CSV File")
        ]),
        style={
            "width": "60%",
            "height": "60px",
            "lineHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
            "textAlign": "center",
            "margin": "10px"
        },
        multiple=False  # only one file at a time
    ),

    # Output: table + graph
    html.Div(id="output-table"),
    dcc.Graph(id="output-graph")
])


def handle_date(df):
    # Find date column
    for header in df.columns:
        if header in const.DATE_HEADER_NAMES:
            date_column_name = header
            break
    # Convert date column to datetime
    try:
        df[date_column_name] = pd.to_datetime(df[date_column_name], format="%d.%m.%Y %H:%M:%S")
    except:
        # fallback if exact format fails
        df[date_column_name] = pd.to_datetime(df[date_column_name], dayfirst=True, errors="coerce")

    return date_column_name


def register_callbacks(app):
    @app.callback(
        [Output("output-table", "children"),
         Output("output-graph", "figure")],
        [Input("upload-data", "contents")],
        [State("upload-data", "filename")]
    )


    def update_output(contents, filename):
        if contents is None:
            return html.P("No file uploaded yet."), {}

        # Parse uploaded content
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))

        date_column_name = handle_date(df)
        # Find amount column
        for header in df.columns:
            if header in const.AMOUNT_HEADER_NAMES:
                amount_column_name = header
            elif header in const.CATEGORY_HEADER_NAMES:
                category_column_name = header
            elif header in const.CURRENCY_HEADER_NAMES:
                currency_column_name = header

        # Insert rows into database
        for _, row in df.iterrows():
            insert_transaction(
                date=row[date_column_name].strftime("%Y-%m-%d %H:%M:%S"),
                description=row[category_column_name],
                currency=row[currency_column_name],
                amount=row[amount_column_name]
            )

        # Create table
        table = dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict("records"),
            page_size=10,
            style_table={"overflowX": "auto"}
        )
        # Aggregate by date (sum amounts per day)
        df_daily = df.groupby(df[date_column_name].dt.date)[amount_column_name].sum().reset_index()

        # Create bar chart
        fig = px.bar(df_daily, x=date_column_name, y=amount_column_name, title="Expenses by Day")

        return table, fig
