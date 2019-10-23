FROM python:2.7-buster

RUN mkdir /ChordPro-master

COPY . /ChordPro-master

WORKDIR /ChordPro-master

RUN pip install -r requirements.txt

ENTRYPOINT python ChordProToPDF.py
