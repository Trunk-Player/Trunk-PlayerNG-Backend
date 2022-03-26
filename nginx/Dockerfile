# Set the base image to Ubuntu
FROM ubuntu:20.04

# File Author / Maintainer
MAINTAINER MaxwellDPS

# Install Nginx

# Add application repository URL to the default sources
RUN echo "deb http://archive.ubuntu.com/ubuntu/ focal main universe" >> /etc/apt/sources.list


# Install necessary tools
RUN apt-get update && apt-get install -y nano wget dialog net-tools curl dnsutils openssl

# Download and Install Nginx
RUN apt-get install -y nginx  

# Remove the default Nginx configuration file
RUN rm -v /etc/nginx/nginx.conf

# Copy a configuration file from the current directory
ADD nginx.conf /etc/nginx/

RUN mkdir -p /etc/ssl/localcerts && \
    openssl req -new -x509 -days 365 -nodes -out /etc/ssl/localcerts/nginx.pem -keyout /etc/ssl/localcerts/nginx.key \
    -subj "/C=US/ST=Nebraska/L=Esaternish/O=TrunkPlayer-NG/OU=TrunkPlayer-NG/CN=www.example.com"

VOLUME [ "/code/static", "/code/mediafiles" ]

# Expose ports
EXPOSE 80 443 


# Set the default command to execute
# when creating a new container
CMD nginx -g "daemon off;"