import matplotlib.pyplot as plt
import numpy as np
import PyDAQmx

# https://pythonhosted.org/PyDAQmx/usage.html
# Declaration of variable passed by reference
taskHandle = PyDAQmx.TaskHandle()
read = PyDAQmx.int32()
data = np.zeros((1000,), dtype=np.float64)

try:
    # DAQmx Configure Code
    PyDAQmx.DAQmxCreateTask("", PyDAQmx.byref(taskHandle))
    PyDAQmx.DAQmxCreateAIVoltageChan(
        taskHandle,
        "Dev1/ai0",
        "",
        PyDAQmx.DAQmx_Val_Cfg_Default,
        0.0,
        5.0,
        PyDAQmx.DAQmx_Val_Volts,
        None,
    )
    PyDAQmx.DAQmxCfgSampClkTiming(
        taskHandle,
        "",
        10000.0,
        PyDAQmx.DAQmx_Val_Rising,
        PyDAQmx.DAQmx_Val_FiniteSamps,
        1000,
    )

    # DAQmx Start Code
    PyDAQmx.DAQmxStartTask(taskHandle)

    # DAQmx Read Code
    PyDAQmx.DAQmxReadAnalogF64(
        taskHandle,
        1000,
        10.0,
        PyDAQmx.DAQmx_Val_GroupByChannel,
        data,
        1000,
        PyDAQmx.byref(read),
        None,
    )

    print(f"Acquired {read.value} points")
    print(data)
    plt.plot(data)
    plt.show()

except PyDAQmx.DAQError as err:
    print(f"DAQmx Error: {err}")

finally:
    if taskHandle:
        # DAQmx Stop Code
        PyDAQmx.DAQmxStopTask(taskHandle)
        PyDAQmx.DAQmxClearTask(taskHandle)
