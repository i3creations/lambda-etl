import pandas as pd
import requests

def send(data: list) -> dict:
  auth_url = 'https://gii-dev.ardentmc.net/dhsopsportal.api/api/auth/token'

  headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }

  creds = {
    'clientId': '',
    'clientSecret': ''
  }

  session = requests.session()
  session.headers.update(headers)
  ## TESTING ##
  session.verify = False
  ## TESTING ##

  token = session.post(
    auth_url,
    json = creds
  ).json()
  session.headers.update(
    {'Authorization': f'Bearer {token}'}
  )

  item_url = 'https://gii-dev.ardentmc.net/dhsopsportal.api/api/Item'

  responses = {}
  for record in data:
    response = session.post(
      item_url,
      json = record
    )

    responses[record['tenantItemID']] = (response.status_code, response.json())

  return responses