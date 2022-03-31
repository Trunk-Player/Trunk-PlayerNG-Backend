# Local Install Instructions
> Use at your own risk, this is a more complicated deploment than OG TP. 

> **THIS IS NOT OFFICALLY A SUPPORTED INSTALL METHOD**

## Prereques
> Theses items have great support and are out of scope for this documentation
1. RabbitMQ (Local or Remote)
2. MYSQL/MardiaDB (Local or Remote)
3. **Python 3.9+**
4. python-dev
5. python-venv
6. Nginx
7SO . libmariadbclient-dev

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
mkdir /opt/tpng/src/mediafiles/
mkdir /opt/tpng/src/staticfiles/
cp local-tools/settings.local.py src/trunkplayer_ng/settings_local.py
nano src/trunkplayer_ng/settings_local.py
```
Update settings.local.py


```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

```bash
sudo ln -s /opt/tpng/local-tools/nginx.local.conf /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t 
sudo systemctl restart nginx
```

```bash
sudo ln -s /opt/tpng/local-tools/trunkplayer-ng.supervisor.conf /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo supervisorctl add tpng
sudo supervisorctl start tpng:
```

```bash
/opt/tpng/src/manage.py migrate
/opt/tpng/src/manage.py collectstatic
```

And youre done
