#!/bin/bash
VENV_BIN=.venv/bin

cd $(dirname $0)/../..
. $VENV_BIN/activate
sudo $VENV_BIN/python wifi_manager