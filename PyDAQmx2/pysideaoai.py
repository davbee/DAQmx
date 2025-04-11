"""
Created by VSCodeGPT
Date: 2023-10-05 16:00:00
Last Modified: 2023-10-05 16:00:00
Director: David Pih
Description: DAQmx Real-Time Strip Chart Application

DAQmx Real-Time Strip Chart Application

This program is a PyQt-based GUI application that uses the NI-DAQmx library to
perform real-time data acquisition and generation.
It is designed to interface with National Instruments (NI) DAQ devices to read
analog input signals and generate analog output signals.

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

8. **Save Data**:
   - Provides options to save the data displayed in the text box or the full data in memory to a CSV file.

Requirements:
- National Instruments DAQ device with properly configured channels.
- Python libraries: PySide6, PyQtGraph, PyDAQmx, numpy, csv, datetime, os, time.

How to Use:
1. Specify the AO and AI channels in the input fields (default: "Dev2/ao0" and "Dev2/ai0").
2. Click the "Start" button to begin data acquisition and generation.
3. View the real-time plot of the input voltage.
4. Use the "Autoscale Y-Axis" and "Autoscale X-Axis" buttons to adjust the plot scaling.
5. Click the "Stop" button to stop the acquisition and save the data to a CSV file.

Note:
- Ensure that the NI-DAQ device is connected and configured correctly before running the program.
- The program assumes a voltage range of 0 to 5 volts for both AO and AI channels.
"""

import csv
import datetime
import os
import time

import numpy as np
import PyDAQmx
import pyqtgraph as pg
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

# # Load environment variables from .env file
# load_dotenv()

# # Get channel configurations from environment variables
# AICHANNEL = os.getenv("AICHANNEL", "Dev2/ai0")  # Default to "Dev2/ai0" if not set
# AOCHANNEL = os.getenv("AOCHANNEL", "Dev2/ao0")  # Default to "Dev2/ao0" if not set

# Ensure the testdata/ folder exists
os.makedirs("testdata", exist_ok=True)


class DAQApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DAQmx Real-Time Strip Chart")
        self.resize(800, 450)

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

        # Start/Stop button
        self.start_stop_button = QPushButton("Start")
        self.start_stop_button.setFixedSize(100, 30)  # Set fixed size for the button
        main_layout.addWidget(self.start_stop_button)
        self.start_stop_button.clicked.connect(self.toggle_acquisition)

        # Autoscale button for y-axis
        self.autoscale_y_button = QPushButton("Autoscale Y-Axis")
        self.autoscale_y_button.setFixedSize(150, 30)  # Set fixed size for the button
        main_layout.addWidget(self.autoscale_y_button)
        self.autoscale_y_button.clicked.connect(self.autoscale_y_axis)

        # Autoscale button for x-axis
        self.autoscale_x_button = QPushButton("Autoscale X-Axis")
        self.autoscale_x_button.setFixedSize(150, 30)  # Set fixed size for the button
        main_layout.addWidget(self.autoscale_x_button)
        self.autoscale_x_button.clicked.connect(self.autoscale_x_axis)

        # Text box for displaying print statements
        self.text_box = QTextEdit()
        self.text_box.setMinimumHeight(150)  # Set minimum height for the text box
        self.text_box.setReadOnly(True)  # Make the text box read-only
        main_layout.addWidget(self.text_box)

        # Timer for updating the plot
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

        # DAQ tasks
        self.aotask = None
        self.aitask = None
        self.aopoints = self.generate_output_points()
        self.current_index = 0
        self.aout = []  # Reset ain
        self.idata = np.zeros(1, dtype=np.float64)
        self.samples_read = PyDAQmx.int32()
        self.acquiring = False
        self.start_time = None  # To track the start time of the acquisition

    def autoscale_y_axis(self):
        """Autoscale the y-axis based on the current data."""
        if self.ain:
            self.plot_widget.setYRange(min(self.ain), max(self.ain), padding=0.1)
        else:
            self.log_message("No data available to autoscale.")

    def autoscale_x_axis(self):
        """Autoscale the x-axis based on the current data."""
        if self.deltat:
            self.plot_widget.setXRange(min(self.deltat), max(self.deltat), padding=0.1)
        else:
            self.log_message("No data available to autoscale.")

    def generate_output_points(self):
        """Generate a sine wave oscillating between 0 and 5 with a mean of 2.5."""
        t = np.linspace(
            0, 2 * np.pi, 100, endpoint=False
        )  # Generate 100 points for one sine wave cycle
        amplitude = 2.5  # Half the range (max - min) / 2
        offset = 2.5  # Mean value
        return amplitude * np.sin(t) + offset

    def toggle_acquisition(self):
        if self.acquiring:
            self.stop_acquisition()
        else:
            self.start_acquisition()

    def start_acquisition(self):
        # Get AO and AI channels from input fields
        ao_channel = self.ao_channel_input.toPlainText().strip()
        ai_channel = self.ai_channel_input.toPlainText().strip()

        if not ao_channel or not ai_channel:
            self.log_message("Error: Please specify both AO and AI channels.")
            return

        self.aotask = ao(ao_channel)
        self.aitask = ai(ai_channel)
        self.current_index = 0
        self.deltat = []  # Reset deltat
        self.ain = []  # Reset ain
        self.aout = []  # Reset aout
        self.acquiring = True
        self.start_stop_button.setText("Stop")
        self.start_time = time.time()  # Reset start time to T=0
        self.timer.start(50)  # Update every 50 ms

    def stop_acquisition(self):
        self.timer.stop()
        if self.aotask:
            self.aotask.StopTask()
            self.aotask.ClearTask()
        if self.aitask:
            self.aitask.StopTask()
            self.aitask.ClearTask()
        self.acquiring = False
        self.start_stop_button.setText("Start")
        self.save_data_to_file()  # Save data when acquisition stops

    def update_plot(self):
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
        self.log_message(f"{current_time:.3f},{output_voltage:.3f},{self.idata[0]:.3f}")

        # Update the plot (only show the last 10 seconds of data)
        visible_deltat = self.deltat[
            -100:
        ]  # Last 100 points (10 seconds at 100ms intervals)
        visible_ain = self.ain[-100:]
        self.curve.setData(visible_deltat, visible_ain)

        self.current_index += 1

    def log_message(self, message):
        """Log a message to the text box."""
        self.text_box.append(message)  # Append the message to the text box
        self.text_box.ensureCursorVisible()  # Ensure the latest message is visible

    def save_data_to_file(self):
        """Save the deltat and ain to a file in the testdata/ folder."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"testdata/data_{timestamp}.csv"
        data = np.column_stack(
            (self.deltat, self.aout, self.ain)
        )  # Save all data in memory
        # data = self.text_box.toPlainText()
        np.savetxt(
            filename,
            data,
            delimiter=",",
            header="Time (s), AO (V), AI (V)",  # Header for the CSV file
            comments="",
            fmt="%.3f",  # Format each value to three decimal points
        )
        self.log_message(f"Data saved to {filename}")

    def save_data_to_file1(self):
        """Save the data from the text box to a file in the testdata/ folder."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"testdata/data_{timestamp}.csv"

        # Get the content of the text box
        text_content = self.text_box.toPlainText()

        # Split the content into lines
        lines = text_content.split("\n")

        # Parse the lines into rows (skip empty lines)
        data = [line.split(",") for line in lines if line.strip()]

        # Save the data to a CSV file
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Time (s)", "AO (V)", "AI (V)"])  # Write header
            writer.writerows(data)  # Write data rows

        self.log_message(f"Data saved to {filename}")


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
    app.exec()
