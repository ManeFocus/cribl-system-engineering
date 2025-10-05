import os
import getpass
import requests
import json
import time



#----------------------------------------------------------------------
def gen_cloud_token(client_id, client_secret):
  url = "https://login.cribl.cloud/oauth/token"
  headers = {"Content-type": "application/json"}
  data = { "grant_type": "client_credentials", "client_id": client_id,
    "client_secret": client_secret, "audience": "https://api.cribl.cloud" }
  try:
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
      return(response.json()["access_token"])
    else:
      return(False)
  except Exception as e:
    raise Exception("General exception raised while attempting to fetch cloud access token: %s" % str(e))

#----------------------------------------------------------------------
def grab_creds():
  client_api_id = input('Please enter your user Cribl API ID: ')
  client_api_secret = getpass.getpass('Enter Cribl API Secret: ')
  return(client_api_id, client_api_secret)

#----------------------------------------------------------------------
def grab_input(base_url, cribl_auth_token, worker_group, cribl_configuration_item):
  url = f"{base_url}/m/{worker_group}/system/inputs/{cribl_configuration_item}"
  headers = {"Content-type": "application/json", "Authorization": "Bearer " + cribl_auth_token}
  try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      data = response.json()
      return(data)
  except Exception as e:
    raise Exception(f"General exception raised while attempting to get {cribl_configuration_item} from Cribl: %s" % str(e))

#----------------------------------------------------------------------
def import_input(base_url, cribl_auth_token, worker_group, input_id, json_object):
  url = f"{base_url}/m/{worker_group}/system/inputs"
  print(url)
  headers = {"Content-type": "application/json", "Authorization": "Bearer " + cribl_auth_token}
  try:
    response = requests.post(url, headers=headers, json=json_object)
    if response.status_code == 200:
      data = response.json()
      return(True)
    else:
      return(False)
  except Exception as e:
    raise Exception(f"General exception raised while attempting to get {input_id} from Cribl: %s" % str(e))
    return (False)
 
#----------------------------------------------------------------------
def import_cribl_input(base_url, cribl_auth_token, worker_group, json_file):
  if not os.path.exists(json_file):
    print(f"FIle NOT found: {json_file}")
    return(False)
  
  with open(json_file, "r") as jfile:
    json_object = json.load(jfile)
  input_id = json_file.split('\\')[-1].split('/')[-1].split('.')[0]
  print(input_id)
  if import_input(base_url, cribl_auth_token, worker_group, input_id, json_object):
    print("Input Successfully Imported.")
    return (True)
  else:
    print("ERROR - Input Import FAILED!")
    return (False)

#----------------------------------------------------------------------
def commit_update(base_url, cribl_auth_token, worker_group, commit_msg):
  url = f"{base_url}/m/{worker_group}/version/commit"
  headers = { "Authorization": f"Bearer {cribl_auth_token}", "Content-Type": "application/json" }
  data = { "effective": True, "group": f"{worker_group}", "message": "commit worker group update" }
  try:
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
      data = response.json()
      version = data["items"][0]["commit"]
      return(version)
    else:
      return(None)
  except Exception as e:
    raise Exception("General exception raised while attempting to commit update: %s" % str(e))

#----------------------------------------------------------------------
def deploy_update(script_log, base_url, cribl_auth_token, worker_group, version):
  url = f"{base_url}/master/groups/{worker_group}/deploy"
  headers = { "Authorization": f"Bearer {cribl_auth_token}", "Content-Type": "application/json" }
  data = {"version": version}
  try:
    response = requests.patch(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
      data = response.json()
      print("Worker Group Deployment Successful.")
      return(True)
    else:
      return(False)
  except Exception as e:
    script_log.info("General exception raised while attempting to deploy update: %s" % str(e))
    raise Exception("General exception raised while attempting to deploy update: %s" % str(e))

#----------------------------------------------------------------------
def deploy_to_worker_group(script_log, base_url, cribl_auth_token, worker_group):
  version = commit_update(base_url, cribl_auth_token, worker_group, 'test msg')
  if version:
    script_log.info("Worker Group Commit Successful.")
    print("Worker Group Commit Successful.")
    if deploy_update(script_log, base_url, cribl_auth_token, worker_group, version):
      script_log.info("Worker Group Deployment Successful.")
      return(True)
    else:
      script_log.info("ERROR - Worker Group Deployment Failed!")
      print("ERROR - Worker Group Deployment Failed!")
      return(False)
  else:
    script_log.info("ERROR - Unable to gen version Worker Group Deployment Failed!")
    print("ERROR - Unable to gen version Worker Group Deployment Failed!")
    return(False)

#----------------------------------------------------------------------
def version_commit(script_log, base_url, cribl_auth_token):
  url = f"{base_url}/version/commit"
  headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {cribl_auth_token}'}
  data = {'message': 'commit message'}
  try:
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
      script_log.info("Version Successfully Commited.")
      print("Version Successfully Commited.")
      return (True)
    else:
      script_log.info("ERROR - version commit FAILED!")
      print("ERROR - version commit FAILED!")
      return (False)
  except Exception as e:
    script_log.info("General exception raised while attempting to commit version: %s" % str(e))
    raise Exception("General exception raised while attempting to commit version: %s" % str(e))

#----------------------------------------------------------------------
def import_cribl_cloud_input(cribl_auth_token):
  instance_url = input('Please enter your Cribl Instance URL: ')
  base_url = f"{instance_url}/api/v1"
  print(base_url)
  worker_group = input('Enter Cribl Worker Group: ')
  print(worker_group)
  json_file = input('Enter Input Json File: ')
  print(json_file)
  import_cribl_input(base_url, cribl_auth_token, worker_group, json_file)

#----------------------------------------------------------------------
def main():
    client_api_id, client_api_secret = grab_creds()
    if client_api_id and client_api_secret:
      cribl_auth_token = gen_cloud_token(client_api_id, client_api_secret)
      if cribl_auth_token:
        import_cribl_cloud_input(cribl_auth_token)
      else:
        print('\n  Bearer Token Creation FAILED!\n')

#----------------------------------------------------------------------
if __name__ == "__main__":
  main()

