import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
from utils import *

DATA_PATH = '/home/wei/code/adversarial_binary/data/final_2020/'
list_av_folder = [
                    'ember/',
                    'clamav/',
                    'avast',
                    'avira/',
                    'bitdefender/',
                    'kaspersky/',
                    ]

def get_from_log(log):
    list_rate = []
    with open(log, 'r') as fp:
        for line in fp:
            if 'skip' in line:
                line = line.strip()
                rate = float(line.split(' ')[-1].replace('%', ''))#/500*437
                if 'avast' in log and 'noTS' in log:
                    rate = rate * 30/31
                if 'avast' in log and 'TS_parent' in log:
                    rate = rate * 29/30
                if 'avira' in log and 'noTS' in log:
                    rate = rate * 45/47
                if 'avira' in log and 'TS_parent' in log:
                    rate = rate * 56/57
                if 'bitdefender' in log and 'noTS' in log:
                    rate = rate * 42/44
                if 'bitdefender' in log and 'TS_parent' in log:
                    rate = rate * 42/44
                if 'avast' in log and 'noTS' in log:
                    rate = rate * 29/33
                if 'avast' in log and 'TS_parent' in log:
                    rate = rate * 28/32
                rate = round(rate, 2)
                list_rate.append(rate)
    return list_rate

def main():
    list_av = [
            'avast',
            'avira',
            'bitdefender',
            'kaspersky',
            ]
    for av in list_av:
        y3_list_rate = get_from_log('/home/wei/code/adversarial_malware/output_100/output_' + av + '_100_noTS/rewriter.log')
        y0_list_rate = get_from_log('/home/wei/code/adversarial_malware/output_100/output_' + av + '_100_TS_parent/rewriter.log')
        x = np.array(range(len(y3_list_rate)))
        
        fig, ax = plt.subplots()
        l3, = ax.plot(x, y3_list_rate, fillstyle='none', linewidth=1, color='blue', label=av+' Random')
        l0, = ax.plot(x, y0_list_rate, fillstyle='none', linewidth=1, color='red', label=av+' TS micro minimize')
        axes = plt.gca()
        axes.set_ylim([0,60])
        axes.set_xlim([0,6600])
        
        plt.annotate(str(y3_list_rate[-1]), (6000,y3_list_rate[-1]), color='blue', textcoords="offset points", xytext=(15,0), ha='center', fontsize=9)
        plt.annotate(str(y0_list_rate[-1]), (6000,y0_list_rate[-1]), color='red', textcoords="offset points", xytext=(15,0), ha='center', fontsize=9)
        print(str(y0_list_rate[-1]))

        plt.xlabel('total number of attempts', fontsize=12)
        plt.ylabel('evasion rate %', fontsize=12)
        ax.legend(loc='lower right', ncol=2)#, framealpha=0)
        
        plt.show()

if __name__ == '__main__':
    main()

