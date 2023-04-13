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
 * @file ${example_envelope_plot.py} 
 * @brief This example shows how to display the envelope plot of a bipolar channel.
 */


'''

import sys
from os.path import join, dirname, realpath
Example_dir = dirname(realpath(__file__)) # directory of this file
modules_dir = join(Example_dir, '..') # directory with all modules
measurements_dir = join(Example_dir, '../measurements') # directory with all measurements
sys.path.append(modules_dir)

from PySide2 import QtWidgets

from TMSiSDK import tmsi_device
from TMSiPlotters.gui import PlottingGUI
from TMSiPlotters.plotters import PlotterFormat
from TMSiSDK.device import DeviceInterfaceType, ChannelType, DeviceState
from TMSiFileFormats.file_writer import FileWriter, FileFormat
from TMSiSDK.error import TMSiError, TMSiErrorCode, DeviceErrorLookupTable
from TMSiProcessing import filters


try:
    # Initialise the TMSi-SDK first before starting using it
    tmsi_device.initialize()
    
    # Execute a device discovery. This returns a list of device-objects for every discovered device.
    discoveryList = tmsi_device.discover(tmsi_device.DeviceType.saga, DeviceInterfaceType.docked, 
                                         DeviceInterfaceType.usb)

    if (len(discoveryList) > 0):
        # Get the handle to the first discovered device.
        dev = discoveryList[0]
        
        # Open a connection to the SAGA-system
        dev.open()
        
        # Set the sample rate of the BIP channel to 4000 Hz
        dev.config.base_sample_rate = 4000
        dev.config.set_sample_rate(ChannelType.BIP, 1)
        
        # Enable BIP 01
        BIP_list = [0]
        
        # Retrieve all channels from the device and update which should be enabled
        ch_list = dev.config.channels
        
        # The counters are used to keep track of the number of BIP channels 
        # that have been encountered while looping over the channel list
        BIP_count = 0
        for idx, ch in enumerate(ch_list):
            if (ch.type == ChannelType.BIP):
                if BIP_count in BIP_list:
                    ch.enabled = True
                else:
                    ch.enabled = False
                BIP_count += 1
            else :
                ch.enabled = False
        dev.config.channels = ch_list
        
        # Update sensor information
        dev.update_sensors()
        
        # Initialise a file-writer class (Poly5-format) and state its file path
        file_writer = FileWriter(FileFormat.poly5, join(measurements_dir,"Example_envelope_plot.poly5"))
        
        # Initialise filter variables for the envelope
        # Initialise BandPass filter variables
        BPF_lowfc = 10      # Lower bound
        BPF_highfc = 500    # Upper bound
        
        # Initialise LowPass filter variable
        LPF_fc = 10
        
        # Define the handle to the device
        file_writer.open(dev)
        
        # Check if there is already a plotter application in existence
        plotter_app = QtWidgets.QApplication.instance()
        
        # Initialise the plotter application if there is no other plotter application
        if not plotter_app:
            plotter_app = QtWidgets.QApplication(sys.argv)
        
        # Define the GUI object and show it
        plot_window = PlottingGUI(plotter_format = PlotterFormat.envelope,
                                  figurename = 'A RealTime Envelope plot', 
                                  device = dev,
                                   BPF_fc1 = BPF_lowfc,
                                   BPF_fc2 = BPF_highfc,
                                   LPF_fc = LPF_fc)
        plot_window.show()
        
        # Enter the event loop
        plotter_app.exec_()
        
        # Quit and delete the Plotter application
        QtWidgets.QApplication.quit()
        del plotter_app
        
        # Close the file writer after GUI termination
        file_writer.close()
        
        # Close the connection to the SAGA device
        dev.close()
    
except TMSiError as e:
    print("!!! TMSiError !!! : ", e.code)
    if (e.code == TMSiErrorCode.device_error) :
        print("  => device error : ", hex(dev.status.error))
        DeviceErrorLookupTable(hex(dev.status.error))
        
finally:
    # Close the connection to the device when the device is opened
    if dev.status.state == DeviceState.connected:
        dev.close()
