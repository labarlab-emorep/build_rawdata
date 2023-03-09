#!/bin/bash

function Usage {
    cat <<USAGE

    Organize CAMRD DICOMs for the EMOREP study.

    Read the DICOM header of each file in <dcm_dir>/2022*, find the
    protocol name, make a new directory <dcm_dir>/<protocol-name>,
    and relocate the DICOM.

    Requires AFNI's dicom_hdr function.

    Required Arguments:
        -d <dcm_dir> = Location of parent DICOM directory, contains
                        sub-directy named in YMD format (e.g. 20220606*)

    Example Usage:
        $0 -d /path/to/ER0009/day2_movies/DICOM

USAGE
}

# capture arguments
while getopts ":d:h" OPT; do
    case $OPT in
    d)
        dcm_dir=${OPTARG}
        if [ ! -d $dcm_dir ]; then
            echo -e "\n\t ERROR: $dcm_dir not found or is not a directory." >&2
            Usage
            exit 1
        fi
        ;;

    h)
        Usage
        exit 0
        ;;
    :)
        echo -e "\n\t ERROR: option '$OPTARG' missing argument." >&2
        Usage
        exit 1
        ;;
    \?)
        echo -e "\n\t ERROR: invalid option '$OPTARG'." >&2
        Usage
        exit 1
        ;;
    esac
done

# print help if no arg
if [ $OPTIND == 1 ]; then
    Usage
    exit 0
fi

# Check anticipated organization
if [ ! -d ${dcm_dir}/20* ]; then
    echo -e "\n\tERROR: Expected sub-directory ${dcm_dir}/20*" >&2
    Usage
    exit 1
fi

# Check for AFNI command
dicom_hdr 1>/dev/null 2>&1
if [ $? != 0 ]; then
    echo -e "\n\tERROR: AFNI's dicom_hdr required." >&2
    Usage
    exit 1
fi

# Check for DICOMs
dcm_list=($(ls ${dcm_dir}/20*))
if [ ${#dcm_list[@]} == 0 ]; then
    echo -e "\n\t No DICOMs detected in ${dcm_dir}/20*\n" >&1
    exit 0
fi

# Reorganize dcms
cd ${dcm_dir}/20*
c=0
for i in *dcm; do

    # Extract, check name
    prot_name=$(dicom_hdr $i | grep "0008 103e" | sed 's/^.*tion\/\///' | sed 's/ //g')
    if [ ${#prot_name} == 0 ]; then
        echo -e "No Name detected for $i"
        continue
    fi

    # Setup output location, move dcm
    # Remove any ">"s protocol name with a single "_".
    prot_dir=${dcm_dir}/${prot_name//+([>])/_}
    [ ! -d $prot_dir ] && mkdir -p $prot_dir
    echo -e "$c\t$prot_name <- $i"
    mv $i ${prot_dir}/$i
    let c+=1
done
