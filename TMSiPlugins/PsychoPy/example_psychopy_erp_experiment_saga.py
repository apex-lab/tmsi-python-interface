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
 * @file ${example_psychopy_erp_experiment_saga.py} 
 * @brief This example shows how to combine sending triggers to SAGA with running a 
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
import time
from threading import Thread
from TMSiSDK.devices.saga.mask_type import MaskType
from TMSiPlugins.external_devices.usb_ttl_device import TTLError


try:
    # Initialise the TMSi-SDK first before starting using it
    tmsi_device.initialize()
    
    # Create the device object to interface with the SAGA-system.
    discoveryList = tmsi_device.discover(tmsi_device.DeviceType.saga, DeviceInterfaceType.docked, DeviceInterfaceType.usb)
    
    if (len(discoveryList)>0):
        # Get the handle to the first discovered device.
        dev = discoveryList[0]
        
        # Open a connection to the SAGA-system
        dev.open()
        
        # Load the EEG channel set and configuration
        print("load EEG config")
        if dev.config.num_channels<64:
            cfg = get_config("saga_config_EEG32")
        else:
            cfg = get_config("saga_config_EEG64")
        dev.load_config(cfg)
        
          # Set the sample rate of the AUX channels to 4000 Hz
        dev.config.base_sample_rate = 4000
        dev.config.triggers = True
       
        # Downsample
        dev.config.set_sample_rate(ChannelType.UNI, 4)
        dev.config.set_sample_rate(ChannelType.AUX, 4)
        dev.config.set_sample_rate(ChannelType.BIP, 4)
        
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
        
        # Find the trigger channel index number
        for i in range(len(dev.channels)):   
            if dev.channels[i].name == 'TRIGGERS':
                trigger_channel = i

        # Apply mask on trigger channel. This mask is applied because SAGA TRIGGER input has inverse logic. 
        # By applying the mask, the baseline of the triggers is low again
        dev.apply_masks([trigger_channel],[MaskType.REVERSE])
    
    
    # Initialize PsychoPy Experiment, for arguments description see class
    print('\n Initializing PsychoPy experiment and TTL module \n')
    print('\n  Please check if red LED is turned on ... \n')
    # !! NOTE: Available options for the (non)target_value inputs are all numbers between 1 and 255 for SAGA
    experiment = PsychopyExperimentSetup(TMSiDevice="SAGA", COM_port = 'COM7', n_trials = 5, target_value = 128, nontarget_value= 64)



    
    # Initialise a file-writer class (Poly5-format) and state its file path
    file_writer = FileWriter(FileFormat.poly5, join(measurements_dir,"Example_PsychoPy_ERP_experiment.poly5"))
    
    
    # # Define the handle to the device
    file_writer.open(dev)
    
    
    # Define the GUI object
    plot_window = PlottingGUI(plotter_format = PlotterFormat.signal_viewer,
                              figurename = 'A RealTimePlot', 
                              device = dev,
                              channel_selection = [4, 5, trigger_channel])

    # Start measurement & define thread to start experiment
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
    # Close the connection to the SAGA device
    dev.close()
    


except TMSiError as e:
    print("!!! TMSiError !!! : ", e.code)
    if (e.code == TMSiErrorCode.device_error) :
        print("  => device error : ", hex(dev.status.error))
        DeviceErrorLookupTable(hex(dev.status.error))
        
except TTLError:
    raise TTLError("Please try again and check if LEDs blink")
        
finally:
    # Close the connection to the device when the device is opened
    if dev.status.state == DeviceState.connected:
        dev.close()