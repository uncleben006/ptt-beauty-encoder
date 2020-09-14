
# build image base on Dockerfile
docker build . -t uncleben006/beauty-line-bot

# push to my docker hub
docker push uncleben006/beauty-line-bot

# pull and run on the cloud
docker run -it --name beauty-line-bot -p 80:80 -p 443:443 -e LC_ALL=C.UTF-8 uncleben006/beauty-line-bot bash

uwsgi uwsgi.ini
service nginx start
/etc/init.d/redis-server start

