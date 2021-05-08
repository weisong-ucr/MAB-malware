import os
import sys
import datetime
import numpy as np
import matplotlib.pyplot as plt
from utils import *

def get_from_log(log, r):
    list_rate = []
    with open(log, 'r') as fp:
        for line in fp:
            if 'skip' in line and 'start' in line:
                line = line.strip()
                skip = int(line.split(' ')[-2])
                holdout = int(line.split(' ')[-8].split('/')[1])
    total_sample = holdout - skip
    total_sample -= 1
    print(skip, holdout, total_sample)
    total_pull = 0
    with open(log, 'r') as fp:
        for line in fp:
            if 'action:' in line:
                total_pull += 1
    print(skip, holdout, total_sample, total_pull)
    success = 0
    with open(log, 'r') as fp:
        for line in fp:
            if 'success' in line:
                success += 1
            if 'action:' in line:
                rate = success / total_sample
                rate = round(rate * 100, 2)
                list_rate.append(rate)
                #total = int(line.split(' ')[4].split('/')[-1])
    #return list_rate + [rate]*(total-len(list_rate)), total
    return list_rate, total_pull

def main():
    av = sys.argv[1]
    print(av)
    r1 = 1
    r2 = 1
    r3 = 1

    y1_list_rate, _ = get_from_log('/home/wei/code/adversarial_malware/final_output/gym/%s/rewriter_random.log' %av, r1)
    y2_list_rate, total = get_from_log('/home/wei/code/adversarial_malware/final_output/gym/%s/rewriter_agent.log' %av, r2)
    #y3_list_rate, total = get_from_log('/home/wei/code/adversarial_malware/output_' + av + '_1000_TS_parent/rewriter.log', r3)

    x1 = np.array(range(len(y1_list_rate)))
    x2 = np.array(range(len(y2_list_rate)))
    #x3 = np.array(range(len(y3_list_rate)))
    
    fig, ax = plt.subplots()
    ax.plot(x1, y1_list_rate, fillstyle='none', linewidth=1, color='blue', label='Random')
    ax.plot(x2, y2_list_rate, fillstyle='none', linewidth=1, color='red', label='Agent')
    #ax.plot(x3, y3_list_rate, fillstyle='none', linewidth=1, color='green', label='TS (p)')
    axes = plt.gca()
    axes.set_ylim([0, 20])
    axes.set_xlim([0, total * 1.1])
    
    #plt.annotate(str(y1_list_rate[-1]), (total,y1_list_rate[-1]), color='blue', textcoords="offset points", xytext=(15,15), ha='center', fontsize=9)
    plt.annotate(str(y1_list_rate[-1]), (total*1.05, y1_list_rate[-1]*0.95), color='blue', ha='center', fontsize=9)
    #plt.annotate(str(y2_list_rate[-1]), (total,y2_list_rate[-1]), color='red', textcoords="offset points", xytext=(15,0), ha='center', fontsize=9)
    plt.annotate(str(y2_list_rate[-1]), (total*1.05, y2_list_rate[-1]*1.05), color='red', ha='center', fontsize=9)
    #plt.annotate(str(y3_list_rate[-1]), (total,y3_list_rate[-1]+1), color='green', textcoords="offset points", xytext=(15,0), ha='center', fontsize=9)

    plt.xlabel('total number of attempts', fontsize=12)
    plt.ylabel('evasion rate %', fontsize=12)
    ax.legend(loc='upper left', ncol=2)#, framealpha=0)
    fig.subplots_adjust(bottom=0.5)
    
    #plt.show()
    #matplotlib.pyplot.title(av_to_title(av));
    plt.savefig("/home/wei/Share/evasion_rate_of_attempts_%s.pdf" %av)

def av_to_title(av):
    if av == 'ember_2020':
        return 'EMBER (T&H)'
    elif av == 'ember_2019':
        return 'EMBER'
    elif av == 'malconv':
        return 'MalConv'
if __name__ == '__main__':
    main()

