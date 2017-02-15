#!/usr/bin/env python

from __future__ import print_function
import subprocess
import requests
import signal
import time
import json
import os
import test_config

pobj = subprocess.Popen(["python", "../lambda_function.py", "-s"], 
        env={"TABLE_NAME": test_config.TABLE_NAME, "AWS_PROFILE": test_config.AWS_PROFILE})
time.sleep(6)

response = requests.post("http://127.0.0.1:5000/", json=json.loads(open('test.json').read()))
print(str(response.status_code))
print(response.text)
os.kill(pobj.pid, signal.SIGTERM) #or signal.SIGKILL 
