import os
import pandas as pd
from dash import Dash, dcc, html, Input, Output, dash_table

# Define the folder containing the CSV files
testdata_folder = os.path.join(os.path.dirname(__file__), "testdata")

# Initialize the Dash app
app = Dash(__name__)
app.title = "NI-USB-6008 Data Viewer"

# Get the list of CSV files in the folder
if os.path.exists(testdata_folder):
    csv_files = [f for f in os.listdir(testdata_folder) if f.endswith(".csv")]
else:
    csv_files = []

# Layout of the Dash app
app.layout = html.Div(
    [
        html.H1("NI-USB-6008 Data Viewer", style={"textAlign": "center"}),
        html.Div(
            [
                html.Label("Select a CSV file:"),
                dcc.Dropdown(
                    id="file-dropdown",
                    options=[{"label": f, "value": f} for f in csv_files],
                    placeholder="Select a file",
                ),
            ],
            style={"width": "50%", "margin": "auto"},
        ),
        html.Div(
            [
                dcc.Checklist(
                    id="toggle-table",
                    options=[{"label": "Show Table", "value": "show"}],
                    value=[],  # Default to not showing the table
                    style={"textAlign": "center", "marginTop": "10px"},
                ),
            ]
        ),
        html.Div(id="file-info", style={"marginTop": "20px", "textAlign": "center"}),
        html.Div(id="table-container", style={"marginTop": "20px"}),
        html.Div(
            [
                html.H3("Data Plot", style={"textAlign": "center"}),
                dcc.Graph(id="data-plot"),
            ],
            style={"marginTop": "20px"},
        ),
    ]
)


# Callback to update the table, file info, and plot
@app.callback(
    [
        Output("file-info", "children"),
        Output("table-container", "children"),
        Output("data-plot", "figure"),
    ],
    [Input("file-dropdown", "value"), Input("toggle-table", "value")],
)
def update_table_and_plot(selected_file, toggle_table):
    if not selected_file:
        return "No file selected.", None, {}

    file_path = os.path.join(testdata_folder, selected_file)
    try:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(file_path)

        # Create a Dash DataTable to display the data
        if "show" in toggle_table:
            table = dash_table.DataTable(
                data=df.to_dict("records"),
                columns=[{"name": col, "id": col} for col in df.columns],
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "padding": "5px"},
                page_size=10,  # Display 10 rows per page
            )
        else:
            table = None  # Hide the table if the checkbox is unchecked

        # Create a plot using the first two columns of the DataFrame
        if len(df.columns) >= 2:
            figure = {
                "data": [
                    {
                        "x": df[df.columns[0]],
                        "y": df[df.columns[1]],
                        "type": "line",
                        "name": f"{df.columns[1]} vs {df.columns[0]}",
                    }
                ],
                "layout": {
                    "title": f"Plot of {df.columns[1]} vs {df.columns[0]}",
                    "xaxis": {"title": df.columns[0]},
                    "yaxis": {"title": df.columns[1]},
                },
            }
        else:
            figure = {"data": [], "layout": {"title": "Insufficient data for plotting"}}

        return f"Displaying data from: {selected_file}", table, figure
    except Exception as e:
        return f"Failed to load file: {e}", None, {}


# Run the app
if __name__ == "__main__":
    app.run(debug=True, port=8051)
