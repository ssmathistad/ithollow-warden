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
   # Add the Jetstack Helm repository
   helm repo add jetstack https://charts.jetstack.io

   # Update your local Helm chart repository cache
   helm repo update

   # Install the cert-manager Helm chart (including cert-manager CRDs)
   helm install cert-manager \
   --namespace cert-manager \
   --create-namespace \
   --set installCRDs=true \
   --version v1.6.1 \
   jetstack/cert-manager
   ```

1. Update `certs.yaml` if you're using different namespace/names etc.

1. Create the validation namespace, the root CA, and self signed certificate:

   ```bash
   kubectl apply -f certs.yaml
   ```

1. Get the base64 value of the ca.crt file in the secret

   ```bash
   CA=`kubectl -n validation get secret validation-ca-tls -o jsonpath='{.data.ca\.crt}'`
   ```

1. Build the container using the Dockerfile within the directory. Push the image to your image repository.

   #### Example with Docker Hub
   ```bash
   docker build . -f validating.Dockerfile -t octumn/validating-webhook:latest
   docker push octumn/validating-webhook:latest 
   ```

1. Load your image into kind.
   ```bash
   kind load docker-image octumn/validating-webhook:latest
   ```

1. Update the warden-k8s.yaml file to point to your new image.

1. apply the warden-k8s.yaml file to deploy your admission controller within the
   cluster.

   ```bash
   kubectl apply -f warden-k8s.yaml
   ```

1. Apply the validating-webhook.yaml file to deploy the validation configuration to the
   Kubernetes API server.

   ```bash
   cat validating-webhook.yaml | sed "s/      caBundle: .*/      caBundle: ${CA}/" | kubectl apply -f -
   ```

1. Test your app. If using the default warden-validating.py included with this repository,
    there are three test manifests in the [test-pods](/test-pods) folder.

   ```bash
   kubectl apply -f test-pods
   ```

   The output should be:
   ```
   pod/test1 created
   Error from server: error when creating "test-pods/test2.yaml": admission webhook "warden.validation.svc" denied the request: No labels exist. A Billing label is required
   Error from server: error when creating "test-pods/test3.yaml": admission webhook "warden.validation.svc" denied the request: Not allowed without a billing label
   ```

1. Add a mutating webhook
- Delete pod `test1`
   ```
   kubectl delete po test1
   ```
- Delete validatingwebhookconfigurations `warden-validating-webhook`
   ```
   kubectl delete validatingwebhookconfigurations warden-validating-webhook
   ```
- Remove the pod and service for the validating webhook.
   ```
   kubectl delete -f warden-k8s.yaml
   ```
- Build the container using the Dockerfile within the directory. Push the image to your image repository.
   #### Example with Docker Hub
   ```bash
   docker build . -f mutating.Dockerfile -t octumn/mutating-webhook:latest
   docker push octumn/mutating-webhook:latest 
   ```

- Load your image into kind.
   ```bash
   kind load docker-image octumn/mutating-webhook:latest
   ```
- *Update* the warden-k8s.yaml file to point to your new image and re-apply.
   ```
   kubectl apply -f warden-k8s.yaml
   ```
- Apply the mutating-webhook.yaml file to deploy the mutating configuration to the
   Kubernetes API server.
   ```bash
   cat mutating-webhook.yaml | sed "s/      caBundle: .*/      caBundle: ${CA}/" | kubectl apply -f -
   ```

1. Test your app again. If using the default mutating-warden.py included with this repository,
    there are three test manifests in the [test-pods](/test-pods) folder.

   ```bash
   kubectl apply -f test-pods
   ```

   The output should be:
   ```
   pod/test1 created
   pod/test2 created
   pod/test3 created
   ```

1. Cleanup

   ```bash
   kubectl delete -f test-pods
   kubectl delete mutatingwebhookconfigurations warden-mutating-webhook
   kubectl delete namespace validation
   helm uninstall -n cert-manager cert-manager
   kind delete cluster 
```