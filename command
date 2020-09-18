
# build image base on Dockerfile
docker build . -t uncleben006/beauty-line-bot

# push to my docker hub
docker push uncleben006/beauty-line-bot

# pull and run on the cloud
docker run -it -d --name beauty-line-bot \
-p 80:80 -p 443:443 \
-e LC_ALL=C.UTF-8 \
-v ~/temp:/usr/src/app/static/temp \
-v ~/ptt_nginx.conf:/etc/nginx/sites-available/ptt_nginx.conf \
-v ~/letsencrypt:/etc/letsencrypt \
uncleben006/beauty-line-bot bash

