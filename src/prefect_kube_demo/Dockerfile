# docker image used in kubernetes agent's deployment
# extends miniconda3's default image
FROM continuumio/miniconda3

# name conda environment
ARG conda_env=prefect-k8-demo
ENV conda_env=${conda_env}

WORKDIR /app

# Create the environment:
COPY requirements/environment.yml .
RUN conda env create -f environment.yml

# install pip dependencies
COPY requirements/requirements.txt .
RUN conda activate ${conda_env} && \
    python -m pip install -r requirements.txt

# prepend conda environment to path
ENV PATH "${CONDA_DIR}/envs/${conda_env}/bin:${PATH}"
# make the specified environment the default one
ENV CONDA_DEFAULT_ENV ${conda_env}

# copy bash script to install user-defined package
COPY src/prefect_kube_demo/prepare.sh /usr/bin/prepare.sh
RUN chmod +x /usr/bin/prepare.sh