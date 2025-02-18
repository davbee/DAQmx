import sys
import numpy as np
import nidaqmx
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg


class NI_USB6009_GUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Initialize attributes
        self.sampling_rate = 1000  # Default sampling rate for input
        self.time_window = 5  # 5-second time window
        self.max_data_points = 0  # Will be set based on sampling rate
        self.sine_wave_frequency = 10  # Frequency of the sinusoidal wave
        self.sine_wave_amplitude = (
            2  # Amplitude of the sinusoidal wave (2V peak-to-peak)
        )
        self.sine_wave_offset = (
            2.5  # DC offset to shift the sine wave into the 0V to 5V range
        )
        self.sine_wave_phase = 0  # Phase of the sinusoidal wave

        self.initUI()
        self.input_task = None
        self.output_task = None
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.data = []

    def initUI(self):
        self.setWindowTitle("NI-USB-6009 Data Acquisition and Output")

        # Layout
        layout = QtWidgets.QVBoxLayout()

        # Device Selection
        self.device_label = QtWidgets.QLabel("Device:")
        self.device_combo = QtWidgets.QComboBox()
        self.device_combo.addItems(self.get_ni_devices())
        layout.addWidget(self.device_label)
        layout.addWidget(self.device_combo)

        # Sampling Rate
        self.sampling_rate_label = QtWidgets.QLabel("Sampling Rate (Hz):")
        self.sampling_rate_input = QtWidgets.QLineEdit(str(self.sampling_rate))
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
        """Start data acquisition and output."""
        if self.input_task is not None or self.output_task is not None:
            self.stop_acquisition()

        device = self.device_combo.currentText()
        self.sampling_rate = float(self.sampling_rate_input.text())

        # Calculate the maximum number of data points for a 10-second window
        self.max_data_points = int(self.time_window * self.sampling_rate)

        # Create and start the output task (on-demand)
        self.output_task = nidaqmx.Task()
        self.output_task.ao_channels.add_ao_voltage_chan(
            f"{device}/ao0", min_val=0.0, max_val=5.0
        )

        # Create and start the input task
        self.input_task = nidaqmx.Task()
        self.input_task.ai_channels.add_ai_voltage_chan(
            f"{device}/ai0", min_val=0.0, max_val=5.0
        )
        self.input_task.timing.cfg_samp_clk_timing(
            rate=self.sampling_rate,
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
        )

        # Start the timer for updating the plot and generating the sine wave
        interval = int(1000 / self.sampling_rate)
        self.timer.start(interval)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_acquisition(self):
        """Stop data acquisition and output."""
        self.timer.stop()
        if self.input_task is not None:
            self.input_task.close()
            self.input_task = None
        if self.output_task is not None:
            self.output_task.close()
            self.output_task = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_plot(self):
        """Update the plot with new data and generate the sine wave."""
        if self.input_task is not None and self.output_task is not None:
            # Generate the next sample of the sine wave
            t = self.sine_wave_phase / self.sampling_rate
            sine_sample = self.sine_wave_amplitude * np.sin(
                2 * np.pi * self.sine_wave_frequency * t
            )

            # Shift the sine wave to the 0V to 5V range
            shifted_sample = sine_sample + self.sine_wave_offset

            # Write the shifted sample to the analog output
            self.output_task.write(shifted_sample, auto_start=True)

            # Increment the phase for the next sample
            self.sine_wave_phase += 1

            # Read the input data
            new_data = self.input_task.read(number_of_samples_per_channel=10)
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
        """Ensure tasks are closed when the window is closed."""
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
