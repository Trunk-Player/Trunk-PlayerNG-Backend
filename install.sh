#!/bin/bash

install() {
  echo -e "\n[+] Creating $INSTALL_DIR..."
  mkdir -p $INSTALL_DIR
  cd $INSTALL_DIR



  echo -e "\n[+] Pulling Trunk-PlayerNG-Backend..."
  wget https://github.com/Trunk-Player/Trunk-PlayerNG-Backend/archive/refs/tags/latest.tar.gz \
    -O /tmp/tpng.tgz
  tar -xzf /tmp/tpng.tgz --strip-components=1
  rm /tmp/tpng.tgz
  
  echo -e "\n[+] Make sure to edit .env..."
  cp .env.sample .env

  echo -e "\n[+] Make sure to edit .env\n\n"
  echo "Start: chaosctl start"
  echo "Stop: chaosctl stop"
  echo "destroy: chaosctl destroy"
  echo "logs: chaosctl logs"

  install $INSTALL_DIR/chaosctl /usr/bin/

}

if [ "$EUID" -ne 0 ]
then echo "Please run as root"
exit
fi

install