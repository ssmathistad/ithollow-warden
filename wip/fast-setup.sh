#!/bin/bash
# create registry container unless it already exists
reg_name='kind-registry'
reg_port='6000'
running="$(docker inspect -f '{{.State.Running}}' "${reg_name}" 2>/dev/null || true)"
if [ "${running}" != 'true' ]; then
  docker run \
    -d --restart=always -p "127.0.0.1:${reg_port}:6000" --name "${reg_name}" \
    registry:2
fi

sleep 10

kind create cluster --config kind.yaml

# connect the registry to the cluster network
# (the network may already be connected)
docker network connect "kind" "${reg_name}" || true

# tell https://tilt.dev to use the registry
# https://docs.tilt.dev/choosing_clusters.html#discovering-the-registry
for node in $(kind get nodes); do
  kubectl annotate node "${node}" "kind.x-k8s.io/registry=localhost:${reg_port}";
done

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

docker build . -f validating.Dockerfile -t localhost:6000/validating-webhook:latest
docker push localhost:6000/validating-webhook:latest 

#kind load docker-image localhost:6000/validating-webhook:latest

kubectl apply -f warden-k8s.yaml

# cat validating-webhook.yaml | sed "s/      caBundle: .*/      caBundle: ${CA}/" | kubectl apply -f -

# sleep 20

# kubectl apply -f test-pods/test.yaml

# sleep 30

# kind delete cluster
