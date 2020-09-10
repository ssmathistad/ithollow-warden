# theITHollow Warden

This project is for setting up a basic Kubernetes validating Admission
Controller using python.

Steps to deploy and test this admission controller.

1. Deploy a KIND cluster with Admission Controller enabled

   ```bash
   kind create cluster --config kind.yaml
   ```


1. Install cert-manager

   ```bash
   kubectl create namespace cert-manager
   kubectl apply --validate=false -f https://github.com/jetstack/cert-manager/releases/download/v0.13.1/cert-manager.yaml
   ```

1. Update `certs.yaml` if you're using different namespace/names etc.

1. Create root CA and self signed certificate:

   ```bash
   kubectl create namespace validation
   kubectl -n validation apply -f certs.yaml
   ```

1. Get the base64 value of the ca.crt file in the secret

   ```bash
   CA=kubectl -n validation get secret validation-ca-tls -o jsonpath='{.data.ca\.crt}'
   ```

1. Build the container using the Dockerfile within the directory. Push the image
   to your image repository

1. Update the warden-k8s.yaml file to point to your new image.

1. apply the warden-k8s.yaml file to deploy your admission controller within the
   cluster.

   ```bash
   kubectl -n validation apply -f warden-k8s.yaml
   ```

1. Apply the webhook.yaml file to deploy the validation configuration to the
   Kubernetes API server.

   ```bash
   cat webhook.yaml | sed "s/      caBundle: .*/      caBundle: ${CA}/" | kubectl -n validation apply -f -
   ```

1. Test your app. If using the default warden.py included with this repository,
    there are three test manifests in the [test-pods](/test-pods) folder.

   ```bash
   kubectl -n default apply -f test-pods
   ```

1. Cleanup

   ```bash
   kubectl -n default delete -f test-pods
   kubectl delete validatingwebhookconfigurations validating-webhook
   kubectl delete namespace validation
   kubectl delete -f https://github.com/jetstack/cert-manager/releases/download/v0.13.1/cert-manager.yaml
```