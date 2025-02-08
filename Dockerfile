# Base image with CUDA and cuDNN support for GPU acceleration
FROM nvidia/cuda:11.3.1-cudnn8-devel

# Add NVIDIA's package signing key for secure package installation
RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub

# Update system packages
RUN apt-get update && apt-get upgrade -y

# Set timezone to UTC to avoid interactive prompts during installation
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata && apt-get clean

# Install dependencies for Miniconda
RUN apt-get install -y wget bzip2 ca-certificates libglib2.0-0 libxext6 libsm6 libxrender1 git mercurial subversion && apt-get clean

# Install Miniconda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-py312_24.4.0-0-Linux-x86_64.sh -O ~/miniconda.sh && \
        /bin/bash ~/miniconda.sh -b -p /opt/conda && \
        rm ~/miniconda.sh && \
        ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
        echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
        find /opt/conda/ -follow -type f -name '*.a' -delete && \
        find /opt/conda/ -follow -type f -name '*.js.map' -delete && \
        /opt/conda/bin/conda clean -afy

# Add Miniconda to PATH
ENV PATH /opt/conda/bin:$PATH

# Set working directory for the application
WORKDIR /app

# Copy environment configuration and create Conda environment
COPY env.yaml .
RUN conda env create -f env.yaml

# Use Bash as the shell and activate the ColBERT environment
SHELL ["/bin/bash", "-c"]
RUN echo "source activate colbert" > ~/.bashrc && source ~/.bashrc

# Ensure subsequent RUN commands use the Conda environment
SHELL ["conda", "run", "-n", "colbert", "/bin/bash", "-c"]

# Copy application source code
COPY . /app

# Install ColBERT package
RUN pip install colbert-ai

# Verify that ColBERT environment is activated and ColBERT package is installed
RUN echo "Make sure colbert is installed:"
RUN python -c "from colbert import Searcher"

# Fix for missing crypt.h in the environment
# (related to issue https://github.com/stanford-futuredata/ColBERT/issues/309)
RUN cp /usr/include/crypt.h /opt/conda/envs/colbert/include/python3.8/crypt.h

# Set locale settings for compatibility
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Define the entry point to start the application with Flask
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "colbert", "flask", "--app", "main", "run", "--host", "0.0.0.0", "-p", "9881", "--debug"]
