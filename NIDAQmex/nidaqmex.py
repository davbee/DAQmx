'''
Python NI DAQmx example
from
https://nidaqmx-python.readthedocs.io/en/latest/

'''


import matplotlib.pyplot as plt
import nidaqmx
from nidaqmx.constants import (READ_ALL_AVAILABLE, AcquisitionType,
                               LineGrouping, LoggingMode, LoggingOperation,
                               VoltageUnits)
from nidaqmx.types import CtrTime
from nptdms import TdmsFile

# import nidaqmx.system


"""
Example code that adds an analog input channel to a task, 
configures the range, and reads data:
"""
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("Dev1/ai0",
                                         min_val = 0.0,
                                         max_val = 5.0)
    ai0 = task.read()
    print(ai0)

"""
Example code that adds multiple analog input channels to a task, 
configures their range, and reads data:
"""

with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("Dev1/ai0",
                                         min_val = 0.0,
                                         max_val = 5.0)
    task.ai_channels.add_ai_voltage_chan("Dev1/ai1",
                                         min_val = 0.0,
                                         max_val = 5.0)
    ai0, ai1 = task.read()
    print(ai0, ai1)

"""
Example code to acquire finite amount of data using hardware timing:
"""
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
    task.timing.cfg_samp_clk_timing(
        1000.0, sample_mode=AcquisitionType.FINITE, samps_per_chan=10
    )
    data = task.read(READ_ALL_AVAILABLE)
    print("Acquired data: [" + ", ".join(f"{value:f}" for value in data) + "]")

"""
Example code to acquire finite amount of data and log it to a TDMS file:
"""
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
    task.timing.cfg_samp_clk_timing(
        1000.0, sample_mode=AcquisitionType.FINITE, samps_per_chan=10
    )
    task.in_stream.configure_logging(
        "TestData.tdms",
        LoggingMode.LOG_AND_READ,
        operation=LoggingOperation.CREATE_OR_REPLACE,
    )
    data = task.read(READ_ALL_AVAILABLE)
    print("Acquired data: [" + ", ".join(f"{value:f}" for value in data) + "]")

"""
Example code to read the TDMS file created from example above and display the data:
"""
with TdmsFile.read("TestData.tdms") as tdms_file:
    for group in tdms_file.groups():
        for channel in group.channels():
            data = channel[:]
            print("data: [" + ", ".join(f"{value:f}" for value in data) + "]")

"""
Example code to plot waveform for acquired data using matplotlib.pyplot module:
"""
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
    task.timing.cfg_samp_clk_timing(
        1000.0, sample_mode=AcquisitionType.FINITE, samps_per_chan=50
    )
    data = task.read(READ_ALL_AVAILABLE)
    # plt.plot(data)
    # plt.ylabel("Amplitude")
    # plt.title("Waveform")
    # plt.show()

# single, dynamic nidaqmx.task.Task.read method returns the appropriate data type
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
    ai0 = task.read()
    print(ai0)

with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
    ai0 = task.read(number_of_samples_per_channel=2)
    print(ai0)

with nidaqmx.Task() as task:
    task.di_channels.add_di_chan(
        "Dev1/port0/line0:1", line_grouping=LineGrouping.CHAN_PER_LINE
    )
    dio01 = task.read(number_of_samples_per_channel=2)
    print(dio01)

# A single, dynamic nidaqmx.task.Task.write method also exists
# with nidaqmx.Task() as task:
#     task.co_channels.add_co_pulse_chan_time("Dev1/ctr0")
#     sample = CtrTime(high_time=0.001, low_time=0.001)
#     task.write(sample)

with nidaqmx.Task() as task:
    task.ao_channels.add_ao_voltage_chan("Dev1/ao0",
                                         "",
                                         0.0,
                                         5.0,
                                         VoltageUnits.VOLTS,
                                         "")
    # task.timing.
    task.write([1.1, 2.2, 3.3, 4.4, 4.9], auto_start=True)

# example of using an nidaqmx.system.System object
system = nidaqmx.system.System.local()
print(system.driver_version)

for device in system.devices:
    print(device)

import collections

# print(isinstance(system.devices, collections.Sequence))
device = system.devices["Dev1"]
print(device == nidaqmx.system.Device("Dev1"))
