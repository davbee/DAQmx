"""
This example is a PyDAQmx version of the ContAcq_IntClk.c example
It illustrates the use of callback functions

This example demonstrates how to acquire a continuous amount of
data using the DAQ device's internal clock. It incrementally stores the data
in a Python list.

https://pythonhosted.org/PyDAQmx/callback.html
"""

import PyDAQmx
from numpy import zeros
from PyDAQmx import Task


class CallbackTask(Task):
    def __init__(self):
        Task.__init__(self)
        self.data = zeros(1000)
        self.a = []
        self.CreateAIVoltageChan(
            "Dev1/ai0",
            "",
            PyDAQmx.DAQmx_Val_RSE,
            0.0,
            5.0,
            PyDAQmx.DAQmx_Val_Volts,
            None,
        )
        self.CfgSampClkTiming(
            "",
            10000.0,
            PyDAQmx.DAQmx_Val_Rising,
            PyDAQmx.DAQmx_Val_ContSamps,
            1000
        )
        self.AutoRegisterEveryNSamplesEvent(
            PyDAQmx.DAQmx_Val_Acquired_Into_Buffer,
            1000,
            0
        )
        self.AutoRegisterDoneEvent(0)

    def EveryNCallback(self):
        read = PyDAQmx.int32()
        self.ReadAnalogF64(
            1000,
            10.0,
            PyDAQmx.DAQmx_Val_GroupByScanNumber,
            self.data,
            1000,
            PyDAQmx.byref(read),
            None,
        )
        self.a.extend(self.data.tolist())
        print(self.data[0])  # print only the first data point
        # print(self.data)  # print all data points
        return 0  # The function should return an integer

    def DoneCallback(self, status):
        print("Status", status.value)
        return 0  # The function should return an integer


task = CallbackTask()
task.StartTask()

input('Acquiring samples continuously. Press Enter to interrupt\n')

task.StopTask()
task.ClearTask()
