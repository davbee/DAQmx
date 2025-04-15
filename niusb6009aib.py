import sys

# import numpy as np
import nidaqmx
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets


class NI_USB6009_GUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.task = None
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.data = []
        self.time_window = 10  # 10-second time window
        self.max_data_points = 0  # Will be set based on sampling rate

    def initUI(self):
        self.setWindowTitle("NI-USB-6009 Data Acquisition")

        # Layout
        layout = QtWidgets.QVBoxLayout()

        # Device Selection
        self.device_label = QtWidgets.QLabel("Device:")
        self.device_combo = QtWidgets.QComboBox()
        self.device_combo.addItems(self.get_ni_devices())
        layout.addWidget(self.device_label)
        layout.addWidget(self.device_combo)

        # Port Selection
        self.port_label = QtWidgets.QLabel("Port:")
        self.port_combo = QtWidgets.QComboBox()
        self.port_combo.addItems(["ai0", "ai1", "ai2", "ai3"])
        layout.addWidget(self.port_label)
        layout.addWidget(self.port_combo)

        # Sampling Rate
        self.sampling_rate_label = QtWidgets.QLabel("Sampling Rate (Hz):")
        self.sampling_rate_input = QtWidgets.QLineEdit("60")
        layout.addWidget(self.sampling_rate_label)
        layout.addWidget(self.sampling_rate_input)

        # Plot Widget
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        # Buttons
        self.start_button = QtWidgets.QPushButton("Start")
        self.start_button.clicked.connect(self.start_acquisition)
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_acquisition)
        self.clear_button = QtWidgets.QPushButton("Clear Graph")
        self.clear_button.clicked.connect(self.clear_graph)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_ni_devices(self):
        """Get list of connected NI devices."""
        return nidaqmx.system.System.local().devices.device_names

    def start_acquisition(self):
        """Start data acquisition."""
        if self.task is not None:
            self.task.close()

        device = self.device_combo.currentText()
        port = self.port_combo.currentText()
        sampling_rate = float(self.sampling_rate_input.text())

        # Calculate the maximum number of data points for a 10-second window
        self.max_data_points = int(self.time_window * sampling_rate)

        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan(f"{device}/{port}")
        self.task.timing.cfg_samp_clk_timing(sampling_rate, samps_per_chan=100)

        # Start the timer with the calculated interval
        interval = int(1000 / sampling_rate)
        self.timer.start(interval)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_acquisition(self):
        """Stop data acquisition."""
        self.timer.stop()
        if self.task is not None:
            self.task.close()
            self.task = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_plot(self):
        """Update the plot with new data."""
        if self.task is not None:
            new_data = self.task.read(number_of_samples_per_channel=1)
            self.data.append(new_data[0])

            # Keep only the last `max_data_points` data points
            if len(self.data) > self.max_data_points:
                self.data.pop(0)  # Remove the oldest data point

            # Plot the data
            self.plot_widget.plot(self.data, clear=True, pen="b")

    def clear_graph(self):
        """Clear the graph."""
        self.data = []
        self.plot_widget.clear()

    def closeEvent(self, event):
        """Ensure the task is closed when the window is closed."""
        self.stop_acquisition()
        event.accept()


if __name__ == "__main__":
    # Create the QApplication object before any QWidget
    app = QtWidgets.QApplication(sys.argv)

    # Create the main window
    gui = NI_USB6009_GUI()
    gui.show()

    # Execute the application
    sys.exit(app.exec_())
