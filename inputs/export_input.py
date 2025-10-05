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
def write_json_file(input_id, target_directory, json_data):
  json_file = target_directory + '/' + input_id + '.json'
  with open(json_file, 'w') as jfile:
    json.dump(json_data, jfile, indent=4)
  print(f"  Data has been written to {json_file}")

#----------------------------------------------------------------------
def export_input(worker_group, input_id, json_data):
  TS = time.strftime('%Y%m%d%H%M%S')
  target_directory = f"backup/{TS}/{worker_group}/inputs"
  os.makedirs(target_directory)
  write_json_file(input_id, target_directory, json_data)

#----------------------------------------------------------------------
def export_cribl_input(cribl_auth_token):
  instance_url = input('Please enter your Cribl Instance URL: ')
  base_url = f"{instance_url}/api/v1"
  print(base_url)
  worker_group = input('Enter Cribl Worker Group: ')
  print(worker_group)
  input_id = input('Enter Worker Group Input: ')
  print(input_id)
  input_json = grab_input(base_url, cribl_auth_token, worker_group, input_id)
  export_input(worker_group, input_id, input_json["items"][0])

#----------------------------------------------------------------------
def main():
    client_api_id, client_api_secret = grab_creds()
    if client_api_id and client_api_secret:
      cribl_auth_token = gen_cloud_token(client_api_id, client_api_secret)
      if cribl_auth_token:
        export_cribl_input(cribl_auth_token)
      else:
        print('\n  Bearer Token Creation FAILED!\n')

#----------------------------------------------------------------------
if __name__ == "__main__":
  main()

