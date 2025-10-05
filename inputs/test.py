Import 
import os.path
import sys
from dotenv import load_dotenv
import os
import getpass
import requests
import json
import logging
import shutil
import time



log_directory = 'log/'

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
  load_dotenv()
  client_api_id = os.environ.get("cribl_api_id")
  client_api_secret = os.environ.get("cribl_api_secret")
  if not client_api_id:
    client_api_id = getpass.getpass('\nEnter Cribl Client ID: ')
  if not client_api_secret:
    client_api_secret = getpass.getpass('Enter Cribl Client Secret: ')
  return(client_api_id, client_api_secret)

#----------------------------------------------------------------------
def directory_exists(directory_path):
  if not os.path.exists(directory_path):
    os.makedirs(directory_path)
  if os.path.exists(directory_path):
    return(True)
  else:
    return(False)

# ----------------------------------------------------------------------
def script_logger(script_name, log_directory):
  logger = logging.getLogger(script_name.split('.')[0])
  logger.setLevel(logging.DEBUG)
  fh = logging.FileHandler(log_directory + script_name.replace('.py', '') + '.log')
  fh.setLevel(logging.INFO)
  formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
  fh.setFormatter(formatter)
  logger.addHandler(fh)
  return (logger)

#----------------------------------------------------------------------
def set_script_logger(log_directory, script_name):
  if directory_exists(log_directory):
    script_log = script_logger(script_name, log_directory)
    return(script_log)
  else:
    print(f"ERROR - Unable to create log directory: {log_directory}")
    return(False)

#----------------------------------------------------------------------
def grab_configuration_items(script_log, base_url, cribl_auth_token, cribl_ci, ci_prefix):
  url = base_url + f"{ci_prefix}{cribl_ci}"
  headers = {"Content-type": "application/json", "Authorization": "Bearer " + cribl_auth_token}
  try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      data = response.json()
      return(data)
  except Exception as e:
    raise Exception(f"General exception raised while attempting to get {cribl_ci} from Cribl: %s" % str(e))

#----------------------------------------------------------------------
def list_configuration_items(data, search_fields):
  ci_list = []
  for i, result in enumerate(data):
    ci_fields = []
    for value in search_fields:
      ci_fields.append(result[value])
    ci_list.append(":".join(map(str,ci_fields)))
  return(sorted(set(ci_list)))

#----------------------------------------------------------------------
def search_for_configuration_items(json_list, field_paths):
  results = []
  for item in json_list:
    item_result = {}
    for path in field_paths:
      keys = path.split(".")
      value = item
      try:
        for key in keys:
          value = value[key]
        item_result[path] = value
      except (KeyError, TypeError):
        item_result[path] = "Field not found"
    results.append(item_result)
  return results

# ----------------------------------------------------------------------
def filter_configuration_items(items, exclude_values):
  def should_exclude(item):
    for exclude in exclude_values:
      key, value = exclude.split(":")
      item_value = str(item.get(key))
      if item_value == value:
        return True
    return False
  return [item for item in items if not should_exclude(item)]

#----------------------------------------------------------------------
def grab_worker_groups(script_log, base_url, cribl_auth_token):
  worker_groups_json = grab_configuration_items(script_log, base_url, cribl_auth_token, "groups", "/master/")
  search_fields = ["name", "job.title", "job.manager", "location", "job.department"]
  search_fields = ["id"]
  exclude_list = ["id:default","id:defaultHybrid","id:default_fleet","id:default_search"]
  worker_groups_found = filter_configuration_items(search_for_configuration_items(worker_groups_json["items"], search_fields),
  exclude_list)
  worker_group_list = list_configuration_items(worker_groups_found, search_fields)
  return(worker_group_list)

#----------------------------------------------------------------------
def write_json_file(ci_id, target_directory, data):
  json_file = target_directory + '/' + ci_id + '.json'
  with open(json_file, 'w') as jfile:
    json.dump(data, jfile, indent=4)
  print(f"  Data has been written to {json_file}")

#----------------------------------------------------------------------
def grab_value(textID):
  load_dotenv()
  text_output = os.environ.get(textID)
  if not text_output:
    text_output = os.getenv(textID)
  if not text_output:
    text_output = getpass.getpass('Enter Cribl Client Secret: ')
  return(text_output)

#----------------------------------------------------------------------
def import_configuration_item(script_log, base_url, cribl_auth_token, ci_prefix, cribl_ci, json_object):
  url = base_url + f"{ci_prefix}{cribl_ci}"
  headers = {"Content-type": "application/json", "Authorization": "Bearer " + cribl_auth_token}
  try:
    response = requests.post(url, headers=headers, json=json_object)
    if response.status_code == 200:
      data = response.json()
      return(True)
    else:
      return(False)
  except Exception as e:
    raise Exception(f"General exception raised while attempting to get {cribl_ci} from Cribl: %s" % str(e))
    return (False)

#----------------------------------------------------------------------
def import_output(script_log, base_url, cribl_auth_token, worker_group, json_file):
  with open(json_file, "r") as jfile:
    json_object = json.load(jfile)
  if import_configuration_item(script_log, base_url, cribl_auth_token, f"/m/{worker_group}/system/", "outputs", json_object):
    script_log.info("Output Successfully Imported.")
    print("Output Successfully Imported.")
    return (True)
  else:
    script_log.info("ERROR - Output Import FAILED!")
    print("ERROR - Output Import FAILED!")
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
def recent_action(script_log, base_url, cribl_auth_token):
  url = "https://production-jovial-semple-q5k1z2x.cribl.cloud/api/v1/ui/recentActions.group"
  headers = {
    "Authorization": "Bearer " + cribl_auth_token,
    "Content-Type": "application/json"
  }
  data = {
    "op": "push-recent",
    "value": [
        {
            "action": "update",
            "entityId": "bullpen",
            "timestamp": 1756938701909,
            "context": "stream",
            "type": "group",
            "key": "-bullpen",
            "author": "Robert DeLeon Jr-2a"
        }
    ]
  }

  response = requests.patch(url, headers=headers, json=data)

  print(response.status_code)
  print(response.text)

#----------------------------------------------------------------------
def grab_worker_groups_cis(script_log, base_url, cribl_auth_token, worker_group, output_json):
  worker_groups = grab_worker_groups(script_log, base_url, cribl_auth_token)
  if worker_group in worker_groups:
    if import_output(script_log, base_url, cribl_auth_token, worker_group, output_json):
      if deploy_to_worker_group(script_log, base_url, cribl_auth_token, worker_group):
        version_commit(script_log, base_url, cribl_auth_token)
#        recent_action(script_log, base_url, cribl_auth_token)
  else:
    print("Worker Group NOT Found")

#----------------------------------------------------------------------
def import_worker_group_output(worker_group, output_json):
  base_url = 'https://<url>/api/v1'
  script_log = set_script_logger(log_directory, sys.argv[0].split('/')[-1])
  if script_log:
    client_api_id, client_api_secret = grab_creds()
    if client_api_id and client_api_secret:
      cribl_auth_token = gen_cloud_token(client_api_id, client_api_secret)
      if cribl_auth_token:
        grab_worker_groups_cis(script_log, base_url, cribl_auth_token, worker_group, output_json)
  else:
    print("ERROR - Unable to setup script logging!")
    return 1

#----------------------------------------------------------------------
def main():
  if len(sys.argv) != 3:
    print('\nusage: %s <worker group> <output json file>\n' % sys.argv[0])
    return 1
  else:
    import_worker_group_output(sys.argv[1], sys.argv[2])

#----------------------------------------------------------------------
if __name__ == "__main__":
  main()
