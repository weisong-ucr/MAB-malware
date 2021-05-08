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
    REST_URL = "http://xxxxxxxx/tasks/create/file"
    SAMPLE_FILE = filepath

    with open(SAMPLE_FILE, "rb") as sample:
        files = {"file": (os.path.basename(filepath), sample)}
        r = requests.post(REST_URL, files=files)

    task_id = r.json()["task_id"][0]
    return task_id

def submit_single_sample(file):
    r = requests.post("http://xxxxxxxx/tasks/create/submit", files=[
	    ("files", open(file,'rb')),
	])
    submit_id = r.json()["submit_id"]
    task_ids = r.json()["task_ids"][0]
    errors = r.json()["errors"]
    return task_ids

def query_task_status():
    r = requests.get("http://xxxxxxx/tasks/list")
    tasks=r.json()['tasks']
    reports=[]
    for i in tasks:
        reports.append(i['status'])
    return reports

def submit_samples():
    filepath_list = get_file_info_from_path('data')
    i=1
    ids=[]
    for filepath in filepath_list[:]:
        ids.append(submit_single_sample_debug(filepath))
    print(ids)

def get_report_score(id):
    r=requests.get("http://xxxxxxxx/tasks/report/"+str(id))
    if r.status_code!=200:
        print("fail to get report! code:"+str(r.status_code))
        return 0
    score=r.json()['info']['score']
    return score

def delete_task(ids):
    print("delete:")
    for id in ids:
        print("task:"+str(id))
        r=requests.get("http://xxxxxxxx/tasks/delete/"+str(id))
        errors = r.json()
        print(r.json())

def submit_query_report(file):
    id=submit_single_sample(file)
    time.sleep(10)
    reports=query_task_status()
    i=0
    while i<len(reports):
        if reports[i]!='reported':
            time.sleep(5)
            reports=query_task_status()
        else:
            i+=1
    score=get_report_score(id)
    print(score)
    delete_task([id])

    return score>5.0