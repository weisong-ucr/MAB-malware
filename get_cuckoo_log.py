import os
import sys
import json
from utils import *

#INTERPRETER_INPUT_PATH = ''
#MINIMIZED_PATH = ''

def log(content):
    time_string = get_time_str()
    print('[' + time_string + ']', content)
    #with open(LOG_PATH, 'a') as fp:
    #    fp.write('[%s] %s\n' %(time_string, content))
    #sys.stdout.flush()

def main():
    #if len(sys.argv) < 2:
    #    print('Usage: verifier.py [av_name]')
    #    exit()
    #av_name = sys.argv[1]

    #update_global_variable(av_name)

    #create_output_folder()

    token = Utils.get_cuckoo_token()
    verifier_path = 'data/verifier/'
    os.system('mkdir -p %s' %verifier_path)
    os.system('curl -H "Authorization: Bearer %s" http://localhost:8090/tasks/list > %s/list' %(token, verifier_path))
    with open('%s/list' %verifier_path, 'r') as fp:
        task_list_json = json.loads(fp.read())
        task_count = task_list_json['tasks'][-1]['id']
    print(task_count)

    dict_f_to_info = {}
    #for idx in range(1, task_count + 1):
    for idx in range(201, 331):
        os.system('curl -H "Authorization: Bearer %s" http://localhost:8090/tasks/report/%d > %s/%d.json' %(token, idx, verifier_path, idx))
        with open('%s/%d.json' %(verifier_path, idx), 'r') as fp:
            rep_json = json.loads(fp.read())
            filename = rep_json['target']['file']['name']
            score = rep_json['info']['score']
            sha256 = filename.split('.')[0]
            list_sig = rep_json['signatures']
            list_des = []
            for sig in list_sig:
                severity = sig['severity']
                description = sig['description']
                list_des.append(description)
                name = sig['name']
            dict_f_to_info[filename] = {}
            dict_f_to_info[filename]['score'] = score
            dict_f_to_info[filename]['list_des'] = list_des
        os.system('mv %s/%d.json %s/%d_%s_%s.json' %(verifier_path, idx, verifier_path, idx, score, filename))
    exit()

    list_filename = dict_f_to_info.keys()
    for filename in list_filename:
        if len(filename) > 64:
            log(filename)
            for tmp in list_filename:
                if tmp != filename and tmp in filename:
                    list_des_ori = dict_f_to_info[filename]['list_des']
                    list_des_new = dict_f_to_info[tmp]['list_des']
                    if compare_sig_list(list_des_ori, list_des_new):
                        log('behavior is the same')
                        os.system('cp -p %s%s %s' %(MINIMIZED_PATH, filename, INTERPRETER_INPUT_PATH))
                    else:
                        log('behavior is changed')
                    break
    log('=== Finish! ===')
    log('functional minimized samples can be found in %s' %INTERPRETER_INPUT_PATH)

#def update_global_variable(av_name):
#    global MINIMIZED_PATH, INTERPRETER_INPUT_PATH
#    MINIMIZED_PATH = 'output/%s_minimized/' %(av_name)
#    INTERPRETER_INPUT_PATH = 'output/%s_interpreter_input/' %(av_name)

def create_output_folder():
    os.system('rm -fr %s' %INTERPRETER_INPUT_PATH)
    os.system('mkdir -p %s' %INTERPRETER_INPUT_PATH)

def compare_sig_list(list_sig, list_sig_ori):
    encrypt = False
    for sig in list_sig:
        if 'encrypt' in sig:# or 'ansomware' in sig:
            encrypt = True
    count = 0
    for sig_ori in list_sig_ori:
        for sig in list_sig:
            if sig == sig_ori:
                count += 1
                break
    same_rate = float(count) / len(list_sig_ori)
    #print('len(ori), len(sig), same, rate, encrypt: %d, %d, %d, %f, %s' %(len(list_sig_ori), len(list_sig), count, same_rate, encrypt))
    if encrypt == True or len(list_sig_ori) - count <= 1 or same_rate >= 0.8:
        return True
    else:
        return False

if __name__ == '__main__':
    main()
