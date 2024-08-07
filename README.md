# build_rawdata
This package generates BIDS rawdata for Exp2_Compute_Emotion and Exp3_Classify_Archival via the sub-packages [build_emorep](#build_emorep) and [build_nki](#build_nki), respectively. It is written for execution on labarserv2.


## Requirements
The following software suites are required to be installed and executable from the shell.
- [dcm2niix](https://github.com/rordenlab/dcm2niix)
- [AFNI](https://afni.nimh.nih.gov/)
- [NeuroKit2](https://github.com/neuropsychology/NeuroKit)


## Setup and Entrypoint
- Install into project conda environment on labarserv2 (see [here](https://github.com/labarlab/conda_labarserv2)) via `$python setup.py install --record record.txt`
- Trigger package help and usage via entrypoint `$build_rawdata`

```
(emorep)[nmm51-vm: ~]$build_rawdata

Version : 2.4.0

The package build_rawdata consists of sub-packages that can be accessed
from their respective entrypoints:

    build_emorep    : convert sourcedata to rawdata for Exp2_Compute_Emotion
    build_nki       : build rawdata from NKI Rockland Archival data
                        for Exp3_Classify_Archival
```


## Testing
Planned unit and integration tests are available at tests/run_tests.py, and executable via `$cd tests; python run_tests.py`.


## build_emorep
Build BIDS rawdata directory for Exp2_Compute_Emotion using data collected by scanning for the EmoRep project. Orients to, validates, and organizes sourcedata, then builds BIDS-complaint rawdata for each subject and session. Also coordiantes defacing of T1w files for NDAR hosting.


### Setup
`build_emorep` assumes the in-house sourcedata organization for EmoRep:

```bash
ER0009
├── day2_movies
│   ├── DICOM
│   │   └── 20220422.ER0009.ER0009
│   ├── Scanner_behav
│   └── Scanner_physio
└── day3_scenarios
    ├── DICOM
    │   └── 20220430.ER0009.ER0009
    ├── Scanner_behav
    └── Scanner_physio
```
Failure to organize data in this structure, and those below, will not pass validation and result in (a) printed error messages to stdout and (b) skipping rawdata conversion for the offending data.

The subdirectory of **DICOM** (e.g. 20220422.ER0009.ER00009) should contain all DICOMs for one session in a flat structure.

**Scanner_behav** should contain all behavior files gathered from the EmoRep [task](https://github.com/labarlab-emorep/scanner_tasks) with the following organization and naming convention:

```bash
Scanner_behav/
├── emorep_scannermovieData_ER0009_sesday2_run-1_04222022.csv
..
├── emorep_scannermovieData_ER0009_sesday2_run-8_04222022.csv
├── emorep_scannermovieData_sub-ER0009_ses-day2_run-1_04222022.mat
..
└── emorep_scannermovieData_sub-ER0009_ses-day2_run-8_04222022.mat
```

__Note:__ the file name of the CSV was changed partway through the study to have better agreement with the MAT file, e.g. `emorep_scannermovieData_sub-ER0697_ses-day2_run-1_09012023.csv`, both formats are acceptable.

**Scanner_physio** should contain all physio files gathered during the same EmoRep task with the following organization and naming convention:

```bash
Scanner_physio/
├── ER0697_physio_day2_run1.acq
..
└── ER0697_physio_day2_run8.acq
```


### Usage
Trigger this sub-package via the CLI `$build_emorep`, which also supplies a help and description of arguments:

```
(emorep)[nmm51-vm: ~]$build_emorep
usage: build_emorep [-h] [--deface] [--proj-dir PROJ_DIR] [--sub-all] [--sub-list SUB_LIST [SUB_LIST ...]]

Version : 2.4.0

Build BIDS rawdata for EmoRep experiment.

Written for for use on labarserv2.

Referencing data collected at the scanner, build a BIDS-organized
rawdata with NIfTIs, behavioral events, resting-state task response,
and physiological data. Optional defacing is available for NDAR
purposes and is written to derivatives.

Requires in-house EmoRep sourcedata organization.

Examples
--------
build_emorep --deface --sub-all
build_emorep --deface --sub-list ER0009 ER0016

options:
  -h, --help            show this help message and exit
  --deface              Deface anat files via @afni_refacer_run
  --proj-dir PROJ_DIR   Path to BIDS organized parent directory, containing sourcedata
                        and rawdata.
                        (default : /mnt/keoki/experiments2/EmoRep/Exp2_Compute_Emotion/data_scanner_BIDS)
  --sub-all             Build rawdata for all participants in sourcedata
  --sub-list SUB_LIST [SUB_LIST ...]
                        Subject IDs

```

It is possible to build rawdata for all subjects via the `--sub-all` option, or by specifying 1+ subjects via the `--sub-list` option. Using the boolean `--deface` option triggers defacing of the session anatomical file. Finally `--proj-dir` is used to specify the parent directory, containing sourcedata and where rawdata and derivatives will be constructed.


### Functionality
`build_emorep` conducts a series of workflows to generate BIDS-compliant rawdata and defaced derivates using data from sourcedata. The steps are:

1. Setup rawdata and derivatives
1. Organize sourcedata DICOMs
1. Convert DICOMs to NIfTI files via dcm2niix
1. BIDS-organize rawdata NIfTI files
    1. (optional) Deface anatomical NIfTI via `@afni_refacer_run` and write to derivatives/deface
1. Generate BIDS events TSV files from Scanner_behav and organize in func
1. Clean rest rating responses (from Scanner_behav) and organize in beh
1. Copy Scanner_phys ACQ files to phys and also generate TXT format via `NeuroKit2` for autonomate.

Output written to rawdata are organized following the BIDS scheme:

```
rawdata/
└── sub-ER0009
    └── ses-day3
       ├── anat
       │   ├── sub-ER0009_ses-day3_T1w.json
       │   └── sub-ER0009_ses-day3_T1w.nii.gz
       ├── beh
       │   └── sub-ER0009_ses-day3_rest-ratings_2022-04-28.tsv
       ├── fmap
       │   ├── sub-ER0009_ses-day3_acq-rpe_dir-PA_epi.json
       │   └── sub-ER0009_ses-day3_acq-rpe_dir-PA_epi.nii.gz
       ├── func
       │   ├── sub-ER0009_ses-day3_task-movies_run-01_bold.json
       │   ├── sub-ER0009_ses-day3_task-movies_run-01_bold.nii.gz
       │   ├── sub-ER0009_ses-day3_task-movies_run-01_events.json
       │   └── sub-ER0009_ses-day3_task-movies_run-01_events.tsv
       └── phys
           ├── sub-ER0009_ses-day3_task-movies_run-01_recording-biopack_physio.acq
           └── sub-ER0009_ses-day3_task-movies_run-01_recording-biopack_physio.txt
```
Note that participant responses to the rest-rating task are saved to the 'beh' directory (and excluded from validation), and both ACQ and TXT formats are available for physio data.

Conversely, organization of the defaced derivatives does not fully comply to the BIDS scheme:

```
derivatives/deface/
└── sub-ER0009
    ├── ses-day2
    │   └── sub-ER0009_ses-day2_T1w_defaced.nii.gz
    └── ses-day3
        └── sub-ER0009_ses-day3_T1w_defaced.nii.gz
```

Also, see [Diagrams](#diagrams).


### Considerations
- fmap JSON files are updated with the `IntendedFor` field. If multiple fmap files are found then the default is to use fmap1 for EPI runs 1-4 and fmap2 for runs 5-8 + rest. If this is not appropriate then the researcher can specify the exact mapping in `build_rawdata.reference_files.unique_fmap.json`.


## build_nki
Build BIDS rawdata for Exp3_Classify_Archival (archival). This will download archival data from the [Nathan Kline Institute](http://fcon_1000.projects.nitrc.org/indi/enhanced/index.html) archival dataset and BIDS-organize certain files for resting-state analyses.


### Setup
`build_nki` requires resources detailed [here](http://fcon_1000.projects.nitrc.org/indi/enhanced/neurodata.html), organized according to the following structure and naming scheme:

```bash
nki_resources/
├── aws_links.csv
└── download_rockland_raw_bids_ver2.py
```

This nki_resources directory can be found at experiments2/EmoRep/Exp3_Classify_Archival/code/nki_resources.


### Usage
Trigger help and usage of this sub-package via the CLI `$build_nki`:

```
(emorep)[nmm51-vm: nki_resources]$build_nki
usage: build_nki [-h] [--age AGE] [--dryrun] [--hand {L,R}] [--nki-dir NKI_DIR] [--proj-dir PROJ_DIR]
                 [--protocol {REST645,REST1400,RESTCAP,RESTPCASL}] [--session {BAS1,BAS2,BAS3}] -t {anat,func,dwi}
                 [{anat,func,dwi} ...]

Version : 2.4.0

Download NKI Rockland Archival Data.

Download anatomical and resting-state EPI data from the
NKI Rockland Archive and setup a BIDS-organized rawdata
directory.

Essentially a project-specific wrapper for methods detailed at:
    http://fcon_1000.projects.nitrc.org/indi/enhanced/neurodata.html

The EmoRep project employed the method used in the first example,
and additional options are supplied for 'future-proofing'.

Examples
--------
build_nki -t anat func
build_nki -t anat func --hand R --dryrun
build_nki -t anat func --age 80 --dryrun
build_nki -t anat func --protocol REST645 --session BAS3 --dryrun

options:
  -h, --help            show this help message and exit
  --age AGE             Threshold age, will pull data for participants
                        of older (>) than specified age.
                        (default : 17)
  --dryrun              Test download parameters
  --hand {L,R}          Handedness of participants, unspecified pulls both
  --nki-dir NKI_DIR     Path to parent directory containing download script and AWS links
                        (default : /mnt/keoki/experiments2/EmoRep/Exp3_Classify_Archival/code/nki_resources)
  --proj-dir PROJ_DIR   Path to parent directory of archival study
                        (default : /mnt/keoki/experiments2/EmoRep/Exp3_Classify_Archival)
  --protocol {REST645,REST1400,RESTCAP,RESTPCASL}
                        Resting protocol name
                        (default : REST1400)
  --session {BAS1,BAS2,BAS3}
                        Session, Visit name
                        (default : BAS1)

Required Arguments:
  -t {anat,func,dwi} [{anat,func,dwi} ...], --scan-type {anat,func,dwi} [{anat,func,dwi} ...]
                        Scan type(s) to download


```
Current usage for the EmoRep Archival project involves using the default options via the first example, and additional options are available for increased usability.


### Functionality
`build_nki` conducts a single workflow that downloads and then BIDS-organizes the NKI archival data. Data for 1000 subjects will be downloaded with default options. The steps are:

1. Download data
1. Update EPI file names with BIDS 'run' field
1. Remove accompanying physio files
1. Shorten IDs
1. Finalize BIDS organization

Output are written to the archival project rawdata directory:

```
rawdata/
└── sub-08326
    └── ses-BAS1
        ├── anat
        │   ├── sub-08326_ses-BAS1_T1w.json
        │   └── sub-08326_ses-BAS1_T1w.nii.gz
        └── func
            ├── sub-08326_ses-BAS1_task-rest_run-01_acq-1400_bold.json
            ├── sub-08326_ses-BAS1_task-rest_run-01_acq-1400_bold.nii.gz
            └── sub-08326_ses-BAS1_task-rest_run-01_acq-1400_events.tsv
```

Also, see [Diagrams](#diagrams).


## Diagrams
Diagram of processes, showing workflow as a function of package methods.
![Process](diagrams/process.png)

Diagram of imports.
![Imports](diagrams/imports.png)

