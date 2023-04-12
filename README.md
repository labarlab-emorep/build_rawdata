# build_rawdata

This in-house python package is written for the EmoRep project, intended to be executed via command line on the labarserv2 computer.

## Functionality
- Convert DICOMs to NIfTI format
- Organize directories and file names according BIDS specifications
- Generate events sidecar and JSON files for EmoRep task
- Generate dataframe for rest ratings task
- Update fmap sidecar with "IntendedFor" field
- Copy physio data to rawdata, and generate a txt version for Autonomate

## Usage
- Install to local python environment `$ python setup.py install --record record.txt`
    - (should already be done)
- Trigger package help and usage via entrypoint `$ build_rawdata`

## Documentation
_TODO: take readthedocs live_
