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
 * @file ${example_stream_lsl.py} 
 * @brief This example shows the functionality to stream to LSL.
 *
 */


'''

import sys

from os.path import join, dirname, realpath
Example_dir = dirname(realpath(__file__)) # directory of this file
modules_dir = join(Example_dir, '..') # directory with all modules
measurements_dir = join(Example_dir, '../measurements') # directory with all measurements
sys.path.append(modules_dir)

from apex_sdk.tmsi_sdk import TMSiSDK, DeviceType, DeviceInterfaceType, DeviceState
from apex_sdk.tmsi_errors.error import TMSiError, TMSiErrorCode, DeviceErrorLookupTable
from TMSiFileFormats.file_writer import FileWriter, FileFormat
from PySide2 import QtWidgets
from TMSiPlotters.gui import PlottingGUI
from TMSiPlotters.plotters import PlotterFormat


try:
    # Execute a device discovery. This returns a list of device-objects for every discovered device.
    TMSiSDK().discover(DeviceType.apex, DeviceInterfaceType.usb)
    discoveryList = TMSiSDK().get_device_list()

    if (len(discoveryList) > 0):
        # Get the handle to the first discovered device.
        dev = discoveryList[0]
        
        # Open a connection to the device
        dev.open()
        
        # Check if there is already a plotter application in existence
        plotter_app = QtWidgets.QApplication.instance()
        
        # Initialise the plotter application if there is no other plotter application
        if not plotter_app:
            plotter_app = QtWidgets.QApplication(sys.argv)
        
        # Initialise the lsl-stream
        stream = FileWriter(FileFormat.lsl, "APEX")
        
        # Pass the device information to the LSL stream.
        stream.open(dev)
 
        # Define the GUI object and show it 
        # The channel selection argument states which channels need to be displayed initially by the GUI
        plot_window = PlottingGUI(plotter_format = PlotterFormat.signal_viewer,
                                  figurename = 'A RealTimePlot', 
                                  device = dev, 
                                  channel_selection = [0,1,2])
        plot_window.show()
        
        # Enter the event loop
        plotter_app.exec_()
        
        # Quit and delete the Plotter application
        QtWidgets.QApplication.quit()
        del plotter_app
       
        # Close the LSL stream after GUI termination
        stream.close()
        
        # Close the connection to the device
        dev.close()
    
except TMSiError as e:
    print(e)
        
finally:
    # Close the connection to the device when the device is opened
    if dev.get_device_state() == DeviceState.connected:
        dev.close()