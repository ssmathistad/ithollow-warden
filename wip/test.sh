#!/bin/sh
set -o errexit

# create registry container unless it already exists
reg_name='kind-registry'
reg_port='5001'
running="$(docker inspect -f '{{.State.Running}}' "${reg_name}" 2>/dev/null || true)"
if [ "${running}" != 'true' ]; then
  docker run \
    -d --restart=always -p "127.0.0.1:${reg_port}" --name "${reg_name}" \
    registry:2
fi

# create a cluster with the local registry enabled in containerd
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."localhost:${reg_port}"]
    endpoint = ["http://${reg_name}:${reg_port}"]
EOF

# connect the registry to the cluster network
docker network connect "kind" "${reg_name}" || true

# Document the local registry
# https://github.com/kubernetes/enhancements/tree/master/keps/sig-cluster-lifecycle/generic/1755-communicating-a-local-registry
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: local-registry-hosting
  namespace: kube-public
data:
  localRegistryHosting.v1: |
    host: "localhost:${reg_port}"
    help: "https://kind.sigs.k8s.io/docs/user/local-registry/"
EOF

###

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

docker build . -f validating.Dockerfile -t localhost:5001/validating-webhook:latest

echo "------"

docker push localhost:5001/validating-webhook:latest 

#kind load docker-image localhost:6000/validating-webhook:latest

kubectl apply -f warden-k8s.yaml