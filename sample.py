from utils import *
import copy
#import hashlib
from models import *
from arm import *
from pathlib import Path

class Sample:
    def __init__(self, path):
        self.path = path
        self.current_exe_path = path
        self.sname = Utils.short_name(self.path)
        self.max_length = Utils.get_max_length()
        self.copy_time = None
        # queue types of which the sample is in. option: [None/pending/working/evasive/minimal/functional]
        self.status = None
        self.scan_status = None   # file status on classifier
        #self.broken_action_idxs = set()

        self.list_applied_arm = []
        self.list_useful_arm_idxs = []

        self.current_applied_arm_subset = []
        self.seq_cur_x = -1
        self.seq_cur_y = 0
        self.seq_cur_x_to_kept_arm = {}
        self.list_minimal_arm = []
        self.latest_minimal_path = None

        self.evasive_path = None
        #self.current_exe_md5 = Utils.get_md5(path)
        
        self.pull_count = 0

    def reset(self):
        self.current_exe_path = self.path
        self.copy_time = None
        self.status = None
        self.scan_status = None
        self.list_applied_arm = []
        self.current_applied_arm_subset = []
        self.seq_cur_x = -1
        self.seq_cur_y = 0
        self.seq_cur_x_to_kept_arm = {}
        self.list_minimal_arm = []
        self.latest_minimal_path = None
        self.evasive_path = None
        self.list_useful_arm_idxs = []
        self.pull_count = 0

    #def clone(self):
    #    return copy.deepcopy(self)

    #def update_broken_action_idxs(self):
    #    for arm in self.list_minimal_arm:
    #        if arm and arm.idx >= 4:
    #            self.broken_action_idxs.add(arm.idx)

    def set_current_exe_path(self, path):
        self.current_exe_path = path
        #self.current_exe_md5 = Utils.get_md5(path)
        #logger_rew.info('set %s md5 %s' %(path, self.current_exe_md5))

    def inc_seq_cur_x(self):
        self.seq_cur_x += 1
        self.seq_cur_y = 0

    def inc_seq_cur_y(self):
        action = self.list_applied_arm[self.seq_cur_x].action
        list_mic_action = ACTION_TO_MICROACTION[action]

        if self.seq_cur_x == -1:
            if self.seq_cur_y == len(list_mic_action) - 1:          # TODO need test case
                self.seq_cur_y = -1         # try the original last action
                return
            if self.seq_cur_y == -1:
                self.inc_seq_cur_x()        # from Quick minimize back to normal
                return
        if self.seq_cur_y < len(list_mic_action) - 1:
            self.seq_cur_y += 1
        else:
            self.inc_seq_cur_x()

    #def get_md5(self, path):
    #    if os.path.exists(path) == False:
    #        logger_rew.info('error! file not exists: %s' % path)
    #        return None
    #    hash_md5 = hashlib.md5()
    #    try:
    #        with open(path, 'rb') as f:
    #            content = f.read()
    #            # for chunk in iter(lambda: f.read(4096), b''):
    #            #    logger_rew.info('3')
    #            hash_md5.update(content)
    #            # logger_rew.info(len(content))
    #            md5 = hash_md5.hexdigest()
    #        #logger_rew.info('md5: %s' %md5)
    #        return md5
    #    except Exception as e:
    #        exc_type, exc_obj, exc_tb = sys.exc_info()
    #        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    #        logger_rew.error('%s %s:%s cannot get md5' %
    #                         (exc_type, fname, exc_tb.tb_lineno))
    #        return None

    def delete_applied_arm(self):
        # clean attributes
        # self.copy_time = None       # need?
        # selfNone.scan_status = None       # need?

        # clean arms
        for arm in self.list_applied_arm:
            del arm
        self.list_applied_arm = []

    def delete_tmp_files(self, folder):
        logger_rew.info('delete generated tmp files in %s' % folder)
        os.system('rm -f %s/%s.*' % (folder, basename(self.path)))
        #self.set_current_exe_path(self.path)

#    def delete_files_except_current_exe(self, folder):
#        #list_others = [x for x in os.listdir(folder) if basename(self.path) in x and x != basename(self.current_exe_path)]
#        sha256 = basename(self.path)
#        #list_others = [basename(x) for x in glob.glob('%s/*' %folder) if sha256 in x and basename(x) != basename(self.current_exe_path)]
#        list_others = [x for x in glob.glob('%s%s*' %(folder, sha256)) if x != self.current_exe_path]
#        for x in list_others:
#            os.system('rm -f %s' %(x))
        
    def delete_files_except_current_exe(self, folder):
        sha256 = basename(self.path)
        #list_file = [x for x in glob.glob('%s%s*' %(folder, sha256))]
        list_file = [folder + x for x in os.listdir(folder) if sha256 in x]
        list_sorted = sorted(list_file, key=os.path.getmtime)
        for x in list_sorted[:-1]:
            if x != self.current_exe_path:
                os.system('rm -f %s' %x)
        
    def append_arm(self, arm):
        self.list_applied_arm.append(arm)

    def copy_to_scan_folder(self, scan_folder):
        self.scan_status = SCAN_STATUS_WAITING
        self.copy_time = time.time()
        Utils.safe_copy(self.current_exe_path, scan_folder + basename(self.current_exe_path))
        #if Utils.get_vm_location() == VM_LOCAL:
        #    Utils.safe_copy(self.current_exe_path, scan_folder + basename(self.current_exe_path))
        #elif Utils.get_vm_location() == VM_CLOUD:
        #    #Utils.send_file_to_cloud(self.current_exe_path, scan_folder)
        #else:
        #    logger_rew.error('bad vm location, check configration, exiting...')
        #    exit()

    #def can_be_renamed(self, path):
    #    if Utils.get_vm_location() == VM_LOCAL:
    #        tmp_path = dirname(path) + '/__tmp__' + basename(path)
    #        try:
    #            if os.path.exists(path):
    #                os.system('mv %s %s' % (path, tmp_path))
    #                if os.path.exists(tmp_path):
    #                    os.system('mv %s %s' % (tmp_path, path))
    #                    if os.path.exists(path):
    #                        return True
    #        except Exception as e:
    #            exc_type, exc_obj, exc_tb = sys.exc_info()
    #            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    #            logger_rew.error('%s %s:%s cannot rename' %
    #                             (exc_type, fname, exc_tb.tb_lineno))
    #        return False
    #    else:
    #        logger_rew.error('error. Exiting...')
    #        print('error. Exiting...')
    #        exit()

    #def can_be_renamed_on_cloud(sekf, scan_folder, filepath):
    #    if Utils.get_vm_location() == VM_CLOUD:
    #        old_name = basename(filepath)
    #        new_name = '__tmp__' + old_name
    #        Utils.rename_file_on_cloud(scan_folder, old_name, new_name)
    #        if Utils.check_file_exists_on_cloud(scan_folder, new_name):
    #            Utils.rename_file_on_cloud(scan_folder, new_name, old_name)
    #            return True
    #        else:
    #            return False
    #    else:
    #        logger_rew.error('error. Exiting...')
    #        print('error. Exiting...')
    #        exit()

    #def check_md5(self, filepath):
    #    file_md5 = Utils.get_md5(filepath)
    #    #logger_rew.info('%s: %s %s' %(self.sname, file_md5, self.current_exe_md5))
    #    if file_md5 and self.current_exe_md5:
    #        if file_md5 == self.current_exe_md5:
    #            return True
    #        else:
    #            logger_rew.info('%s: md5 changed. delete file.' % self.sname)
    #            os.system('rm -f %s' % filepath)
    #            return False
    #    return None

    def is_remain_after_threshold_time(self):
        wait_time = Utils.get_wait_time()
        existing_time = time.time() - self.copy_time
        #logger_rew.info('existing_time: %d/%d' %(existing_time, wait_time))
        if existing_time > wait_time:
            return True
        else:
            return False

    #def delete_scan_folder_copy(self, scan_folder):
    #    #os.system('rm -f %s/%s*' % (scan_folder, basename(self.path)))
    #    if Utils.get_vm_location() == VM_LOCAL:
    #        os.system('rm -f %s/%s*' %(scan_folder, basename(self.path)))
    #    elif Utils.get_vm_location() == VM_CLOUD:
    #        Utils.remove_file_on_cloud(scan_folder, '%s*' %(basename(self.path)))

    #def check_scan_status(self, scan_folder, dict_sha256_to_md5):
    def check_scan_status(self, scan_folder):
        Utils.wait_on_stop_sign()
        if Utils.get_classifier_scan_type() == SCAN_TYPE_MODEL:
            scan_status = SCAN_STATUS_DELETED
            sha256 = basename(self.path)
            for file_path in glob.glob('%s%s*' %(scan_folder, sha256)):
                if '.benign' in file_path:
                    scan_status = SCAN_STATUS_PASS
                else:
                    scan_status = SCAN_STATUS_WAITING
                break
            if scan_status in [SCAN_STATUS_PASS]:
                os.system('rm -f %s/*%s*' %(scan_folder, basename(self.path)))
            return scan_status
        else:
            #for filename in os.listdir(scan_folder) if basename(self.path) in x]
            sha256 = basename(self.path)
            list_file = glob.glob('%s%s*' %(scan_folder, sha256))
            if len(list_file) == 0:
                scan_status = SCAN_STATUS_DELETED
            else:
                if self.is_remain_after_threshold_time():
                    scan_status = SCAN_STATUS_PASS
                else:
                    scan_status = SCAN_STATUS_WAITING
        return scan_status
        #elif Utils.get_vm_location() == VM_LOCAL:                   # antivirus systems, need to copy file to vm
        #    list_file = []
        #    try:
        #        list_file = [scan_folder + x for x in os.listdir(scan_folder)]
        #    except Exception as e:
        #        exc_type, exc_obj, exc_tb = sys.exc_info()
        #        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        #        logger_rew.info('%s %s:%s cannot listdir' %
        #                        (exc_type, fname, exc_tb.tb_lineno))
        #        logger_rew.info(e)
        #    for filepath in list_file:
        #        if Utils.get_ori_name(filepath) == basename(self.path):
        #            md5_status = self.check_md5(filepath)
        #            #logger_rew.info('%s: md5_status: %s' %(self.sname, md5_status))
        #            if md5_status == None:      # cannot access file to get md5
        #                scan_status = SCAN_STATUS_WAITING
        #                # if self.is_remain_after_threshold_time():
        #                #    scan_status = SCAN_STATUS_OVERTIME
        #                # else:
        #                #    scan_status = SCAN_STATUS_WAITING
        #            elif md5_status == False:   # file md5 is changed
        #                scan_status = SCAN_STATUS_DELETED
        #            else:                       # file md5 stay the same
        #                if self.is_remain_after_threshold_time():
        #                    if self.can_be_renamed(filepath):
        #                        logger_rew.info(
        #                            '%s: md5 ok; time ok; rename ok' % self.sname)
        #                        scan_status = SCAN_STATUS_PASS
        #                    else:
        #                        logger_rew.info(
        #                            '%s: cannot rename' % self.sname)
        #                        scan_status = SCAN_STATUS_DELETED
        #                else:
        #                    scan_status = SCAN_STATUS_WAITING  # time is not long enough
        #            #logger_rew.info('%s: scan_status: %s' %(self.sname, scan_status))
        #            if scan_status in [SCAN_STATUS_PASS, SCAN_STATUS_DELETED]:
        #                os.system('rm -f %s/*%s*' %(scan_folder, basename(self.path)))
        #            return scan_status
        #    #logger_rew.info('%s: file not exist' %self.sname)
        #    scan_status = SCAN_STATUS_DELETED
        #    os.system('rm -f %s/*%s*' %(scan_folder, basename(self.path)))
        #    return scan_status
        #elif Utils.get_vm_location() == VM_CLOUD:               # the mv is in the cloud
        #    #md5 = Utils.get_md5_from_cloud(scan_folder, basename(self.current_exe_path))
        #    sha256 = Utils.get_ori_name(self.path)
        #    if sha256 not in dict_sha256_to_md5:
        #        md5 = MD5_FILE_NOT_EXIST
        #    else:
        #        md5 = dict_sha256_to_md5[sha256]
        #    #print('md5:', md5)
        #    if md5 == MD5_TIMEOUT:      # TODO
        #        if self.is_remain_after_threshold_time():
        #            scan_status = SCAN_STATUS_OVERTIME
        #            #Utils.remove_file_on_cloud(scan_folder, '%s*' %(basename(self.path)))
        #        else:
        #            scan_status = SCAN_STATUS_WAITING
        #    elif md5 == MD5_FILE_NOT_EXIST:
        #        scan_status = SCAN_STATUS_DELETED
        #    elif md5 != self.current_exe_md5:
        #        scan_status = SCAN_STATUS_MD5_CHANGED
        #        #Utils.remove_file_on_cloud(scan_folder, '%s*' %(basename(self.path)))
        #    else:   # md5 is the same
        #        if self.is_remain_after_threshold_time():
        #            scan_status = SCAN_STATUS_PASS
        #            #Utils.remove_file_on_cloud(scan_folder, '%s*' %(basename(self.path)))

        #            # TODO support batch rename
        #            #if self.can_be_renamed_on_cloud(scan_folder, basename(self.current_exe_path)):
        #            #    logger_rew.info('%s: md5 ok; time ok; rename ok' % self.sname)
        #            #    scan_status = SCAN_STATUS_PASS
        #            #    Utils.remove_file_on_cloud(scan_folder, '%s*' %(basename(self.path)))
        #            #else:
        #            #    logger_rew.info('%s: cannot rename' % self.sname)
        #            #    scan_status = SCAN_STATUS_DELETED
        #            #    Utils.remove_file_on_cloud(scan_folder, '%s*' %(basename(self.path)))
        #        else:
        #            scan_status = SCAN_STATUS_WAITING  # time is not long enough
        #    #if scan_status in [SCAN_STATUS_PASS, SCAN_STATUS_DELETED]:
        #    #    Utils.remove_file_on_cloud(scan_folder, '%s*' %(basename(self.path)))
        #    return scan_status

    def prepare_action_subset(self):
        if self.seq_cur_x == -1:        # Quick minimzier
            if self.seq_cur_y == 0:
                self.seq_cur_y = 1     # skip the first ''                         # TODO need test case
            elif self.seq_cur_y == -1:  # special -1, try only the last original arm
                self.current_applied_arm_subset = [self.list_applied_arm[-1]]       # TODO need test case
                return
            # Quick Minimizer: try only the last arm first
            list_arm = [None for x in range(len(self.list_applied_arm))]
            action = self.list_applied_arm[self.seq_cur_x].action
            list_mic_action = ACTION_TO_MICROACTION[action]
            # no need to test the original sample

        elif self.seq_cur_x < len(self.list_applied_arm):
            list_arm = copy.deepcopy(self.list_applied_arm)

            # replace kept arm
            for k, v in self.seq_cur_x_to_kept_arm.items():
                #logger_min.info('%s: %d' %(self.sname, k))
                list_arm[k] = v
            action = self.list_applied_arm[self.seq_cur_x].action
            list_mic_action = ACTION_TO_MICROACTION[action]

            # predict not need to apply OA1 if there are other actions
            minimal_action = list_mic_action[self.seq_cur_y]
            if minimal_action == 'OA1' and len([arm for arm in list_arm if arm != None]) > 0:       # TODO need test case, bug
                #self.seq_cur_y += 1
                self.inc_seq_cur_y()
                if self.seq_cur_x > len(list_arm) - 1:
                    return -1
        else:
            return -1

        #logger_min.info('%s %s %s' %(list_mic_action, self.seq_cur_y, list_mic_action[self.seq_cur_y]))
        minimal_action = list_mic_action[self.seq_cur_y]
        if minimal_action == '':          # remove current action
            minimal_arm = None
        elif minimal_action == 'OA':      # only SA need to be minimized to OA
            content = self.list_applied_arm[self.seq_cur_x].content
            minimal_arm = ArmOA(0, content=content)
        elif minimal_action == 'OA1':
            minimal_arm = ArmOA(0, content=bytes([1]))
        elif minimal_action == 'SA1':     # only SA need to be minimized to SA1
            minimal_arm = copy.deepcopy(self.list_applied_arm[self.seq_cur_x])
            minimal_arm.set_content(bytes([1]))
        elif minimal_action == 'SP1':     # only SP need to be minimized to SP1
            minimal_arm = copy.deepcopy(self.list_applied_arm[self.seq_cur_x])
            minimal_arm.set_content(bytes([1]))
        elif minimal_action == 'SR1':     # only SR need to be minimized to SR1
            minimal_arm = copy.deepcopy(self.list_applied_arm[self.seq_cur_x])
            minimal_arm.mutate_section_name_one_byte()
        elif minimal_action == 'CP1':
            minimal_arm = ArmCP1(12)
        else:
            logger_min.error('%s: minimal_action unexpected: [%s]' % (
                self.sname, minimal_action))
            exit()
        list_arm[self.seq_cur_x] = minimal_arm
        #logger_min.info('%s: next try arms:\t%s (%d %d)' %(self.sname, self.get_names_from_arm_list(list_arm), self.seq_cur_x, self.seq_cur_y))
        self.current_applied_arm_subset = list_arm

    def get_names_from_arm_list(self, list_arm):
        list_arm_name = []
        for x in list_arm:
            if x:
                list_arm_name.append(x.action)
            else:
                list_arm_name.append(None)
        return list_arm_name

    def get_minimal_file(self):
        if self.latest_minimal_path:                # minimal sample
            #logger_min.info('%s: latest_minimal_path %s' %(self.sname, self.latest_minimal_path))
            minimal_path = self.latest_minimal_path
        else:                                           # cannot be minimized
            #list_file = [x for x in os.listdir(evasive_folder) if basename(self.path) in x]
            sha256 = basename(self.path)
            list_file = glob.glob('%s%s*' %(evasive_folder, sha256))
            if len(list_file) == 0:
                logger_min.error('cannot find original evasive sample')
                exit()
            minimal_path = list_file[0]
            #logger_min.info('%s: cannot be minimized' %(self.sname))
        return minimal_path

    def replay_action_subset(self):     # For MAB Rewriter
        if len(self.current_applied_arm_subset) == 0:
            logger_min.error('empty replay subset')
            exit()
        input_path = self.path
        for arm in self.current_applied_arm_subset:
            if arm:
                output_path = arm.transfer(input_path, minimizer_output_folder, verbose=False)
                if 'minimizer_output' in os.path.dirname(input_path):
                    os.system('rm %s' %input_path)
                input_path = output_path
                self.set_current_exe_path(output_path)
            ########### else:
            ###########     self.set_current_exe_path(input_path)
        #logger_rew.info('output_path: %s' %output_path)

    def replay_trace(self, trace, output_folder=rewriter_output_folder):   # For GP Rewriter only
        if len(trace) == 0:
            print('empty replay subset')
            logger_min.error('empty replay subset')
            exit()
        input_path = self.path
        for arm in trace:
            if arm:
                output_path = arm.transfer(input_path, output_folder)
                input_path = output_path
                self.set_current_exe_path(output_path)
            else:
                self.set_current_exe_path(input_path)
        return output_path
        #logger_rew.info('output_path: %s' %output_path)

    def get_applied_actions(self):
        return self.get_names_from_arm_list(self.list_applied_arm)
