import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
from utils import *
from collections import defaultdict

def get_from_log(log, r):
    list_rate = []
    with open(log, 'r') as fp:
        for line in fp:
            if 'skip' in line:
                line = line.strip()
                rate = float(line.split(' ')[-1].replace('%', ''))
                rate = round(rate * r, 2)
                list_rate.append(rate)
                total = int(line.split(' ')[4].split('/')[-1])
    list_rate += [rate]*(total-len(list_rate))
    list_rate = list_rate[::123]
    print(list_rate)
    print(len(list_rate))
    #return list_rate + [rate]*(total-len(list_rate)), None
    return [x/100 for x in list_rate][:60], None

def get_from_log2(log, r):
    list_rate = []
    dict_time_to_succ = {}#defaultdict(int)
    action_count = 0
    cur_succ = cur_fail = 0
    c = 0
    with open(log, 'r') as fp:
        for line in fp:
            if ' === ' in line:
                action_count += 1
            if 'RESULT' in line:
                line = line.strip()
                total = int(line.split()[5])
                succ = int(line.split()[7][:-1])
                fail = int(line.split()[9])
                if succ == cur_succ + 1:
                    cur_succ = succ
                    c += 1
                    #print(action_count, total, succ, fail)
                    if action_count not in dict_time_to_succ:
                        dict_time_to_succ[action_count] = 1
                    else:
                        dict_time_to_succ[action_count] += 1
                elif fail == cur_fail + 1:
                    cur_fail = fail
                    #print(action_count, total, succ, fail)
                action_count = 0
                #print(dict_time_to_succ)
    c = 0
    output = []
    for i in range(max(dict_time_to_succ)+1):
        if i in dict_time_to_succ:
            c += dict_time_to_succ[i]
        #print(i, c)
        output.append(c/total)
    print(output[:60])
    return output[:60], 60#max(dict_time_to_succ)

def main():
    av = 'malconv'
    r1 = 1
    r2 = 1
    r3 = 1

    #y1_list_rate, total = get_from_log2('/home/wei/Desktop/evasive_MCTS_malware200/rewriter.log', r1)
    y1_list_rate, total = get_from_log2('/home/wei/code/MAB-malware/final_output/evasive_GP_malware200_malconv/rewriter.log', r1)
    #y2_list_rate, _ = get_from_log('/media/wei/Backup/final_output/our/ember_2019/output_ember_2019_holdout_TS_parent/rewriter.log', r2)
    y2_list_rate, _ = get_from_log('/media/wei/Backup/final_output/our/malconv/output_malconv_holdout_TS_parent/rewriter.log', r2)
    y3_list_rate, total = get_from_log2('/home/wei/code/MAB-malware/final_output/evasive_MCTS_malware200_malconv/rewriter.log', r3)

    x1 = np.array(range(len(y1_list_rate)))
    x2 = np.array(range(len(y2_list_rate)))
    x3 = np.array(range(len(y3_list_rate)))
    
    fig, ax = plt.subplots()
    ax.plot(x1, y1_list_rate, fillstyle='none', linewidth=1, label='GP', color='blue')
    ax.plot(x2, y2_list_rate, fillstyle='none', linewidth=1, label='MAB', color='red')
    ax.plot(x3, y3_list_rate, fillstyle='none', linewidth=1, label='MCTS', color='green')

    axes = plt.gca()
    axes.set_ylim([0,1.1])
    axes.set_xlim([0, total * 1.2])
    
    plt.annotate(str(round(y1_list_rate[-1],4)), (total,round(y1_list_rate[-1],4)+0.02), color='blue', fontsize=9)
    plt.annotate(str(round(y2_list_rate[-1],4)), (total,y2_list_rate[-1]), color='red', fontsize=9)
    plt.annotate(str(round(y3_list_rate[-1],4)), (total,round(y3_list_rate[-1],4)-0.02), color='green', fontsize=9)

    plt.xlabel('number of attempts', fontsize=12)
    plt.ylabel('evasion rate %', fontsize=12)
    #ax.legend(loc='lower right', ncol=2)#, framealpha=0)
    ax.legend(ncol=2)#, framealpha=0)
    fig.subplots_adjust(bottom=0.5)
    
    #plt.show()
    #matplotlib.pyplot.title(av);
    plt.savefig("evasion_rate.pdf")

if __name__ == '__main__':
    main()

