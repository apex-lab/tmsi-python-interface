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
 * @file ${example_xdf_to_MNE.py} 
 * @brief This example shows how to read data from an edf-file to an MNE-object.
 */


'''

import sys
from os.path import join, dirname, realpath
import mne

ipython = get_ipython()
ipython.magic("matplotlib qt")

Example_dir = dirname(realpath(__file__)) # directory of this file
modules_dir = join(Example_dir, '..') # directory with all modules
measurements_dir = join(Example_dir, '../measurements') # directory with all measurements
sys.path.append(modules_dir)

from TMSiFileFormats.file_readers import Edf_Reader

reader = Edf_Reader(add_ch_locs=True)
# When no filename is given, a pop-up window allows you to select the file you want to read. 
# You can also use reader=EDF_to_MNE(full_path) to load a file. Note that the full file path is required here.
# add_ch_locs can be used to include TMSi EEG channel locations

# Add impedance data from .txt file 
reader.add_impedances()

# mne_object is created in reader
mne_object = reader.mne_object


#%% Basis plotting commands with MNE
mne_object.plot_sensors(ch_type='eeg', show_names=True) 
mne_object.plot(scalings='auto', start=0, duration=5, n_channels=5, title='Edf Plot') 
mne_object.plot_psd(fmin = 1, fmax = 100, picks = 'eeg')