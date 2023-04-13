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
 * @file ${example_psychopy_erp_experiment_apex.py} 
 * @brief This example shows how to combine sending triggers to APEX with running a 
 * pre-coded experiment with PsychoPy with the TTL trigger module
 *
 */


'''

import sys
from os.path import join, dirname, realpath
Plugin_dir = dirname(realpath(__file__)) # directory of this file
modules_dir = join(Plugin_dir, '..', '..') # directory with all modules
measurements_dir = join(Plugin_dir, '../../measurements') # directory with all measurements
sys.path.append(modules_dir)
import os
from apex_sdk.tmsi_sdk import TMSiSDK, DeviceType, DeviceInterfaceType, DeviceState
from apex_sdk.tmsi_errors.error import TMSiError, TMSiErrorCode, DeviceErrorLookupTable
import PySide2
from PySide2 import QtWidgets 
from TMSiSDK import tmsi_device
from TMSiSDK.device import DeviceInterfaceType, ChannelType, DeviceState
from TMSiSDK.error import TMSiError, TMSiErrorCode, DeviceErrorLookupTable
from TMSiPlotters.plotters import PlotterFormat
from TMSiPlotters.gui import PlottingGUI
from TMSiFileFormats.file_writer import FileWriter, FileFormat
from TMSiSDK import get_config
from experiment_psychopy import PsychopyExperimentSetup
from TMSiPlugins.external_devices.usb_ttl_device import TTLError
import time
from threading import Thread

try:
    # Execute a device discovery. This returns a list of device-objects for every discovered device.
    TMSiSDK().discover(DeviceType.apex, DeviceInterfaceType.bluetooth)
    dongle = TMSiSDK().get_dongle_list()[0]
    discoveryList = TMSiSDK().get_device_list()

    # Set up device
    if (len(discoveryList) > 0):
        # Get the handle to the paired device.
        for i, dev_i in enumerate(discoveryList):
            if dev_i.get_dongle_serial_number() == dongle.get_serial_number():
                dev_id = i   
        dev = discoveryList[dev_id]
        
        # Open a connection to the APEX-system
        dev.open(dongle_id = dongle.get_id())
        
        # Load the EEG channel set and configuration (in this case for 32 channels)
        print("load EEG config")
        cfg = get_config("APEX_config_EEG32")
        dev.import_configuration(cfg)
        
    
    # Initialize PsychoPy Experiment, for arguments description see class
    print('\n Initializing PsychoPy experiment and TTL module \n')
    print('\n  Please check if red and green LEDs are turned on ... \n')
    # !! NOTE: Available options for the (non)target_value inputs are all EVEN numbers between 2 and 30 for APEX
    experiment = PsychopyExperimentSetup(TMSiDevice="APEX", COM_port = 'COM7', n_trials = 3, target_value = 16, nontarget_value= 2)
    
    # Check if there is already a plotter application in existence
    plotter_app = QtWidgets.QApplication.instance()
    
    # Initialise the plotter application if there is no other plotter application
    if not plotter_app:
        plotter_app = QtWidgets.QApplication(sys.argv)
    
    # Show impedances
    # Define the GUI object and show it
    window = PlottingGUI(plotter_format = PlotterFormat.impedance_viewer,
                          figurename = 'An Impedance Plot', 
                          device = dev, 
                          layout = 'head')
    window.show()

    # Enter the event loop
    plotter_app.exec_()

    
    # Pause for a while to properly close the GUI after completion
    print('\n Wait for a bit while we close the plot... \n')
    time.sleep(1)
    
    # Initialise a file-writer class (Poly5-format) and state its file path
    file_writer = FileWriter(FileFormat.poly5, join(measurements_dir,"Example_PsychoPy_ERP_experiment.poly5"))
    
    
    # # Define the handle to the device
    file_writer.open(dev)
    
    
    # Define the GUI object
    plot_window = PlottingGUI(plotter_format = PlotterFormat.signal_viewer,
                              figurename = 'A RealTimePlot', 
                              device = dev,
                              channel_selection = [4, 5])

    # Define thread to run the experiment
    thread = Thread(target=experiment.runExperiment)
    
    # Open the plot window, start the PsychoPy thread and show the signals
    plot_window.show()
    thread.start()
    plotter_app.exec_()
    
    
    # Quit and delete the Plotter application
    QtWidgets.QApplication.quit()
    # Delete the Plotter application
    del plotter_app

    # Close the file writer after GUI termination
    file_writer.close()
    
    # Close the connection to APEX
    dev.close()
        

except TMSiError as e:
    print(e)

except TTLError as e:
   raise TTLError("Is the TTL module connected? Please try again")

        
finally:
    # Close the connection to the device when the device is opened
    if dev.get_device_state().value == DeviceState.connected.value:
        dev.close()