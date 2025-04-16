"""
Date: 2025-04-16
Last Modified: 2025-04-16
Description: NI-USB-6008 Data Viewer Dashboard

This program is a Dash-based web application designed to visualize data acquired
from the NI-USB-6008 device. It allows users to select `.csv` files from a specified
folder, view the data in a table, and plot the data dynamically.

Key Features:
1. **File Selection**:
   - Lists all `.csv` files in the `testdata` folder.
   - Allows users to select a file from a dropdown menu.

2. **Data Table**:
   - Displays the contents of the selected `.csv` file in a paginated table.
   - Includes an option to toggle the visibility of the table.

3. **Dynamic Plotting**:
   - Plots the data from the first two columns of the selected `.csv` file.
   - Automatically updates the plot when a new file is selected.

4. **Error Handling**:
   - Displays appropriate error messages if the file cannot be loaded or if the data is insufficient for plotting.

5. **Responsive Design**:
   - The layout is designed to be user-friendly and works well on different screen sizes.

Requirements:
- Python libraries: `dash`, `pandas`.
- A `testdata` folder containing `.csv` files in the same directory as this script.

How to Use:
1. Place the `.csv` files in the `testdata` folder.
2. Run the script using the command:
   ```bash
   python Dashboard.py
3. Open the application in your browser at http://127.0.0.1:8051.
4. Select a file from the dropdown menu to view its data and plot.

Note:

The .csv files should have at least two columns for plotting.
Ensure the testdata folder exists and contains valid .csv files.
"""

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
                    # value=["show"],  # Default to showing the table
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
