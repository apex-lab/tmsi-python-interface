'''
(c) 2023 Twente Medical Systems International B.V., Oldenzaal The Netherlands

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

#######  #     #   #####   #
   #     ##   ##  #        
   #     # # # #  #        #
   #     #  #  #   #####   #
   #     #     #        #  #
   #     #     #        #  #
   #     #     #  #####    #

/**
 * @file eeg_measurement.py 
 * @brief 
 * Class to handle the communication with the device for  EEG acquisition.
 */


'''

from copy import deepcopy
from ctypes import *
import time

from .....tmsi_utilities.tmsi_logger import TMSiLogger as logger
from .....sample_data_server.sample_data_server import SampleDataServer, TMSiLoggerActivity
from .....sample_data_server.sample_data import SampleData
from .....tmsi_utilities import support_functions
from .....tmsi_utilities.decorators import LogPerformances
from ..apex_API_structures import TMSiDevSampleRequest
from ..apex_API_enums import SampleControl, TMSiDeviceRetVal
from ....tmsi_measurement import TMSiMeasurement

OVERFLOW = 4294967296000000.0

class EEGMeasurement(TMSiMeasurement):
    """Class to handle the EEG measurements."""
    def __init__(self, dev, name = "EEG Measurement"):
        """Initialize the EEG measurement.

        :param dev: Device to measure from.
        :type dev: TMSiDevice
        :param name: name of the measurement, defaults to "EEG Measurement"
        :type name: str, optional
        """
        super().__init__(dev = dev, name = name)
        self._sample_data_buffer = (c_float * self._sample_data_buffer_size)(0)
        self._num_samples_per_set = dev.get_num_channels()
        self._converter = {}
        channels = self._dev.get_device_channels()
        for i in range(self._num_samples_per_set):
            conversion_factor = 10**channels[i].get_channel_exp()
            if conversion_factor in self._converter:
                self._converter[conversion_factor].append(i)
            else:
                self._converter[conversion_factor] = [i]

    @LogPerformances
    def start(self):
        """Start the measurement.
        """
        self._dev.reset_device_data_buffer()
        measurement_request = TMSiDevSampleRequest()
        measurement_request.DisableLiveImp = self._disable_live_impedance
        measurement_request.DisableAvrRefCalc = self._disable_average_reference_calculation
        measurement_request.StartStop = SampleControl.StartSampling.value
        TMSiLoggerActivity().log("{}->>APEX-SDK: set device sampling request ON".format(self.get_name()))
        self._dev.set_device_sampling_request(measurement_request)
        TMSiLoggerActivity().log("{}->>Sampling Thread: start".format(self.get_name()))
        self._sampling_thread.start()
        TMSiLoggerActivity().log("{}->>Conversion Thread: start".format(self.get_name()))
        self._conversion_thread.start()

    @LogPerformances
    def stop(self):
        """Stop the measurement.
        """
        measurement_request = TMSiDevSampleRequest()
        measurement_request.DisableLiveImp = self._disable_live_impedance
        measurement_request.DisableAvrRefCalc = self._disable_average_reference_calculation
        measurement_request.StartStop = SampleControl.StopSampling.value
        TMSiLoggerActivity().log("{}->>APEX-SDK: set device sampling request OFF".format(self.get_name()))
        self._dev.set_device_sampling_request(measurement_request)
        TMSiLoggerActivity().log("{}->>Sampling Thread: stop".format(self.get_name()))
        self._sampling_thread.stop()
        TMSiLoggerActivity().log("{}->>Conversion Thread: stop".format(self.get_name()))
        self._conversion_thread.stop()

    @LogPerformances
    def _conversion_function(self):
        while not self._conversion_queue.empty():
            sample_data_buffer, retrieved_sample_sets = self._conversion_queue.get()
            TMSiLoggerActivity().log("Conversion Queue->>Conversion Thread: GET samples | package size:{} - new size:{}".format(
                    retrieved_sample_sets, self._conversion_queue.qsize()))
            if retrieved_sample_sets > 0:
                sample_mat = support_functions.array_to_matrix(
                    sample_data_buffer[:self._num_samples_per_set*retrieved_sample_sets],
                    self._num_samples_per_set)
                for i in self._float_channels:
                    sample_mat[i] = support_functions.float_to_uint(sample_mat[i])
                for factor in self._converter.keys():
                    for channel in self._converter[factor]:
                        sample_mat[channel] = [i/factor for i in sample_mat[channel]]
                samples = support_functions.matrix_to_multiplexed_array(sample_mat)
                samples = [0.0 if  i == OVERFLOW else i for i in samples]
                sd = SampleData(retrieved_sample_sets, self._num_samples_per_set, samples)
                TMSiLoggerActivity().log("Conversion Thread->>Conversion Thread: convert samples to sample data")
                TMSiLoggerActivity().log("Conversion Thread->>SDS: PUT sample data")
                SampleDataServer().put_sample_data(self._dev.get_id(), sd)
                logger().debug("Data delivered to sample data server: {} channels, {} samples".format(self._num_samples_per_set, retrieved_sample_sets))

    @LogPerformances
    def _sampling_function(self):
        TMSiLoggerActivity().log("Sampling Thread->>APEX-SDK: GET eeg samples request")
        ret = self._dev.get_device_data(
            pointer(self._sample_data_buffer), 
            self._sample_data_buffer_size, 
            pointer(self._retrieved_sample_sets), 
            pointer(self._retrieved_data_type))
        TMSiLoggerActivity().log("APEX-SDK->>Sampling Thread: GET eeg samples response")
        if (ret == TMSiDeviceRetVal.TMSiStatusOK):
            TMSiLoggerActivity().log("Sampling Thread->>Sampling Thread: positive response")
            if self._retrieved_sample_sets.value > 0:
                self._conversion_queue.put((deepcopy(self._sample_data_buffer), self._retrieved_sample_sets.value))
                TMSiLoggerActivity().log("Sampling Thread->>Conversion Queue: PUT samples | package size:{} - new size:{}".format(
                    self._retrieved_sample_sets.value, self._conversion_queue.qsize()))
                self._tic_timeout = time.perf_counter()
                self._empty_read_counter = 0
            else:
                TMSiLoggerActivity().log("Sampling Thread->>Sampling Thread: empty package")
                if self._empty_read_counter == 0:
                    self._empty_read_counter = 1
        else:
            TMSiLoggerActivity().log("APEX-SDK->>Sampling Thread: negative response: {}".format(ret))
        if self._download_samples_limit is not None:
            self._downloaded_samples += self._retrieved_sample_sets.value
            self._download_percentage = self._downloaded_samples * 100.0 / self._download_samples_limit
            TMSiLoggerActivity().log("Sampling Thread->>Sampling Thread: downloaded {} samples of {}".format(self._downloaded_samples, self._download_samples_limit))
    