'''
(c) 2022, 2023 Twente Medical Systems International B.V., Oldenzaal The Netherlands

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
 * @file ${example_filter_and_plot.py} 
 * @brief This example shows how to use a filtered plotter.The application 
 * of a bandpass filter is demonstrated. 
 * The filter is only applied to the plotter, the saved data does not contain 
 * any filtered data.
 *
 */


'''

from PySide2.QtWidgets import *
import sys
from os.path import join, dirname, realpath
Example_dir = dirname(realpath(__file__)) # directory of this file
modules_dir = join(Example_dir, '..') # directory with all modules
measurements_dir = join(Example_dir, '../measurements') # directory with all measurements
sys.path.append(modules_dir)

from TMSiSDK.tmsi_sdk import TMSiSDK, DeviceType, DeviceInterfaceType, DeviceState
from TMSiSDK.tmsi_errors.error import TMSiError, TMSiErrorCode, DeviceErrorLookupTable

from TMSiFileFormats.file_writer import FileWriter, FileFormat
from TMSiGui.gui import Gui
from TMSiPlotterHelpers.filtered_signal_plotter_helper import FilteredSignalPlotterHelper


try:
    # Execute a device discovery. This returns a list of device-objects for every discovered device.
    TMSiSDK().discover(DeviceType.apex, DeviceInterfaceType.usb)
    discoveryList = TMSiSDK().get_device_list(DeviceType.apex)

    if (len(discoveryList) > 0):
        # Get the handle to the first discovered device.
        dev = discoveryList[0]
        
        # Open a connection to APEX
        dev.open()
        
        # Initialise a file-writer class (Poly5-format) and state its file path
        file_writer = FileWriter(FileFormat.poly5, join(measurements_dir,"example_filter_and_plot.poly5"))
        
        # Define the handle to the device
        file_writer.open(dev)
        
        # Initialise the plotter application
        app = QApplication(sys.argv)
        # Initialise filtered plotter helper
        plotter_helper = FilteredSignalPlotterHelper(device=dev, hpf=1, lpf=100, order=1)
        gui = Gui(plotter_helper = plotter_helper)
        app.exec_()
        
        # Close the file writer after GUI termination
        file_writer.close()
        
        # Close the connection to the device
        dev.close()
    
except TMSiError as e:
    print(e)
        
finally:
    if 'dev' in locals():
        # Close the connection to the device when the device is opened
        if dev.get_device_state() == DeviceState.connected:
            dev.close()