import os
import json

def compare_sig(path_ori, path_rew):
    set_sig_rew = set()
    fp_rew = open(path_rew, 'r')
    j_rew = json.loads(fp_rew.read())
    score = j_rew['info']['score']
    list_sig = j_rew['signatures']
    for sig in list_sig:
        name = sig['name']
        set_sig_rew.add(name)
    fp_rew.close()

    set_sig_ori = set()
    fp_ori = open(path_ori, 'r')
    j_ori = json.loads(fp_ori.read())
    score = j_ori['info']['score']
    list_sig = j_ori['signatures']
    for sig in list_sig:
        name = sig['name']
        set_sig_ori.add(name)
    fp_ori.close()

    hit = miss = 0
    for sig in set_sig_ori:
        if sig in set_sig_rew:
            hit += 1
        else:
            miss += 1
    print(hit, miss)

    rate = hit / (hit + miss)
    if miss <= 1 or rate > 0.8:
        return True
    #    preserve += 1
    #    list_preserve_rate.append(rate)
    else:
        return False
    #    print(rate)
    #    list_broken_rate.append(rate)
    #    print(set_sig_rew)
    #    print(set_sig_ori)
    #    broken += 1
    #    list_broken.append(sha256)
    #print("result: ", preserve, broken)
    #print(list_broken)
    #list_preserve_rate.sort()
    #list_broken_rate.sort()
    #print(list_preserve_rate)
    #print(list_broken_rate)

def test():
    list_rew = os.listdir('cuckoo_json_rewritten/our_framework_TS_parent/')
    list_ori = os.listdir('cuckoo_json_ori/')
    
    preserve = 0
    broken = 0
    list_broken = []
    list_broken_rate = []
    list_preserve_rate = []

    for f_rew in list_rew:
        #if 'cc929a6c24c4d931d451d72a2446d2ad257c32c2827a08fcdad0ec4754a10f10' not in f_rew:
        #    continue
        print('#############################################################')
        match = 0
        mismatch = 0
        if f_rew.startswith('.'):
            continue
        sha256 = f_rew.split('_')[2].split('.')[0]
        for f_ori in list_ori:
            if f_ori.startswith('.'):
                continue
            if sha256 in f_ori:
                print(f_rew)
                print(f_ori)
                #dict_name_to_apis_rew = {}
                #dict_name_to_apis_ori = {}
                set_sig_rew = set()
                set_sig_ori = set()
                with open('cuckoo_json_rewritten/our_framework_TS_parent/%s' %f_rew, 'r') as fp_rew:
                    j_rew = json.loads(fp_rew.read())
                    score = j_rew['info']['score']
                    list_sig = j_rew['signatures']
                    for sig in list_sig:
                        name = sig['name']
                        set_sig_rew.add(name)
                    with open('cuckoo_json_ori/%s' %f_ori, 'r') as fp_ori:
                        j_ori = json.loads(fp_ori.read())
                        score = j_ori['info']['score']
                        list_sig = j_ori['signatures']
                        for sig in list_sig:
                            name = sig['name']
                            set_sig_ori.add(name)
                hit = miss = 0
                for sig in set_sig_ori:
                    if sig in set_sig_rew:
                        hit += 1
                    else:
                        miss += 1
                print(hit, miss)
                break
        rate = hit / (hit + miss)
        if miss <= 1 or rate > 0.8:
            return True
            #preserve += 1
            #list_preserve_rate.append(rate)
        else:
            return False
            #print(rate)
            #list_broken_rate.append(rate)
            #print(set_sig_rew)
            #print(set_sig_ori)
            #broken += 1
            #list_broken.append(sha256)
        #print("result: ", preserve, broken)
        #print(list_broken)
        #list_preserve_rate.sort()
        #list_broken_rate.sort()
        #print(list_preserve_rate)
        #print(list_broken_rate)
