import os
import datetime
import numpy as np
import matplotlib.pyplot as plt

DATA_PATH = '/home/wei/code/adversarial_binary/data/final_2020/'
list_av = [
            'ember',
            'clamav',
            'avast',
            'avira',
            'bitdefender',
            'kaspersky',
            ]
dict_action_list_to_count = {}

def get_display_name(av):
    if 'kaspersky' in av:
        display_name = 'AV4'
    elif 'bitdefender' in av:
        display_name = 'AV3'
    elif 'avast' in av:
        display_name = 'AV1'
    elif 'avira' in av:
        display_name = 'AV2'
    elif 'ember' in av:
        display_name = 'EMBER'
    elif 'clamav' in av:
        display_name = 'ClamAV'
    return display_name

def autolabel(rects, ax, evasive):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        percent = round(height/evasive * 100, 2)
        print(height, evasive)
        ax.annotate('{}%'.format(percent),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

def get_av_to_evasive_miss_list():
    dict_av_to_evasive_list = {}
    dict_av_to_miss_list = {}
    for toav in list_av:
        av_path = DATA_PATH + toav + '/' 
        list_data_folder = os.listdir(av_path)
        list_data_folder.sort()
        for data_folder in list_data_folder:
            if '2020' in data_folder:
                feature_folder = [x for x in os.listdir(av_path + data_folder) if x.endswith('func')]
                list_exe = os.listdir(av_path + data_folder + '/' + feature_folder[0] + '/')
                if toav not in dict_av_to_evasive_list:
                    dict_av_to_evasive_list[toav] = []
                for exe in list_exe:
                    sha256 = exe.split('.')[0]
                    if len(sha256) == 64:
                        dict_av_to_evasive_list[toav].append(sha256)

                missed_folder = [x for x in os.listdir(av_path + data_folder) if x.endswith('survived')]
                list_exe = os.listdir(av_path + data_folder + '/' + missed_folder[0] + '/')
                if toav not in dict_av_to_miss_list:
                    dict_av_to_miss_list[toav] = []
                for exe in list_exe:
                    sha256 = exe.split('.')[0]
                    if len(sha256) == 64:
                        dict_av_to_miss_list[toav].append(sha256)
    return dict_av_to_evasive_list, dict_av_to_miss_list

def main():
    dict_av_to_evasive_list, dict_av_to_miss_list = get_av_to_evasive_miss_list()
    print('='*30)
    for av, evasive_list in dict_av_to_evasive_list.items():
        print(av, len(evasive_list))
    print('='*30)
    for av, miss_list in dict_av_to_miss_list.items():
        print(av, len(miss_list))

    dict_av2av_to_evasive_list = {}
    for toav in list_av:
        print('============ %s ==============' %toav)
        av_path = DATA_PATH + toav + '/'
        list_data_folder = os.listdir(av_path)
        list_data_folder.sort()
        for data_folder in list_data_folder:
            if 'transfer' in data_folder:
                list_tmp = os.listdir(av_path + data_folder)
                list_tmp.sort()
                for tmp in list_tmp:
                    s = tmp.split('_')
                    if len(s) <= 1:
                        fromav = tmp
                    else:
                        fromav = tmp.split('_')[1]
                    list_exe = os.listdir(av_path + 'transfer/' + tmp)
                    if fromav + '_' + toav not in dict_av2av_to_evasive_list:
                        dict_av2av_to_evasive_list[fromav + '_' + toav] = []
                    for exe in list_exe:
                        sha256 = exe.split('.')[0]
                        if len(sha256) == 64:
                            #print(sha256)
                            if sha256 not in dict_av_to_miss_list[toav]:
                                dict_av2av_to_evasive_list[fromav + '_' + toav].append(sha256)
                            #    print('transfer')
                            #else:
                            #    print('already miss')
    #print(dict_av2av_to_evasive_list)

    for av in list_av:
        print('-' * 10)
        print(av)
        #print(dict_av_to_evasive_list[av])
        #for toav in list_av:
        #    if av + '_' + toav in dict_av2av_to_evasive_list:
        #        print(av + '_' + toav, len(dict_av2av_to_evasive_list[av + '_' + toav]))

        if True:
            dict_larger = {}
            for k,v in dict_av2av_to_evasive_list.items():
                if av + '_' in k:
                    dict_larger[k] = len(v)
            #listofTuples = sorted(dict_larger.items(), key=lambda x:(-x[1]))
            listofTuples = dict_larger.items()
            #print(listofTuples)

            y = []
            label = []
            for elem in listofTuples :
                print(elem[0], '%d/%d (%s\\%%)' %(elem[1], len(dict_av_to_evasive_list[av]), round(100*elem[1]/len(dict_av_to_evasive_list[av]),2)))
                y.append(elem[1])
                label.append(get_display_name(elem[0].split('_')[1]))
            x = np.arange(len(y))
            fig, ax = plt.subplots()

            #plt.xlabel('evasive sample of ' + get_display_name(av) + ' transfer to other AVs', fontsize=12)
            #plt.xlabel('other AVs', fontsize=12)
            plt.ylabel('# transferable', fontsize=14)
            axes = plt.gca()
            axes.set_ylim([0,80])

            bars = plt.bar(x, y, color='silver')
            autolabel(bars, ax, len(dict_av_to_evasive_list[av]))
            plt.xticks(x, label, fontsize=14)#, rotation=90)
            fig.subplots_adjust(bottom=0.5)
            #plt.show()
            #exit()
            plt.savefig('/home/wei/transfer_%s.pdf' %get_display_name(av).lower())

if __name__ == '__main__':
    main()
