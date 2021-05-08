import os
import sys
import datetime
import numpy as np
import matplotlib.pyplot as plt
from utils import *

def get_from_log(log):
    dict_pull_to_count = {x:0 for x in range(61)}
    with open(log, 'r') as fp:
        for line in fp:
            if '### Evade!' in line:
                line = line.strip()
                pull = int(line.split(' ')[-1][:-1])
                for idx in range(pull, 61):
                    dict_pull_to_count[idx] += 1
    #print(dict_pull_to_count)
    list_rate = [0]
    for idx in range(1, 61):
        list_rate.append(dict_pull_to_count[idx])
    #print(list_rate)
    return list_rate

def get_from_log_gym(log, t):
    dict_pull_to_count = {x:0 for x in range(61)}
    dict_sha256_to_pull = {}
    RL = False
    with open(log, 'r') as fp:
        for line in fp:
            if '## RL: pull latest stored model' in line:
                RL = True
            if t=='rl':
                if RL and 'success' in line:
                    line = line.strip()
                    sha256 = line.split(' ')[3]
                    dict_sha256_to_pull[sha256] = 0
            else:
                if not RL and 'success' in line:
                    line = line.strip()
                    sha256 = line.split(' ')[3]
                    dict_sha256_to_pull[sha256] = 0
    RL = False
    with open(log, 'r') as fp:
        for line in fp:
            if '## RL: pull latest stored model' in line:
                RL = True
            if t=='rl':
                if RL and ' action: ' in line:
                    line = line.strip()
                    sha256 = line.split(' ')[3]
                    if sha256 in dict_sha256_to_pull:
                        dict_sha256_to_pull[sha256] += 1
            else:
                if not RL and ' action: ' in line:
                    line = line.strip()
                    sha256 = line.split(' ')[3]
                    if sha256 in dict_sha256_to_pull:
                        dict_sha256_to_pull[sha256] += 1
    #print(dict_sha256_to_pull)
    for pull in list(dict_sha256_to_pull.values()):
        for idx in range(pull, 61):
            dict_pull_to_count[idx] += 1
    list_rate = [0]
    for idx in range(1, 61):
        list_rate.append(dict_pull_to_count[idx])
    print(list_rate)
    return list_rate

def main():
    for av in ['malconv', 'ember']:
        MAB_rate = [0 for _ in range(61)]
        GP_rate = [0 for _ in range(61)]
        MCTS_rate = [0 for _ in range(61)]
        RAND_rate = [0 for _ in range(61)]
        GYM_rate = [0 for _ in range(61)]
        GYM_rand_rate = [0 for _ in range(61)]

        count = 0
        for idx in range(1,6):
            MAB_rate_t = get_from_log('/home/wei/code/MAB-malware/final_CCS2021/output_%s_MAB_%d/rewriter.log' %(av, idx))
            GP_rate_t = get_from_log('/home/wei/code/MAB-malware/final_CCS2021/output_%s_GP_%d/rewriter.log' %(av, idx))
            MCTS_rate_t = get_from_log('/home/wei/code/MAB-malware/final_CCS2021/output_%s_MCTS_%d/rewriter.log' %(av, idx))
            RAND_rate_t = get_from_log('/home/wei/code/MAB-malware/final_CCS2021/output_%s_RAND_%d/rewriter.log' %(av, idx))
            if os.path.exists('/home/wei/code/MAB-malware/final_CCS2021/output_%s_GYM_%d/rewriter.log' %(av, idx)):
                GYM_rate_t = get_from_log_gym('/home/wei/code/MAB-malware/final_CCS2021/output_%s_GYM_%d/rewriter.log' %(av, idx), 'rl')
                GYM_rand_rate_t = get_from_log_gym('/home/wei/code/MAB-malware/final_CCS2021/output_%s_GYM_%d/rewriter.log' %(av, idx), 'rand')
                count += 1
        
            for i in range(61):
                MAB_rate[i] += MAB_rate_t[i]
                GP_rate[i] += GP_rate_t[i]
                MCTS_rate[i] += MCTS_rate_t[i]
                RAND_rate[i] += RAND_rate_t[i]
                if os.path.exists('/home/wei/code/MAB-malware/final_CCS2021/output_%s_GYM_%d/rewriter.log' %(av, idx)):
                    GYM_rate[i] += GYM_rate_t[i]
                    GYM_rand_rate[i] += GYM_rand_rate_t[i]

        #print(MAB_rate)
        print('total', GYM_rate)

        print(count)
        for idx in range(61):
            MAB_rate[idx] /= 5000
            GP_rate[idx] /= 5000
            MCTS_rate[idx] /= 5000
            RAND_rate[idx] /= 5000
            GYM_rate[idx] /= count * 200
            GYM_rand_rate[idx] /= count * 200

        #print(MAB_rate[60])
        #print(GP_rate[60])
        #print(MCTS_rate[60])
        #print(RAND_rate[60])
        print(GYM_rate[60])

        x1 = np.array(range(len(MAB_rate)))
        x2 = np.array(range(len(GP_rate)))
        x3 = np.array(range(len(MCTS_rate)))
        x4 = np.array(range(len(RAND_rate)))
        #if os.path.exists('/home/wei/code/MAB-malware/final_CCS2021/output_%s_GYM_%d/rewriter.log' %(av, idx)):
        x5 = np.array(range(len(GYM_rate)))
        #x6 = np.array(range(len(GYM_rand_rate)))

        fig, ax = plt.subplots()
        ax.plot(x1, MAB_rate, fillstyle='none', linewidth=1, color='red', label='MAB')
        ax.plot(x2, GP_rate, fillstyle='none', linewidth=1, color='green', label='GP')
        ax.plot(x3, MCTS_rate, fillstyle='none', linewidth=1, color='orange', label='MCTS')
        ax.plot(x4, RAND_rate, fillstyle='none', linewidth=1, color='blue', label='RAND')
        #if os.path.exists('/home/wei/code/MAB-malware/final_CCS2021/output_%s_GYM_%d/rewriter.log' %(av, idx)):
        ax.plot(x5, GYM_rate, fillstyle='none', linewidth=1, color='magenta', label='GYM')
        #ax.plot(x6, GYM_rand_rate, fillstyle='none', linewidth=1, color='green', label='GYM_rand')

        axes = plt.gca()
        axes.set_ylim([0, 1.1])
        axes.set_xlim([0, 67.5])

        plt.annotate(str(round(MAB_rate[-1]*100,2))+'%', (60.5, MAB_rate[-1]-0.02), color='red', fontsize=9)
        plt.annotate(str(round(GP_rate[-1]*100,2))+'%', (60.5, GP_rate[-1]-0.02), color='green', fontsize=9)
        if av == 'malconv':
            plt.annotate(str(round(MCTS_rate[-1]*100,2))+'%', (60.5, MCTS_rate[-1]-0.05), color='orange', fontsize=9)
            plt.annotate(str(round(RAND_rate[-1]*100,2))+'%', (60.5, RAND_rate[-1]+0.02), color='blue', fontsize=9)
            plt.annotate(str(round(GYM_rate[-1]*100,2))+'%', (60.5, GYM_rate[-1]), color='magenta', fontsize=9)
            #plt.annotate(str(round(GYM_rand_rate[-1]*100,2))+'%', (60.5, GYM_rand_rate[-1]), color='magenta', fontsize=9)
        else:
            plt.annotate(str(round(MCTS_rate[-1]*100,2))+'%', (60.5, MCTS_rate[-1]+0.02), color='orange', fontsize=9)
            plt.annotate(str(round(RAND_rate[-1]*100,2))+'%', (60.5, RAND_rate[-1]-0.02), color='blue', fontsize=9)
            plt.annotate(str(round(GYM_rate[-1]*100,2))+'%', (60.5, GYM_rate[-1]-0.08), color='magenta', fontsize=9)
            #plt.annotate(str(round(GYM_rand_rate[-1]*100,2))+'%', (60.5, GYM_rand_rate[-1]-0.08), color='magenta', fontsize=9)

        plt.xlabel('total number of attempts', fontsize=12)
        plt.ylabel('evasion rate %', fontsize=12)
        #ax.legend(loc='lower right', ncol=2)#, framealpha=0)
        ax.legend(loc='upper left')#, ncol=2)#, framealpha=0)
        #ax.legend(ncol=2)#, framealpha=0)
        fig.subplots_adjust(bottom=0.5)

        #plt.show()
        #matplotlib.pyplot.title(av);
        plt.savefig("/home/wei/evasion_rate_%s_all.pdf" %(av))

if __name__ == '__main__':
    main()

