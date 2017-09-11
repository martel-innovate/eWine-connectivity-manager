#!/bin/bash

cd $(dirname $0)/..
sudo python test_core.py
sudo python test_rest.py