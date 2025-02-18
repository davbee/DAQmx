import time

import numpy as np
import PyDAQmx
from PyDAQmx import Task

# Create a task
aitask = Task()

# Define the analog input channel
aichannel: str = "Dev1/ai0"

# Create an analog input voltage channel
# https://documentation.help/NI-DAQmx-C-Functions/DAQmxCreateAIVoltageChan.html
aitask.CreateAIVoltageChan(
    aichannel,  # const char physicalChannel[]
    "",  # const char nameToAssignToChannel[]
    PyDAQmx.DAQmx_Val_Cfg_Default,  # int32 terminalConfig
    0.0,  # float64 minVal
    5.0,  # float64 maxVal
    PyDAQmx.DAQmx_Val_Volts,  # int32 units
    None,  # const char customScaleName[])
)

# Start the task
aitask.StartTask()

try:
    for i in range(10):
        # Read a single sample from the channel
        idata = np.zeros(1, dtype=np.float64)  # Array to store the read value
        samples_read = PyDAQmx.int32()  # the number of samples read

        aitask.ReadAnalogF64(
            1,  # Number of samples to read per channel
            5.0,  # Timeout in seconds
            PyDAQmx.DAQmx_Val_GroupByChannel,  # Fill mode
            idata,  # Array to store the read data
            1,  # Size of the array
            PyDAQmx.byref(samples_read),  # Number of samples actually read
            None,  # Reserved
        )

        print(f"Analog input value: {idata[0]:.3f} V")

        # Pause for a short time
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Stopping the task...")

# Stop and clear the task
aitask.StopTask()
aitask.ClearTask()
