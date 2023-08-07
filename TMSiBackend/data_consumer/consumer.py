import queue

from TMSiSDK.sample_data_server import SampleDataServer
from TMSiSDK.tmsi_errors.error import TMSiError, TMSiErrorCode

class Consumer:
    def __init__(self):
        self.reading_queue = queue.Queue(1000)
        self.consumer_thread = None
        
    def close(self):
        if self.consumer_thread is not None:
            self.consumer_thread.stop_sampling()
            self.consumer_thread.join()
            
        SampleDataServer().unregister_consumer(self.reading_queue_id, self)
    
    def open(self, server, reading_queue_id, consumer_thread):
        self.server = server
        self.reading_queue_id = reading_queue_id
        try:
            SampleDataServer().register_consumer(self.reading_queue_id, self)
            self.consumer_thread = consumer_thread
            self.consumer_thread.start()
        except OSError as e:
            raise TMSiError(TMSiErrorCode.file_writer_error)
        except Exception as e:
            raise TMSiError(TMSiErrorCode.file_writer_error)
        
    def put(self, sample_data):
        try:
            self.reading_queue.put(sample_data)
        except:
            raise TMSiError(TMSiErrorCode.file_writer_error)