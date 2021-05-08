import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
from utils import *

dict_av_to_path = {
        'ember_2019': '/home/wei/code/adversarial_malware/final_output/our/ember_2019/output_ember_2019_holdout_TS_parent/mic_minimizer_evasive/',
        'ember_2020': '/home/wei/code/adversarial_malware/final_output/our/ember_2020/output_ember_2020_holdout_TS_parent/mic_minimizer_evasive_scan/',
        'malconv': '/home/wei/code/adversarial_malware/final_output/our/malconv/output_malconv_holdout_TS_parent/mic_minimizer_evasive/',
        'avast': '/home/wei/code/adversarial_malware/final_output/our/avast/output_avast_1000_TS_parent/mic_minimizer_evasive/',
        'bitdefender': '/home/wei/code/adversarial_malware/final_output/our/bitdefender/output_bitdefender_1000_TS_parent/mic_minimizer_evasive_TS_parent_scan/'
        }


def action_rename(action_name):
    action_name = action_name.replace('O1', 'OA1')
    action_name = action_name.replace('S1', 'SA1')
    action_name = action_name.replace('R1', 'SR1')
    action_name = action_name.replace('P1', 'SP1')
    action_name = action_name.replace('CP', 'SP1')
    return action_name

dict_av_to_min = {
        'ember_2019':1,
        'ember_2020':1,
        'malconv':0,
        'clamav':0,
        'avast':1,
        'avira':1,
        'bitdefender':3,
        'kaspersky':0#1,
        }

def main():
    for av, path in dict_av_to_path.items():
        dict_action_list_to_count = {}
        print('='*40)
        print(av)
        list_action = []
        print(path)
        list_exe = os.listdir(path)
        print(len(list_exe))
        for exe in list_exe:
            list_action = [action_rename(x) for x in exe.split('.') if len(x) == 2 or (len(x) == 3 and x != 'exe')]
            list_action.sort()
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
        fig.subplots_adjust(bottom=0.5)
        #plt.show()
        plt.savefig('/home/wei/Share/combination_%s.pdf' %av.lower())

if __name__ == '__main__':
    main()
