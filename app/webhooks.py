from flask import Flask, request, jsonify
import re
import jsonpatch
import base64

warden = Flask(__name__)

#POST route for Admission Controller  
@warden.route('/validate', methods=['POST'])
#Admission Control Logic - validating
def validating_webhook():
    request_info = request.get_json()
    uid = request_info["request"].get("uid")
    allowed = True

    try:
        if request_info["request"]["object"]["metadata"].get("namespace") == "busybox":
            for container_spec in request_info["request"]["object"]["spec"]["containers"]:
                if container_spec.get("image") != "busybox:latest":
                    allowed = False

            if allowed == True:
                return k8s_response(allowed, uid, "Pod created. All the pod's containers have the image 'busybox'.")
            else:
                return k8s_response(allowed, uid, "Pod not created. There is a container it attempted to create in the busybox namespace that does not have an 'busybox' image.")
    except:
        return k8s_response(False, uid, "An error occured.")

    return k8s_response(True, uid, "The pod has been created in a namespace other than 'busybox'")

#POST route for Admission Controller
@warden.route("/mutate", methods=["POST"])
#Admission Control Logic - mutating
def mutatating_webhook():
    request_info = request.get_json()
    uid = request_info["request"].get("uid")
    counter = 0

    try:
        print("BEFORE request_info")
        if request_info["request"]["object"]["metadata"].get("namespace") == "busybox":
            print("IN request_info (IF")
            for container_spec in request_info["request"]["object"]["spec"]["containers"]:
                print("CHECK")
                print(str(container_spec.get("image")))

                if re.search("busybox", container_spec.get("image")) == None:
                    return k8s_response(False, uid, "Pod not created. There is a container it attempted to create in the busybox namespace that does not have an 'busybox' image.")
                
                if container_spec.get("image") != "busybox:latest":
                    return k8s_response_mutating(False, uid, "All containers should be using the latest 'busybox' image", counter)

                counter = counter + 1

            return k8s_response(True, uid, "Pod created. All the pod's containers have the image 'busybox'.")
        else:
            print("IN request_info (ELSE")
            return k8s_response(True, uid, "The pod has been created in a namespace other than 'busybox'") #
            # return k8s_response(False, uid, "Pod not created. There is a container it attempted to create in the busybox namespace that does not have an 'busybox' image.")
    except:
        return k8s_response(False, uid, "An error occured.")

#Function to respond back to the Admission Controller - validate
def k8s_response(allowed, uid, message):
    return jsonify({"apiVersion": "admission.k8s.io/v1", "kind": "AdmissionReview", "response": {"allowed": allowed, "uid": uid, "status": {"message": message}}})

#Function to respond back to the Admission Controller - validate
def k8s_response(allowed, uid, message):
    return jsonify({"apiVersion": "admission.k8s.io/v1", "kind": "AdmissionReview", "response": {"allowed": allowed, "uid": uid, "status": {"message": message}}})

# Function to respond back to the Admission Controller - mutate
def k8s_response_mutating(allowed, uid, message, counter):
    print("CHECK IN FUNCTION")
    mutating_path = "/spec/containers/" + str(counter) + "/image"
    json_patch = jsonpatch.JsonPatch([{"op": "replace", "path": mutating_path, "value": "busybox:latest"}])
    base64_patch = base64.b64encode(json_patch.to_string().encode("utf-8")).decode("utf-8")
    print(str(base64_patch))
    return jsonify({"apiVersion": "admission.k8s.io/v1", "kind": "AdmissionReview", "response": {"allowed": True, "uid": uid, "status": {"message": message}, "patchType": "JSONPatch", "patch": base64_patch}})

if __name__ == '__main__':
    warden.run(ssl_context=('certs/wardencrt.pem', 'certs/wardenkey.pem'),debug=True, host='0.0.0.0')