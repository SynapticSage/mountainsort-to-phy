# ----------------------------------------------
# Spikeinterface : Mountainsort curation via Phy
# ----------------------------------------------
import json, os, tqdm
import spikeinterface.core.waveform_extractor as wave_extract
import spikeinterface.exporters.to_phy as phy
import spikeinterface.extractors.mdaextractors as mda_extract

# -------------
# Configuration
# -------------
config = {}
config['filtered']        = True # Use filt.mda instead of raw.mda?
config['toleratemissing'] = True # Throw an error for missing tetrodes? Or just skip...
config['skipproc']        = True # Skip already processed folders?

# Directory to look for tetrodes to send into Phy
config['parent_path'] = '/Volumes/GenuDrive/RY16_direct/MountainSort/RY16_36.mountain/'
config['remote_path'] = 'citadel:/volume1/data/Projects/RY16_experiment/RY16_direct/MountainSort/RY16_36.mountain/'

# TODO
#from localremote import Rsync
#rsync = Rsync(path_local=config['parent_path'],
#              path_remote=config['remote_path'],
#              dry_run=True)

# Store some data from the error
error = {}
error['missing'] = []
error['incompletemda'] = []

for folder in tqdm.tqdm(os.listdir(config['parent_path']),
                        desc="Process mountainsort folders"):

    # Set the full path to the tetrdode folder
    local_path = os.path.join(config['parent_path'], folder)

    # The files that we may be using ...
    phyplace    = local_path + os.path.sep + "phy"
    prv_file    = local_path + os.path.sep + 'raw.mda.prv'
    filt_file   = local_path + os.path.sep + 'filt.mda'
    params_file = local_path + os.path.sep + 'params.json'
    firings_file = local_path + os.path.sep + 'firings_raw.mda'
    curated_firings_file = local_path + os.path.sep + 'firings_raw.mda'

    # If skipproc and a phy foler already created, skip this folder
    if config['skipproc'] and os.path.exists(os.path.join(phyplace, 'params.py')):
        continue
    if not os.path.isdir(local_path):
        continue

    print("Processing " + local_path)

    # Derive the properties of the prv
    with open(params_file, 'r') as F:
        params_dict = json.load(F)

    # Create the mda object
    if config['filtered']:
        if config['toleratemissing'] and not os.path.exists(filt_file):
            print(f"Warning {local_path} has no filt.mda")
            error['missing'].append(filt_file)
            continue

        not_complete = True
        geom_empty   = False
        print("Extracting MDA")
        while not_complete and not geom_empty:

            try:
                mda = mda_extract.read_mda_recording(local_path,
                                                         raw_fname=filt_file)
                not_complete = False

            # When an assertion error occurs, it's usually due to the geom.csv
            # having more coordinates than there are channels in the *.mda. So
            # we remove a line from the file (remove a coordinate) until the
            # coordinate count matches. Janky, but it works.
            except AssertionError:
                geom_file = os.path.join(local_path, 'geom.csv')
                with open(geom_file, 'r') as F:
                    lines = F.readlines()
                    lines = lines[:len(lines)-1]
                    if len(lines) == 0:
                        print("geom_file is empty!")
                        geom_empty = True
                        continue
                with open(geom_file, 'w') as F:
                    F.writelines(lines)

        # If the geom file is empty, because it never converges to
        # the proper number of channels, continue to the next tetrode
        if geom_empty:
            continue

        # If we're using filt.mda, the file is already filtered
        mda.annotate(is_filtered=True)

    else:
        with open(prv_file, 'r') as F:
            json_dict = json.load(F)
        original_path = json_dict['original_path']
        mda = mda_extract.read_mda_recording(local_path,
                                                 raw_fname=original_path)

    # ----------------------------------------------
    # Derive a file pointing to filtered spikes file
    # ----------------------------------------------
    print("Getting spikes file")
    samprate = params_dict['samplerate']
    spikes = (
        mda_extract.read_mda_sorting(firings_file,
                                     sampling_frequency=samprate))

    # Remove any folders and files that will hamper this process
    print("Processing waveform")
    waveform_file = local_path + os.path.sep + 'waveform' + os.path.sep + "PCA"
    if os.path.exists(waveform_file):
        [os.remove(os.path.join(waveform_file, f)) for f in
         os.listdir(waveform_file)]
        os.rmdir(waveform_file)
    waveform_file = local_path + os.path.sep + 'waveform' + os.path.sep + "waveforms"
    if os.path.exists(waveform_file):
        [os.remove(os.path.join(waveform_file, f)) for f in
         os.listdir(waveform_file)]
        os.rmdir(waveform_file)
    waveform_file = local_path + os.path.sep + 'waveform'
    if os.path.exists(waveform_file):
        [os.remove(os.path.join(waveform_file, f)) for f in
         os.listdir(waveform_file)]
        os.rmdir(waveform_file)

    # ----------------------
    # Extract spike waveform
    # ----------------------
    try:
        waveform = wave_extract.extract_waveforms(mda,
                                                  spikes,
                                                  waveform_file,
                                                  max_spikes_per_unit=None,
                                                  ms_before=3., 
                                                  ms_after=4.,
                                                  return_scaled=False, 
                                                  n_jobs=10,
                                                  total_memory='50M',
                                                  progress_bar=True)
    except ValueError:
        error['incompletemda'] = (mda, spikes, waveform_file)

    # ----------------------------------
    # Perform the actual export process
    # ----------------------------------
    print("Processing phy")
    phyplace = local_path + os.path.sep + "phy"
    if os.path.exists(phyplace):
        [os.remove(os.path.join(phyplace, f)) for f in os.listdir(phyplace)]
        os.rmdir(phyplace)
    phyfiles = phy.export_to_phy(waveform, phyplace)
