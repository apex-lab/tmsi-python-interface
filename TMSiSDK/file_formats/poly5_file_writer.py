'''
Copyright 2021 Twente Medical Systems international B.V., Oldenzaal The Netherlands

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

#######  #     #   #####   #  ######      #     #
   #     ##   ##  #        #  #     #     #     #
   #     # # # #  #        #  #     #     #     #
   #     #  #  #   #####   #  ######       #   #
   #     #     #        #  #  #     #      #   #
   #     #     #        #  #  #     #       # #
   #     #     #  #####    #  ######   #     #     #

TMSiSDK: Poly5 File Writer

@version: 2021-06-07

'''
import sys

from datetime import datetime

import os
import threading
import queue
import struct
import time

from ..error import TMSiError, TMSiErrorCode
from .. import sample_data
from .. import sample_data_server

_QUEUE_SIZE = 1000

class Poly5Writer:
    def __init__(self, filename):
        self.q_sample_sets = queue.Queue(_QUEUE_SIZE)
        self.device = None
       
        now = datetime.now()
        filetime = now.strftime("%Y%m%d_%H%M%S")
        fileparts=filename.split('.')
        if fileparts[-1]=='poly5' or fileparts[-1]=='Poly5':
            self.filename='.'.join(fileparts[:-1])+ '-' + filetime + '.poly5'
        else:
            self.filename = filename + '-' + filetime + '.poly5'
        self._fp = None
        self._date = None

    def open(self, device):
        print("Poly5Writer-open")
        self.device = device
        try:
            self._fp = open(self.filename, 'wb')
            self._date = datetime.now()
            self._sample_rate = device.config.sample_rate
            self._num_channels = len(device.channels)

            # Calculate nr of sample-sets within one sample-data-block:
            # This is the nr of sample-sets in 150 milli-seconds or when the
            # sample-data-block-size exceeds 64kb the it will become the nr of
            # sample-sets that fit in 64kb
            self._num_sample_sets_per_sample_data_block = int(self._sample_rate * 0.15)
            size_one_sample_set = len(self.device.channels) * 4
            if ((self._num_sample_sets_per_sample_data_block * size_one_sample_set) > 64000):
                self._num_sample_sets_per_sample_data_block = int(64000 / size_one_sample_set)
            #print('num_sample_sets_per_sample_data_block : {0}'.format(self._num_sample_sets_per_sample_data_block))

            # Write poly5-header for thsi measurement
            Poly5Writer._writeHeader(self._fp, \
                                     "measurement", \
                                     device.config.sample_rate,\
                                     len(device.channels),\
                                     len(device.channels),\
                                     0,
                                     0,
                                     self._date)
            for (i, channel) in enumerate(self.device.channels):
                Poly5Writer._writeSignalDescription(self._fp, i, channel.name, channel.unit_name)

            sample_data_server.registerConsumer(self.device.id, self.q_sample_sets)

            self._sampling_thread = ConsumerThread(self, name='poly5-writer : dev-id-' + str(self.device.id))
            self._sampling_thread.start()
        except OSError as e:
            print(e)
            raise TMSiError(TMSiErrorCode.file_writer_error)
        except:
            raise TMSiError(TMSiErrorCode.file_writer_error)

    def close(self):
        print("Poly5Writer-close")
        self._sampling_thread.stop_sampling()
        
        sample_data_server.unregisterConsumer(self.q_sample_sets)

    ## Write header of a poly5 file.
    #
    # This function writes the header of a poly5 file to a file.
    # @param f File object
    # @param name Name of measurement
    # @param numSignals Number of signals
    # @param numSamples Number of samples
    # @param numDataBlocks Number of data blocks
    # @param date Date of measurement
    @staticmethod
    def _writeHeader(f, name, sample_rate, num_signals, num_samples, num_data_blocks, num_sample_sets_per_sample_data_block, date):

        data = struct.pack("=31sH81phhBHi4xHHHHHHHiHHH64x",
            b"POLY SAMPLE FILEversion 2.03\r\n\x1a",
            203,
            bytes(name, 'ascii'),
            int(sample_rate),
            int(sample_rate),
            0,
            num_signals * 2,
            num_samples,
            date.year,
            date.month,
            date.day,
            date.isoweekday() % 7,
            date.hour,
            date.minute,
            date.second,
            num_data_blocks,
            num_sample_sets_per_sample_data_block,
            num_signals * 2 * num_sample_sets_per_sample_data_block * 2,
            0
        )
        f.write(data)

    ## Write a signal description
    #
    # @param f File object
    # @param index Index of the signal description
    # @param name Name of the signal (channel)
    # @param unitname The unit name of the signal
    @staticmethod
    def _writeSignalDescription(f, index, name, unit_name):
        data = struct.pack("=41p4x11pffffH62x",
            bytes("(Lo) " + name, 'ascii'),
            bytes(unit_name, 'utf-8'),
            0.0, 1000.0, 0.0, 1000.0,
            index
        )
        f.write(data)

        data = struct.pack("=41p4x11pffffH62x",
            bytes("(Hi) " + name, 'ascii'),
            bytes(unit_name, 'utf-8'),
            0.0, 1000.0, 0.0, 1000.0,
            index
        )
        f.write(data)

    ## Write a signal block
    #
    # @param f File object
    # @param index Index of the data block
    # @param date Date of the sample_data block (measurement)
    # @param signals A list of sample_data, containing NumPy arrays
    @staticmethod
    def _writeSignalBlock(f, index, date, sample_sets_block, num_sample_sets_per_sample_data_block):
        data = struct.pack("=i4xHHHHHHH64x",
            int(index * num_sample_sets_per_sample_data_block),
            date.year,
            date.month,
            date.day,
            date.isoweekday() % 7,
            date.hour,
            date.minute,
            date.second
        )
        f.write(data)

        for i in range(num_sample_sets_per_sample_data_block):
            for j in range(sample_sets_block[i].num_samples):
                f.write(struct.pack("f", sample_sets_block[i].samples[j]))

class ConsumerThread(threading.Thread):
    def __init__(self, file_writer, name):
        super(ConsumerThread,self).__init__()
        self.name = name
        self.q_sample_sets = file_writer.q_sample_sets
        self.sampling = True;
        self._sample_set_block_index = 0;
        self._date = datetime.now()
        self._fp = file_writer._fp
        self._sample_rate = file_writer._sample_rate
        self._num_channels = file_writer._num_channels
        self._num_sample_sets_per_sample_data_block = file_writer._num_sample_sets_per_sample_data_block
        self._sample_sets_in_block = []

    def run(self):
        print(self.name, " started")
        while ((self.sampling) or (not self.q_sample_sets.empty())) :
            while not self.q_sample_sets.empty():
                sd = self.q_sample_sets.get()
                self.q_sample_sets.task_done()

                try:
                    for i in range(sd.num_sample_sets):
                        sample_set = sample_data.SampleSet(sd.num_samples_per_sample_set, sd.samples[i*sd.num_samples_per_sample_set:(i+1)*sd.num_samples_per_sample_set])
                        self._sample_sets_in_block.append(sample_set)
                        if (len(self._sample_sets_in_block) >= self._num_sample_sets_per_sample_data_block):
                            Poly5Writer._writeSignalBlock(self._fp,\
                                                          self._sample_set_block_index,\
                                                          self._date,\
                                                          self._sample_sets_in_block,\
                                                          self._num_sample_sets_per_sample_data_block)
                            self._sample_set_block_index += 1
                            self._sample_sets_in_block = []

                            # Go back to start and rewrite header
                            self._fp.seek(0)
                            Poly5Writer._writeHeader(self._fp,\
                                                     "measurement",\
                                                     self._sample_rate,\
                                                     self._num_channels,\
                                                     self._sample_set_block_index * self._num_sample_sets_per_sample_data_block,\
                                                     self._sample_set_block_index,\
                                                     self._num_sample_sets_per_sample_data_block,\
                                                     self._date)

                            # Flush all data from buffers to the file
                            self._fp.flush()
                            os.fsync(self._fp.fileno())

                            # Go back to end of file
                            self._fp.seek(0, os.SEEK_END)
                except OSError as e:
                    print(e)
                    raise TMSiError(TMSiErrorCode.file_writer_error)
                except:
                    raise TMSiError(TMSiErrorCode.file_writer_error)

            time.sleep(0.01)

        print(self.name, " ready, closing file")
        self._fp.close()
        return

    def stop_sampling(self):
        print(self.name, " stop sampling")
        self.sampling = False;