FROM nginx:stable-alpine

#----------------------------------------------------------------------------------------------------------------------
# SET DEFAULTS
#----------------------------------------------------------------------------------------------------------------------

ARG APP_USER=www-data
ARG APP_UID=1000

ARG APP_GROUP=chaos
ARG APP_GID=1000

#----------------------------------------------------------------------------------------------------------------------
# Setup User / Group
#----------------------------------------------------------------------------------------------------------------------
RUN addgroup -g ${APP_GID} ${APP_GROUP} && \
  adduser --ingroup ${APP_GROUP} -D -u ${APP_UID} --no-create-home -s /bin/bash ${APP_USER} && \
  addgroup nginx ${APP_GROUP} 

# --------------------------------------------------------
# NGINX CONFIG SETUP
# --------------------------------------------------------
# Remove the stock nginx config - It just wasnt meant to be
RUN rm /etc/nginx/conf.d/default.conf

# Add our AIO Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN apk add bash openssl

# --------------------------------------------------------
# NGINX TLS SETUP
# --------------------------------------------------------
# Generate SnakeOil TLS for transit
RUN mkdir /etc/nginx/ssl && \
  openssl req -x509 -nodes -days 365 \
    -subj "/C=US/ST=YES/O=CHAOS/CN=TPNG.io" \
    -addext "subjectAltName=DNS:TPNG" \
    -newkey rsa:4096 \
    -keyout /etc/nginx/ssl/cert.key \
    -out /etc/nginx/ssl/cert.crt; 

# --------------------------------------------------------
# NGINX LOGS SETUP
# --------------------------------------------------------
# Forward logs to stdout
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

#---------------------------------------------------------
# Harden the container - remove all root execution
#---------------------------------------------------------

# Fix them permissions so those l337 hackers cant b naughty and Nginx is happy
RUN touch /var/run/nginx.pid && \
  chown -R ${APP_USER} /var/run/nginx.pid && \
  chown -R ${APP_USER} /etc/nginx/ && \
  chown -R ${APP_USER} /var/log/nginx/ && \
  chown -R nginx:${EXTRA_GROUP} /var/cache/nginx/ && \
  chown -R ${APP_USER} /etc/nginx/ssl  && \
  chmod -R 740 /var/log/nginx/ && \
  chmod -R 740 /var/cache/nginx/ && \
  chmod 744 /var/run/nginx.pid && \
  chmod -R 540 /etc/nginx/ && \
  chmod -R 540 /etc/nginx/ssl && \
  mkdir -p /code/static && \
  chmod -R 774 /code/static
  
# Change to a non-root user - Beacuse well duh
# USER ${APP_USER}:${APP_USER}

# --------------------------------------------------------
# CONTAINER SETUP STUFFz
# --------------------------------------------------------

# Expose HTTP/HTTPS
EXPOSE 80
EXPOSE 443

VOLUME [ "/code/mediafiles", "/code/static", "/etc/nginx/ssl/" ]

# Make sure we kill Nginx with no mercy
STOPSIGNAL SIGTERM

# Tell that webserver to not fork off - We need him ;P
CMD ["nginx", "-g", "daemon off;"]