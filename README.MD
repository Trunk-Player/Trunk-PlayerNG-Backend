# TrunkPlayer-NG

[Trunk-PlayerNG](https://github.com/Trunk-Player) an Enterprise Grade Trunking API with ACLs, notifications, User management, a filterable API, Mertics, and more... WebUI not guaranteed™ 

## Setup
### Installing the API
```
git clone https://github.com/Trunk-Player/Trunk-PlayerNG-Backend.git
cd Trunk-PlayerNG-Backend
cp .env.sample .env
docker-compose up
```
4. Your API Base URL is https://<your.site>/api/v1

### S3 Support
An S3 compatable provider can be used to store the audio for Trunk-Player. S3 is provided by boto3 & [django storages](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html)

| Setting | Description | 
|---------|-------------|
| USE_S3 | Enable S3 for audio storage |
| S3_ACCESS_KEY_ID | This is your AWS Access Key |
| S3_SECRET_ACCESS_KEY | This is your AWS Secret Key |
| S3_BUCKET_NAME | This is your S3 Bucketname |
| S3_ENDPOINT_URL | This is your AWS S3 endpoint, For [AWS check here](https://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region) for [Wasibi check here](https://docs.wasabi.com/docs/what-are-the-service-urls-for-wasabis-different-storage-regions) |

### Connect to Trunk-Recorder
See the [Trunk-Recoder Plugin](https://github.com/robotastic/trunk-recorder/blob/master/docs/Plugins.md#trunk-player-next-gen-plugin)

## 🚧 TrunkPlayer-NG is still under active development 🚧

![image](https://user-images.githubusercontent.com/11069376/152628284-ec1ba428-c8e4-4ba3-bac4-6ca13ed5ea59.png)

Planned Features 🎁
Please note some of these may change

- [DOA] New REACT Web UI
- [COMPLETE] Better Multi-System Support
- [COMPLETE] Multiple site Recorder per System support
- [COMPLETE] System / Incident Transmission Forwarding (Allowing you to share transmissions with a whole separate TrunkPlayer instance)
- [COMPLETE] System ACLs
- [COMPLETE] Talkgroup ACLs
- [IN PROGRESS] Helm Chart For releasing to the Kubernetes (Allows for scaling for massive sites)
- [COMPLETE] Better Security, ACLs and S3 Signing
- [COMPLETE] All REST API based
- [SCRUBBED**] Trunk-Recorder Status server Metrics Dashboard
- [SCRUBBED**] File and TX Metrics Dashboard
- [COMPLETE] User and Global Scan Lists
- [COMPLETE] Sockets.IO for Better playback and fewer interruptions on playback
- [COMPLETE] Talkgroup / Unit activity alert with Apprise
- [DOA] Mobile app w/ push notifications
- [COMPLETE] Audio Authentication/signing in s3
- [COMPLETE] Historical Transmission API
- [COMPLETE] Improved Incident System
- [COMPLETE] Improved Global Notifications
- [UNSTARTED] Pulse Point integration (UnOffical)
- [NEEDS WORK] System email customization
- [NEEDS WORK] Branding Support
- [UNSTARTED] Add /metrics endpoint to offload to prometheus of opentelem **