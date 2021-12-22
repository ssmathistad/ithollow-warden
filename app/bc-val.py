from flask import Flask, request, jsonify
import re
import jsonpatch
import base64

warden = Flask(__name__)

#POST route for Admission Controller  
@warden.route('/validate', methods=['POST'])
#Admission Control Logic
def validating_webhook():
    request_info = request.get_json()   
    uid = request_info["request"].get("uid")
    allowed = True

    try:
        if request_info["request"]["object"].get("namespace") == "nginx":
            for container_spec in request_info["request"]["object"]["spec"]["containers"]:
                print(container_spec)
                print("---------")
                if container_spec.get("image") != "nginx":
                    allowed = False

            if allowed == True:
                return k8s_response(allowed, uid, "Pod created. All the pod's containers have the image 'nginx'.")
            else:
                return k8s_response(allowed, uid, "Pod not created. There is a container it attempted to create in the nginx namespace that does not have an 'nginx' image.")
    except:
        return k8s_response(True, uid, "The pod has been created in a namespace other than 'nginx'")

    #return k8s_response(False, uid, f"{request_info}")
    return k8s_response(False, uid, "Check")

# @warden.route("/mutate", methods=["POST"])
# def mutate():
#     request_info = request.get_json()
#     uid = request_info["request"].get("uid")
#     counter = 0

#     try:
#         if request_info["request"]["object"].get("namespace") == "nginx":
#             for container_spec in request_info["request"]["object"]["spec"]["containers"]:
#                 if re.search("nginx", container_spec.get("image")) != None & re.search("nginx:latest", container_spec.get("image")) == None:
#                     return k8s_response_mutating(True, uid, "The pod is using an 'nginx' image", counter)

#                 counter = counter + 1
#             # return k8s_response_mutating(True, uid, "The pod has been created in a namespace other than 'nginx'", counter)
#         else:
#             return k8s_response(False, uid, "Pod not created. There is a container it attempted to create in the nginx namespace that does not have an 'nginx' image.")    

#     except:
#         return k8s_response_mutating(True, uid, "The pod has been created in a namespace other than 'nginx'", counter)

#Function to respond back to the Admission Controller
def k8s_response(allowed, uid, message):
     return jsonify({"apiVersion": "admission.k8s.io/v1", "kind": "AdmissionReview", "response": {"allowed": allowed, "uid": uid, "status": {"message": message}}})

#Function to respond back to the Admission Controller
# def k8s_response_mutating(allowed, uid, message, counter):
#     mutating_path = f"/spec/containers/{counter}/image"
#     json_patch = jsonpatch.JsonPatch([{"op": "replace", "path": mutating_path, "value": "nginx:latest"}])
#     base64_patch = base64.b64encode(json_patch.to_string().encode("utf-8")).decode("utf-8")
#     return jsonify({"apiVersion": "admission.k8s.io/v1", "kind": "AdmissionReview", "response": {"allowed": True, "uid": uid, "status": {"message": message}, "patchType": "JSONPatch", "patch": base64_patch}})

if __name__ == '__main__':
    warden.run(ssl_context=('certs/wardencrt.pem', 'certs/wardenkey.pem'),debug=True, host='0.0.0.0')