import os
import sys
from rewriter import *
from utils import *

DATA_PATH = 'data/'
VM_PATH = get_share_path() + 'interpreter/'
MALWARE_RANDOM_PATH = DATA_PATH + 'randomize/'
LOG_PATH = '/dev/null'
MALWARE_PATH = get_malware_path()
INTERPRETER_INPUT_PATH = ''
INTERPRETER_OUTPUT_PATH = ''
REWRITTEN_PATH = ''
JSON_PATH = ''
CONTENT_PATH = ''

list_file_hash = []
list_section_hash = []
list_header = []
list_body = []
list_ml = []
g_action_to_mini_action_list = {
        'CR': ['', 'OA1', 'CP1'],
        'SA': ['', 'OA1', 'SA1', 'OA'],
        'SP': ['', 'OA1', 'SP1'],
        'SR': ['', 'OA1', 'SR1'],
        'RD': ['', 'OA1', 'CP1'],
        'RC': ['', 'OA1'],
        'RS': ['', 'OA1'],
        'BC': ['', 'OA1'],
        'OA': ['', 'OA1'],
        }

dict_action_to_feature = {
        'OA1': 'file hash',
        'SP1': 'section hash',
        'SA1': 'section count',
        'SR1': 'section name',
        'CP1': 'section hash',
        'OA': 'data dist',
        'SP': 'section padding',
        'SA': 'data dist',
        'SR': 'section name',
        'RC': 'certificate',
        'RD': 'debug',
        'BC': 'checksum',
        'CR': 'code seq'
        }

g_sha256_to_action_position = {}
g_sha256_to_current_output_path = {}
g_sha256_to_kept_idx_mini_action = {}
g_sha256_to_action_list = {}
g_md5_to_create_time = {}
g_sha256_to_recopy = {}
g_sha256_to_json_list = {}
g_list_input_file = []

def main():
    global g_sha256_to_current_output_path, g_sha256_to_action_list, g_md5_to_create_time, g_sha256_to_recopy, g_list_input_file
    if len(sys.argv) < 2:
        print('Usage: interpreter.py [av_name]')
        exit()

    av_name = sys.argv[1]

    update_global_variable(av_name)
    
    if os.path.exists(INTERPRETER_INPUT_PATH) == False or len(os.listdir(INTERPRETER_INPUT_PATH)) == 0:
        os.system('mkdir -p %s' %INTERPRETER_INPUT_PATH)
        log('Please copy functional evasive sample to the folder %s' %INTERPRETER_INPUT_PATH)
        exit()

    create_output_folder()

    time.sleep(3)   # check share folder

    #g_list_input_file = [x for x in os.listdir(INTERPRETER_INPUT_PATH) if len(x.split('.')[0]) == 64]
    g_list_input_file = [x for x in os.listdir(INTERPRETER_INPUT_PATH)]
    g_list_input_file.sort()
    log('len(g_list_input_file): %d' %len(g_list_input_file))

    list_finished = []
    finish = False
    json_miss_count = 0
    while finish == False:
        log('=' * 70)
        list_working = [x for x in g_list_input_file if x.split('.')[0] not in list_finished]
        list_working.sort()
        if len(list_working) == 0:
            finish = True
            break
        elif len(list_working) < 10:
            time.sleep(1)
        for filename in list_working:
            log('-' * 70)
            log('list_working: %d, list_finished: %d' %(len(list_working), len(list_finished)))
            sha256 = filename.split('.')[0]
            log(filename)
            action_seq = get_action_seq(filename)
            log('action_seq: %s' %action_seq)
            if sha256 not in g_sha256_to_action_list:
                g_sha256_to_action_list[sha256] = action_seq
            list_json = get_json_list(sha256)
            if len(list_json) != len(action_seq):
                json_miss_count += 1
                #time.sleep(2)
                list_finished.append(sha256)
                continue
            current_output_path = get_current_output_path(sha256)
            log('current actions: %s' %get_action_seq(current_output_path))
            wait_time = get_wait_time('interpreter')
            log('wait time threshold: %d' %wait_time)
            file_status, file_path_on_vm = check_file_status_on_vm(current_output_path, VM_PATH, REWRITTEN_PATH, g_md5_to_create_time, wait_time, av_name)
            log('[%s]' %file_status)
            if file_status == 'waiting':
                pass
            elif file_status == 'almost_evasive':                # almost_evasive
                pass
                if RECOPY and sha256 not in g_sha256_to_recopy:
                    log('recopy to VM')
                    g_sha256_to_recopy[sha256] = True
                    os.system('mv %s %s/almost/' %(file_path_on_vm, INTERPRETER_OUTPUT_PATH))
                    #time.sleep(1)
                    os.system('mv %s/almost/%s %s' %(INTERPRETER_OUTPUT_PATH, basename(file_path_on_vm), VM_PATH))
            else:# evasive or detected
                res = True
                if file_status == 'evasive':     # evasive
                    keep_mini_action(sha256)
                    res = inc_action_idx_position(sha256)
                
                if file_status == 'detected':
                    if sha256 in g_sha256_to_current_output_path:
                        res = inc_mini_action_idx_position(sha256)

                if sha256 not in list_finished and res == False:
                    list_finished.append(sha256)
                else:
                    list_new_action = get_new_action_list(sha256)
                    log('new actions: %s' %list_new_action)

                    if len(list_new_action) > 0:
                        output_path = apply_action_list(sha256, list_new_action, list_json)
                        log(basename(output_path))
                        if output_path == False:
                            list_finished.append(sha256)
                            continue
                        g_sha256_to_current_output_path[sha256] = output_path
                        os.system('cp %s %s' %(output_path, VM_PATH))
    log('json_miss_count: %d' %json_miss_count)

    # cp the latest file to output
    for filename in g_list_input_file:
        sha256 = filename.split('.')[0]
        action_seq = get_action_seq(filename)
        list_file = [VM_PATH + x for x in os.listdir(VM_PATH) if sha256 in x]
        if len(list_file) > 0:
            latest_file = max(list_file, key=os.path.getctime)
            log(latest_file)
            os.system('cp %s %s' %(latest_file, INTERPRETER_OUTPUT_PATH))
            list_mini_action = get_action_seq(latest_file)
        else:
            print('not exist')
            os.system('cp %s %s%s' %(INTERPRETER_INPUT_PATH + filename, INTERPRETER_OUTPUT_PATH, filename.replace('.exe', '')))

    # plot result
    plot(av_name)
    log('=== Finish! ===')

def log(content):
    time_string = datetime.datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
    print('[' + time_string + ']', content)
    with open(LOG_PATH, 'a') as fp:
        fp.write('[%s] %s\n' %(time_string, content))
    sys.stdout.flush()

def update_global_variable(av_name):
    global JSON_PATH, CONTENT_PATH, LOG_PATH, INTERPRETER_INPUT_PATH, INTERPRETER_OUTPUT_PATH, REWRITTEN_PATH
    REWRITTEN_PATH = 'output/%s_rewritten_interpreter/' %(av_name)
    JSON_PATH = CONTENT_PATH = 'output/%s_json/' %(av_name)
    INTERPRETER_INPUT_PATH = 'output/%s_interpreter_input/' %(av_name)
    INTERPRETER_OUTPUT_PATH = 'output/%s_interpreter_output/' %(av_name)
    LOG_PATH = 'log/interpreter.%s.%s.log' %(av_name, get_time_str())

def get_action_seq_by_sha256(sha256):
    return g_sha256_to_action_list[sha256]

def inc_action_idx_position(sha256):
    global g_sha256_to_action_position
    action_seq = get_action_seq_by_sha256(sha256)
    i1, i2 = get_action_position(sha256)
    if i1 < len(action_seq) - 1:
        g_sha256_to_action_position[sha256] = (i1+1, 0)
        return True
    else:
        return False

def inc_mini_action_idx_position(sha256):
    global g_sha256_to_action_position
    action_seq = get_action_seq_by_sha256(sha256)
    i1, i2 = get_action_position(sha256)
    action = action_seq[i1]
    list_mini_action = g_action_to_mini_action_list[action]
    if i2 < len(list_mini_action) - 1:
        g_sha256_to_action_position[sha256] = (i1, i2+1)
        return True
    else:
        return inc_action_idx_position(sha256)

def keep_mini_action(sha256):
    global g_sha256_to_kept_idx_mini_action
    action_seq = get_action_seq_by_sha256(sha256)
    (action_idx, mini_action_idx) = g_sha256_to_action_position[sha256]
    mini_action = g_action_to_mini_action_list[action_seq[action_idx]][mini_action_idx]
    log('keep: %d %s' %(action_idx, mini_action))
    if sha256 not in g_sha256_to_kept_idx_mini_action:
        g_sha256_to_kept_idx_mini_action[sha256] = []
    g_sha256_to_kept_idx_mini_action[sha256].append((action_idx, mini_action))

def plot(av_name):
    list_values = []
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
            'data dist': set(),
    }
    print('='*40)
    list_exe = os.listdir(INTERPRETER_OUTPUT_PATH)

    for exe in list_exe:
        sha256 = exe.split('.')[0]
        action_seq = get_action_seq(exe)
        action_seq.sort()
        for action in action_seq:
            dict_feature_to_sha256[dict_action_to_feature[action]].add(sha256)

    dict_larger = {}
    total_amount = 0
    for k in dict_feature_to_sha256.keys():
        total_amount += len(dict_feature_to_sha256[k])
    if total_amount == 0:
        print('nothing to do')
        exit()
    for k in dict_feature_to_sha256.keys():
        dict_larger[k] = len(dict_feature_to_sha256[k])/total_amount * 100
    listofTuples = dict_larger.items()
    print(dict_larger)
    list_values.append(list(dict_larger.values()))

    value_array = None
    features = list(dict_larger.keys())
    print(features)
    print(list_values)
    plot_feature([av_name], features, list_values)

def plot_feature(avs, features, list_values):

    value_array = np.array(list_values)

    print(features)
    print(value_array)
    fig, ax = plt.subplots()

    im = heatmap(value_array, avs, features, ax=ax,
                       cmap="YlOrBr")
    texts = annotate_heatmap(im, valfmt="{x:.2f} %")

    fig.tight_layout()
    fig.set_size_inches(10, 5.5)
    fig.subplots_adjust(top=0.85)
    plt.show()
    #plt.savefig('feature_contribution_heatmap.pdf')

def get_current_output_path(sha256):
    if sha256 in g_sha256_to_current_output_path:
        current_output_path = g_sha256_to_current_output_path[sha256]
    else:
        current_output_path = 'none'
    return current_output_path

def get_action_position(sha256):
    global g_sha256_to_action_position
    if sha256 not in g_sha256_to_action_position:
        g_sha256_to_action_position[sha256] = (0,0)
    action_position = g_sha256_to_action_position[sha256]
    return action_position

def get_new_action_list(sha256):
    action_seq = get_action_seq_by_sha256(sha256)
    list_new_action = action_seq.copy()
    action_idx, mini_action_idx = get_action_position(sha256)
    action = list_new_action[action_idx]
    list_new_action[action_idx] = g_action_to_mini_action_list[action][mini_action_idx]
    list_kept_idx_mini_action = []
    if sha256 in g_sha256_to_kept_idx_mini_action:
        list_kept_idx_mini_action = g_sha256_to_kept_idx_mini_action[sha256]
    for (idx, mini_action) in list_kept_idx_mini_action:
        list_new_action[idx] = mini_action
    return list_new_action

def apply_action_list(sha256, list_new_action, list_json):
    action_list = get_action_seq_by_sha256(sha256)
    file_path = MALWARE_PATH + sha256
    for idx, action in enumerate(list_new_action):
        output_path = REWRITTEN_PATH + basename(file_path) + '.' + action
        json = list_json[idx]
        if action == '':
            output_path = file_path
            if REWRITTEN_PATH not in output_path:      # copy the original binary to REWRITTEN_PATH
                os.system('cp -p %s %s' %(output_path, REWRITTEN_PATH))
            res = True
        elif action == 'OA':
            content_path = json['content_path']
            res = overlay_append(file_path, output_path, content_path)
        elif action == 'CR':
            res = code_randomize(file_path, MALWARE_RANDOM_PATH, output_path)
        elif action == 'SA':
            section_name = json['section_name']
            content_path = json['content_path']
            if os.path.exists(content_path) == False:           # debug !!!!!!!!!!!!!!!!!!!
                log('Data file not exists, return False')
                log(content_path)
                res = False
            else:
                res = section_add(file_path, output_path, section_name, content_path)
        elif action == 'SP':
            section_idx = json['section_idx']
            content_path = json['content_path']
            if os.path.exists(content_path) == False:
                log('something is wrong, skipping this sample...')
                return False
            res = section_append(file_path, output_path, section_idx, content_path)
        elif action == 'SR':
            section_idx = json['section_idx']
            old_name = json['old_name']
            new_name = json['new_name']
            res = section_rename(file_path, output_path, section_idx=section_idx, new_name=new_name)
        elif action == 'RD':
            res = remove_debug(file_path, output_path)
        elif action == 'RS':
            res = remove_signature(file_path, output_path)
        elif action == 'BC':
            res = break_optional_header_checksum(file_path, output_path)
        ###########################################################
        elif action == 'SP1':
            section_idx = json['section_idx']
            res = section_append_one_byte(file_path, output_path, section_idx)
        elif action == 'SR1':
            section_idx = json['section_idx']
            old_name = json['old_name']
            log('old_name: %s' %old_name)
            new_name_letter = list(old_name)
            letters = string.ascii_lowercase
            new_name = old_name
            while(new_name == old_name):
                name_idx = random.randint(0, len(new_name_letter)-1)
                new_name_letter[name_idx] = random.choice(letters)
                new_name = "".join(new_name_letter)
            res = section_rename(file_path, output_path, section_idx=section_idx, new_name=new_name)
        elif action == 'CP1':
            res = code_section_append_one_byte(file_path, output_path)
        elif action == 'OA1':      #'overlay_append_one_byte':
            res = overlay_append_one_byte(file_path, output_path)
        elif action == 'SA1':    #'section_add_one_byte':
            res = section_add_one_byte(file_path, output_path)
        elif action == 'DD':    #'remove_debug_only_diretory':
            res = remove_debug(file_path, output_path, remove_entry=False)
        elif action == 'DE':    #'remove_debug_only_diretory':
            res = remove_debug(file_path, output_path, remove_directory=False)
        elif action == 'RS':    #'remove_signature':
            res = remove_signature(file_path, output_path)
        elif action == 'SE':    #'remove_signature_only_entry':
            res = remove_signature(file_path, output_path, remove_directory=False)
        elif action == 'SD':    #'remove_signature_only_directory':
            res = remove_signature(file_path, output_path, remove_entry=False)
        if res == False:
            log('error! apply action fail %s' %action)
            output_path = file_path
        file_path = output_path
    return output_path

def get_json_list(sha256):
    global g_sha256_to_json_list
    if sha256 not in g_sha256_to_json_list:
        list_json = []
        json_path = JSON_PATH + sha256 + '.json'
        if os.path.exists(json_path) == False:
            print(json_path)
            print('json does not exist, exiting...')
            exit()  # todo
            return False
        with open(json_path, 'r') as fp:
            for line in fp:
                line = line.strip()
                data = json.loads(line)
                list_json.append(data)
                if 'content_path' in data:
                    data['content_path'] = CONTENT_PATH + basename(data['content_path'])
        g_sha256_to_json_list[sha256] = list_json
    else:
        list_json = g_sha256_to_json_list[sha256]
    return list_json

def create_output_folder():
    os.system('rm -fr %s' %INTERPRETER_OUTPUT_PATH)
    os.system('mkdir -p %s' %INTERPRETER_OUTPUT_PATH)
    os.system('mkdir -p %s/almost/' %INTERPRETER_OUTPUT_PATH)

    os.system('rm -fr %s' %REWRITTEN_PATH)
    os.system('mkdir -p %s' %REWRITTEN_PATH)

    os.system('mkdir -p %s' %VM_PATH)
    os.system('rm -fr %s/*' %VM_PATH)

    os.system('sudo umount %s' %get_share_path())
    os.system('mkdir -p %s' %get_share_path())
    os.system('sudo mount -t cifs -o username=%s,domain=MYDOMAIN,uid=1000 //%s/share/ %s' %(get_vm_username(), get_vm_ip(), get_share_path()))

if __name__ == '__main__':
    main()
