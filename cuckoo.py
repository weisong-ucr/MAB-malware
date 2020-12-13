from utils import *
import json
import requests

class Cuckoo():
    def __init__(self):
        self.dict_path_to_task_id = {}
        self.headers = {'Authorization': 'Bearer %s' %Utils.get_cuckoo_token()}
        self.ori_json_folder = Utils.get_ori_json_folder()
        self.del_all_tasks()

    def get_des(self, report_json):
        list_sig = report_json['signatures']
        list_des = []
        for sig in list_sig:
            severity = sig['severity']
            description = sig['description']
            list_des.append(description)
        return list_des
    
    def get_task_id(self, file_path):
        if file_path not in self.dict_path_to_task_id:
            #logger_cuc.info('new sample, submit to cuckoo')
            task_id = self.submit_task(file_path)
        else:
            #logger_cuc.info('existing sample, get task_id')
            task_id = self.dict_path_to_task_id[file_path]
        return task_id

    def get_ori_json(self, sample_path):
        list_file = os.listdir(self.ori_json_folder)
        filename = basename(sample_path)
        for x in list_file:
            if filename in x:
                ori_json_path = self.ori_json_folder + x
                with open(ori_json_path) as fp:
                    ori_json = json.loads(fp.read())
                    return ori_json
        else:
            return False

    
    def get_report_by_path(self, sample_path):
        task_id = self.dict_path_to_task_id[sample_path]
        self.get_report_by_task_id(task_id)
    
    def print_name_score(self, report_json):
        filename = report_json['target']['file']['name']
        score = report_json['info']['score']
        logger_cuc.info('filename: %s [%s]' %(filename, score))
    
    def get_report_by_task_id(self, task_id):
        report_json = requests.get('http://localhost:8090/tasks/report/%d' %task_id, headers=self.headers).json()
        return report_json
    
    def del_all_tasks(self):
        tasks = self.get_tasks()
        for task in tasks:
            task_id = task['id']
            self.del_task(task_id)
    
    def del_sample_and_task(self, sample_path):
        if sample_path in self.dict_path_to_task_id:
            task_id = self.dict_path_to_task_id[sample_path]
            del self.dict_path_to_task_id[sample_path]
            self.del_task(task_id)
        else:
            logger_cuc.error('path not in dict_path_to_task_id, exiting...')
            exit()

    def del_task(self, task_id):
        r = requests.get('http://localhost:8090/tasks/delete/%s' %task_id, headers=self.headers)
    
    def submit_task(self, sample_path):
        with open(sample_path, 'rb') as sample:
            files = {'file': (basename(sample_path), sample)}
            r = requests.post('http://localhost:8090/tasks/create/file', headers=self.headers, files=files)
            task_id = r.json()['task_id']
        self.dict_path_to_task_id[sample_path] = task_id
        return task_id
    
    def get_tasks(self):
        r = requests.get('http://localhost:8090/tasks/list', headers=self.headers).json()
        tasks = r['tasks']
        return tasks
    
    def get_task_status(self, task_id):
        tasks = self.get_tasks()
        for task in tasks:
            cur_task_id = task['id']
            if cur_task_id == task_id:
                status = task['status']
                return status
    
    def create_output_folder(self):
        os.system('rm -fr %s' %INTERPRETER_INPUT_PATH)
        os.system('mkdir -p %s' %INTERPRETER_INPUT_PATH)
    
    def is_functional(self, task_id, sample_path):
        report_json = self.get_report_by_task_id(task_id)
        self.save_json(report_json)
        ori_json = self.get_ori_json(sample_path)
        if ori_json:
            self.print_name_score(report_json)
            self.print_name_score(ori_json)
            report_des = self.get_des(report_json)
            ori_des = self.get_des(ori_json)
            if self.compare_sig_list(ori_des, report_des):
                logger_cuc.info('%s behavior is the same' %(basename(sample_path)))
                return True
            else:
                logger_cuc.info('%s behavior is changed' %(basename(sample_path)))
                return False
        else:   # todo: auto cuckoo ori sample
            logger_cuc.error('ori json file does not exist. existing...')
            exit()

    def save_json(self, report_json):
        filename = report_json['target']['file']['name']
        score = report_json['info']['score']
        output_path = json_folder + '%s_%s.json' %(score, filename)

        d = {}
        d['signatures'] = report_json['signatures']
        d['target'] = {'file':{'name':filename}}
        d['info'] = {'score':score}
        
        with open(output_path, 'w') as fp:
            json.dump(d, fp)
        
    def compare_sig_list(self, list_sig_ori, list_sig):
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
        logger_cuc.info('original: %d, modified: %d, same: %d, same rate: %f, encrypt: %s' %(len(list_sig_ori), len(list_sig), count, same_rate, encrypt))
        if encrypt == True or len(list_sig_ori) - count <= 1 or same_rate >= 0.8:
            return True
        else:
            return False
