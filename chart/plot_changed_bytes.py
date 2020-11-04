import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
from utils import *

dict_av_to_path = {
        'ember_2019': '/home/wei/code/adversarial_malware/final_output/our/ember_2019/output_ember_2019_holdout_TS_parent/mic_minimizer_evasive/',
        'ember_2020': '/home/wei/code/adversarial_malware/final_output/our/ember_2020/output_ember_2020_holdout_TS_parent/mic_minimizer_evasive_scan/',
        'malconv': '/home/wei/code/adversarial_malware/final_output/our/malconv/output_malconv_holdout_TS_parent/mic_minimizer_evasive/',
        'clamav': '/home/wei/code/adversarial_malware/final_output/our/clamav/output_clamav_1000_TS_parent/mic_minimizer_evasive/',
        'avast': '/home/wei/code/adversarial_malware/final_output/our/avast/output_avast_1000_TS_parent/mic_minimizer_evasive/',
        'avira': '/home/wei/code/adversarial_malware/final_output/our/avira/output_avira_1000_TS_parent_91/mic_minimizer_evasive/',
        'bitdefender': '/home/wei/code/adversarial_malware/final_output/our/bitdefender/output_bitdefender_1000_TS_parent/mic_minimizer_evasive_TS_parent_scan/'
        }

def main():
    for av, path in dict_av_to_path.items():
        print('='*40)
        print(av)
        list_diff_count = []
        less_100_evade_count = 0
        less_1_evade_count = 0
        less_1_dict_action_to_exe = {}
        print(path)
        list_exe = os.listdir(path)
        print(len(list_exe))
        for exe in list_exe:
            sha256 = exe.split('.')[0]
            list_action = [x for x in exe.split('.') if len(x) == 2 or (len(x) == 3 and x != 'exe')]
            #print(list_action)
            diff_count = 0
            exe_path_ori = '/home/wei/code/adversarial_malware/data/malware_1000/' + sha256
            exe_path = path + exe
            fp1 = open(exe_path_ori, 'rb')
            fp2 = open(exe_path, 'rb')
            content1 = fp1.read()
            content2 = fp2.read()
            for idx, byte in enumerate(content2):
                if idx >= len(content1) or byte != content1[idx]:
                    diff_count += 1
            fp1.close()
            fp2.close()
            #if diff_count < 100:
            if diff_count < 10:
                print(exe, diff_count)
            if diff_count < 100:
                less_100_evade_count += 1
            if diff_count == 1:
                less_1_evade_count += 1
                action = list_action[0]
                if action not in less_1_dict_action_to_exe:
                    less_1_dict_action_to_exe[action] = []
                less_1_dict_action_to_exe[action].append(exe)
            list_diff_count.append(diff_count)
        list_diff_count.sort()
        print(list_diff_count)
        #with open('%s' %av, 'w') as fp:
        #    for diff in list_diff_count:
        #        fp.write('%d\n' %diff)
        print('less_100_evade_count:', less_100_evade_count)
        print('less_1_evade_count:', less_1_evade_count)
        for action, list_exe in less_1_dict_action_to_exe.items():
            print(action, len(list_exe), list_exe)
        plot(list_diff_count, av)

def plot(y,av):
    x = np.arange(len(y))
    fig, ax = plt.subplots()
    ax.set_yscale('log')

    plt.xlabel('evasive samples %d - %d' %(1, len(y)), fontsize=12)
    plt.ylabel('change byte amount', fontsize=12)

    plt.bar(x, y, color='silver')
    plt.tick_params(
    axis='x',          # changes apply to the x-axis
    which='both',      # both major and minor ticks are affected
    bottom=False,      # ticks along the bottom edge are off
    top=False,         # ticks along the top edge are off
    labelbottom=False) # labels along the bottom edge are off
    fig.subplots_adjust(bottom=0.5)
    #plt.show()
    plt.savefig('/home/wei/Share/byte_%s.pdf' %av.lower())

if __name__ == '__main__':
    main()
