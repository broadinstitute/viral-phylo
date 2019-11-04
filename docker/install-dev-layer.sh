#!/bin/bash
#
# This script is intended to facilitate a development environment for working
# on viral-phylo. It is intended to be run within a viral-core container
# that has a git checkout of viral-phylo mounted into the container as
# /opt/viral-ngs/viral-phylo.
#
# It should be run once after spinning up a plain viral-core container.
# It will install conda dependencies and create symlinks for code modules.
# You do not need to run or source this afterwards as long as you docker commit
# or otherwise save the state of your container.
#
# Not intended for use in docker build contexts (see Dockerfile for that)
#
# Must have $INSTALL_PATH and $VIRAL_NGS_PATH defined (from viral-core docker)
set -e -o pipefail

VIRAL_PHYLO_PATH=/opt/viral-ngs/viral-phylo

$VIRAL_NGS_PATH/docker/install-conda-dependencies.sh $VIRAL_PHYLO_PATH/requirements-conda.txt

ln -s $VIRAL_PHYLO_PATH/phylo $VIRAL_PHYLO_PATH/test $VIRAL_PHYLO_PATH/interhost.py $VIRAL_PHYLO_PATH/intrahost.py $VIRAL_PHYLO_PATH/ncbi.py $VIRAL_NGS_PATH
