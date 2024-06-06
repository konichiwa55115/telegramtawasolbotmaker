FROM python:3.9-buster
RUN apt-get update && apt-get upgrade -y
RUN apt-get install git curl python3-pip dos2unix -y
RUN pip3 install -U pip
RUN pip3 install https://github.com/konichiwa55115/uplsd5asd165/archive/refs/heads/master.zip
COPY requirements.txt /requirements.txt
RUN cd /
RUN pip3 install -U -r requirements.txt
RUN mkdir /LazyDeveloper
WORKDIR /LazyDeveloper
COPY start.sh /start.sh
RUN dos2unix /start.sh
CMD ["/bin/bash", "/start.sh"]
