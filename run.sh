#!/bin/bash

# Set container and image names
BACKEND_CNAME=backend_container
BACKEND_INAME=backend_image
BACKEND_PORT=8000
BACKEND_DATA_DIR="$(pwd)/app/data"


FRONTEND_CNAME=front_container
FRONTEND_INAME=front_image
FRONTEND_PORT=3000

EXTERNAL_PORT=8080

NETWORK_NAME=web-network

# Stop and remove the existing container if it's running
docker stop $BACKEND_CNAME 2>/dev/null || true
docker rm $BACKEND_CNAME 2>/dev/null || true
docker stop $FRONTEND_CNAME 2>/dev/null || true
docker rm $FRONTEND_CNAME 2>/dev/null || true

docker system prune -af

# Build the image with no cache
docker build --no-cache -t $BACKEND_INAME -f ./image/DockerFile.backend .
# Prune dangling images
docker image prune -f

# Build the web image with no cache
docker build --no-cache -t $FRONTEND_INAME -f ./image/DockerFile.frontend .
# Prune dangling images
docker image prune -f

docker network inspect $NETWORK_NAME >/dev/null 2>&1 || docker network create $NETWORK_NAME

# Run the new container
docker run -d \
  --name $BACKEND_CNAME \
  --network $NETWORK_NAME \
  -p $BACKEND_PORT:$BACKEND_PORT \
  -v "$BACKEND_DATA_DIR:/code/app/data" \
  $BACKEND_INAME

# Run the new container
docker run -d \
  --name $FRONTEND_CNAME \
  --network $NETWORK_NAME \
  -p $EXTERNAL_PORT:$FRONTEND_PORT \
  $FRONTEND_INAME