#!/bin/bash

LOG_LEVEL=WARNING coverage run --source '.' manage.py test
apt install zip
coverage html
zip -r html.zip htmlcov/
coverage report
curl -s --upload-file html.zip $1
echo ""