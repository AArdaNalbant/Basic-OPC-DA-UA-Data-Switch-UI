import time
import OpenOPC
from threading import Timer, Thread, Event
from multiprocessing import Process, Queue, JoinableQueue
from opcua import Client

global bla
import time
import h5py
import numpy as np

global buff
global firstline
global f
global cycles
global xtimes
global timers
global timer_queues
global time_periods
global groups

time_periods = [0.05, 0.1, 0.25, 0.5, 1, 5, 10, 60, 600, 3600]

firstline = []
cycles = []
groups = ["50ms", "100ms", "250ms", "500ms", "1s", "5s", "10s", "1m", "10min", "60min"]


def init_conn():
##  opc = OpenOPC.open_client("***.***.**.**")
##  opc.connect("Matrikon.OPC.Simulation.1")
    client = Client("opc.tcp://127.0.0.1:16664")
    client.connect()
    return client


def init_file():
    loop_cnt = 0
    f = h5py.File("mytestfile2_electric_boogaloo.hdf5", "w")
    dt = h5py.special_dtype(vlen=bytes)
    for times in groups:
##      dset = f.create_group(times, (3,), dtype=dt)
        cycles.append('')
        cycles[loop_cnt] = f.create_group(str(times))
        loop_cnt = loop_cnt + 1
    f.close()


class RepeatingTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        super(RepeatingTimer, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self.function = function
        self.interval = interval
        self.start()

    def start(self):
        self.callback()

    def stop(self):
        self.interval = False

    def callback(self):
        starttim = time.clock()
        if self.interval:
            self.function(*self.args, **self.kwargs)
            Timer(self.interval - (time.clock() - starttim), self.callback, ).start()
            ##print(time.clock())


def readtags(tag_to_read):
    client = tag_to_read[0]
    trywrite = []

    for i in range(len(tag_to_read[1])):
        trywrite.append([])
        for j in range(len(tag_to_read[2])):
            trywrite[i].append(
                str(tag_to_read[2][j].get_browse_name()).split(":")[1][:-1] + ", Value:" +
                str(tag_to_read[2][j].get_value()))

    print(str(tag_to_read[3].get_browse_name()).split(":")[1][:-1])
    print(trywrite[i])
    print("-----•-----")
    print("-----•-----")
    print()


if __name__ == "__main__":

    try:
        client = init_conn()
        init_file()

        obj_node = client.get_objects_node()
        obj_children = obj_node.get_children()
        del obj_children[0]
        all_children_vars = []
        for i in range(len(obj_children)):
            all_children_vars.append([])
            all_children_vars[i] = obj_children[i].get_children()

        ind = 0
        timers = []
        timer_queues = []
        timer_queue = Queue()
        timer_queues.append(timer_queue)
        for i in range(len(obj_children)):
            for j in range(len(obj_children[i].get_children())):
                holdThisTime = int(str(obj_children[i].get_browse_name()).split(":")[1][:-3]) / 1000
                timertest = RepeatingTimer(holdThisTime, readtags,
                                           [client, obj_children, obj_children[i].get_children(), obj_children[i]])

        ##timertest.start()

    finally:
        ##client.disconnect()
        print()
