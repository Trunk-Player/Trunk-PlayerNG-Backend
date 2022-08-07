#!/usr/bin/python3

# usage: tpng.py [-h] --json JSON --m4a M4A --token TOKEN --url URL

# Process some integers.

# optional arguments:
#   -h, --help     show this help message and exit
#   --json JSON    The json file to send
#   --m4a M4A      The M4A audio file
#   --token TOKEN  The System recorder token
#   --url URL      The url to TP-NG ie http://panik.io


import sys, json, base64, requests, time, argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--json', type=str, help='The json file to send', required=True)
parser.add_argument('--m4a', type=str, help='The M4A audio file', required=True)
parser.add_argument('--token', type=str, help='The System recorder token', required=True)
parser.add_argument('--url', type=str, help='The url to TP-NG API ie http://panik.io/apiv1', required=True)

args = parser.parse_args()

JSON = args.json
M4A = args.m4a
Recordertoken= args.token
URL = args.url

with open(JSON, "r") as FILE:
        DATA = json.load(FILE)

with open(M4A, "rb") as FILE:
        AUDIO = base64.b64encode(FILE.read())

name = M4A.split("/")[-1]

payload = {
        "recorder": Recordertoken,
        "json": DATA,
        "name": name,
        "audio_file": AUDIO.decode()
}

try:
    Request = requests.post(f"{URL.rstrip('/')}/radio/transmission/create", json=payload)
except:
    Request = requests.post(f"{URL.rstrip('/')}/radio/transmission/create", json=payload)

if Request.ok:
    print(Request.text)
print(Request.text)

i =0
while not Request.ok:
    print(f"[*] RE-TRYING TX {name}")
    Request = requests.post(f"{URL.rstrip('/')}/radio/transmission/create", json=payload)
    time.sleep(5)
    i += 1
    if i >= 5:
       print(f"[!] FAILED RE-TRYING TX {name}")
       break