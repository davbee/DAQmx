import time

import numpy as np
import PyDAQmx
from PyDAQmx import Task


def ao():
    # Create an analog output task
    task = Task()

    # Define the analog output channel
    aochannel = "Dev1/ao0"

    # Create an analog output voltage channel
    # https://documentation.help/NI-DAQmx-C-Functions/DAQmxCreateAOVoltageChan.html
    task.CreateAOVoltageChan(
        aochannel,  # const char physicalChannel[]
        "",  # const char nameToAssignToChannel[]
        0.0,  # float64 minVal
        5.0,  # float64 maxVal
        PyDAQmx.DAQmx_Val_Volts,  # int32 units
        None,  # const char customScaleName[]
    )

    # Start the analog output task
    task.StartTask()

    return task


def ai():
    # Create an analog input task
    task = Task()

    # Define the analog input channel
    aichannel = "Dev1/ai0"

    # Create an analog input voltage channel
    # https://documentation.help/NI-DAQmx-C-Functions/DAQmxCreateAIVoltageChan.html
    task.CreateAIVoltageChan(
        aichannel,  # const char physicalChannel[]
        "",  # const char nameToAssignToChannel[]
        PyDAQmx.DAQmx_Val_Cfg_Default,  # int32 terminalConfig
        0.0,  # float64 minVal
        5.0,  # float64 maxVal
        PyDAQmx.DAQmx_Val_Volts,  # int32 units
        None,  # const char customScaleName[])
    )

    # Start the task
    task.StartTask()

    return task


def aiao():
    # Instantiate analog output task
    aotask = ao()

    # create output points
    ao1 = np.linspace(0.0, 5.0, num=11)
    ao2 = np.linspace(4.5, 0.0, num=10)
    aopoints = np.append(ao1, ao2)

    # Instantiate analog input task
    aitask = ai()

    # create read buffers
    idata = np.zeros(1, dtype=np.float64)  # Array to store the read value
    samples_read = PyDAQmx.int32()  # the number of samples read

    for i in aopoints:
        # Define the output voltage
        output_voltage = i

        # Write the voltage to the channel
        odata = np.array([output_voltage], dtype=np.float64)

        # Writes multiple floating-point samples to a task that
        # contains one or more analog output channels
        # https://documentation.help/NI-DAQmx-C-Functions/DAQmxWriteAnalogF64.html
        aotask.WriteAnalogF64(
            1,  # int32 numSampsPerChan
            1,  # bool32 autoStart
            5.0,  # float64 timeout
            PyDAQmx.DAQmx_Val_GroupByChannel,  # bool32 dataLayout
            odata,  # float64 writeArray[]
            None,  # int32 *sampsPerChanWritten
            None,  # bool32 *reserved
        )

        print(f"Analog output set to {output_voltage:.3f} V")

        aitask.ReadAnalogF64(
            1,  # Number of samples to read per channel
            5.0,  # Timeout in seconds
            PyDAQmx.DAQmx_Val_GroupByChannel,  # Fill mode
            idata,  # Array to store the read data
            1,  # Size of the array
            PyDAQmx.byref(samples_read),  # Number of samples actually read
            None,  # Reserved
        )

        print(f"Analog input measurement: {idata[0]:.3f} V")

        # pause time
        time.sleep(0.1)

    # Stop and clear the AO tasks
    aotask.StopTask()
    aotask.ClearTask()
    # Stop and clear the AI tasks
    aitask.StopTask()
    aitask.ClearTask()


if __name__ == "__main__":
    # analog output and input read
    aiao()
