#!/bin/bash

# The directory containing this script.
DIR=$(dirname "$(readlink -f "${0}")")

USAGE="$(basename "$0") [-h] FILE

Download all the Android applications whose package names are
listed in FILE, one package name per line.

where:
    -h, --help   show this help message
    FILE         the file containing the package name list"

if [ "$#" -ne 1 ]; then
    echo "1 argument required, "$#" provided. Usage:" >&2
    echo "" >&2
    echo "$USAGE" >&2
    exit 1
fi

while [[ $# -gt 0 ]]; do
    key="${1}"
    case "${key}" in
        -h|--help)
            echo "$USAGE"
            exit 0
        ;;
        *)
            # Check if the specified file exists.
            if [ -f "${key}" ]; then
                # The name of the file from which to read the package names.
                filename="${key}"
                break
            else
                echo "${key} does not exist or it's not a valid file!" >&2
                exit 1
            fi
        ;;
    esac
done

# Read the file line by line and remove from the file the
# packages names after they are processed.
while read -r line || [[ -n "${line}" ]]; do

    # Skip empty lines.
    if [[ -z "${line//[$'\t\r\n ']}" ]]; then
        sed -i '1,1 d' "${filename}"
        continue
    fi

    # Try to download the Android application and keep track
    # of the package names for which the download failed.
    if python3 download.py "${line}"; then
        :
    else
        echo "${line}" >> "${DIR}/errors.txt"
    fi

    # This package name was processed, so remove it from the
    # file (this is useful if the download of the applications
    # in the list is interrupted and then resumed later).
    sed -i '1,1 d' "${filename}"

    # Don't stress the server too much.
    sleep $[($RANDOM % 10) + 1]s

done < "${filename}"
