import matplotlib.pyplot as plt
import numpy
import PyDAQmx

analog_input = PyDAQmx.Task()
read = PyDAQmx.int32()
data = numpy.zeros((1000,), dtype=numpy.float64)

# DAQmx Configure Code
analog_input.CreateAIVoltageChan(
    "Dev1/ai0",
    "",
    PyDAQmx.DAQmx_Val_Cfg_Default,
    0.0,
    5.0,
    PyDAQmx.DAQmx_Val_Volts,
    None,
)
analog_input.CfgSampClkTiming(
    "",
    10000.0,
    PyDAQmx.DAQmx_Val_Rising,
    PyDAQmx.DAQmx_Val_FiniteSamps,
    1000,
)

# DAQmx Start Code
analog_input.StartTask()

# DAQmx Read Code
analog_input.ReadAnalogF64(
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
