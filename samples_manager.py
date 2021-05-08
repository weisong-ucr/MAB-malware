from utils import *
import random
from models import *
from sample import Sample
from arm import *

class SamplesManager:
    def __init__(self, sample_folder, bandit):
        self.sample_folder = sample_folder
        self.bandit = bandit
        self.bandit.samples_manager = self
        self.cuckoo = Cuckoo() if Utils.is_cuckoo_enable() else None
        self.list_sample = []   # all samples

        self.sample_concurrent_limit = Utils.get_max_working_sample_count()

        #list_file = os.listdir(sample_folder)
        list_file = glob.glob('%s*' %sample_folder)
        list_file.sort()
        for x in list_file:
            sample = Sample(x)
            self.list_sample.append(sample)
        
        # vm last delete time
        #self.dict_vm_ip_to_delete_time = {}

        #self.rewriter_deleted_samples = []
        #self.minimizer_deleted_samples = []

    def get_samples_with_status(self, status):
        return [ sample for sample in self.list_sample if sample.status == status ]

    def get_count_with_status(self, status):
        count = 0
        for sample in self.list_sample:
            if sample.status == status:
                count += 1
        return count

    #def send_files_to_cloud(self, folder_path, dst_path, move=True):
    #    list_sha256_send = [Utils.get_ori_name(x) for x in os.listdir(folder_path)]
    #    if len(list_sha256_send) == 0:
    #        return
    #    #print(dst_path)

    #    vm_ip = Utils.get_random_vm_ip()    # TODO support multiple vms
    #    for sha256 in list_sha256_send:
    #        dict_sha256_to_vm_ip[sha256] = vm_ip    # TODO

    #    tmp_folder = 'output/%s' %datetime.now().strftime("%y%m%d_%H%M%S")
    #    os.system('mkdir %s' %tmp_folder)
    #    if move:
    #        os.system('mv %s/* %s' %(folder_path, tmp_folder))
    #    else:
    #        os.system('cp -p %s/* %s' %(folder_path, tmp_folder))

    #    package_path = 'output/%s.tar' %basename(tmp_folder)
    #    cmd = 'tar --directory=%s -cvf %s . > /dev/null 2>&1' %(tmp_folder, package_path)
    #    #print(cmd)
    #    os.system(cmd)

    #    vm_username = Utils.get_vm_username()

    #    cmd = 'scp %s %s@%s:%s' %(package_path, vm_username, vm_ip, dst_path)
    #    #print(cmd)
    #    Utils.execute_on_cloud(cmd)

    #    cmd = 'ssh %s@%s "tar -xf %s%s -C %s"' %(vm_username, vm_ip, dst_path, basename(package_path), dst_path)
    #    #print(cmd)
    #    Utils.execute_on_cloud(cmd)

    #    cmd = 'ssh %s@%s del /Q %s%s' %(vm_username, vm_ip, dst_path, basename(package_path))
    #    #print(cmd)
    #    Utils.execute_on_cloud(cmd)

    #    os.system('rm -r %s' %tmp_folder)
    #    os.system('rm -r %s' %package_path)

    #    # TODO update send time and sample.status
    #    for sample in self.list_sample:
    #        #print(basename(sample.path))
    #        if basename(sample.path) in list_sha256_send:
    #            sample.scan_status = SCAN_STATUS_WAITING
    #            sample.copy_time = time.time()

    #def remove_files_on_cloud(self, scan_folder, samples):
    #    #list_file = [basename(sample.path) + '*' for sample in samples]
    #    list_file = [basename(sample.current_exe_path) for sample in samples]
    #    vm_ips = Utils.get_vm_ips()
    #    for vm_ip in vm_ips:
    #        cmd = 'ssh %s@%s "cd %s & del /Q %s"' %(Utils.get_vm_username(), vm_ip, scan_folder, ' '.join(list_file))
    #        #print(cmd)
    #        Utils.execute_on_cloud(cmd)
    #    samples[:] = []

    def get_next_sample(self):
        list_pending = self.get_samples_with_status(SAMPLE_STATUS_PENDING)
        max_pull_count = Utils.get_max_pull()
        list_pending = [x for x in list_pending if x.pull_count < max_pull_count]
        if len(list_pending) > 0:
            #for _ in range(10):
            count_working = self.get_count_with_status(SAMPLE_STATUS_WORKING)
            if count_working >= self.sample_concurrent_limit:
                logger_rew.info('concurrent sample %d is more than %d, waiting...' %(count_working, self.sample_concurrent_limit))
                return None
            else:
                sample = random.choice(list_pending)
                sample.status = SAMPLE_STATUS_WORKING
                count_working = self.get_count_with_status(SAMPLE_STATUS_WORKING)
                logger_rew.info('select pending sample: %s (pull_count:%d)' %(sample.sname, sample.pull_count))
                logger_rew.info('count_working: %d' %count_working)
                return sample

    def get_initial_pending_list(self):
        logger_rew.info('check whether classifier can detect the original samples...')
        #if Utils.get_vm_location() == VM_LOCAL:
        for sample in self.list_sample:
            #logger_rew.info('copy_to_scan_folder: %s' %sample.sname)
            sample.copy_to_scan_folder(rewriter_scan_folder)
            if Utils.get_classifier_scan_type() == SCAN_TYPE_AV:
                time.sleep(1)
        logger_rew.info('copy finish')
        while(True):
            for sample in self.list_sample:
                if sample.status == None:
                    scan_status = sample.check_scan_status(rewriter_scan_folder)
                    #logger_rew.info('%s: %s' %(sample.sname, scan_status))
                    #if scan_status in [SCAN_STATUS_DELETED, SCAN_STATUS_OVERTIME]:
                    if scan_status == SCAN_STATUS_DELETED:
                        sample.status = SAMPLE_STATUS_PENDING
                    elif scan_status == SCAN_STATUS_PASS:
                        sample.status = SAMPLE_STATUS_SKIP
            count_all = len(self.list_sample)
            count_pending = count_skip = 0
            for sample in self.list_sample:
                if sample.status == SAMPLE_STATUS_PENDING:
                    count_pending += 1
                elif sample.status == SAMPLE_STATUS_SKIP:
                    count_skip += 1
            logger_rew.info('(%d/%d): detect %d, fail %d' %(count_pending + count_skip, count_all, count_pending, count_skip))
            time.sleep(2)
            if count_pending + count_skip == len(self.list_sample):
                break
        logger_rew.info('check finish.')
        logger_rew.info('remove remaining files.')
        #if Utils.get_vm_location() == VM_LOCAL:
        os.system('rm -f %s/*' %rewriter_scan_folder)
        #elif Utils.get_vm_location() == VM_CLOUD:
        #    Utils.remove_file_on_cloud(rewriter_scan_folder, '*')
        #elif Utils.get_vm_location() == VM_CLOUD:
        #    self.send_files_to_cloud(Utils.get_malware_folder(), rewriter_scan_folder, move=False)
        #    #time.sleep(Utils.get_wait_time())
        #    time.sleep(30)
        #    #dict_sha256_to_md5 = Utils.get_md5s_from_cloud(rewriter_scan_folder)
        #    for sample in self.list_sample:
        #        #scan_status = sample.check_scan_status(rewriter_scan_folder, dict_sha256_to_md5)
        #        scan_status = sample.check_scan_status(rewriter_scan_folder)
        #        if scan_status == SCAN_STATUS_DELETED:
        #            sample.status = SAMPLE_STATUS_PENDING
        #        elif scan_status == SCAN_STATUS_PASS:
        #            sample.status = SAMPLE_STATUS_SKIP
        #    count_all = len(self.list_sample)
        #    count_pending = count_skip = 0
        #    for sample in self.list_sample:
        #        if sample.status == SAMPLE_STATUS_PENDING:
        #            count_pending += 1
        #        elif sample.status == SAMPLE_STATUS_SKIP:
        #            count_skip += 1
        #    logger_rew.info('(%d/%d): detect %d, fail %d' %(count_pending + count_skip, count_all, count_pending, count_skip))
        #    logger_rew.info('check finish.')
        #    logger_rew.info('remove remaining files.')
        #    #if Utils.get_vm_location() == VM_LOCAL:
        #    #    os.system('rm -f %s/*' %rewriter_scan_folder)
        #    #elif Utils.get_vm_location() == VM_CLOUD:
        #    #    Utils.remove_file_on_cloud(rewriter_scan_folder, '*')
        #    os.system('rm -f %s/*' %rewriter_scan_folder)

    def update_working_list(self):
        # send all remaining files in send_buffer_folder
        #self.send_files_to_cloud(rewriter_send_buffer_folder, rewriter_scan_folder)
        list_working = self.get_samples_with_status(SAMPLE_STATUS_WORKING)
        logger_rew.info('len list_working: %d' %len(list_working))
        list_fail = []
        list_succ = []
        #dict_sha256_to_md5 = Utils.get_md5s_from_cloud(rewriter_scan_folder)
        #print(dict_sha256_to_md5)

        #print('len(list_working):', len(list_working))
        for sample in list_working:
            sha256 = Utils.get_ori_name(sample.path)
            #vm_ip = Utils.get_vm_ip(sha256)
            #scan_status = sample.check_scan_status(rewriter_scan_folder, dict_sha256_to_md5)
            scan_status = sample.check_scan_status(rewriter_scan_folder)
            #print('scan_status:', sha256, scan_status)
            #if scan_status in [SCAN_STATUS_OVERTIME, SCAN_STATUS_PASS, SCAN_STATUS_MD5_CHANGED]:
            #    #print(basename(sample.current_exe_path), scan_status)
            #    #TODO
            #    pass
            #    #self.rewriter_deleted_samples.append(sample)
            #if scan_status == SCAN_STATUS_DELETED:
            #    self.dict_vm_ip_to_delete_time[vm_ip] = datetime.now()
            # TODO
            #if vm_ip not in self.dict_vm_ip_to_delete_time:
            #    time_diff = 0
            #else:
            #    time_diff = (datetime.now() - self.dict_vm_ip_to_delete_time[vm_ip]).total_seconds()
            #print(time_diff)
            #if time_diff > 60:
            #    print('vm get stuck, sleep, waiting for interaction')
            #    time.sleep(1000)
            #logger_rew.info('update rewriter: %s [%s]' %(sample.sname, scan_status))
            if len(sample.list_applied_arm) > 0:
                #logger_rew.info('arm list: %s' %[id(x) for x in sample.list_applied_arm])
                if scan_status == SCAN_STATUS_DELETED:
                    list_fail.append(sample)
                elif scan_status == SCAN_STATUS_PASS:
                    list_succ.append(sample)

        #print('fail:', len(list_fail))
        #print('succ:', len(list_succ))

        for sample in list_fail:
            if len(sample.list_applied_arm) > 0:
                last_arm = sample.list_applied_arm[-1]
                # update reward for the last arm beta +1
                self.bandit.update_reward_with_alpha_beta(last_arm.idx, 0, 1)
                if len(sample.list_applied_arm) >= sample.max_length:
                    # restart: delete all related 1) arms 2) files on disk after max_length(10) tries
                    logger_rew.info('restart: delete %s related arms and files on disk after max_length(%d) tries' %(sample.sname, sample.max_length))
                    sample.delete_applied_arm()
                    sample.delete_tmp_files(rewriter_output_folder)
                    sample.set_current_exe_path(sample.path)
                #self.rewriter_deleted_samples.append(sample)
                sample.status = SAMPLE_STATUS_PENDING
        for sample in list_succ:
            last_arm = sample.list_applied_arm[-1]
            logger_rew.info('### Evade! %s (pull_count: %d)' %(sample.current_exe_path, sample.pull_count))
            ## upate reward the last arm alpha +1       # now we update reward only after minimization
            #self.bandit.update_reward_with_alpha_beta(last_arm.idx, 1, 0)
            #if last_arm.idx in [0, 1, 2, 3]:        # OA SA SR SP
            #    self.bandit.add_new_arm(last_arm)

            logger_rew.info('%s exists: %d' %(sample.current_exe_path, os.path.exists(sample.current_exe_path)))
            logger_rew.info('mv %s %s' %(sample.current_exe_path, evasive_folder))
            os.system('mv %s %s' %(sample.current_exe_path, evasive_folder))
            new_path = evasive_folder + basename(sample.current_exe_path)
            logger_rew.info('%s exists: %d' %(new_path, os.path.exists(new_path)))

            sample.evasive_path = evasive_folder + basename(sample.current_exe_path)
            sample.set_current_exe_path(sample.evasive_path)
            # remove tmp files  # TODO
            #sample.delete_scan_folder_copy(rewriter_scan_folder)
            #self.rewriter_deleted_samples.append(sample)
            os.system('rm -f %s%s' %(rewriter_scan_folder, basename(sample.current_exe_path)))
            sample.delete_tmp_files(rewriter_output_folder)
            sample.scan_status = SCAN_STATUS_DELETED        # for minimization
            sample.status = SAMPLE_STATUS_EVASIVE
        logger_rew.info('==============================================')
        logger_rew.info('list_arm: %d' %len(self.bandit.list_arm))
        for idx, arm in enumerate(self.bandit.list_arm):
            # Bayesian UCB
            logger_rew.info('%-2d %-12s alpha: %-3d beta: %-3d' %(arm.idx, arm.description, self.bandit._as[idx], self.bandit._bs[idx]))
        logger_rew.info('==============================================')

        # TODO
        #if len(self.rewriter_deleted_samples) > 0:
        #    self.remove_files_on_cloud(rewriter_scan_folder, self.rewriter_deleted_samples)
        #    #self.rewriter_deleted_samples = []

    def minimize_evasive_sample(self):
        list_evasive = self.get_samples_with_status(SAMPLE_STATUS_EVASIVE)
        for sample in list_evasive:
            #logger_min.info('sample.scan_status: %s' %sample.scan_status)
            if sample.scan_status in [SCAN_STATUS_DELETED, SCAN_STATUS_PASS]:
                if sample.seq_cur_x < len(sample.list_applied_arm):
                    ret = sample.prepare_action_subset()
                    if ret == -1:
                        continue
                    sample.replay_action_subset()
                    ori_arm_names = str(sample.get_names_from_arm_list(sample.list_applied_arm)).replace('\'', '').replace(' ', '').replace('None', '--')
                    cur_arm_names = str(sample.get_names_from_arm_list(sample.current_applied_arm_subset)).replace('\'', '').replace(' ', '').replace('None', '--')
                    logger_min.info('%s: %s (%d, %d) %s' %(sample.sname, ori_arm_names, sample.seq_cur_x, sample.seq_cur_y, cur_arm_names))
                    #if Utils.get_vm_location() == VM_CLOUD:
                    #    Utils.safe_copy(sample.current_exe_path, minimizer_scan_folder)
                    #else:
                    #   sample.copy_to_scan_folder(minimizer_scan_folder)
                    #   sample.scan_status = SCAN_STATUS_WAITING
                    sample.copy_to_scan_folder(minimizer_scan_folder)

                    # clean up output_folder
                    ################################ sample.delete_files_except_current_exe(minimizer_output_folder)
                    #list_previous = [x for x in os.listdir(minimizer_output_folder) if basename(sample.path) in x and x != basename(sample.current_exe_path)]
                    #for x in list_previous:
                    #    os.system('rm %s%s' %(minimizer_output_folder, x))

    def update_evasive_list(self):
        # send all remaining files in send_buffer_folder
        #self.send_files_to_cloud(minimizer_send_buffer_folder, minimizer_scan_folder)
        #dict_sha256_to_md5 = Utils.get_md5s_from_cloud(minimizer_scan_folder)
        #print(dict_sha256_to_md5)
        list_evasive = self.get_samples_with_status(SAMPLE_STATUS_EVASIVE)
        #print('len evasive:', len(list_evasive))
        for sample in list_evasive:
            if sample.scan_status == SCAN_STATUS_WAITING:
                #sample.scan_status = sample.check_scan_status(minimizer_scan_folder, dict_sha256_to_md5)
                sample.scan_status = sample.check_scan_status(minimizer_scan_folder)
                #print('sample.scan_status:', sample.scan_status)
                #print(basename(sample.path), 'sample.scan_status:', sample.scan_status)
                #if scan_status in [SCAN_STATUS_OVERTIME, SCAN_STATUS_PASS, SCAN_STATUS_MD5_CHANGED]:
                #    self.minimizer_deleted_samples.append(sample)
                #logger_min.info('%s: [%s]' %(sample.sname, sample.scan_status))
                if sample.scan_status == SCAN_STATUS_DELETED:
                    logger_min.info('%s: [FAIL] %s' %(sample.sname, sample.current_exe_path))
                    if sample.seq_cur_y == 0:
                        sample.list_useful_arm_idxs.append(sample.seq_cur_x)
                    sample.inc_seq_cur_y()
                    # clean up: remove current sample
                    #if 'minimizer_output' in sample.current_exe_path:
                    #    #logger_min.info('rm -f %s' %(sample.current_exe_path))
                    #    os.system('rm -f %s' %(sample.current_exe_path))
                elif sample.scan_status == SCAN_STATUS_PASS:
                    sample.latest_minimal_path = sample.current_exe_path
                    logger_min.info('%s: [SUCC] %s' %(sample.sname, sample.current_exe_path))
                    if len([arm for arm in sample.current_applied_arm_subset if arm]) == 1:
                        logger_min.info('%s: [SUCC] Quick Minimize ' %(sample.sname))
                        sample.list_useful_arm_idxs.append(len(sample.list_applied_arm) - 1)
                        sample.status = SAMPLE_STATUS_MINIMAL
                    sample.seq_cur_x_to_kept_arm[sample.seq_cur_x] = sample.current_applied_arm_subset[sample.seq_cur_x]

                    # clean up scan_folder
                    os.system('rm -f %s/%s*' %(minimizer_scan_folder, basename(sample.path)))
                    #sample.delete_scan_folder_copy(minimizer_scan_folder)
                    #self.minimizer_deleted_samples.append(sample)

                    ## clean up output_folder 
                    #list_previous_evasive = [x for x in os.listdir(minimizer_output_folder) if basename(sample.path) in x and x != basename(sample.current_exe_path)]
                    #for x in list_previous_evasive:
                    #    #logger_min.info('rm %s%s' %(minimizer_output_folder, x))
                    #    os.system('rm %s%s' %(minimizer_output_folder, x))

                    #sample.scan_status = SCAN_STATUS_DELETED
                    sample.list_minimal_arm = [ arm for arm in sample.current_applied_arm_subset if arm ]
                    sample.inc_seq_cur_x()
            if sample.seq_cur_x >= len(sample.list_applied_arm) or sample.status == SAMPLE_STATUS_MINIMAL:
                sample.status = SAMPLE_STATUS_MINIMAL

                minimal_path = sample.get_minimal_file()
                logger_min.info('%s: ###### [FINISH] %s' %(sample.sname, minimal_path))
                os.system('cp -p %s %s' %(minimal_path, minimal_folder))

                # find essential arms
                if len(sample.list_minimal_arm) == 0:
                    sample.list_minimal_arm = [ arm for arm in sample.list_applied_arm if arm ]
                logger_min.info('list_minimal_arm: %s' %sample.get_names_from_arm_list(sample.list_minimal_arm))

                # update reward
                for idx in sample.list_useful_arm_idxs:
                    ori_arm = sample.list_applied_arm[idx]
                    if idx < len(sample.list_applied_arm) - 1:
                        logger_min.info('update_reward_with_alpha_beta(%d, 1, -1)' %ori_arm.idx)
                        self.bandit.update_reward_with_alpha_beta(ori_arm.idx, 1, -1)   # beta -1 because +1 when fail
                    else:
                        logger_min.info('update_reward_with_alpha_beta(%d, 1, 0)' %ori_arm.idx)
                        self.bandit.update_reward_with_alpha_beta(ori_arm.idx, 1, 0)
                    if ori_arm.idx in [0, 1, 2, 3]:     # OA SA SR SP
                        self.bandit.add_new_arm(ori_arm)

                # clean up at the end
                #sample.delete_scan_folder_copy(minimizer_scan_folder)
                #self.minimizer_deleted_samples.append(sample)
                sample.delete_tmp_files(minimizer_output_folder)

        #if len(self.minimizer_deleted_samples) > 0:
        #    self.remove_files_on_cloud(minimizer_scan_folder, self.minimizer_deleted_samples)

    def update_minimal_list(self):
        list_minimal = self.get_samples_with_status(SAMPLE_STATUS_MINIMAL)
        for sample in list_minimal:
            # if not submitted, submit, otherwise get existing task_id
            minimal_path = sample.get_minimal_file()
            task_id = self.cuckoo.get_task_id(minimal_path)
            #logger_cuc.info('task_id: %s' %task_id)

            cuckoo_status = self.cuckoo.get_task_status(task_id)
            #logger_cuc.info('%s: cuckoo_status: %s' %(sample.sname, cuckoo_status))

            if cuckoo_status == 'reported':
                functional = self.cuckoo.is_functional(task_id, sample.path)
                if functional:
                    # evasive and functional, copy to the final output folder
                    logger_cuc.info('%s: Evasive sample is functional' %sample.sname)
                    os.system('mv %s %s' %(minimal_path, functional_folder))
                    sample.status = SAMPLE_STATUS_FUNCTIONAL    ########################## this sample is done.
                else:
                    # non-functional, try again
                    logger_cuc.info('%s: Evasive sample is broken, add it back to pool' %sample.sname)
                    #sample.update_broken_action_idxs()
                    sample.reset()      # reset members, except broken_action_idxs!!
                    sample.status = SAMPLE_STATUS_PENDING   ########################## add back to pending queue
                self.cuckoo.del_sample_and_task(minimal_path)    # clean up cuckoo
            else:
                time.sleep(1)
