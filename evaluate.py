from kubernetes import config
import kubernetes.client
from kubernetes import client, config
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
configuration = kubernetes.client.Configuration()

def check_env_variable(namespace, pod_name, env_variable, env_value, i):
    count=0
    found="0"
    for count in range(len(i.spec.containers[0].env)):
        if ((i.spec.containers[0].env[count].name) == env_variable and (i.spec.containers[0].env[count].value) == env_value):
            print("Provided environment variable match with the existing values for the pod %s" % (pod_name))
            found="1"
            break
    if (found == "0"):
            print("Provided environment variable doesn't match with the existing values for the pod %s" % (pod_name))

def check_command_string(namespace, pod_name, check_command, i):
    print(i.spec.containers[0].command)
    if ( check_command in str((i.spec.containers[0].command))):
        print("Provided command %s match the command in pod %s. PASS" % (check_command, pod_name))
    else:
        print("Provided command %s doesn't match the command in pod %s. FAIL" % (check_command, pod_name))

def check_init_container(namespace, pod_name, i, init_container_name="null", init_container_command="null", init_container_image="null"):
    for count in range(len(i.spec.init_containers)):
        if (init_container_name != "null"):
            if (str(i.spec.init_containers[count].name) == init_container_name):
                print("Init_container_name is correct %s . PASS" % (init_container_name))
                if (init_container_command == "null" and init_container_image == "null"):
                    break
                else:
                    if (init_container_command != "null"):
                        if ((init_container_command in str(i.spec.init_containers[count].command))):
                            print("Init_container_name %s has command %s . PASS" % (init_container_name, init_container_command))
                            if (init_container_image == "null"):
                                break
                        else:
                            print("Init_container_name %s doesn't have command %s . FAIL" % (init_container_name, init_container_command))
                    if (init_container_image != "null"):
                        if ( init_container_image in str(i.spec.init_containers[count].image) ):
                            print("Init_container_name %s has image %s . PASS" % (init_container_name, init_container_image))
                            break
                        else:
                            print("Init_container_name %s doesn't has image %s. FAIL" % (init_container_name, init_container_image))
                            break
            else:
                print("Init_container_name is incorrect %s . FAIL" % (init_container_name))


def check_container(container_name, container_list, container_image="null", container_command="null"):
    found="0"
    for i in range(len(container_list)):
        if (str(container_list[i].name) == container_name):
            print("Container %s present. PASS" % (container_name))
            found="1"
            if (container_image == "null" and container_command == "null"):
                break
            if ( container_image != "null" and ( container_image in str(container_list[i].image)) ):
                print("Container %s has image set to %s. PASS" % (container_name, container_image))
                if (container_command == "null"):
                    break
            else:
                print("Container %s doesn't have image set to %s. FAIL" % (container_name, container_image))
                break
            if ( container_command != "null" and ( container_command in str(container_list[i].command)) ):
                print("Container %s has command set to %s. PASS" % (container_name, container_command))
                break
            else:
                print("Container %s doesn't have command set to %s. FAIL" % (container_name, container_command))
                break
    if (found == "0"):
            print("Container %s is not present in the deployment. FAIL" % (container_name))

def get_deployment_status(namespace, deploy_name, container_name="null", container_image="null", container_command="null"):
    #Checks deployment is the specified namespace. Checks if the container's name. image and command which is specified
    config.load_kube_config()
    # Create an instance of the API class
    api_instance = kubernetes.client.AppsV1Api()
    found="0"
    try:
        api_response = api_instance.list_namespaced_deployment(namespace, pretty=True, watch=False)
        for count in range(len(api_response.items)):
            if (str(api_response.items[count].metadata.name) == deploy_name):
                print("Deployment %s is present. PASS" % (deploy_name))
                if (container_name != "null"):
                    print("Checking %s container in Deployment %s ..." % (container_name,deploy_name))
                    check_container(container_name=container_name, container_list=api_response.items[count].spec.template.spec.containers, container_image=container_image, container_command=container_command)
                found="1"
    except ApiException as e:
        print("Exception when calling AppsV1Api->list_namespaced_deployment: %s\n" % e)
    if (found == "0"):
            print("Deployment %s is not present. FAIL" % (deploy_name))


def get_daemonset_status(namespace, daemonset_name):
    #Checks daemonsets status. Also checks the desired and available values
    config.load_kube_config()
    # Create an instance of the API class
    api_instance = kubernetes.client.AppsV1Api()
    found="0"

    try:
        api_response = api_instance.list_namespaced_daemon_set(namespace, pretty=True, watch=False)
        for count in range(len(api_response.items)):
            if (str(api_response.items[count].metadata.name) == daemonset_name):
                print("Daemonset %s is present checking status. PASS" % (daemonset_name))
                found="1"
                if ((api_response.items[count].status.desired_number_scheduled) == (api_response.items[count].status.number_ready) ):
                    print("Daemonset %s is running on all nodes. PASS" % (daemonset_name))
                else:
                    print("Daemonset %s is not running on all nodes. FAIL" % (daemonset_name))
    except ApiException as e:
        print("Exception when calling AppsV1Api->list_namespaced_daemon_set: %s\n" % e)
    if (found == "0"):
            print("Daemonset %s is not present. FAIL" % (daemonset_name))

def get_pod_status(namespace, pod_name, check_command="null", env_variable="null", env_value="null", init_container="null", init_container_name="null", init_container_command="null", init_container_image="null"):
    #Checks deployment is the specified namespace. Checks if the pod has init_container's with it's name. image and command which is specified
    config.load_kube_config()
    found="0"
    v1 = core_v1_api.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces(watch=False, pretty=True)
    for i in ret.items:
        if ((str(i.metadata.namespace) == namespace) and (str(i.metadata.name) == pod_name)):
            print("Pod %s is present checking status. PASS" % (i.metadata.name))
            found="1"
            if (str((i.status.phase)) == "Running"):
                print("Pod %s is running. PASS" % (i.metadata.name))
                if (env_variable != "null" and env_value != "null"):
                    print("Checking environonment variables..")
                    check_env_variable(namespace, pod_name, env_variable, env_value, i)
                if (check_command != "null"):
                    check_command_string(namespace, pod_name, check_command, i)
                if (init_container != "null"):
                    check_init_container(namespace, pod_name, i, init_container_name=init_container_name, init_container_command=init_container_command, init_container_image=init_container_image)
                    break
            else:
                print("Pod %s is not running. FAIL" % (i.metadata.name))
                exit(1)
    if (found == "0"):
            print("Pod %s is not present. FAIL" % (pod_name))

def get_servcie_status(namespace, svc_name, check_string="null"):
    #Checks service is the specified namespace. Checks if the service is accessible and the message which it is displaying
    config.load_kube_config()
    v1 = core_v1_api.CoreV1Api()
    # ret = v1.list_namespaced_service(namespace, watch=False, pretty=True)
    try:
        api_response = v1.read_namespaced_service_status(svc_name, namespace , pretty=True)
    except ApiException as e:
        if e.status != 404:
            print("Unknown error: %s" % e)
            exit(1)
        else:
            print("Service %s not found in %s namespace" % (svc_name, namespace))
            exit(1)

    print("Deploy dummy pod for testing the service")

    name = 'busybox-test'
    resp = None
    try:
        resp = v1.read_namespaced_pod(name=name, namespace='default')
    except ApiException as e:
        if e.status != 404:
            print("Unknown error: %s" % e)
            exit(1)

    if not resp:
        print("Pod %s does not exist. Creating it..." % name)
        pod_manifest = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {
                'name': name
            },
            'spec': {
                'containers': [{
                    'image': 'alpine:3.12',
                    'name': 'sleep',
                    "args": [
                        "/bin/sh",
                        "-c",
                        "while true;do date;sleep 5; done"
                    ]
                }]
            }
        }
        resp = v1.create_namespaced_pod(body=pod_manifest, namespace='default')
        while True:
            resp = v1.read_namespaced_pod(name=name, namespace='default')
            if resp.status.phase != 'Pending':
                break
            time.sleep(1)
        print("Done.")

    print ("Checking service endpoint response")

    # Calling exec and waiting for response
    success_status = "200 OK"
    if (check_string != "null"):
        exec_command = [
            '/bin/sh',
            '-c',
            'apk add curl && curl -i http://' + str(api_response.spec.cluster_ip) + ':' + str(api_response.spec.ports[0].port)]
        print(exec_command)
    else:
        exec_command = [
            '/bin/sh',
            '-c',
            'apk add curl && curl -I http://' + str(api_response.spec.cluster_ip) + ':' + str(api_response.spec.ports[0].port)]
        print(exec_command)
    resp = stream(v1.connect_get_namespaced_pod_exec,
                  name,
                  'default',
                  command=exec_command,
                  stderr=True, stdin=False,
                  stdout=True, tty=False)

    if success_status in resp:
        print("Service %s is accessible. PASS" % (svc_name))
        if (check_string != "null"):
            print("Checking displayed message for updated string %s " % (check_string))
            if check_string in resp:
                print("Updated Message dispalyed %s. PASS " % (check_string))
            else:
                print("Updates Message not dispalyed. FAIL ")
    else:
        print("Service %s is not accessible. FAIL" % (svc_name))

