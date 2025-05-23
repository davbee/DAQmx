# coding= latin-1
import PyDAQmx
from PyDAQmx.DAQmxConstants import *
from PyDAQmx.DAQmxFunctions import *


class ContinuousPulseTrainGeneration:
    """Class to create a continuous pulse train on a counter

    Usage:  pulse = ContinuousTrainGeneration(period [s],
                duty_cycle (default = 0.5), counter (default = "dev1/ctr0"),
                reset = True/False)
            pulse.start()
            pulse.stop()
            pulse.clear()
    """

    def __init__(self, period=1.0, duty_cycle=0.5, counter="Dev1/ctr0", reset=False):
        if reset:
            PyDAQmx.DAQmxResetDevice(counter.split("/")[0])
        taskHandle = TaskHandle(0)
        PyDAQmx.DAQmxCreateTask("", PyDAQmx.byref(taskHandle))
        PyDAQmx.DAQmxCreateCOPulseChanFreq(
            taskHandle,
            counter,
            "",
            PyDAQmx.DAQmx_Val_Hz,
            PyDAQmx.DAQmx_Val_Low,
            0.0,
            1 / float(period),
            duty_cycle,
        )
        PyDAQmx.DAQmxCfgImplicitTiming(taskHandle, PyDAQmx.DAQmx_Val_ContSamps, 1000)
        self.taskHandle = taskHandle

    def start(self):
        PyDAQmx.DAQmxStartTask(self.taskHandle)

    def stop(self):
        PyDAQmx.DAQmxStopTask(self.taskHandle)

    def clear(self):
        PyDAQmx.DAQmxClearTask(self.taskHandle)


if __name__ == "__main__":
    pulse_gene1 = ContinuousPulseTrainGeneration(1.0, 0.5, "dev1/ctr0", reset=True)
    pulse_gene1.start()
    a = input("Generating pulse train. Press Enter to interrupt\n")
    pulse_gene1.stop()
    pulse_gene1.clear()
