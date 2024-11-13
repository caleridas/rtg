import time
import numpy as np
import matplotlib.pyplot as plt

import time
import numpy as np
import matplotlib.pyplot as plt

def CollectAndPlot(*args):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.ion()
    fig.show()
    fig.canvas.draw()
    series = {}
    while True:
        for fn in args:
            k, val = fn()
            if k not in series:
                series[k]=list()
            series[k].append(val)
        ax.clear()
        lines = [ax.plot(series[k], label=k)[0] for k in series]
        ax.legend(handles=lines)
        fig.canvas.draw()
        time.sleep(1)