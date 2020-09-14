FROM ubuntu:18.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends apt-utils && \
    apt-get install -y nginx && \
    apt-get install -y curl && \
    apt-get install -y vim && \
    apt-get install -y libgl1-mesa-glx && \
    apt-get install -y redis && \
    apt-get install -y python3 && \
    apt-get install -y python3-pip

RUN pip3 install --upgrade pip && \
#    pip install scikit-build && \
#    pip install opencv-python && \
#    pip install tensorflow && \
#    pip install mtcnn && \
#    pip install matplotlib && \
    pip install wheel && \
    pip install cmake && \
    pip install dlib && \
    pip install face_recognition && \
    pip install flask && \
    pip install line-bot-sdk && \
    pip install uwsgi && \
    pip install python-dotenv && \
    pip install numpy && \
    pip install redis

RUN apt-get install -y software-properties-common && \
    add-apt-repository universe && \
    add-apt-repository ppa:certbot/certbot && \
    apt-get update && \
    apt-get install certbot python-certbot-nginx

COPY ./ptt_nginx.conf /etc/nginx/sites-available/ptt_nginx.conf
COPY . /usr/src/app
WORKDIR /usr/src/app

RUN uwsgi uwsgi.ini && \
    chmod +x ./start.sh && ./start.sh

EXPOSE 443
EXPOSE 80

# CMD ["nginx", "-g", "daemon off;"]