#!/bin/bash
docker run --privileged --rm tonistiigi/binfmt --install all
docker buildx create --name mybuilder
docker buildx use mybuilder
docker buildx inspect --bootstrap
docker buildx build --platform linux/amd64,linux/arm64,linux/arm64/v8,linux/arm/v7,linux/arm/v6,linux/aarch64 \
    -t trunkplayer/trunkplayer-ng-api:latest -t trunkplayer/trunkplayer-ng-api:$1 --push .
docker buildx build --platform linux/amd64,linux/arm64,linux/arm64/v8,linux/arm/v7,linux/arm/v6,linux/aarch64 \
    -t trunkplayer/trunkplayer-ng-nginx:latest -t trunkplayer/trunkplayer-ng-nginx:$1 --push nginx/
docker buildx rm  --builder mybuilder