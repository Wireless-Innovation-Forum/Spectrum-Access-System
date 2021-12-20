FROM osgeo/gdal:latest

RUN apt-get update -y
RUN apt-get install -y make build-essential libssl-dev zlib1g-dev \
     libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev \
    libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl \
    git
ENV PYENV_ROOT="/.pyenv"
RUN git clone https://github.com/pyenv/pyenv.git $PYENV_ROOT
ENV PATH="$PYENV_ROOT/bin:$PATH"

ENV PYTHON_VERSION=3.7.12
RUN pyenv install $PYTHON_VERSION
ENV PATH="$PYENV_ROOT/versions/$PYTHON_VERSION/bin:$PATH"

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENV APP_DIRECTORY=/cu_pass/dpa
WORKDIR $APP_DIRECTORY

COPY ../../../../requirements.txt .
COPY ../../../../requirements-sas.txt .

RUN apt-get install -y libcurl4-openssl-dev libssl-dev libgeos++-dev libproj-dev

RUN pip install -r requirements.txt
RUN pip install -r requirements-sas.txt

ENV LOCAL_ROOT_DIRECTORY=../../../..
COPY $LOCAL_ROOT_DIRECTORY .

ENV CONTENT_ROOT=$APP_DIRECTORY/src/harness
ENV UNINSTALLED_PROPAGATION_DIRECTORY=$CONTENT_ROOT/reference_models/propagation
ENV UNINSTALLED_ITM_DIRECTORY=$UNINSTALLED_PROPAGATION_DIRECTORY/itm
ENV UNINSTALLED_EHATA_DIRECTORY=$UNINSTALLED_PROPAGATION_DIRECTORY/ehata

RUN cd $UNINSTALLED_ITM_DIRECTORY \
    && python setup.py build_ext -i

RUN cd $UNINSTALLED_EHATA_DIRECTORY \
    && python setup.py build_ext -i

ENV PYTHONPATH "${PYTHONPATH}:$CONTENT_ROOT"

ENTRYPOINT python3 src/harness/cu_pass/dpa_calculator/main
