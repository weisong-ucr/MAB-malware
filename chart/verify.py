import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
import clamd
from feature_contribution import *

DATA_PATH = '/home/wei/code/adversarial_binary/data/final_2020/'

def action_rename(action_name):
    action_name = action_name.replace('O1', 'OA1')
    action_name = action_name.replace('S1', 'SA1')
    action_name = action_name.replace('R1', 'SR1')
    action_name = action_name.replace('P1', 'SP1')
    action_name = action_name.replace('CP', 'SP1')
    return action_name

dict_av_to_min = {
        'ember':1,
        'clamav':0,
        'avast':1,
        'avira':1,
        'bitdefender':2,
        'kaspersky':0#1,
        }

def main():
    av = 'clamav'
    dict_action_list_to_count = {}
    dict_action_list_to_exe_list = {}
    print('='*40)
    print(av)
    av_path = DATA_PATH + av + '/'
    list_action = []
    for data_folder in os.listdir(av_path):
        if '2020' not in data_folder:
            continue
        print(data_folder)
        if av == 'avast':
            if '_0' not in data_folder:
                continue
        print(data_folder)
        feature_folder = [x for x in os.listdir(av_path + data_folder) if x.endswith('func_feature')]
        #feature_folder = [x for x in os.listdir(av_path + data_folder) if x.endswith('func')]
        if len(feature_folder) == 0:
            print('!!!!!!!!!!! Need sandbox !!!!!!!!!')
            exit()
            feature_folder = [x for x in os.listdir(av_path + data_folder) if x.endswith('scan')]
        path = av_path + data_folder + '/' + feature_folder[0] + '/'
        print(path)
        list_exe = os.listdir(path)
        print(len(list_exe))
        for exe in list_exe:
            list_action = [action_rename(x) for x in exe.split('.') if len(x) == 2]
            list_action.sort()
            #if len(list_action) > 3:
            #    continue
            list_action = str(list_action).replace('\'', '').replace(' ', '')
            if list_action not in dict_action_list_to_count:
                dict_action_list_to_count[list_action] = 0
            if list_action not in dict_action_list_to_exe_list:
                dict_action_list_to_exe_list[list_action] = []
            dict_action_list_to_count[list_action] += 1
            dict_action_list_to_exe_list[list_action].append(exe)

    #listofTuples = sorted(dict_action_list_to_count.items(), key=lambda x:(len(x[0]), -x[1]))
    model = clamd.ClamdUnixSocket()
    dict_larger = {}
    for k,v in dict_action_list_to_count.items():
        print(k, v)
    for k,v in dict_action_list_to_exe_list.items():
        print('=======', k, '=======')
        for exe in v:
            sha256 = exe.split('.')[0]
            print(sha256)
            res = model.scan('/home/wei/0/malware/%s' %sha256)
            name = str(res).split('\'')[5]
            print(name)
            print('sigtool --find-sigs %s' %name)
            os.system('sigtool --find-sigs %s' %name)


if __name__ == '__main__':
    main()
