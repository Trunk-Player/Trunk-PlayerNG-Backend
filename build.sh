#!/bin/bash
docker run --privileged --rm tonistiigi/binfmt --install all
docker buildx create --name mybuilder
docker buildx use mybuilder
docker buildx inspect --bootstrap
docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 -t trunkplayer/trunkplayer-ng-api:latest --push .
docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 -t trunkplayer/trunkplayer-ng-nginx:latest --push nginx/
docker buildx rm  --builder mybuilder