#!/bin/bash

# requires python3
# call with -h for help

CALL_DIR=$(pwd)

USAGE="Usage: $(basename $0) [-p proto_path] [-o output_dir] <filename1> <filename2> ..."

ARGS=("$@")

cd /tmp

# Can be changed to diff. version
DL_NAME="nanopb-0.4.9.tar.gz"

TMP_NANOPB_DIR="nanopb-tmp"

if [ ! -d ${TMP_NANOPB_DIR} ]; then
  # Download the nanopb tarball
  curl -O https://jpa.kapsi.fi/nanopb/download/${DL_NAME}

  # Create a temporary directory for extraction
  mkdir -p ${TMP_NANOPB_DIR}

  # Extract the tarball to the temporary directory
  tar -xzf ${DL_NAME} -C ${TMP_NANOPB_DIR} --strip-components=1

  # Delete the tarball
  rm ${DL_NAME}
fi



TMP_VENV_NAME="temp_nanopb_generation_venv"

if ! source ${TMP_VENV_NAME}/bin/activate 2>/dev/null; then
    python3 -m venv ${TMP_VENV_NAME}
    source ${TMP_VENV_NAME}/bin/activate
fi

pip install protobuf grpcio-tools  # nanopb_generator.py dependencies

cd ${CALL_DIR}

"/tmp/${TMP_NANOPB_DIR}/generator/nanopb_generator.py" \
    ${ARGS}

deactivate