#----------------------------------------------------------------------------------------------------------------------
# Docker TrunkPlayerNG API v2
#----------------------------------------------------------------------------------------------------------------------
FROM python:3.12-alpine

#----------------------------------------------------------------------------------------------------------------------
# SET DEFAULTS
#----------------------------------------------------------------------------------------------------------------------

ARG APP_USER=chaotic
ARG APP_UID=1000

ARG APP_GROUP=chaos
ARG APP_GID=1000

ARG CODE_DIR=/opt/chaos.corp/tpng
ENV INSTALL_DIR=${CODE_DIR}

#----------------------------------------------------------------------------------------------------------------------
# Setup User / Group
#----------------------------------------------------------------------------------------------------------------------
RUN addgroup -g ${APP_GID} ${APP_GROUP} && \
  adduser --ingroup ${APP_GROUP} -D -u ${APP_UID} --home ${CODE_DIR} -s /bin/bash ${APP_USER}

#----------------------------------------------------------------------------------------------------------------------
# Setup working dir
#----------------------------------------------------------------------------------------------------------------------
WORKDIR ${CODE_DIR}
RUN mkdir ${CODE_DIR}/static && \
  mkdir ${CODE_DIR}/staticfiles && \
  mkdir ${CODE_DIR}/media

#----------------------------------------------------------------------------------------------------------------------
# Install Deps
#----------------------------------------------------------------------------------------------------------------------

# Install CAs abd build deps
RUN apk update && apk add ca-certificates postgresql-dev libxml2 libxml2-dev libxslt libxslt-dev bash && \
  apk add --virtual build-dependencies \
    build-base \
    gcc \
    wget \
    git \
    libffi-dev

#----------------------------------------------------------------------------------------------------------------------
# Install Build libs
#----------------------------------------------------------------------------------------------------------------------
# Copy in your requirements file
COPY src/requirements.txt /tmp/requirements.txt

#----------------------------------------------------------------------------------------------------------------------
# Install Python Packages
#----------------------------------------------------------------------------------------------------------------------
# Update PIP or risk the wrath of the python 
# Install our packages and hope it dosent catch fire
# get rid of our requirements file, I didnt like him anyhow
RUN python -m pip install --upgrade pip --no-cache-dir && \
  python -m pip install --upgrade --no-cache-dir -r /tmp/requirements.txt

#----------------------------------------------------------------------------------------------------------------------
# Remove Build libs
#----------------------------------------------------------------------------------------------------------------------
# Trash that build junk
RUN rm /tmp/requirements.txt
RUN apk del build-dependencies
#----------------------------------------------------------------------------------------------------------------------
# Copy Code & primary files
# Copy your application code to the container (make sure you create a .dockerignore file if any large files or directories should be excluded)
#----------------------------------------------------------------------------------------------------------------------
# Copy the main codebase
COPY src/ ${CODE_DIR}/
COPY --chown=root:root chaosctl /bin/chaosctl
RUN  chmod +rx /usr/bin/chaosctl

#----------------------------------------------------------------------------------------------------------------------
# Set launch config
#----------------------------------------------------------------------------------------------------------------------
# Define Static files volume
VOLUME ${CODE_DIR}/static
VOLUME ${CODE_DIR}/media

#----------------------------------------------------------------------------------------------------------------------
# Set for Sekurity
#----------------------------------------------------------------------------------------------------------------------
RUN chown -R ${APP_USER}:${APP_GROUP} ${CODE_DIR}/ && \
  chmod -R 540 ${CODE_DIR}/* && \
  chmod -R 774 ${CODE_DIR}/static && \
  chmod -R 774 ${CODE_DIR}/staticfiles && \
  chmod -R 770 ${CODE_DIR}/media


# Change to a non-root user - Beacuse we dont want anybody being naughty if they ever manage to get in ;P
USER ${APP_USER}:${APP_GROUP}

# Expose the HTTP TCP socket - this way Nginx can do all the hard work
EXPOSE 40269

# Start
CMD ["chaosctl", "help"]
