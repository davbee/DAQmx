import time

import numpy as np
import PyDAQmx
from PyDAQmx import Task


# Create a task
aotask = Task()

# Define the analog output channel
channel: str = "Dev1/ao0"  # Replace 'Dev1' with your device name if different

# Create an analog output voltage channel
"""
DAQmxCreateAOVoltageChan
int32 DAQmxCreateAOVoltageChan (TaskHandle taskHandle,
const char physicalChannel[], const char nameToAssignToChannel[],
float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);

TaskHandle taskHandle = null; do not set
"""
aotask.CreateAOVoltageChan(channel, "", 0.0, 5.0, PyDAQmx.DAQmx_Val_Volts, None)

ao1 = np.linspace(0.0, 5.0, num=11)
ao2 = np.linspace(4.5, 0.0, num=10)
aopoints = np.append(ao1, ao2)

# Start the task
aotask.StartTask()

for i in aopoints:
    # Define the output voltage
    output_voltage = i  # Voltage you want to output

    # Write the voltage to the channel
    aodata = np.array([output_voltage], dtype=np.float64)

    # Writes multiple floating-point samples to a task that
    # contains one or more analog output channels.
    """
    DAQmxWriteAnalogF64
    int32 DAQmxWriteAnalogF64 (TaskHandle taskHandle, int32 numSampsPerChan,
    bool32 autoStart, float64 timeout, bool32 dataLayout,
    float64 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved);

    TaskHandle taskHandle = null; do not set
    """
    aotask.WriteAnalogF64(
        1, 1, 5.0, PyDAQmx.DAQmx_Val_GroupByChannel, aodata, None, None
    )

    print(f"Analog output set to {output_voltage:.3f} V")

    # pause time
    time.sleep(0.1)

# Stop and clear the task
aotask.StopTask()
aotask.ClearTask()
