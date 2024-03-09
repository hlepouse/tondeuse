#!/bin/bash

GCP_PROJECT=tondeuse-414816
GCP_REGION=europe-west1
APP_NAME=tondeuse
IMAGE_NAME=$GCP_REGION-docker.pkg.dev/$GCP_PROJECT/docker/$APP_NAME

docker build --tag $IMAGE_NAME --platform=linux/amd64 app
docker push $IMAGE_NAME

gcloud run deploy $APP_NAME \
    --project="$GCP_PROJECT" \
    --region="$GCP_REGION" \
    --platform=managed \
    --timeout="60m" \
    --ingress=all \
    --image="$IMAGE_NAME" \
    --no-use-http2 \
    --cpu-boost \
    --allow-unauthenticated 
