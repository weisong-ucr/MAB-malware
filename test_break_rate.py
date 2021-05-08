import os
import json
from compare_cuckoo_sig import *

ori_path = 'final_output/cuckoo_json_ori/'
rew_path = 'final_output/cuckoo_json_rewritten/test_break_rate/'

list_ori = [ x for x in os.listdir(ori_path) if '.json' in x ]
print(len(list_ori))

list_file = os.listdir(rew_path)
list_file.sort()
print(len(list_file))

dict_type_to_dict_action_to_count = dict()
dict_type_to_dict_action_to_count['gym'] = dict()
dict_type_to_dict_action_to_count['our'] = dict()

dict_type_to_dict_action_to_func = dict()
dict_type_to_dict_action_to_func['gym'] = dict()
dict_type_to_dict_action_to_func['our'] = dict()

for idx, f_rew in enumerate(list_file):
    print('[%d/%d (%.2f%%)]----------------------' %(idx, len(list_file), idx / len(list_file)*100))
    print(f_rew)
    s = f_rew.split('_')
    sha256 = s[2]
    action = s[3].split('.')[0]
    if 'gym' in f_rew:
        set_type = 'gym'
    else:
        set_type = 'our'
    #print(set_type, action)
    for f_ori in list_ori:
        if f_ori.startswith('.'):
            continue
        if sha256 in f_ori:
            print(f_ori)
            print(set_type, action)
            res = compare_sig(ori_path + f_ori, rew_path + f_rew)
            print(res)
            if action not in dict_type_to_dict_action_to_count[set_type]:
                dict_type_to_dict_action_to_count[set_type][action] = 1
            else:
                dict_type_to_dict_action_to_count[set_type][action] += 1
            if res == True:
                if action not in dict_type_to_dict_action_to_func[set_type]:
                    dict_type_to_dict_action_to_func[set_type][action] = 1
                else:
                    dict_type_to_dict_action_to_func[set_type][action] += 1
            #print('func: ', dict_type_to_dict_action_to_func)
            #print('count:', dict_type_to_dict_action_to_count)
            print('='*30)
            for k, v in dict_type_to_dict_action_to_count.items():
                func = total = 0
                for k2, v2 in dict_type_to_dict_action_to_count[k].items():
                    total += v2
                    if k2 in dict_type_to_dict_action_to_func[k].keys():
                        func += dict_type_to_dict_action_to_func[k][k2]
                        print('%s %s %d/%d (%.2f%%)' %(k, k2, dict_type_to_dict_action_to_func[k][k2], v2, dict_type_to_dict_action_to_func[k][k2]/v2*100))
                    else:
                        print('%s %s %d/%d (%.2f%%)' %(k, k2, 0, v2, 0))
                print('-'*30)
                if total > 0:
                    print('%s %s %d/%d (%.2f%%)' %(k, 'Total', func, total, func/total*100))
                print('='*30)
            break
