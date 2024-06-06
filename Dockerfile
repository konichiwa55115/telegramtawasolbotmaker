FROM python:3.9-buster
RUN apt update && apt upgrade -y
RUN apt install git curl python3-pip -y
RUN apt install dos2unix -y
RUN pip3 install -U pip
COPY requirements.txt /requirements.txt
RUN cd /
RUN pip3 install -U -r requirements.txt
RUN mkdir /LazyDeveloper
WORKDIR /LazyDeveloper
COPY start.sh /start.sh
RUN dos2unix /start.sh
CMD ["/bin/bash", "/start.sh"]
