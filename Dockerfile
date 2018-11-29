# An incomplete base Docker image for running JupyterHub
#
# Add your configuration to create a complete derivative Docker image.
#
# Include your configuration settings by starting with one of two options:
#
# Option 1:
#
# FROM jupyterhub/jupyterhub:latest
#
# And put your configuration file jupyterhub_config.py in /srv/jupyterhub/jupyterhub_config.py.
#
# Option 2:
#
# Or you can create your jupyterhub config and database on the host machine, and mount it with:
#
# docker run -v $PWD:/srv/jupyterhub -t jupyterhub/jupyterhub
#
# NOTE
# If you base on jupyterhub/jupyterhub-onbuild
# your jupyterhub_config.py will be added automatically
# from your docker directory.

FROM centos:7
LABEL maintainer="Jupyter Project <jupyter@googlegroups.com>"

# install nodejs, utf8 locale, set CDN because default httpredir is unreliable
RUN localedef -c -f UTF-8 -i en_US en_US.UTF-8 && \
    yum -y update && \
    yum -y install wget git bzip2 sudo \
    yum clean all
ENV LANG C.UTF-8

# install Python + NodeJS with conda
RUN wget -q https://repo.continuum.io/miniconda/Miniconda3-4.5.11-Linux-x86_64.sh -O /tmp/miniconda.sh  && \
    echo 'e1045ee415162f944b6aebfe560b8fee */tmp/miniconda.sh' | md5sum -c - && \
    bash /tmp/miniconda.sh -f -b -p /opt/conda && \
    /opt/conda/bin/conda install --yes -c conda-forge \
      python=3.6 sqlalchemy tornado jinja2 traitlets requests pip pycurl \
      nodejs configurable-http-proxy sudospawner && \
    /opt/conda/bin/pip install --upgrade pip && \
    rm /tmp/miniconda.sh
ENV PATH=/opt/conda/bin:$PATH

# fix permissions on sudo executable (how did this get messed up?)
RUN chmod 4755 /usr/bin/sudo

RUN python3 -m pip install notebook jupyterhub-ldapauthenticator

# add the rhea user, who will run the server
# she needs to be in the shadow group in order to access the PAM service
# DONE: removed rhea's password
RUN groupadd shadow
RUN groupadd jupyterhub
RUN useradd -m -G shadow,jupyterhub rhea

# Give rhea passwordless sudo access to run the sudospawner mediator on behalf of users:
ADD centos/sudoers /tmp/sudoers
RUN cat /tmp/sudoers >> /etc/sudoers
RUN rm /tmp/sudoers

# DONE: pull config files based on TEAM_NAME (TEAM_NAME > user config, data ingestion config) from a git repo
## To run: docker build -t jupyterhub-sudo -f examples/Dockerfile . --build-arg TEAM_NAME=SAMPLE_TEAM
# DONE: removed user passwords
# add some regular users
ARG TEAM_NAME
RUN git clone https://github.com/kuriakinzeng/ai-training-configs.git /tmp/ai-training-configs
RUN while IFS= read -r name; do useradd -m -G jupyterhub $name; done < /tmp/ai-training-configs/$TEAM_NAME/users
RUN rm -rf /tmp/ai-training-configs

# make home directories private
RUN chmod o-rwx /home/*

ADD . /src/jupyterhub
WORKDIR /src/jupyterhub

RUN pip install . && \
    rm -rf $PWD ~/.cache ~/.npm

# RUN mkdir -p /srv/jupyterhub/
ADD centos/audit-log.py /srv/jupyterhub/audit-log.py
ADD centos/get_all_ports.sh /srv/jupyterhub/get_all_ports.sh

WORKDIR /srv/jupyterhub/
RUN chown rhea .
RUN chmod +x get_all_ports.sh
EXPOSE 8000

LABEL org.jupyter.service="jupyterhub"

CMD ["jupyterhub"]

USER rhea
ADD centos/jupyterhub_config.py ./jupyterhub_config.py
