from getpass import getpass
from re import S
from typing import List
import requests, os, uuid, time, argparse
from datetime import date, datetime, timedelta
import socketio

parser = argparse.ArgumentParser(description='TP-NG CLI Client')
parser.add_argument('--user', type=str, help='TrunkPlayerNG User', required=True)
parser.add_argument('--password', type=str, help='TrunkPlayerNG User')
parser.add_argument('--url', type=str, help='The url to TP-NG ie http://panik.io', required=True)
parser.add_argument('--alerts', help='Enable Web Alerts in CLI', action='store_true')
parser.add_argument('--no_verify', help='Dont verify TLS', action='store_true')
parser.add_argument('--no_audio', help='Dont play audio', action='store_true')
parser.add_argument('--no_transmission', help='Dont Show new TXs', action='store_true')
parser.add_argument('--debug', help='Show Debug Messages', action='store_true')
parser.add_argument('--json', help='Output in json', action='store_true')
parser.set_defaults(alerts=True)

args = parser.parse_args()
url = f"{args.url.strip('/').strip()}/"

class tp_ng_api:
    def __init__(self, user, password, host, page_limit=None, verify_ssl=True):
        self.user = user
        self.password = password
        self.host = host

        self.City = self.city(self.make_request)
        self.Agency = self.agency(self.make_request)
        self.SystemACL = self.systemacl(self.make_request)
        self.System = self.system(self.make_request)
        self.TalkGroup = self.talkgroup(self.make_request)
        self.SystemRecorder = self.systemRecorder(self.make_request)
        self.SystemForwarder = self.systemForwarder(self.make_request)
        self.Incident = self.incident(self.make_request)
        self.Transmission = self.transmission(self.make_request)
        self.Scanlist = self.scanlist(self.make_request)
        self.Scanner = self.scanner(self.make_request)
        self.Units = self.units(self.make_request)
        self.GlobalAnnouncement = self.globalAnnouncement(self.make_request)
        self.GlobalEmailtemplate = self.globalEmailtemplate(self.make_request)
        self.page_limit = page_limit
        self.verify_ssl = verify_ssl

        self.get_token()

    def get_token(self):

        payload = {"email": self.user, "password": self.password}

        auth = requests.post(self.host + "/api/auth/login/", json=payload, verify=self.verify_ssl)

        data = auth.json()
        self.token = data["access_token"]
        self.token_time = datetime.now()

        return self.token

    def make_request(self, EP,  Method="GET", data=None, Page=False, limit=100):

        if self.page_limit:
            limit = self.page_limit


        if self.token_time < datetime.now() - timedelta(minutes=5):
            self.get_token()

        if Page:
            prams = {
                "limit": limit,
                "offset": 0
            }
        else:
            prams = None

        headers = {"Authorization": f"Bearer {self.token}"}
        URL = self.host + "/api/" + EP
        Response = requests.request(Method, URL, json=data, headers=headers, params=prams, verify=self.verify_ssl)
        
        assert Response.ok
        payload = Response.json()

        payloadX = payload["results"]
        payloadz = [None]
        if Page:
            while len(payloadz) > 0:
                prams["offset"] =  prams["offset"] +  prams["limit"]
                Response = requests.request(Method, URL, json=data, headers=headers, params=prams, verify=self.verify_ssl)
                assert Response.ok
                payloadz = Response.json()["results"]
                payloadX.extend(payloadz)



        


        return payloadX

    class system:
        def __init__(self, make_request):
            self._make_request = make_request

        def list(self):
            return self._make_request("radio/system/list", Page=True)

        def create(self, name, systemACL, enableTalkGroupACLs=False):
            return self._make_request(
                "/radio/system/create",
                "POST",
                {
                    "name": name,
                    "systemACL": systemACL,
                    "enableTalkGroupACLs": enableTalkGroupACLs,
                },
            )

        def get(self, UUID):
            return self._make_request(f"/radio/system/{UUID}")

        def import_radioRefrence(self, UUID, SiteID, rrusername, rrpassword):
            payload = {"username": rrusername, "password": rrpassword, "siteid": SiteID}
            return self._make_request(f"/radio/system/{UUID}/importrr", "POST", payload)

        def delete(self, UUID):
            return self._make_request(f"/radio/system/{UUID}", "DELETE")

        def update(self, UUID, name=None, systemACL=None, enableTalkGroupACLs=None):
            data = {}
            if name:
                data["name"] = name
            if systemACL:
                data["name"] = systemACL
            if enableTalkGroupACLs:
                data["name"] = enableTalkGroupACLs

            return self._make_request(f"/radio/system/{UUID}", "PUT", data=data)

    class systemacl:
        def __init__(self, make_request):
            self._make_request = make_request

        def list(self):
            return self._make_request("radio/systemacl/list", Page=True)

        def create(self, name, public=False, users=[]):
            if len(users) > 0:
                return self._make_request(
                    "/radio/systemacl/create",
                    "POST",
                    {"name": name, "public": public, "users": users},
                )
            else:
                return self._make_request(
                    "/radio/systemacl/create", "POST", {"name": name, "public": public}
                )

        def get(self, UUID):
            return self._make_request(f"/radio/systemacl/{UUID}")

        def delete(self, UUID):
            return self._make_request(f"/radio/systemacl/{UUID}", "DELETE")

        def update(self, UUID, name=None, public=None, users=None):
            data = {}
            if name:
                data["name"] = name
            if public:
                data["name"] = public
            if users:
                data["name"] = users

            return self._make_request(f"/radio/systemacl/{UUID}", "PUT", data=data)

    class city:
        def __init__(self, make_request):
            self._make_request = make_request

        def list(self):
            return self._make_request("radio/city/list", Page=True)

        def create(self, name, description=""):
            return self._make_request(
                "/radio/city/create", "POST", {"name": name, "description": description}
            )

        def get(self, UUID):
            return self._make_request(f"/radio/city/{UUID}")

        def delete(self, UUID):
            return self._make_request(f"/radio/city/{UUID}", "DELETE")

        def update(self, UUID, name=None, description=None):
            data = {}
            if name:
                data["name"] = name
            if description:
                data["name"] = description
            return self._make_request(f"/radio/city/{UUID}", "PUT", data=data)

    class agency:
        def __init__(self, make_request):
            self._make_request = make_request

        def list(self):
            return self._make_request("radio/agency/list", Page=True)

        def create(self, name, city, description=""):
            return self._make_request(
                "/radio/agency/create",
                "POST",
                {"name": name, "city": city, "description": description},
            )

        def get(self, UUID):
            return self._make_request(f"/radio/agency/{UUID}")

        def delete(self, UUID):
            return self._make_request(f"/radio/agency/{UUID}", "DELETE")

        def update(self, UUID, name=None, city=None, description=None):
            data = {}
            if name:
                data["name"] = name
            if description:
                data["name"] = description
            if city:
                data["city"] = city
            return self._make_request(f"/radio/agency/{UUID}", "PUT", data=data)

    class talkgroup:
        def __init__(self, make_request):
            self._make_request = make_request

        def list(self):
            return self._make_request("radio/talkgroup/list", Page=True)

        def create(
            self,
            System,
            decimalID,
            alphatag,
            description="",
            encrypted=False,
            Agencys=[],
        ):
            payload = {
                "system": System,
                "decimalID": decimalID,
                "description": description,
                "alphaTag": alphatag,
                "encrypted": encrypted,
                "agency": Agencys,
            }

            return self._make_request("/radio/talkgroup/create", "POST", payload)

        def get(self, UUID):
            return self._make_request(f"/radio/talkgroup/{UUID}")
        
        def list_transmissions(self, UUID):
            return self._make_request(f"/radio/talkgroup/{UUID}/transmissions", Page=True)

        def delete(self, UUID):
            return self._make_request(f"/radio/talkgroup/{UUID}", "DELETE")

        def update(
            self,
            UUID,
            decimalID=None,
            alphatag=None,
            encrypted=None,
            description=None,
            Agencys=None,
        ):
            data = {}
            if encrypted != None:
                data["encrypted"] = encrypted
            if decimalID:
                data["decimalID"] = decimalID
            if alphatag:
                data["alphatag"] = alphatag
            if description:
                data["description"] = description
            if Agencys:
                data["Agencys"] = Agencys
            return self._make_request(f"/radio/talkgroup/{UUID}", "PUT", data=data)

    class systemRecorder:
        def __init__(self, make_request):
            self._make_request = make_request

        def list(self):
            return self._make_request("radio/systemrecorder/list", Page=True)

        def create(
            self,
            systemUUID,
            siteID,
            name,
            userUUID=None,
            enabled=True,
            talkgroupsAllowed=[],
            talkgroupsDenyed=[],
        ):

            payload = {
                "system": systemUUID,
                "siteID": siteID,
                "name": name,
                "enabled": enabled,
                "talkgroupsAllowed": talkgroupsAllowed,
                "talkgroupsDenyed": talkgroupsDenyed,
            }

            if userUUID:
                payload["user"] = userUUID

            return self._make_request("/radio/systemrecorder/create", "POST", payload)

        def get(self, UUID):
            return self._make_request(f"/radio/systemrecorder/{UUID}")

        def delete(self, UUID):
            return self._make_request(f"/radio/systemrecorder/{UUID}", "DELETE")

        def update(
            self,
            UUID,
            systemUUID=None,
            siteID=None,
            name=None,
            userUUID=None,
            enabled=None,
            talkgroupsAllowed=None,
            talkgroupsDenyed=None,
        ):
            data = {}
            if systemUUID:
                data["system"] = systemUUID
            if siteID:
                data["siteID"] = siteID
            if userUUID:
                data["user"] = userUUID
            if name:
                data["name"] = name
            if enabled != None:
                data["enabled"] = enabled
            if talkgroupsAllowed:
                data["talkgroupsAllowed"] = talkgroupsAllowed
            if talkgroupsDenyed:
                data["talkgroupsDenyed"] = talkgroupsDenyed

            return self._make_request(f"/radio/systemrecorder/{UUID}", "PUT", data=data)

    class systemForwarder:
        def __init__(self, make_request):
            self._make_request = make_request

        def list(self):
            return self._make_request("radio/systemforwarder/list", Page=True)

        def create(
            self,
            name,
            description,
            recorderKey,
            remoteURL,
            forwardedSystems=[],
            enabled=True,
        ):

            payload = {
                "name": name,
                "description": description,
                "recorder_key": recorderKey,
                "remote_url": remoteURL,
                "forwarded_systems": forwardedSystems,
                "enabled": enabled,
            }

            return self._make_request("/radio/systemforwarder/create", "POST", payload)

        def get(self, UUID):
            return self._make_request(f"/radio/systemforwarder/{UUID}")

        def delete(self, UUID):
            return self._make_request(f"/radio/systemforwarder/{UUID}", "DELETE")

        def update(
            self,
            UUID,
            name=None,
            description=None,
            enabled=None,
            recorderKey=None,
            remoteURL=None,
            forwardedSystems=None,
        ):
            data = {}

            if name:
                data["name"] = name
            if description:
                data["description"] = description
            if enabled != None:
                data["enabled"] = enabled
            if recorderKey:
                data["recorderKey"] = recorderKey
            if remoteURL:
                data["remoteURL"] = remoteURL
            if forwardedSystems:
                data["forwardedSystems"] = forwardedSystems

            return self._make_request(
                f"/radio/systemforwarder/{UUID}", "PUT", data=data
            )

    class scanlist:
        def __init__(self, make_request):
            self._make_request = make_request

        def list(self):
            return self._make_request("radio/scanlist/list", Page=True)

        def list_user_scanlists(self, userUUID):
            return self._make_request(f"/radio/scanlist/user/{userUUID}/list", Page=True)

        def list_all(self):
            return self._make_request("radio/scanlist/all/list", Page=True)

        def create(self, name, talkgroups, description="", communityShared=False):

            payload = {
                "name": name,
                "description": description,
                "communityShared": communityShared,
                "talkgroups": talkgroups,
            }

            return self._make_request("/radio/scanlist/create", "POST", payload)

        def get(self, UUID):
            return self._make_request(f"/radio/scanlist/{UUID}")

        def get_transmissions(self, UUID):
            return self._make_request(f"/radio/scanlist/{UUID}/transmissions", Page=True)

        def delete(self, UUID):
            return self._make_request(f"/radio/scanlist/{UUID}", "DELETE")

        def update(
            self,
            UUID,
            name=None,
            description=None,
            communityShared=None,
            talkgroups=None,
        ):
            data = {}
            if name:
                data["name"] = name
            if communityShared != None:
                data["communityShared"] = communityShared
            if description:
                data["description"] = description
            if talkgroups:
                data["talkgroups"] = talkgroups

            return self._make_request(f"/radio/scanlist/{UUID}", "PUT", data=data)

    class scanner:
        def __init__(self, make_request):
            self._make_request = make_request

        def list(self):
            return self._make_request("radio/scanner/list", Page=True)

        def create(self, name, scanlists, description="", communityShared=False):

            payload = {
                "name": name,
                "description": description,
                "communityShared": communityShared,
                "scanlists": scanlists,
            }

            return self._make_request("/radio/scanner/create", "POST", payload)

        def get(self, UUID):
            return self._make_request(f"/radio/scanner/{UUID}")

        def get_transmissions(self, UUID):
            return self._make_request(f"/radio/scanner/{UUID}/transmissions", Page=True)

        def delete(self, UUID):
            return self._make_request(f"/radio/scanner/{UUID}", "DELETE")

        def update(
            self,
            UUID,
            name=None,
            description=None,
            communityShared=None,
            scanlists=None,
        ):
            data = {}
            if name:
                data["name"] = name
            if communityShared != None:
                data["communityShared"] = communityShared
            if description:
                data["description"] = description
            if scanlists:
                data["scanlists"] = scanlists

            return self._make_request(f"/radio/scanner/{UUID}", "PUT", data=data)

    class transmission:
        def __init__(self, make_request):
            self._make_request = make_request

        def list(self):
            return self._make_request("radio/transmission/list", Page=True)

        def create(self, recorder, json, name, audioFile):

            payload = {
                "recorder": recorder,
                "json": json,
                "audioFile": audioFile,
                "name": name,
            }

            return self._make_request("/radio/transmission/create", "POST", payload)

        def list_transmission_freqs(self, UUID):
            return self._make_request(f"/radio/transmission/{UUID}/freqs")

        def get_transmission_frequency(self, UUID):
            return self._make_request(f"/radio/transmission/freq/{UUID}")

        def list_transmissions_units(self, UUID):
            return self._make_request(f"/radio/transmission/{UUID}/units")

        def get_transmission_unit(self, UUID):
            return self._make_request(f"/radio/transmission/unit/{UUID}")

        def get(self, UUID):
            return self._make_request(f"/radio/transmission/{UUID}")

        def delete(self, UUID):
            return self._make_request(f"/radio/transmission/{UUID}", "DELETE")

    class incident:
        def __init__(self, make_request):
            self._make_request = make_request

        def list(self):
            return self._make_request("radio/incident/list", Page=True)

        def create(
            self,
            systemUUID,
            name,
            description,
            time: datetime,
            Transmissions=[],
            active=True,
            agencys=[],
        ):

            payload = {
                "system": systemUUID,
                "name": name,
                "description": description,
                "time": time.isoformat(),
                "active": active,
                "transmission": Transmissions,
                "agency": agencys,
            }

            return self._make_request("/radio/incident/create", "POST", payload)

        def get(self, UUID):
            return self._make_request(f"/radio/incident/{UUID}")

        def delete(self, UUID):
            return self._make_request(f"/radio/incident/{UUID}", "DELETE")

        def update(
            self,
            UUID,
            systemUUID=None,
            name=None,
            description=None,
            time=None,
            Transmissions=None,
            active=None,
            agencys=[],
        ):
            data = {}
            if systemUUID:
                data["system"] = systemUUID
            if name:
                data["name"] = name
            if description:
                data["description"] = description
            if time:
                data["time"] = time
            if active != None:
                data["active"] = active
            if Transmissions:
                data["Transmissions"] = Transmissions
            if agencys:
                data["talkgroupsDenyed"] = agencys

            return self._make_request(f"/radio/incident/{UUID}/update", "PUT", data=data)

    class globalAnnouncement:
        def __init__(self, make_request):
            self._make_request = make_request

        def list(self):
            return self._make_request("radio/globalannouncement/list", Page=True)

        def create(self, name, description, enabled=True):

            payload = {"name": name, "description": description, "enabled": enabled}

            return self._make_request(
                "/radio/globalannouncement/create", "POST", payload
            )

        def get(self, UUID):
            return self._make_request(f"/radio/globalannouncement/{UUID}")

        def delete(self, UUID):
            return self._make_request(f"/radio/globalannouncement/{UUID}", "DELETE")

        def update(self, UUID, name=None, description=None, enabled=None):
            data = {}

            if name:
                data["name"] = name
            if description:
                data["description"] = description
            if enabled != None:
                data["enabled"] = enabled

            return self._make_request(
                f"/radio/globalannouncement/{UUID}", "PUT", data=data
            )

    class globalEmailtemplate:
        def __init__(self, make_request):
            self._make_request = make_request

        def list(self):
            return self._make_request("radio/globalemailtemplate/list", Page=True)

        def create(self, name, type, HTML, enabled=True):

            payload = {"name": name, "type": type, "HTML":HTML, "enabled": enabled}

            return self._make_request(
                "/radio/globalemailtemplate/create", "POST", payload
            )

        def get(self, UUID):
            return self._make_request(f"/radio/globalemailtemplate/{UUID}")

        def delete(self, UUID):
            return self._make_request(f"/radio/globalemailtemplate/{UUID}", "DELETE")

        def update(self, UUID, name=None, type=None, HTML=None, enabled=None):
            data = {}

            if name:
                data["name"] = name
            if type:
                data["type"] = type
            if HTML:
                data["HTML"] = HTML
            if enabled != None:
                data["enabled"] = enabled

            return self._make_request(
                f"/radio/globalemailtemplate/{UUID}", "PUT", data=data
            )

    class units:
        def __init__(self, make_request):
            self._make_request = make_request

        def list(self):
            return self._make_request("radio/unit/list", Page=True)

        def create(self, systemUUID, decimalID, description=""):

            payload = {"system": systemUUID, "decimalID": decimalID, "description":description}

            return self._make_request(
                "/radio/unit/create", "POST", payload
            )

        def get(self, UUID):
            return self._make_request(f"/radio/unit/{UUID}")

        def delete(self, UUID):
            return self._make_request(f"/radio/unit/{UUID}", "DELETE")

        def update(self, UUID, description=None):
            data = {}

            if description:
                data["description"] = description

            return self._make_request(
                f"/radio/unit/{UUID}", "PUT", data=data
            )

sio = socketio.Client()

@sio.on('debug')
def debug(data=""):
    if args.debug:
        if not args.json:
            print(f"[DEBUG]: {data['data']}")
        else:
            print(data)

@sio.event
def unicast(data):
    if not args.json:
        print(f"[UNICAST]: {data}")
    else:
        print(data)

@sio.event
def alert(data):
    if args.alerts:
        if not args.json:
            print(f"[!][{datetime.now().isoformat()}] ALERT -> [{data['title']}] -> {data['body']}")
        else:
            print(data)
        
@sio.event
def disconnect():
    connect_socket(url)
    
@sio.on('tx_response')
def tx_response(data):
    resp = f'[*][{datetime.now().isoformat()}] NEW TRANSMISSION - [{data["data"]["system_name"]}] -> [{str(data["data"]["talkgroup"]["decimal_id"])}] {data["data"]["talkgroup"]["alpha_tag"].ljust(25)} -> Length: {str(data["data"]["length"]).ljust(20)}'
    if not args.no_transmission:
        if not args.json:
            print(resp)
        else:
            print(data)

@sio.on('*')
def print_tx(event, data):
    if 'tx' in event:
        sio.emit('tx_request', {"UUID": data["UUID"]})

def connect_socket(url):
    verify = True
    if args.no_verify:
        verify = False
    tpngAPI = tp_ng_api(user=args.user, password=args.password, host=url, verify_ssl=verify)
    socket_token = tpngAPI.get_token()
    header = {"Authorization": socket_token}
    sio.connect(url, headers=header)
    print("[+] Connected to TP-NG SOCKET\n")

def main():
    print("Welcome to the TrunkPlayer-NG CLI Client\n")

    verify = True
    if args.no_verify:
        verify = False
  
    password = args.password
    if not password:
        password = getpass(f"Enter password for {args.user}: ")

    tpngAPI = tp_ng_api(user=args.user, password=args.password, host=url, verify_ssl=verify)
    connect_socket(url)

 
    

    while(True):
        print("Select an object to listen to")
        print("1. Show Scanlists")
        print("2. Show Talkgroups")
        print("3. Show Scanners")
        choice = int(input("Choice: "))
        print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')
        working_type = None


        if choice == 1:
            print("Scanlists:")
            scanlists = tpngAPI.Scanlist.list()     
            scanlist_numbered = []
            for sl in scanlists:
                scanlist_numbered.append([sl["UUID"], sl["name"]])
            for idx, tg in enumerate(scanlist_numbered):
                print(f"\t{str(idx)}. {tg[1]}")
                working_type = scanlist_numbered
        elif choice == 2:
            print("Talkgroups:")
            talkgroups = tpngAPI.TalkGroup.list()
            talkgroup_numbered = []
            for tg in talkgroups:
                talkgroup_numbered.append([tg["UUID"], tg["alpha_tag"]])
            for idx, tg in enumerate(talkgroup_numbered):
                print(f"\t{str(idx)}. {tg[1]}")
                working_type = talkgroup_numbered
        elif choice == 3:
            print("Scanners:")
            scanners = tpngAPI.Scanner.list()
            scanner_numbered = []
            for scr in scanners:
                scanner_numbered.append([scr["UUID"],scr["alpha_tag"]])
            for idx, tg in enumerate(scanner_numbered):
                print(f"\t{str(idx)}. {tg[1]}")
                working_type = scanner_numbered

        choice = int(input("Please enter the number of the item you want to listen to: "))
        item_uuid = working_type[choice][0]
        sio.emit('register_tx_source', {"UUIDs":[item_uuid]})

        while(True):
            print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')
            print(f"[+] LISTENING ON: {working_type[choice][1]}")
            choice = input("PRESS [ENTER] to select a new Talkgroup / Scanlist / Scanner\n\n[+] Waiting for New Transmissions\n\n")
            sio.emit('deregister_tx_source', {"UUIDs":[item_uuid]})
            sio.
            break

main()

