FROM ubuntu:latest

RUN apt update 
RUN apt install python3 -y python3-pip python3-dev

WORKDIR /usr/app/src

COPY requirements.txt ./
COPY run.py ./run.py
RUN pip3 install -r requirements.txt

CMD python3 run.py