import os
import datetime
import numpy as np
import matplotlib.pyplot as plt

DATA_PATH = '/home/wei/code/adversarial_binary/data/final_2020/'
list_av_folder = [
                    'ember/',
                    'ember_no_weight_old/',
                    ]

def get_datetime_from_log(line):
    if '[' not in line:
        print(line)
        exit()
    time_str = line.split(']')[0].replace('[','')
    time_obj = datetime.datetime.strptime(time_str, '%Y/%m/%d_%H:%M:%S')
    return time_obj

def stat(data_idx):
    total_sample = 1000
    av = list_av_folder[data_idx]
    print('=============== %s =============' %av)
    list_data_folder = os.listdir(DATA_PATH + av)
    list_data_folder.sort()
    dict_attempt_amount_to_total_file_amount = {}
    dict_file_to_attempt_amount = {}
    missed_amount = 0
    total_process_time = 0
    for data_folder in list_data_folder:
        if '2020' not in data_folder and '2019' not in data_folder:
            continue
        #total_sample += 200
        MAIN_PATH = DATA_PATH + av + '/' +  data_folder + '/'
        print(data_folder)
        minimized_scan_func = [MAIN_PATH + x + '/' for x in os.listdir(MAIN_PATH) if x.endswith('minimized_scan_func')]
        if len(minimized_scan_func) > 0:
            exe_path = minimized_scan_func[0]
        else:
            print('!!!!!!!!!!! Need sandbox !!!!!!!!!')
            exe_path = [MAIN_PATH + x + '/' for x in os.listdir(MAIN_PATH) if x.endswith('minimized_scan')][0]
        survived_path = [MAIN_PATH + x + '/' for x in os.listdir(MAIN_PATH) if x.endswith('survived')][0]
        LOG_PATH = [MAIN_PATH + x + '/' for x in os.listdir(MAIN_PATH) if x.endswith('backup')][0]
        log_path = [LOG_PATH + x for x in os.listdir(LOG_PATH) if 'rewriter' in x and '.swp' not in x][0]
        print(log_path)
        
        with open(log_path, 'r') as fp:
            list_log = fp.read().split('\n')
        start_time = get_datetime_from_log(list_log[0])
        end_time = get_datetime_from_log(list_log[-2])
        process_time = end_time - start_time
        total_process_time += int(process_time.seconds)
        print('process time:\t%s h' %(process_time.seconds/3600))
        
        list_file = os.listdir(exe_path)
        print('survived sample amount:\t%d' %len(list_file))

        list_survived = os.listdir(survived_path)
        missed_amount += len(list_survived)
        
        for filename in list_file:
            attempt_amount = 0
            #print('====', filename)
            sha256 = filename.split('.')[0]
            for line in list_log:
                if sha256 in line and 'action' in line:
                    attempt_amount += 1
            dict_file_to_attempt_amount[filename] = attempt_amount
        for x in range(61):
            dict_attempt_amount_to_total_file_amount[x] = 0
            for k, v in dict_file_to_attempt_amount.items():
                if v <= x:
                    dict_attempt_amount_to_total_file_amount[x] += 1
    if av == 'avast' or av == 'clamav' or 'ember' in av:
        sample_amount = 1000
    else:
        sample_amount = total_sample
    list_evaded = np.array(list(dict_attempt_amount_to_total_file_amount.values())[:60])
    list_rate = list_evaded/(sample_amount-missed_amount)
    print('total sample amount:\t%d' %(sample_amount))
    print('missed sample amount:\t%d' %(missed_amount))
    print('detect rate:\t%f' %((sample_amount-missed_amount)/sample_amount))
    print('60 evasive rate:\t%f' %list_rate[-1])
    print('total process time:\t%f h' %(total_process_time/3600))
    print('throughput:\t%f s/sample' %(total_process_time/sample_amount))
    return av, list_rate

def get_display_name(av):
    if 'kaspersky' in av:
        return 'AV4'
    elif 'bitdefender' in av:
        return 'AV3'
    elif 'avast' in av:
        return 'AV1'
    elif 'avira' in av:
        return 'AV2'
    elif 'ember' in av:
        return 'EMBER'
    elif 'clamav' in av:
        return 'ClamAV'

def main():
    x = np.array(range(60))

    y0_name, y0_list_rate = stat(0)
    y1_name, y1_list_rate = stat(1)
    #y2_name, y2_list_rate = stat(2)
    #y3_name, y3_list_rate = stat(3)
    #y4_name, y4_list_rate = stat(4)
    #y5_name, y5_list_rate = stat(5)
    
    fig, ax = plt.subplots()
    print(y0_list_rate)
    print(y1_list_rate)
    l0, = ax.plot(x, y0_list_rate, marker='x', fillstyle='none', linewidth=1, label=get_display_name(y0_name) + ' /w weights and content')
    l1, = ax.plot(x, y1_list_rate, marker='^', fillstyle='none', linewidth=1, label=get_display_name(y1_name) + ' /wo weights and content') 
    #l2, = ax.plot(x, y2_list_rate, marker='>', fillstyle='none', linewidth=1, label=get_display_name(y2_name))
    #l3, = ax.plot(x, y3_list_rate, marker='<', fillstyle='none', linewidth=1, label=get_display_name(y3_name))
    #l4, = ax.plot(x, y4_list_rate, marker='v', fillstyle='none', linewidth=1, label=get_display_name(y4_name))
    #l5, = ax.plot(x, y5_list_rate, marker='+', fillstyle='none', linewidth=1, label=get_display_name(y5_name))
    print(y0_name, y1_name)
    
    plt.xlabel('number of attempts', fontsize=12)
    plt.ylabel('evasion rate', fontsize=12)
    ax.legend(loc='lower right')#, framealpha=0)
    
    plt.show()

if __name__ == '__main__':
    main()

