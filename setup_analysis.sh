#!/bin/zsh

#fail on error
set -e

export PYTHIA8DATA=`pythia8-config --xmldoc`
#we need to work from this subdir for now. so cd into it
cd implementation

#done
