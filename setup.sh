#!/bin/bash

kind create cluster --config kind.yaml

helm install cert-manager \
--namespace cert-manager \
--create-namespace \
--set installCRDs=true \
--version v1.6.1 \
jetstack/cert-manager

kubectl apply -f certs.yaml

sleep 10

CA=`kubectl -n validation get secret validation-ca-tls -o jsonpath='{.data.ca\.crt}'`

echo $CA

docker build . -t octumn/webhooks:latest
docker push octumn/webhooks:latest 

kind load docker-image octumn/webhooks:latest

kubectl apply -f warden-k8s.yaml

# cat validating-webhook.yaml | sed "s/      caBundle: .*/      caBundle: ${CA}/" | kubectl apply -f -
cat mutating-webhook.yaml | sed "s/      caBundle: .*/      caBundle: ${CA}/" | kubectl apply -f -

kubectl create ns busybox

sleep 5

# kubectl apply -f test-pods

# sleep 30

# kind delete cluster
