import time

from PySide2.QtCore import QObject, QThread, Signal, Slot

class Monitor:
    def __init__(self, monitor_function, callback, on_error, pause = 0.1):
        self.callback = callback
        self.on_error = on_error
        self.monitor_function = monitor_function
        self.pause = pause

    def start(self):
        self.monitor_thread = MonitorThread(monitor = self)
        self.monitor_thread.start()

    def stop(self):
        self.monitor_thread.is_active = False

class MonitorThread:
    def __init__(self, monitor):
        self.monitor = monitor
        self.callback = monitor.callback
        self.on_error = monitor.on_error
        self.monitor_function = monitor.monitor_function
        self.pause = monitor.pause

        self.thread = QThread()
        self.worker = MonitorAction(monitor_thread = self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.monitor_loop)

    def start(self):
        self.is_active = True
        self.thread.start()

class MonitorAction(QObject):
    output = Signal(object)
    error_output = Signal(object)

    def __init__(self, monitor_thread):
        super().__init__()
        self.monitor_thread = monitor_thread
        self.output.connect(monitor_thread.callback)
        self.error_output.connect(monitor_thread.on_error)
        self.monitor_function = monitor_thread.monitor_function
        self.pause = monitor_thread.pause

    @Slot()
    def monitor_loop(self):
        while self.monitor_thread.is_active:
            try:
                self.output.emit(self.monitor_function())
            except Exception as e:
                error_message = dict()
                error_message["exception"] = e
                self.error_output.emit(error_message)
            time.sleep(self.pause)
        self.stop()

    def stop(self):
        self.monitor_thread.thread.quit()