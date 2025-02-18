""" Simple example of digital output

    This example outputs the values of data on line 0 to 7
"""

import numpy as np
import PyDAQmx
from PyDAQmx import Task


# [LSB...MSB] = port[0 1 2 3 4 5 6 7]
data = np.array([1, 0, 1, 0, 1, 0, 1, 1], dtype=np.uint8)

task = Task()
task.CreateDOChan("/Dev1/port0/line0:7",
                  "",
                  PyDAQmx.DAQmx_Val_ChanForAllLines)
task.StartTask()
task.WriteDigitalLines(1,
                       1,
                       10.0,
                       PyDAQmx.DAQmx_Val_GroupByChannel,
                       data,
                       None,
                       None)
task.StopTask()
