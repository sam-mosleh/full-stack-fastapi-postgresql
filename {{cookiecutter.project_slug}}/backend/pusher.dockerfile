FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

WORKDIR /app/

ENV GROUP_ID=1000 \
    USER_ID=1000 \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DEFAULT_TIMEOUT=100 \
    TZ=Asia/Tehran

# Create the project user
RUN groupadd -g $GROUP_ID apprunner && \
    useradd -u $USER_ID -g apprunner -m -s /bin/sh apprunner

# Install Poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# For development, Jupyter remote kernel, Hydrogen
# Using inside the container:
# jupyter lab --ip=0.0.0.0 --allow-root --NotebookApp.custom_display_url=http://127.0.0.1:8888
ARG INSTALL_JUPYTER=false
RUN bash -c "if [ $INSTALL_JUPYTER == 'true' ] ; then pip install jupyterlab ; fi"

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./app/pyproject.toml ./app/poetry.lock* /app/
ADD ./app/wheelhouse/ ./wheelhouse/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --no-dev ; fi"

COPY ./app /app

ENV MAX_WORKERS=1 \
    PRE_START_PATH=/app/pusher-prestart.sh \
    MODULE_NAME="app.pusher"
