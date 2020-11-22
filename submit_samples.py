# -*- coding:utf8 -*-
from __future__ import division
import os,sys,os.path
import time
import requests
import threading

def get_file_info_from_path(dir,topdown=True):
    dirinfo=[]
    for root, dirs, files in os.walk(dir, topdown):
        for name in files:
            dirinfo.append(os.path.join(root,name))
    return dirinfo

def submit_single_sample_debug(filepath):
    REST_URL = "http://192.168.4.31:8090/tasks/create/file"
    SAMPLE_FILE = filepath

    with open(SAMPLE_FILE, "rb") as sample:
        files = {"file": (os.path.basename(filepath), sample)}
        r = requests.post(REST_URL, files=files)

    task_id = r.json()["task_id"][0]
    return task_id

def submit_single_sample(filepath):
    r = requests.post("http://192.168.4.31:8090/tasks/create/submit", files=[
	    ("files", open(filepath, "rb")),
	])

    submit_id = r.json()["submit_id"]
    task_ids = r.json()["task_ids"][0]
    errors = r.json()["errors"]
    print('submit id: '+str(submit_id))
    print('task id: '+str(task_ids))
    print('error: '+str(errors))
    return task_ids

def query_task_status():
    r = requests.get("http://192.168.4.31:8090/tasks/list")
    tasks=r.json()['tasks']
    reports=[]
    for i in tasks:
        reports.append(i['status'])
    print(reports)
    return reports

def submit_samples():
    filepath_list = get_file_info_from_path('data')
    i=1
    ids=[]
    for filepath in filepath_list[:]:
        ids.append(submit_single_sample_debug(filepath))
    print(ids)

def get_report_score(id):
    r=requests.get("http://192.168.4.31:8090/tasks/report/"+str(id))
    score=r.json()['info']['score']
    return score

def delete_task(ids):
    print("delete:")
    for id in ids:
        print("task:"+str(id))
        r=requests.get("http://192.168.4.31:8090/tasks/delete/"+str(id))
        errors = r.json()
        print(r.json())

def submit_query_report(samples):
    ids=[]
    scores=[]
    for sample in samples:
        ids.append(submit_single_sample(sample))
    time.sleep(10)
    reports=query_task_status()
    i=0
    while i<len(reports):
        if reports[i]!='reported':
            time.sleep(3)
            reports=query_task_status()
        else:
            i+=1
    print(ids)
    for id in ids:
        scores.append(get_report_score(id))
    print(scores)
    # delete_task(ids)

samples=get_file_info_from_path('data/malware_3/')
print(samples)
exit()
submit_query_report(samples)
