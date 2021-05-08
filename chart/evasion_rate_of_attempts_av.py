import os
import sys
import datetime
import numpy as np
import matplotlib.pyplot as plt
from utils import *
import matplotlib.ticker as ticker


def get_from_log(log, r, append=True):
    list_rate = []
    with open(log, 'r') as fp:
        for line in fp:
            if 'skip' in line:
                line = line.strip()
                rate = float(line.split(' ')[-1].replace('%', ''))
                rate = round(rate * r, 2)
                list_rate.append(rate)
                total = int(line.split(' ')[4].split('/')[-1])
    if append:
        miss = total-len(list_rate)
    if append and miss > 0:
        print([rate])
        a = np.arange(rate, rate + 1, 1/miss)
        print(a)
        return list_rate + list(a[:miss]), total
    else:
        return list_rate, total

def get_from_log2(log, r, append=False):
    list_rate = []
    with open(log, 'r') as fp:
        for line in fp:
            if 'skip' in line:
                line = line.strip()
                rate = float(line.split(' ')[10].replace('(', '').replace('%)', ''))
                rate = round(rate * r, 2)
                list_rate.append(rate)
                total = int(line.split(' ')[4].split('/')[-1])
    if append:
        miss = total-len(list_rate)
        print([rate])
        a = np.arange(rate, rate + 1, 1/miss)
        print(a)
        return list_rate + list(a[:miss]), total
    else:
        return list_rate, total

def main():
    for av in ['clamav', 'avast', 'avira', 'bitdefender']:
        #av = sys.argv[1]
        #sample = sys.argv[2]
        r1 = 1
        r2 = 1
        r3 = 1
        #sample = 'holdout'

        #y1_list_rate, _ = get_from_log('/home/wei/code/adversarial_malware/final_output/our/' + av + '/output_' + av + '_' + sample + '_random/rewriter.log', r1, append=False)
        y1_list_rate, _ = get_from_log('/media/wei/Backup/final_output/our/%s/output_%s_1000_TS_parent/rewriter.log' %(av, av), r1, append=True)
        y2_list_rate, total = get_from_log('/media/wei/Backup/final_output/our/%s/output_%s_1000_random/rewriter.log' %(av, av), r1, append=False)
        #y2_list_rate, _ = get_from_log('/home/wei/code/adversarial_malware/output_' + av + '_1000_TS/rewriter.log', r2)
        #y3_list_rate, total = get_from_log('/home/wei/code/adversarial_malware/final_output/our/' + av + '/output_' + av + '_' + sample + '_TS_parent_91/rewriter.log', r3)
        #y3_list_rate, total = get_from_log2('/home/wei/code/MAB-malware/final_output/output_Avast1000_killed/rewriter.log', r3)

        x1 = np.array(range(len(y1_list_rate)))
        #x2 = np.array(range(len(y2_list_rate)))
        x2 = np.array(range(len(y2_list_rate)))
        
        fig, ax = plt.subplots()
        #ax.plot(x1, y1_list_rate, fillstyle='none', linewidth=1, color='blue', label='Random')
        ax.plot(x1, y1_list_rate, fillstyle='none', linewidth=1, color='red', label='MAB')
        ax.plot(x2, y2_list_rate, fillstyle='none', linewidth=1, color='blue', label='RAND')
        #ax.plot(x2, y2_list_rate, fillstyle='none', linewidth=1, color='red', label='TS')
        #ax.plot(x3, y3_list_rate, fillstyle='none', linewidth=1, color='red', label='TS')
        axes = plt.gca()
        axes.set_ylim([0,55])
        axes.set_xlim([0, total * 1.1])
        
        offset1 = offset2 = 0
        if av == 'avast' or av == 'clamav':
            offset1 = -3
            offset2 = 0
        plt.annotate(str(round(y1_list_rate[-1],2)), (total+1000,y1_list_rate[-1] + offset1), color='red', fontsize=9)
        #plt.annotate(str(y2_list_rate[-1]), (total,y2_list_rate[-1]-1), color='red', textcoords="offset points", xytext=(15,0), ha='center', fontsize=9)
        plt.annotate(str(round(y2_list_rate[-1],2)), (total+1000,y2_list_rate[-1] + offset2), color='blue', fontsize=9)

        ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/1000))
        ax.xaxis.set_major_formatter(ticks_x)

        plt.xlabel('total number of attempts', fontsize=12)
        plt.ylabel('evasion rate %', fontsize=12)
        ax.legend(loc='lower right', ncol=2)#, framealpha=0)
        fig.subplots_adjust(bottom=0.5)
        
        #plt.show()
        #matplotlib.pyplot.title(av);
        #plt.savefig("/home/wei/Share/evasion_rate_of_attempts_%s.pdf" %av)
        plt.savefig("evasion_rate_of_attempts_%s.pdf" %av)

if __name__ == '__main__':
    main()

