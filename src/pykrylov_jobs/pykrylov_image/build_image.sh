#!/bin/sh
DATE=`date +%Y%m%d%H%M%S`
IMAGE_NAME="hub.tess.io/rapid_inov/how-to-agent-science:${DATE}"

echo "Building ${IMAGE_NAME}"
docker buildx build --platform=linux/amd64 \
  -f ./Dockerfile \
  -t ${IMAGE_NAME} . && \
docker push ${IMAGE_NAME}