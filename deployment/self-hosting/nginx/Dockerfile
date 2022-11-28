FROM nginx:1.23.2

COPY deployment/self-hosting/nginx/wallit.conf /etc/nginx/conf.d/wallit.conf
COPY deployment/self-hosting/nginx/cert.pem deployment/self-hosting/nginx/key.pem /home/certs/
COPY app/static /home/static

# set logging to stdout
RUN ln -sf /dev/stdout /var/log/nginx/access.log && ln -sf /dev/stderr /var/log/nginx/error.log
