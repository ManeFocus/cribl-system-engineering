import os
import getpass
import requests
import json



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
def main():
    client_api_id, client_api_secret = grab_creds()
    if client_api_id and client_api_secret:
      cribl_auth_token = gen_cloud_token(client_api_id, client_api_secret)
      if cribl_auth_token:
        print('\n  Bearer Token Creation Successfully\n')
      else:
        print('\n  Bearer Token Creation FAILED!\n')

#----------------------------------------------------------------------
if __name__ == "__main__":
  main()

