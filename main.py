from flask import Flask
from pymongo import MongoClient
import requests
import os
import time
import threading
import json
from dotenv import load_dotenv

import logging
import warnings
warnings.filterwarnings("ignore")
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

os.environ['TZ'] = 'Asia/Calcutta'
time.tzset()

load_dotenv()
app = Flask(__name__)


global netwrk_config_data
netwrk_config_data = []

#mongoDBClient = MongoClient(os.getenv('SMO_MONGO_ADDRESS'),username=os.getenv('SMO_MONGODB_USERNAME'),password=os.getenv('SMO_MONGODB_PASSWORD'))
#db = mongoDBClient[os.getenv('SMO_MONGO_DBNAME')]


def get_network_configuration_data():
  global netwrk_config_data
  import json
  # Opening JSON file
  f = open('./sample_data/network_configuration.json')
  # returns JSON object as dictonaty
  netwrk_config_data = json.load(f)
  print(netwrk_config_data)


def create_and_deploy_policy(type,band,handover_threshold):
   global netwrk_config_data
   selected_band_data = [x for x in netwrk_config_data['data'] if x['band'] == band]
   
   if(type=="carrier_load"):
      policy_id = 20021
      policy_payload = { 
              "name" : "tsapolicy", 
              "description" : "Layer Optimisation Policy by balancing carrier load", 
              "policy_type_id" : policy_id, 
              "create_schema" : { 
                "$schema" : "http://json-schema.org/draft-07/schema#", 
                "type" : "object", 
                "properties" : 
                  { 
                    "carrierId": {
                      "type": "string",
                      "description":"source carrier",
                    },
                    "handover_threshold":{
                      "type": "integer",
                      "description":"Percentage threshold to be handovered"
                    }
                  }, 
                "downstream_schema":{
                      "type":"object",
                      "additionalProperties":false,
                      "required":["policy_type_id", "policy_instance_id", "operation"],
                      "properties":{
                          "policy_type_id":{
                              "type":"integer",
                              "enum":[21000]
                          },
                          "policy_instance_id":{
                              "type":"string"
                          },
                          "operation":{
                              "type":"string",
                              "enum":["CREATE", "UPDATE", "DELETE"]
                          },
                          "payload":{
                              "$schema":"http://json-schema.org/draft-07/schema#",
                              "type":"object",
                              "additionalProperties":false,
                              "required":["class"],
                              "properties":{
                                "carrierId": {
                                    "type": "string",
                                    "description":"source carrier",
                                  },
                                  "handover_threshold":{
                                    "type": "integer",
                                    "description":"Percentage threshold to be handovered"
                                  }
                              }
                          }
                        }
                    },
                    "notify_schema":{
                      "type":"object",
                      "additionalProperties":false,
                      "required":["policy_type_id", "policy_instance_id", "handler_id", "status"],
                      "properties":{
                        "policy_type_id":{
                          "type":"integer",
                          "enum":[21000]
                        },
                        "policy_instance_id":{
                          "type":"string"
                        },
                        "handler_id":{
                          "type":"string"
                        },
                        "status":{
                          "type":"string",
                          "enum":["OK", "ERROR", "DELETED"]
                        }
                      }
                },
                "additionalProperties" : false 
              } 
        }
      
      # create policy
      headers = {'Content-Type': 'application/yang-data+json'}
      policy_create_url = "http://10.99.218.31:10000/A1-P/v2/policytypes/"+policy_id
      r = requests.put(policy_create_url, headers=headers, verify=False, data=policy_payload)

      #create policy instance
      policy_instance_payload ={
        "carrierId": band,
        "handover_threshold": handover_threshold
      }
      policy_instance_url = policy_create_url+"policies/tsapolicy145"
      headers = {'Content-Type': 'application/yang-data+json'}
      r = requests.put(policy_instance_url, headers=headers, verify=False, data=policy_instance_payload)


    

def validate_carrier_load():
  global netwrk_config_data
  while True:
    url = "http://localhost:3330/get_current_kpi_data"
    headers = {'Content-Type': 'application/yang-data+json'}
    r = requests.get(url, headers=headers, verify=False)
    kpi_data = json.loads(r.text)
    print(kpi_data)
    for each_band in kpi_data:
      selected_band_data = [x for x in netwrk_config_data['data'] if x['band'] == each_band['band']]
      print(selected_band_data)
      if(each_band["carrier_load"]>selected_band_data[0]["max_carrier_load"]):
        print("Load exceeded ",each_band["band"],each_band["carrier_load"])
        create_and_deploy_policy("carrier_load",each_band["band"],(each_band["carrier_load"]-selected_band_data[0]["max_carrier_load"]))
    time.sleep(10)

if __name__ == "__main__":

  get_network_configuration_data()

  t0 = threading.Thread(target=validate_carrier_load,args=())
  t0.start()
  


  app.run(debug =False, host='0.0.0.0', port = 55550)