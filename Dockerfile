FROM rtfpessoa/ubuntu-jdk8

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install tzdata
RUN apt-get install -y \
    maven \
    python3.7 \
    python3-pip \
    tesseract-ocr \
    imagemagick \
    libopencv-dev

ADD cephis /usr/src/cephis
ADD normami /usr/src/normami
ADD forestplots /usr/src/forestplots
ADD forestplots.py /usr/src/forestplots.py
ADD requirements.txt /usr/src/requirements.txt

WORKDIR /usr/src/cephis
RUN mvn install -Dmaven.test.skip=true

WORKDIR /usr/src/normami
RUN mvn install -Dmaven.test.skip=true

WORKDIR /usr/src
RUN python3.7 -m pip install -r requirements.txt

ENV PATH="/usr/src/normami/target/appassembler/bin:/usr/src:${PATH}"
