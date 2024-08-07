from flask import Flask,jsonify
from pymongo import MongoClient
import requests
import os
import time
import random
import threading
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
netwrk_kpi_data = []


def get_network_configuration_data():
  global netwrk_config_data
  import json
  # Opening JSON file
  f = open('../sample_data/network_configuration.json')
  # returns JSON object as dictonaty
  netwrk_config_data = json.load(f)
  print(netwrk_config_data)

def simulate_kpi_data():
  global netwrk_kpi_data
  global netwrk_config_data
  while True:
    carrier_len = len(netwrk_config_data['data'])
    netwrk_kpi_data = []
    for i in range(0,carrier_len):
       netwrk_kpi_data.append( {
          'band':netwrk_config_data['data'][i]["band"],
          'carrier_load':random.randint(1, 100)
       })
       
    print(netwrk_kpi_data)
    time.sleep(4)   
        

@app.route('/get_current_kpi_data', methods = ['GET'])
def get_kpi_data():
    global netwrk_kpi_data
    data = netwrk_kpi_data
  
    #print(data)
    return jsonify(data)


if __name__ == "__main__":

  get_network_configuration_data()
  
  th0 = threading.Thread(target=simulate_kpi_data,args=())
  th0.start()
  
  app.run(debug =False, host='0.0.0.0', port = 3330)