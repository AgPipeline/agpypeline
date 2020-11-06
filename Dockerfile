FROM ubuntu:18.04
LABEL maintainer="Chris Schnaufer <schnaufer@email.arizona.edu>"

# Add user
RUN useradd -u 49044 extractor \
    && mkdir /home/extractor
RUN chown -R extractor /home/extractor \
    && chgrp -R extractor /home/extractor

# Install the Python version we want
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        python3.7 \
        python3-pip && \
    ln -sfn /usr/bin/python3.7 /usr/bin/python && \
    ln -sfn /usr/bin/python3.7 /usr/bin/python3 && \
    ln -sfn /usr/bin/python3.7m /usr/bin/python3m && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Perform some upgrades
RUN python3 -m pip install --upgrade --no-cache-dir pip
RUN python3 -m pip install --upgrade --no-cache-dir setuptools

# Install applications we need
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-gdal \
        gdal-bin   \
        libgdal-dev  \
        gcc \
        g++ \
        python3.7-dev && \
    python3 -m pip install --upgrade --no-cache-dir \
        wheel && \
    python3 -m pip install --upgrade --no-cache-dir \
        numpy && \
    python3 -m pip install --upgrade --no-cache-dir \
        pygdal==2.2.3.* && \
    python3 -m pip install --upgrade --no-cache-dir \
        pylint && \
    apt-get remove -y \
        libgdal-dev \
        gcc \
        g++ \
        python3-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install the library
COPY agpypeline /tmp/agpypeline/agpypeline
COPY setup.py README.md /tmp/agpypeline/
COPY tests /tmp/agpypeline/tests
COPY data /tmp/agpypeline/data
COPY images /tmp/agpypeline/images

RUN python3 -m pip install --upgrade /tmp/agpypeline
#RUN python3 -m pip install pytest
#
#ENTRYPOINT ["/bin/bash"]
#RUN python3 -m pytest

USER root
