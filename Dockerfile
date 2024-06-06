FROM python:3.9-buster
RUN apt update && apt upgrade -y
RUN apt-get update && apt-get upgrade -y
RUN apt-get install git curl python3-pip dos2unix make git zlib1g-dev libssl-dev gperf cmake g++ -y
RUN git clone --recursive https://github.com/tdlib/telegram-bot-api.git
RUN cd telegram-bot-api && rm -rf build && mkdir build && cd build && cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX:PATH=.. .. && cmake --build . --target install 
RUN cd ./bin/ && ./telegram-bot-api --api-id=17983098 --api-hash=ee28199396e0925f1f44 && cd ../..
RUN pip3 install -U pip
COPY requirements.txt /requirements.txt
RUN cd /
RUN pip3 install -U -r requirements.txt
RUN mkdir /LazyDeveloper
WORKDIR /LazyDeveloper
COPY start.sh /start.sh
RUN dos2unix /start.sh
CMD ["/bin/bash", "/start.sh"]
