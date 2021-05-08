import os
import sys
import datetime
import numpy as np
import matplotlib.pyplot as plt
from utils import *

def get_from_log(log):
    dict_pull_to_count = {x:0 for x in range(1, 61)}
    with open(log, 'r') as fp:
        for line in fp:
            if '### Evade!' in line:
                line = line.strip()
                pull = int(line.split(' ')[-1][:-1])
                for idx in range(pull, 61):
                    dict_pull_to_count[idx] += 1
    print(dict_pull_to_count)
    list_rate = []
    for idx in range(1, 61):
        list_rate.append(dict_pull_to_count[idx]/2000)
    return list_rate

def main():
    av = sys.argv[1]

    y1_list_rate = get_from_log('/home/azureuser/code/MAB-malware/output_' + av + '/rewriter.log')

    x1 = np.array(range(len(y1_list_rate)))
    #x2 = np.array(range(len(y2_list_rate)))
    #x3 = np.array(range(len(y3_list_rate)))
    
    fig, ax = plt.subplots()
    ax.plot(x1, y1_list_rate, fillstyle='none', linewidth=1, color='red', label='MAB-malware')
    #ax.plot(x2, y2_list_rate, fillstyle='none', linewidth=1, color='red', label='TS')
    #ax.plot(x3, y3_list_rate, fillstyle='none', linewidth=1, color='red', label='TS')
    axes = plt.gca()
    axes.set_ylim([0, 1.05])
    axes.set_xlim([0, 67])
    
    plt.annotate(str(y1_list_rate[-1]), (60,y1_list_rate[-1]), color='red', fontsize=9)
    #plt.annotate(str(y2_list_rate[-1]), (60,y2_list_rate[-1]-3), color='red', textcoords="offset points", fontsize=9)
    #plt.annotate(str(y3_list_rate[-1]), (60,y3_list_rate[-1]-3), color='red', fontsize=9)

    plt.xlabel('total number of attempts', fontsize=12)
    plt.ylabel('evasion rate %', fontsize=12)
    ax.legend(loc='lower right', ncol=2)#, framealpha=0)
    fig.subplots_adjust(bottom=0.5)
    
    #plt.show()
    #matplotlib.pyplot.title(av);
    plt.savefig("evasion_rate_%s_MAB.pdf" %av)

if __name__ == '__main__':
    main()

