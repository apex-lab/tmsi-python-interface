'''
(c) 2022 Twente Medical Systems International B.V., Oldenzaal The Netherlands

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
 * @brief This example shows how to couple an additional signal processing 
 * object to the plotter. The application of a bandpass filter is demonstrated. 
 * The filter is only applied to the plotter, the saved data does not contain 
 * any filtered data.
 *
 */


'''

import sys
from os.path import join, dirname, realpath
Example_dir = dirname(realpath(__file__)) # directory of this file
modules_dir = join(Example_dir, '..') # directory with all modules
measurements_dir = join(Example_dir, '../measurements') # directory with all measurements
sys.path.append(modules_dir)

from PySide2 import QtWidgets
from apex_sdk.tmsi_sdk import TMSiSDK, DeviceType, DeviceInterfaceType, DeviceState
from apex_sdk.tmsi_errors.error import TMSiError, TMSiErrorCode, DeviceErrorLookupTable
from TMSiPlotters.gui import PlottingGUI
from TMSiPlotters.plotters import PlotterFormat
from TMSiFileFormats.file_writer import FileWriter, FileFormat
from TMSiProcessing import filters


try:
    # Execute a device discovery. This returns a list of device-objects for every discovered device.
    TMSiSDK().discover(DeviceType.apex, DeviceInterfaceType.usb)
    discoveryList = TMSiSDK().get_device_list()

    if (len(discoveryList) > 0):
        # Get the handle to the first discovered device.
        dev = discoveryList[0]
        
        # Open a connection to APEX
        dev.open()
        
        # Initialise a file-writer class (Poly5-format) and state its file path
        file_writer = FileWriter(FileFormat.poly5, join(measurements_dir,"example_filter_and_plot.poly5"))
        
        # Define the handle to the device
        file_writer.open(dev)
        
        # Initialise filter
        filter_appl = filters.RealTimeFilter(dev)
        filter_appl.generateFilter(Fc_hp = 1, Fc_lp = 100)
        
        # Check if there is already a plotter application in existence
        plotter_app = QtWidgets.QApplication.instance()
        
        # Initialise the plotter application if there is no other plotter application
        if not plotter_app:
            plotter_app = QtWidgets.QApplication(sys.argv)
        
        # Define the GUI object and show it
        plot_window = PlottingGUI(plotter_format = PlotterFormat.signal_viewer,
                                  figurename = 'A RealTimePlot', 
                                  device = dev, 
                                  channel_selection = [0, 1, 2],
                                  filter_app = filter_appl)
        plot_window.show()
        
        # Enter the event loop
        plotter_app.exec_()
        
        # Quit and delete the Plotter application
        QtWidgets.QApplication.quit()
        del plotter_app
        
        # Close the file writer after GUI termination
        file_writer.close()
        
        # Close the connection to the device
        dev.close()
    
except TMSiError as e:
    print(e)
        
finally:
    # Close the connection to the device when the device is opened
    if dev.get_device_state() == DeviceState.connected:
        dev.close()