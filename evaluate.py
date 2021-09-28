#!/usr/bin/python3
from kubernetes import config
import time
import kubernetes.client
from kubernetes import client, config
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
configuration = kubernetes.client.Configuration()
config.load_kube_config()

def get_node_count():
    #Checks for the nodes in the k8s clsuter and returns the count
    config.load_kube_config()
    # Create an instance of the API class
    api_instance = core_v1_api.CoreV1Api()

    try:
        api_response = api_instance.list_node(pretty=True, watch=False)
        return(len(api_response.items))
    except ApiException as e:
        print("Exception when calling CoreV1Api->list_node: %s\n" % e)
        return(0)

def check_taint( pod_name, taint_variable, taint_value, taint_operator, taint_effect, i):
    found="0"
    for count in range(len(i.spec.tolerations)):
        if ((str(i.spec.tolerations[count].key) == taint_variable) and (str(i.spec.tolerations[count].value) == taint_value) and (str(i.spec.tolerations[count].operator) == taint_operator) and (str(i.spec.tolerations[count].effect) == taint_effect)):
            print("Pod %s is scheduled with proper tolerations. PASS"  % (pod_name))
            found="1"
    if (found == "0"):
            print("Pod %s is not scheduled with proper tolerations. FAIL"  % (pod_name))

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
    command_value=" ".join(i.spec.containers[0].command)
    if ( check_command in str(command_value)):
        print("Provided command %s match the command in pod %s. PASS" % (check_command, pod_name))
    else:
        print("Provided command %s doesn't match the command in pod %s. FAIL" % (check_command, pod_name))

def check_image_value(namespace, pod_name, check_image, i):
    if ( check_image in str((i.spec.containers[0].image))):
        print("Provided image %s match the command in pod %s. PASS" % (check_image, pod_name))
    else:
        print("Provided image %s doesn't match the command in pod %s. FAIL" % (check_image, pod_name))

def check_init_container(namespace, pod_name, i, init_container_name="null", init_container_command="null", init_container_image="null"):
    for count in range(len(i.spec.init_containers)):
        if (init_container_name != "null"):
            if (str(i.spec.init_containers[count].name) == init_container_name):
                print("Init_container_name is correct %s . PASS" % (init_container_name))
                if (init_container_command == "null" and init_container_image == "null"):
                    break
                else:
                    if (init_container_command != "null"):
                        #Remove additional spaces if any
                        init_container_command=' '.join(init_container_command.split())
                        command_check=i.spec.init_containers[count].command
                        command_check=' '.join(command_check)

                        if ((init_container_command.lower() in command_check.lower())):
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
                if ((api_response.items[count].status.desired_number_scheduled) == (get_node_count()) ):
                    print("Daemonset %s is running on all nodes. PASS" % (daemonset_name))
                else:
                    print("Daemonset %s is not running on all nodes. FAIL" % (daemonset_name))
    except ApiException as e:
        print("Exception when calling AppsV1Api->list_namespaced_daemon_set: %s\n" % e)
    if (found == "0"):
            print("Daemonset %s is not present. FAIL" % (daemonset_name))

def get_pod_status(namespace, pod_name, node_name="null", check_command="null", check_image="null", env_variable="null", env_value="null", init_container="null", init_container_name="null", init_container_command="null", init_container_image="null", taint_variable="null", taint_value="null", taint_operator="null", taint_effect="null", pod_user_id="null"):
    #Checks deployment is the specified namespace. Checks if the pod has init_container's with it's name. image and command which is specified
    config.load_kube_config()
    found="0"
    v1 = core_v1_api.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces(watch=False, pretty=True)
    for i in ret.items:
        if ((str(i.metadata.namespace) == namespace) and (pod_name in str(i.metadata.name))):
            print("Pod %s is present checking status. PASS" % (i.metadata.name))
            found="1"
            if (str((i.status.phase)) == "Running"):
                print("Pod %s is running. PASS" % (i.metadata.name))
                if (env_variable != "null" and env_value != "null"):
                    print("Checking environonment variables..")
                    check_env_variable(namespace, pod_name, env_variable, env_value, i)
                if (check_command != "null"):
                    check_command_string(namespace, pod_name, check_command, i)
                if (check_image != "null"):
                    check_image_value(namespace, pod_name, check_image, i)
                if (pod_user_id != "null"):
                    print("Checking pod user id...")
                    exec_command=['/bin/sh','-c','id | grep -ow ' + str(pod_user_id) ] 
                    resp = stream(v1.connect_get_namespaced_pod_exec,pod_name,namespace,command=exec_command,stderr=True, stdin=False, stdout=True, tty=False)
                    if ( resp == pod_user_id ):
                      print("Pod %s is running with userid %s. PASS" % (i.metadata.name, pod_user_id))
                    else:
                      print("Pod %s is running with userid %s. FAIL" % (i.metadata.name, pod_user_id)) 
                    
                if (taint_variable != "null" and taint_value != "null" and taint_operator != "null" and taint_effect != "null"):
                    check_taint( pod_name, taint_variable, taint_value, taint_operator, taint_effect, i)
                if (node_name != "null"):
                    if ( i.spec.node_name == node_name ):
                        print("Pod %s is running on provided node %s. PASS" % (i.metadata.name, i.spec.node_name))
                    else:
                        print("Pod %s is running on provided node %s. FAIL" % (i.metadata.name. node_name))
                if (init_container != "null"):
                    check_init_container(namespace, pod_name, i, init_container_name=init_container_name, init_container_command=init_container_command, init_container_image=init_container_image)
                    break
            else:
                print("Pod %s is not running. FAIL" % (i.metadata.name))
                exit(1)
    if (found == "0"):
            print("Pod %s is not present. FAIL" % (pod_name))

def get_service_status(namespace, svc_name, check_string="null"):
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
    else:
        exec_command = [
            '/bin/sh',
            '-c',
            'apk add curl && curl -I http://' + str(api_response.spec.cluster_ip) + ':' + str(api_response.spec.ports[0].port)]
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
            #Remove additional spaces if any
            check_string=' '.join(check_string.split())

            if check_string.lower() in resp.lower():
                print("Updated Message dispalyed %s. PASS " % (check_string))
            else:
                print("Updates Message not dispalyed. FAIL ")
    else:
        print("Service %s is not accessible. FAIL" % (svc_name))

def get_node_taint(node_name, taint_variable="null", taint_value="null", taint_effect="null"):
    #Checks node_name for the taint
    config.load_kube_config()
    found="0"
    v1 = core_v1_api.CoreV1Api()
    ret = v1.list_node(watch=False, pretty=True)
    for i in ret.items:
        if ((str(i.metadata.name) == node_name)):
            print("Node %s is present checking taints. PASS" % (i.metadata.name))
            found="1"
            if (taint_variable != "null" and taint_value != "null"):
                for count in range(len(i.spec.taints)):
                    if ((str(i.spec.taints[count].key) == taint_variable) and (str(i.spec.taints[count].value) == taint_value) and (str(i.spec.taints[count].effect) == taint_effect)):
                        print("Node %s has the following taint key: %s, value: %s, effect: %s. PASS" % (i.metadata.name, i.spec.taints[count].key, i.spec.taints[count].value, i.spec.taints[count].effect))
                        break
                    else:
                        print("Node %s doesn't have the following taint key: %s, value: %s, effect: %s. FAIL" % (i.metadata.name, i.spec.taints[count].key, i.spec.taints[count].value, i.spec.taints[count].effect))
    if (found == "0"):
            print("Node %s is not present. FAIL" % (node_name))

def get_node_labels(node_name, label_key="" , label_value=""):
    found="0"
    config.load_kube_config()
    v1 = core_v1_api.CoreV1Api()
    ret = v1.list_node(watch=False, pretty=True)
    for i in ret.items:
        if ((str(i.metadata.name) == node_name)):
            print("Node %s is present checking labels. PASS" % (i.metadata.name))
            if (str(i.metadata.labels[label_key]) == label_value ):
                print("Node %s has the following labels=%s with key=%s : PASS" % (i.metadata.name, label_key, label_value))
                found="1"
                break
            else:
                print("Node %s has the following labels=%s with key=%s : FAIL" % (i.metadata.name, label_key, label_value))

def get_sa(namespace, sa_name="null"):
    found="0"
    config.load_kube_config()
    v1 = core_v1_api.CoreV1Api()
    try:
        ret = v1.list_namespaced_service_account(namespace, pretty=True, watch=False)
        for i in ret.items:
            if ((str(i.metadata.name) == sa_name)):
                found="1"
                return True
        if (found == "0"):
                return False
    except ApiException as e:
        print("Exception when calling CoreV1Api->list_namespaced_service_account: %s\n" % e)

def check_cluster_role(role_name="null", resource="null", access_type="null"):
    found=0
    #configuration = kubernetes.client.Configuration()
    # Enter a context with an instance of the API kubernetes.client
    with kubernetes.client.ApiClient() as api_client:
    # Create an instance of the API class
        api_instance = kubernetes.client.RbacAuthorizationV1Api(api_client)
        try:
            api_response = api_instance.list_cluster_role(pretty=True, watch=False)
            for i in api_response.items:
                if ((str(i.metadata.name) == role_name)):
                    found="1"
                    #Checking the ClusterRole Configuration
                    for count in range(len(i.rules)):
                        if((resource in i.rules[count].resources) and (access_type == "read") and (set(i.rules[count].verbs) == set(['get','list','watch']))):
                            return True
                        else:
                            return False
            if (found == "0"):
                    return False
        except ApiException as e:
            print("Exception when calling RbacAuthorizationV1Api->list_cluster_role: %s\n" % e)


def check_cluster_role_binding(namespace="null", role_binding_name="null", role_name="null", sa_name="null"):
    found=0
    #configuration = kubernetes.client.Configuration()
    # Enter a context with an instance of the API kubernetes.client
    with kubernetes.client.ApiClient() as api_client:
    # Create an instance of the API class
        api_instance = kubernetes.client.RbacAuthorizationV1Api(api_client)
        try:
            api_response = api_instance.list_cluster_role_binding(pretty=True, watch=False)
            for i in api_response.items:
                if ((str(i.metadata.name) == role_binding_name)):
                    found="1"
                    #Checking the ClusterRoleBinding Configuration
                    if (str(i.role_ref.name) == role_name):
                        for count in range(len(i.subjects)):
                            if ((str(i.subjects[count].namespace) == namespace) and (str(i.subjects[count].name) == sa_name)):
                                return True
                            else:
                                return False
                    else:
                        return False
            if (found == "0"):
                    return False
        except ApiException as e:
            print("Exception when calling RbacAuthorizationV1Api->list_cluster_role_binding: %s\n" % e)


def check_cluster_role_sceanrio(namespace="null", role_binding_name="null", role_name="null", resource="null", access_type="null", sa_name="null"):
    if (get_sa(namespace=namespace, sa_name=sa_name)):
        print("Service Account %s is present. PASS" % (sa_name))
        if(check_cluster_role(role_name=role_name, resource=resource, access_type=access_type)):
            print("Cluster Role %s is present and has correct configuration. PASS" % (role_name))
            if(check_cluster_role_binding(namespace=namespace, role_binding_name=role_binding_name, role_name=role_name, sa_name=sa_name)):
                print("Cluster Role Binding %s is present has correct configuration. PASS" % (role_binding_name))
            else:
                print("Cluster Role Binding %s is not present has incorrect configuration. FAIL" % (role_binding_name))
        else:
            print("Cluster Role %s is not present or has incorrect configuration. FAIL" % (role_name))
    else:
        print("Service Account %s is not present. FAIL" % (sa_name))

def check_pv_status(pv_name, disk_name="null"):
    print("Checking pv status....")
    config.load_kube_config()
    found=0
    v1 = core_v1_api.CoreV1Api()
    ret = v1.list_persistent_volume(watch=False, pretty=True)
    for i in ret.items:
      if ( i.spec.gce_persistent_disk.pd_name == disk_name  and i.metadata.name == pv_name and i.status.phase == "Available" ):
        print("PV %s status check : PASS" % (i.metadata.name))
        found=1
        break;
    if ( found == 0 ):
      print("PV %s status check : FAIL" % (pv_name))

