FROM quay.io/broadinstitute/viral-core:2.1.10

LABEL maintainer "viral-ngs@broadinstitute.org"

ENV VIRAL_PHYLO_PATH=$INSTALL_PATH/viral-phylo

COPY requirements-conda.txt $VIRAL_PHYLO_PATH/
RUN $VIRAL_NGS_PATH/docker/install-conda-dependencies.sh $VIRAL_PHYLO_PATH/requirements-conda.txt

# Copy all source code into the base repo
# (this probably changes all the time, so all downstream build
# layers will likely need to be rebuilt each time)
COPY . $VIRAL_PHYLO_PATH

# Link key bits of python code into the path
RUN ln -s $VIRAL_PHYLO_PATH/interhost.py $VIRAL_PHYLO_PATH/intrahost.py $VIRAL_PHYLO_PATH/ncbi.py $VIRAL_PHYLO_PATH/phylo $VIRAL_NGS_PATH

# This not only prints the current version string, but it
# also saves it to the VERSION file for later use and also
# verifies that conda-installed python libraries are working.
RUN /bin/bash -c "set -e; echo -n 'viral-ngs version: '; interhost.py --version"

CMD ["/bin/bash"]
