#!/bin/bash

export FPGA_TOOL_PERF_DIR=`pwd`

set_tool_path () {
    local TOOL=$1
    local TOOL_PATH=$2
    local REQUIRED=$3

    if [ -z "${!TOOL}" ]; then
        if [ "$REQUIRED" = "no" ]; then
            echo "Default $TOOL is being used."
            export PATH=${FPGA_TOOL_PERF_DIR}/$TOOL_PATH:${PATH}
        else
            echo "ERROR: $TOOL path is required, but it is not set in the corresponding env variable!"
            return 1
        fi
    else
        echo "Using $TOOL from ${!TOOL}"
        export PATH=${!TOOL}:${PATH}
    fi
}

# Checking that required commands and environmental variables are set
set_tool_path VPR third_party/install/bin no
set_tool_path YOSYS third_party/install/bin no
set_tool_path SYMBIFLOW third_party/symbiflow/bin yes