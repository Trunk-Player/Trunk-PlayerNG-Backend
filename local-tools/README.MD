# Local Install Instructions
> Use at your own risk, this is a more complicated deploment than OG TP. 

> **THIS IS NOT OFFICALLY A SUPPORTED INSTALL METHOD**

## Prereques
> Theses items have great support and are out of scope for this documentation
1. RabbitMQ (Local or Remote)
2. MYSQL/MardiaDB (Local or Remote)
3. UWSGI
4. Python 3.8+
5. Python-Virtualenv
6. Nginx

### Install
We will be using `/opt/tpng` in this install, if you choose to not use this directory be sure to edit the files in the `local-tools/` folder

```bash
sudo mkdir -p /opt/tpng
sudo chown user:user /opt/tpng
sudo chmod 755 /opt/tpng
```


```bash
git clone https://github.com/Trunk-Player/Trunk-PlayerNG-Backend.git /opt/tpng
cd /opt/tpng
mkdir /opt/tpng/mediafiles/
mkdir /opt/tpng/static
cp local-tools/settings.local.py src/trunkplayer_ng/
nano src/trunkplayer_ng/settings.local.py
```
Update settings.local.py


```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

```bash
sudo ln -s local-tools/nginx.local.conf /etc/nginx/sites-enabled/
sudo ln -s local-tools/trunkplayer-ng.supervisor.conf /etc/supervisor/conf.d/
sudo nginx -t 
sudo systemctl restart nginx

sudo supervisorctl add tpng
sudo supervisorctl start tpng:
```

