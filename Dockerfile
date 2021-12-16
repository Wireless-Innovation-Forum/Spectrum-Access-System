FROM osgeo/gdal:latest

ENV PYTHON_VERSION=3.7.12

RUN apt-get update -y
RUN apt-get install -y make build-essential libssl-dev zlib1g-dev \
     libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev \
    libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl \
    git
ENV PYENV_ROOT="/.pyenv"
RUN git clone https://github.com/pyenv/pyenv.git $PYENV_ROOT
ENV PATH="$PYENV_ROOT/bin:$PATH"

RUN pyenv install $PYTHON_VERSION
ENV PATH="$PYENV_ROOT/versions/$PYTHON_VERSION/bin:$PATH"

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /cu_pass/dpa

COPY . .

RUN apt-get install -y libcurl4-openssl-dev libssl-dev libgeos++-dev libproj-dev

RUN pip install -r requirements.txt
RUN pip install -r requirements-sas.txt

ENTRYPOINT bash
