# TrunkPlayer-NG



## Beta Testing
> The API is open to beta testing- help us test APIs and find bugs

** PLEASE NOTE THIS IS JUST THE API BACKEND, THERE IS NO REACT WEB UI YET **

***Report back in the [Trunk-Recorder](https://github.com/robotastic/trunk-recorder) discord #tp-ng channel***

### TELEMETRY NOTICE
This program is integrated with [sentry.io](sentry.io), You are **BY DEFAULT OPTED-OUT OF TELEMETRY**

Please consider turning on telemetry to help us track new errors



### Steps
1. get [tpng.py](https://gist.github.com/MaxwellDPS/b93e6aa63eddef2f5705c10c90c8f1a2) for your radio host
2. [Install docker-compose](https://docs.docker.com/compose/install/)
3. Run the following 
```
git clone https://github.com/Trunk-Player/Trunk-PlayerNG-Backend.git
cd Trunk-PlayerNG-Backend
cp .env.sample .env
# <EDIT .env>
docker-compose -f docker-compose.prod.yaml up
```
4. Visit https://yourip/api/
5. Report any errors 


## 🚧 TrunkPlayer-NG is still under active development 🚧

![image](https://user-images.githubusercontent.com/11069376/152628284-ec1ba428-c8e4-4ba3-bac4-6ca13ed5ea59.png)

This will be a complete rewrite of Trunk-Player! The new version will be all API-based, Kubernetes-ready, and feature a beautiful new REACT UI thanks to @nebraskaCoder!

Don't expect this soon- likely not until summer or fall. We will work to keep updating the community! We are on a mission to build the most functional, feature-rich, and obviously coolest looking trunked radio playback UI


***BROADCASTIFY WE ARE COMING FOR YOU 😉***

Planned Features 🎁
Please note some of these may change

- [IN PROGRESS] New REACT Web UI
- [COMPLETE] Better multi-system Support
- [COMPLETE] Multiple site recorder per system support
- [COMPLETE] System / incident transmission forwarding (Allowing you to share transmissions with a separate TrunkPlayer instance)
- [COMPLETE] System ACLs
- [COMPLETE] Talkgroup ACLs
- [UNSTARTED] Kubernetes support (Allows for scaling for massive sites)
- [COMPLETE] Better security, ACLs and S3 Signing
- [COMPLETE] REST API based
- [UNSTARTED] Trunk-Recorder status server metrics dashboard
- [UNSTARTED] File and TX metrics dashboard
- [COMPLETE] User and global scan lists
- [IN PROGRESS] Sockets.IO for improved playback
- [COMPLETE] Talkgroup and radio ID activity alert with Apprise
- [UNSTARTED] Mobile app w/ push notifications
- [COMPLETE] Audio authentication/signing in with S3
- [UNSTARTED] Historical transmission page / API
- [IN PROGRESS] Improved incident system
- [IN PROGRESS] Improved global notifications
- [UNSTARTED] Pulse Point integration (Unoffical)
- [IN PROGRESS] Click on unit to skip to time in transmission
- [IN PROGRESS] System email customization
- [IN PROGRESS] Branding support

--------------------------------------------------------------------- 
## Development Update 1/1/21
---

### Today I am confident to say to day the API (Only the API, not all functionality) has gone from PreAlpha to Alpha 

- I have connected TrunkPlayer-NG to Trunk Recorder and all seems to be working well!
- Automatic System Radio Reference Import
- Tested New Python feed script (working on site-offline caching (On TR Host))
- I have tested audio file storage locally, and just need to test S3 (Will be natively secured)
- I have Tested System Forwarders (Sending a Systems TX's to separate TP-NG)
- I have Tested native Multi-Site Feed (With Allow/Block Lists)

Next steps:
---
- Setup Tasks for radio operations 
- Setup Sockets.io Web communications
- Setup Metrics App and API
- Make official TR Plugin! 

Just wanted to share the updates, as I was able to get quite a bit done over the holiday... and well the last Dev update was frankly underwhelming :( . We are getting closer! **I'm optimistic that we can see a beta version by spring (Just API Backend for now)**!

As for the frontend, dev is just starting as now the API's are Functional and @nebraskacoder can start to use them. So expect more and more frontend news in the near-distant future!

### STAY TUNED!!!

***We are on a mission to build the most functional, feature rich, and obviously coolest looking Trunk playback UI***

