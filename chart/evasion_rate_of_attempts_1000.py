import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
from utils import *

def get_from_log(log, r):
    list_rate = []
    with open(log, 'r') as fp:
        for line in fp:
            if 'skip' in line:
                line = line.strip()
                rate = float(line.split(' ')[-1].replace('%', ''))#/500*437
                rate = round(rate * r, 2)
                list_rate.append(rate)
    return list_rate

def main():
    av = 'avast'
    r1 = 1#(157+154)/(158+158)
    r2 = 1#(152+155)/(158+159)
    av = 'bitdefender'
    r1 = 1#390/403
    r2 = 1#464/483
    #av = 'ember'
    y1_list_rate = get_from_log('/home/wei/code/adversarial_malware/output_' + av + '_1000_noTS/rewriter.log', r1)
    y2_list_rate = get_from_log('/home/wei/code/adversarial_malware/output_' + av + '_1000_TS_parent/rewriter.log', r2)
    x1 = np.array(range(len(y1_list_rate)))
    x2 = np.array(range(len(y2_list_rate)))
    
    fig, ax = plt.subplots()
    ax.plot(x1, y1_list_rate, fillstyle='none', linewidth=1, color='blue', label=av+' Random')
    ax.plot(x2, y2_list_rate, fillstyle='none', linewidth=1, color='red', label=av+' TS micro minimize')
    axes = plt.gca()
    axes.set_ylim([0,60])
    axes.set_xlim([0,66000])
    
    plt.annotate(str(y1_list_rate[-1]), (60000,y1_list_rate[-1]), color='blue', textcoords="offset points", xytext=(15,0), ha='center', fontsize=9)
    plt.annotate(str(y2_list_rate[-1]), (60000,y2_list_rate[-1]), color='red', textcoords="offset points", xytext=(15,0), ha='center', fontsize=9)

    plt.xlabel('total number of attempts', fontsize=12)
    plt.ylabel('evasion rate %', fontsize=12)
    ax.legend(loc='lower right', ncol=2)#, framealpha=0)
    
    #plt.show()
    plt.savefig("evasion_rate_of_attempts_%s.pdf" %av)

if __name__ == '__main__':
    main()

