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
dict_action_to_feature = {
        'O1': 'file hash',
        'P1': 'section hash',
        'S1': 'section count',
        'R1': 'section name',
        'C1': 'section hash',
        'OA': 'data dist',
        'SP': 'section padding',
        'SA': 'data dist',
        'SR': 'section name',
        'RC': 'certificate',
        'RD': 'debug',
        'BC': 'checksum',
        'CR': 'code seq' 
        }

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

def main():
    for av in list_av:
        dict_feature_to_sha256 = {
                'file hash': set(),
                'section hash': set(),
                'section count': set(),
                'section name': set(),
                'section padding': set(),
                'debug': set(),
                'checksum': set(),
                'certificate': set(),
                'code seq': set(),
                #'section padding': set(),
                'data dist': set(),
        }
        print('='*40)
        print(av)
        av_path = DATA_PATH + av + '/'
        list_action = []
        for data_folder in os.listdir(av_path):
            if '2020' not in data_folder:
                continue
            print(data_folder)
            feature_folder = [x for x in os.listdir(av_path + data_folder) if x.endswith('func_feature')]
            path = av_path + data_folder + '/' + feature_folder[0] + '/'
            print(path)
            list_exe = os.listdir(path)
            print(len(list_exe))

            for exe in list_exe:
                sha256 = exe.split('.')[0]
                print(sha256)
                list_action = [x.replace('CP', 'C1').replace('RS', 'RC') for x in exe.split('.') if len(x) == 2]
                list_action.sort()
                for action in list_action:
                    dict_feature_to_sha256[dict_action_to_feature[action]].add(sha256)

        dict_larger = {}
        total_amount = 0
        for k in dict_feature_to_sha256.keys():
            total_amount += len(dict_feature_to_sha256[k])
        for k in dict_feature_to_sha256.keys():
            dict_larger[k] = len(dict_feature_to_sha256[k])/total_amount * 100
        listofTuples = dict_larger.items()

        y = []
        label = []
        for elem in listofTuples :
            print(elem[0], elem[1] )
            y.append(elem[1])
            label.append(elem[0])
        x = np.arange(len(y))
        fig, ax = plt.subplots()
        plt.ylabel('percentage %', fontsize=14)

        plt.bar(x, y, color='silver')
        plt.xticks(x, label, rotation=90, fontsize=14)
        fig.subplots_adjust(bottom=0.5)
        #plt.show()
        plt.savefig('/home/wei/feature_%s.pdf' %get_display_name(av).lower())

if __name__ == '__main__':
    main()
