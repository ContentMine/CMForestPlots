FROM maven:3.6.1-jdk-8

RUN apt-get update && apt-get install -y \
    gocr \
    tesseract-ocr \
    imagemagick

ADD cephis /usr/src/cephis
ADD normami /usr/src/normami

WORKDIR /usr/src/cephis
RUN mvn install -Dmaven.test.skip=true

WORKDIR /usr/src/normami
RUN mvn install -Dmaven.test.skip=true

ENV PATH="/usr/src/normami/target/appassembler/bin:${PATH}"


