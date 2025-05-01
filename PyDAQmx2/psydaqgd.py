"""
Date: 2023-10-05 16:00:00
Last Modified: 2025-04-16
Description: DAQmx Real-Time Strip Chart Application with Google Drive Integration

This program is a PySide6-based GUI application that uses the NI-DAQmx library to
perform real-time data acquisition and generation. It is designed to interface
with National Instruments (NI) DAQ devices to read analog input signals and
generate analog output signals. Additionally, it integrates with Google Drive
to upload acquired data for cloud storage.

Key Features:
1. **Real-Time Plotting**:
   - Displays a real-time strip chart of the input voltage (AI) over time.
   - The plot updates dynamically as data is acquired.

2. **Analog Output (AO)**:
   - Generates a sine wave signal that oscillates between 0 and 5 volts with a mean of 2.5 volts.
   - The AO channel can be specified dynamically through the GUI.

3. **Analog Input (AI)**:
   - Reads voltage signals from the specified AI channel.
   - The AI channel can be specified dynamically through the GUI.

4. **Autoscaling**:
   - Provides buttons to autoscale the x-axis and y-axis of the plot based on the current data.

5. **Data Logging**:
   - Logs the time, AO voltage, and AI voltage to a text box in the GUI.
   - Allows saving the logged data to a CSV file for further analysis.

6. **Customizable Channels**:
   - Users can specify the AO and AI channels dynamically through input fields in the GUI.

7. **Start/Stop Functionality**:
   - Users can start and stop the data acquisition and generation process using a button in the GUI.

8. **Save Data and Plot**:
   - Provides options to save the data displayed in the text box or the full data in memory to a CSV file.
   - Automatically saves the plot as a PNG image after data acquisition is completed.

9. **SQLite3 Database Archiving**:
   - Archives the acquired data (time, AO voltage, AI voltage) into an SQLite3 database for long-term storage and analysis.
   - Automatically creates the database and table if they do not exist.

10. **Google Drive Integration**:
    - Uploads the latest acquired data file to a specified Google Drive folder.
    - Uses the `gcpdrive` module for Google Drive API integration.

11. **Error Logging**:
    - Logs each step of the acquisition process to a text box in the GUI.
    - Captures and logs errors during acquisition, file saving, database archiving, and Google Drive uploads.

12. **Exit Button**:
    - Includes an "Exit" button to quit the application cleanly.

Requirements:
- National Instruments DAQ device with properly configured channels.
- Python libraries: PySide6, PyQtGraph, PyDAQmx, numpy, csv, datetime, os, time, sqlite3, google-api-python-client.
- A `credentials.json` file for Google Drive API authentication.
- A valid `token.json` file will be created after the first authentication.

How to Use:
1. Specify the AO and AI channels in the input fields (default: "Dev2/ao0" and "Dev2/ai0").
2. Specify the number of iterations for the acquisition loop.
3. Click the "Start" button to begin data acquisition and generation.
4. View the real-time plot of the input voltage.
5. After acquisition:
   - The data is saved to a CSV file and archived in an SQLite3 database.
   - The plot is saved as a PNG image.
   - The CSV file is uploaded to a specified Google Drive folder.
6. Click the "Exit" button to quit the application.

Note:
- Ensure that the NI-DAQ device is connected and configured correctly before running the program.
- The program assumes a voltage range of 0 to 5 volts for both AO and AI channels.
- Ensure the `gcpdrive` module is properly configured for Google Drive API integration.
"""

# import csv
import datetime
import os
import time
import sqlite3  # Import the SQLite3 module

import numpy as np
import PyDAQmx
import pyqtgraph as pg
import pyqtgraph.exporters  # Import the exporter module

# from dotenv import load_dotenv
from PyDAQmx import Task
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from gcpdrive import gDrive

# # Load environment variables from .env file
# load_dotenv()

# # Get channel configurations from environment variables
# AICHANNEL = os.getenv("AICHANNEL", "Dev2/ai0")  # Default to "Dev2/ai0" if not set
# AOCHANNEL = os.getenv("AOCHANNEL", "Dev2/ao0")  # Default to "Dev2/ao0" if not set

# Ensure the testdata/ folder exists
os.makedirs("PyDAQmx2/testdata", exist_ok=True)


class DAQApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DAQmx Real-Time Strip Chart")
        self.resize(800, 450)

        # Center the window on the screen
        # self.center_window()

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Horizontal layout for AO and AI channel input fields
        channel_layout = QHBoxLayout()

        # Input field for AO channel
        self.ao_channel_input = QTextEdit()
        self.ao_channel_input.setText("Dev2/ao0")  # Set default AO channel
        self.ao_channel_input.setFixedSize(200, 25)  # Set fixed size for AO input box
        channel_layout.addWidget(self.ao_channel_input)

        # Input field for AI channel
        self.ai_channel_input = QTextEdit()
        self.ai_channel_input.setText("Dev2/ai0")  # Set default AI channel
        self.ai_channel_input.setFixedSize(200, 25)  # Set fixed size for AI input box
        channel_layout.addWidget(self.ai_channel_input)

        # Input field for loop count
        self.loop_count_input = QTextEdit()
        self.loop_count_input.setText("201")  # Default loop count
        self.loop_count_input.setFixedSize(
            100, 25
        )  # Set fixed size for loop count input
        channel_layout.addWidget(self.loop_count_input)

        # Add the horizontal layout to the main layout
        main_layout.addLayout(channel_layout)

        # PyQtGraph plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setMinimumHeight(400)  # Set minimum height for the plot widget
        main_layout.addWidget(self.plot_widget)

        # Configure plot appearance
        self.plot_widget.setBackground("w")  # Set background to white
        self.plot_widget.showGrid(x=True, y=True)  # Enable gridlines
        self.plot_widget.setLabel("left", "Voltage (V)")  # Y-axis label
        self.plot_widget.setLabel("bottom", "Time (s)")  # X-axis label

        # Plot curve
        self.curve = self.plot_widget.plot(
            pen=pg.mkPen(color="b", width=2)
        )  # Blue line
        self.deltat = []
        self.ain = []

        # Start button
        self.start_button = QPushButton("Start")
        self.start_button.setFixedSize(100, 30)  # Set fixed size for the button
        main_layout.addWidget(self.start_button)
        self.start_button.clicked.connect(self.start_acquisition)

        # Exit button
        self.exit_button = QPushButton("Exit")
        self.exit_button.setFixedSize(100, 30)  # Set fixed size for the button
        main_layout.addWidget(self.exit_button)
        self.exit_button.clicked.connect(
            self.close_application
        )  # Connect to exit function

        # Configure plot appearance
        self.plot_widget.setBackground("w")  # Set background to white
        self.plot_widget.showGrid(x=True, y=True)  # Enable gridlines
        self.plot_widget.setLabel("left", "Voltage (V)")  # Y-axis label
        self.plot_widget.setLabel("bottom", "Time (s)")  # X-axis label
        self.plot_widget.setTitle("NI-USB-6008 AI(t)")  # Add plot title

        # Text box for displaying print statements
        self.text_box = QTextEdit()
        self.text_box.setMinimumHeight(150)  # Set minimum height for the text box
        self.text_box.setReadOnly(True)  # Make the text box read-only
        main_layout.addWidget(self.text_box)

        # DAQ tasks
        self.aotask = None
        self.aitask = None
        self.aopoints = self.generate_output_points()
        self.current_index = 0
        self.aout = []  # Reset ain
        self.idata = np.zeros(1, dtype=np.float64)
        self.samples_read = PyDAQmx.int32()

    def center_window(self):
        """Center the main window on the screen."""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())

    def save_plot_as_png(self):
        """Save the current plot as a PNG image."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"PyDAQmx2/testdata/plot_{timestamp}.png"
        exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
        exporter.parameters()["width"] = 800  # Set the width of the exported image
        exporter.export(filename)
        self.log_message(f"Plot saved as {filename}")
        self.gd(filename, "1TBQsJ8-182ql2_p4eoHABn0vlgHJ7D6v")

    def generate_output_points(self):
        """Generate a sine wave oscillating between 0 and 5 with a mean of 2.5."""
        t = np.linspace(
            0, 2 * np.pi, 100, endpoint=False
        )  # Generate 100 points for one sine wave cycle
        amplitude = 2.5  # Half the range (max - min) / 2
        offset = 2.5  # Mean value
        return amplitude * np.sin(t) + offset

    def start_acquisition(self):
        """Start the data acquisition process."""
        try:
            self.log_message("Stopping and clearing any existing tasks...")
            # Stop and clear any existing tasks to avoid conflicts
            if self.aotask:
                self.aotask.StopTask()
                self.aotask.ClearTask()
                self.aotask = None
            if self.aitask:
                self.aitask.StopTask()
                self.aitask.ClearTask()
                self.aitask = None

            self.log_message("Reading input fields for AO and AI channels...")
            # Get AO and AI channels from input fields
            ao_channel = self.ao_channel_input.toPlainText().strip()
            ai_channel = self.ai_channel_input.toPlainText().strip()
            loop_count_text = self.loop_count_input.toPlainText().strip()

            if not ao_channel or not ai_channel:
                raise ValueError("Error: Both AO and AI channels must be specified.")

            try:
                loop_count = int(loop_count_text)
                if loop_count <= 0:
                    raise ValueError("Error: Loop count must be a positive integer.")
            except ValueError as e:
                self.log_message(str(e))
                raise

            self.log_message("Creating and starting new tasks...")
            # Create and start new tasks
            self.aotask = ao(ao_channel)
            self.aitask = ai(ai_channel)
            self.current_index = 0
            self.deltat = []  # Reset deltat
            self.ain = []  # Reset ain
            self.aout = []  # Reset aout

            self.log_message(f"Starting acquisition for {loop_count} iterations...")
            self.run_acquisition(loop_count)
        except Exception as e:
            self.log_message(f"Error during acquisition: {e}")
            raise

    def run_acquisition(self, loop_count):
        """Run the acquisition for the specified number of iterations."""
        try:
            self.log_message("Initializing acquisition loop...")
            self.start_time = time.time()  # Reset start time to T=0
            self.current_index = 0
            self.loop_count = loop_count
            self.iteration = 0

            # Create a QTimer for periodic updates
            self.timer = QTimer()
            self.timer.timeout.connect(self.perform_iteration)
            self.timer.start(20)  # 20ms interval (equivalent to time.sleep(0.02))

        except Exception as e:
            self.log_message(f"Error during acquisition loop: {e}")
            raise

    def perform_iteration(self):
        """Perform one iteration of the acquisition loop."""
        try:
            if self.iteration >= self.loop_count:
                self.timer.stop()  # Stop the timer when all iterations are complete
                self.log_message("Acquisition completed.")
                fn = self.save_data_to_file()
                self.save_plot_as_png()
                self.gd(fn, "1TBQsJ8-182ql2_p4eoHABn0vlgHJ7D6v")
                return

            if self.current_index >= len(self.aopoints):
                self.current_index = 0  # Loop back to the start of the sine wave

            # Set output voltage
            output_voltage = self.aopoints[self.current_index]
            self.aout.append(output_voltage)  # Append to output data
            odata = np.array([output_voltage], dtype=np.float64)
            self.aotask.WriteAnalogF64(
                1, 1, 5.0, PyDAQmx.DAQmx_Val_GroupByChannel, odata, None, None
            )

            # Read input voltage
            self.aitask.ReadAnalogF64(
                1,
                5.0,
                PyDAQmx.DAQmx_Val_GroupByChannel,
                self.idata,
                1,
                PyDAQmx.byref(self.samples_read),
                None,
            )

            # Update plot data
            current_time = time.time() - self.start_time  # Calculate elapsed time
            self.deltat.append(current_time)
            self.ain.append(self.idata[0])
            self.log_message(
                f"Iteration {self.iteration + 1}/{self.loop_count}: Time={current_time:.3f}s, "
                f"AO={output_voltage:.3f}V, AI={self.idata[0]:.3f}V"
            )

            # Update the plot (only show the last 10 seconds of data)
            visible_deltat = self.deltat[-100:]  # Last 100 points
            visible_ain = self.ain[-100:]
            self.curve.setData(visible_deltat, visible_ain)

            QApplication.processEvents()  # Allow the GUI to update in real time

            self.current_index += 1
            self.iteration += 1

        except Exception as e:
            self.log_message(f"Error during acquisition iteration: {e}")
            self.timer.stop()  # Stop the timer in case of an error
            raise

    def save_data_to_file(self):
        """Save the deltat and ain to a file in the testdata/ folder."""
        try:
            self.log_message("Saving data to CSV file...")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"PyDAQmx2/testdata/data_{timestamp}.csv"
            data = np.column_stack((self.deltat, self.aout, self.ain))
            np.savetxt(
                filename,
                data,
                delimiter=",",
                header="Time (s), AO (V), AI (V)",  # Header for the CSV file
                comments="",
                fmt="%.3f",  # Format each value to three decimal points
            )
            self.log_message(f"Data saved to {filename}")

            # Archive the data into the SQLite3 database
            self.save_data_to_database()
            return filename  # Return only the filename

        except Exception as e:
            self.log_message(f"Error saving data to file: {e}")
            raise

    def save_data_to_database(self):
        """Save the deltat, aout, and ain data to an SQLite3 database."""
        try:
            self.log_message("Archiving data to SQLite3 database...")
            conn = sqlite3.connect("PyDAQmx2/testdata/data_archive.db")
            cursor = conn.cursor()

            # Create a table if it doesn't already exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS acquisition_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    time REAL,
                    ao_voltage REAL,
                    ai_voltage REAL
                )
            """
            )

            # Insert the data into the table
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for time_val, ao_val, ai_val in zip(self.deltat, self.aout, self.ain):
                cursor.execute(
                    """
                    INSERT INTO acquisition_data (timestamp, time, ao_voltage, ai_voltage)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        timestamp,
                        round(time_val, 3),  # Round time to 3 decimal points
                        round(ao_val, 3),  # Round AO voltage to 3 decimal points
                        round(ai_val, 3),  # Round AI voltage to 3 decimal points
                    ),
                )

            conn.commit()
            conn.close()
            self.log_message("Data archived to SQLite3 database.")
        except Exception as e:
            self.log_message(f"Error archiving data to database: {e}")
            raise

    def log_message(self, message):
        """Log a message to the text box."""
        self.text_box.append(message)  # Append the message to the text box
        self.text_box.ensureCursorVisible()  # Ensure the latest message is visible

    # Add the exit function
    def close_application(self):
        """Close the application."""
        self.log_message("Exiting application...")
        QApplication.quit()

    def gd(self, fn, foid):
        """Upload the latest data file to Google Drive."""
        try:
            gdrive = gDrive()
            csvfile = fn
            gdrive.upload_to_folder(csvfile, foid)
            self.log_message(f"File uploaded successfully: {fn}")
        except Exception as e:
            self.log_message(f"Error uploading to Google Drive: {e}")
            raise


def ao(ao_channel):
    task = Task()
    task.CreateAOVoltageChan(
        ao_channel,
        "",
        0.0,
        5.0,
        PyDAQmx.DAQmx_Val_Volts,
        None,
    )
    task.StartTask()
    return task


def ai(ai_channel):
    task = Task()
    task.CreateAIVoltageChan(
        ai_channel,
        "",
        PyDAQmx.DAQmx_Val_Cfg_Default,
        0.0,
        5.0,
        PyDAQmx.DAQmx_Val_Volts,
        None,
    )
    task.StartTask()
    return task


if __name__ == "__main__":
    app = QApplication([])
    window = DAQApp()
    window.show()
    window.center_window()  # Call center_window after the window is shown
    app.exec()
