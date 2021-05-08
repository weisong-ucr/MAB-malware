import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
from feature_contribution import *

DATA_PATH = '/home/wei/code/adversarial_binary/data/final_2020/'
DATA_PATH = '/media/wei/Backup/final_output/our/'
list_av = [
            #'ember',
            #'clamav',
            'avast',
            'avira',
            'bitdefender',
            #'kaspersky',
            ]

def action_rename(action_name):
    action_name = action_name.replace('O1', 'OA1')
    action_name = action_name.replace('S1', 'SA1')
    action_name = action_name.replace('R1', 'SR1')
    action_name = action_name.replace('P1', 'SP1')
    action_name = action_name.replace('CP', 'SP1')
    action_name = action_name.replace('RS', 'RC')
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
    for av in list_av:
        dict_action_list_to_count = {}
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
                #list_action = list(set([dict_action_to_feature[action_rename(x)] for x in exe.split('.') if len(x) == 2]))
                list_action = [action_rename(x) for x in exe.split('.') if len(x) == 2]
                list_action.sort()
                if 'F10' in list_action:
                    list_action.remove('F10')
                    list_action.append('F10')
                #if len(list_action) > 3:
                #    continue
                list_action = str(list_action).replace('\'', '').replace(' ', '')
                if list_action not in dict_action_list_to_count:
                    dict_action_list_to_count[list_action] = 0
                dict_action_list_to_count[list_action] += 1

        #listofTuples = sorted(dict_action_list_to_count.items(), key=lambda x:(len(x[0]), -x[1]))
        dict_larger = {}
        total_count = 0
        for k,v in dict_action_list_to_count.items():
            total_count += v
        for k,v in dict_action_list_to_count.items():
            if v > dict_av_to_min[av]:       # debug!
                dict_larger[k] = v/total_count * 100
        listofTuples = sorted(dict_larger.items(), key=lambda x:(-x[1]))

        y = []
        label = []
        for elem in listofTuples :
            print(elem[0], elem[1] )
            y.append(elem[1])
            label.append(elem[0])
        x = np.arange(len(y))
        fig, ax = plt.subplots()

        #plt.xlabel('action combinations', fontsize=12)
        #plt.ylabel('# evasive sample', fontsize=14)
        plt.ylabel('percentage %', fontsize=14)

        plt.bar(x, y, color='silver')
        #plt.bar(x, y, color='white', edgecolor='gray')
        #plt.xticks(x, label, rotation=90, fontsize=14)
        plt.xticks(x, label, rotation=90)
        fig.subplots_adjust(bottom=0.6)
        #plt.show()
        plt.savefig('/home/wei/action_combination_%s.pdf' %get_display_name(av).lower())

if __name__ == '__main__':
    main()
