from utils import *
import pexpect

class MABRewriter:
    def __init__(self, bandit, samples_manager, rand=False):
        self.randomize_path = Utils.get_randomized_folder() 

        self.bandit = bandit
        self.samples_manager = samples_manager
        self.rand = rand
        
    def run_once(self):
        logger_rew.info('====================== %s =====================' %Utils.get_classifier_name())
        for sample in self.samples_manager.list_sample:
            md5 = sample.get_md5(sample.path)
            print(sample.path, md5)
            for arm in self.bandit.list_arm:
                if arm.action == 'CR':
                    continue
                output_path = arm.pull(sample)
                print(output_path)
                if os.path.exists(output_path):
                    md5_arm = sample.get_md5(output_path)
                    if md5 == md5_arm:
                        print('same arm output. rm %s' %output_path)
                        os.system('rm %s' %output_path)
                with open(sample.path, 'rb') as fp:
                    bytez = fp.read()
                    bytez_new = modify_without_breaking(bytez, [ACTION_MAP[arm.action]])
                    output_path_gym = output_path + '_gym'
                    with open(output_path_gym, 'wb') as fp_out:
                        fp_out.write(bytez_new)
                        if os.path.exists(output_path_gym):
                            md5_arm = sample.get_md5(output_path_gym)
                            if md5 == md5_arm:
                                print('same gym output. rm %s' %output_path_gym)
                                os.system('rm %s' %output_path_gym)
        print('rename \'s/\./\_/\' %s/*' %(dirname(output_path)))
        os.system('rename \'s/\./\_/\' %s/*' %(dirname(output_path)))

    def run(self):
        self.samples_manager.get_initial_pending_list()
        #for sample in self.samples_manager.list_sample:
        #    sample.status = SAMPLE_STATUS_PENDING

        trial_amount = self.samples_manager.get_count_with_status(SAMPLE_STATUS_PENDING) * Utils.get_max_pull()
        #logger_rew.info('trial_amount: %d' %trial_amount)
        logger_rew.info('TS: %d update parent: %d' %(Utils.is_thompson_sampling(), Utils.get_update_parent()))

        total_pull_count = 0
        logger_rew.info('===========================================')
        process_count = 0
        count_skip = 0
        count_solve = 0
        count_need = 0
        #while(total_pull_count < trial_amount):
        max_pull_count = Utils.get_max_pull()
        while True:
            sample = self.samples_manager.get_next_sample()
            if sample:
                arm = self.bandit.get_next_arm(sample, sample.get_applied_actions(), rand=self.rand)
                output_path = arm.pull(sample)
                sample.set_current_exe_path(output_path)
                sample.append_arm(arm)
                total_pull_count += 1
                #if Utils.get_vm_location() == VM_CLOUD:
                #    Utils.safe_copy(sample.current_exe_path, rewriter_send_buffer_folder)
                #    #Utils.send_file_to_cloud(self.current_exe_path, scan_folder)
                #else:
                #    sample.copy_to_scan_folder(rewriter_scan_folder)
                sample.copy_to_scan_folder(rewriter_scan_folder)

                # clean up output_folder
                ################# sample.delete_files_except_current_exe(rewriter_output_folder)
                #list_previous = [x for x in os.listdir(rewriter_output_folder) if basename(sample.path) in x and x != basename(sample.current_exe_path)]
                #for x in list_previous:
                #    os.system('rm %s%s' %(rewriter_output_folder, x))

                process_count += 1
                if process_count % 100 == 0:            # update every x pulls
                    logger_rew.info('update rewriter working list')
                    self.samples_manager.update_working_list()
            else:
                count_working = self.samples_manager.get_count_with_status(SAMPLE_STATUS_WORKING)
                if count_working == 0:
                    count_remain = len([x for x in self.samples_manager.get_samples_with_status(SAMPLE_STATUS_PENDING) if x.pull_count < max_pull_count])
                    #print('count_remain: ', count_remain)
                    if count_remain == 0:
                        logger_rew.info('###### All samples are pulled 60 times!')
                        break
                logger_rew.info('All pending samples are processing by arms, or more than %d samples are handing at the same time' %self.samples_manager.sample_concurrent_limit)
                time.sleep(1)
                self.samples_manager.update_working_list()

            #if Utils.get_vm_location() == VM_CLOUD:
            #    # send files to cloud vms if the send_buffer_folder is full or excess time limit.
            #    file_count = len(os.listdir(rewriter_send_buffer_folder))
            #    if file_count > 10: # TODO
            #        Utils.send_folder_to_cloud(rewriter_send_buffer_folder, rewriter_scan_folder)
            
            count_skip = self.samples_manager.get_count_with_status(SAMPLE_STATUS_SKIP)
            count_evasive = self.samples_manager.get_count_with_status(SAMPLE_STATUS_EVASIVE)
            count_minimal = self.samples_manager.get_count_with_status(SAMPLE_STATUS_MINIMAL)
            count_functional = self.samples_manager.get_count_with_status(SAMPLE_STATUS_FUNCTIONAL)
            count_need = len(self.samples_manager.list_sample) - count_skip
            logger_rew.info('-----------------------------------------------')
            logger_rew.info('### [%d/%d (%.2f%%)] skip: %d evasive: %d/%d (%.2f%%) minimal: %d' \
                    %(total_pull_count, trial_amount, total_pull_count/trial_amount * 100, count_skip, \
                    count_evasive + count_minimal + count_functional, count_need, \
                    ((count_evasive + count_minimal + count_functional)/count_need*100), \
                    count_minimal + count_functional))
            logger_rew.info('-----------------------------------------------')

            if Utils.is_cuckoo_enable():
                if count_functional + count_skip == len(self.samples_manager.list_sample):
                    break
            else:
                if count_minimal + count_skip == len(self.samples_manager.list_sample):
                    break

        # wait for remaining working samples to be deleted or evade
        logger_rew.info('wait for remaining working samples')
        while True:
            count_working = self.samples_manager.get_count_with_status(SAMPLE_STATUS_WORKING)
            count_evasive = self.samples_manager.get_count_with_status(SAMPLE_STATUS_EVASIVE)
            count_minimal = self.samples_manager.get_count_with_status(SAMPLE_STATUS_MINIMAL)
            if Utils.is_cuckoo_enable():
                if count_working + count_evasive + count_minimal == 0:
                    break
            else:
                if self.rand == False:
                    if count_working + count_evasive == 0:
                        break
                else:
                    if count_working == 0:
                        break
            #logger_rew.info('count_working: %d' %count_working)
            logger_rew.info('count_working: %d, count_evasive: %d, count_minimal: %d' %(count_working, count_evasive, count_minimal))
            self.samples_manager.update_working_list()
            time.sleep(10)

        logger_rew.info('delete tmp files for list_pending')
        list_pending = self.samples_manager.get_samples_with_status(SAMPLE_STATUS_PENDING)
        for sample in list_pending:
            logger_rew.info('delete tmp files for list_pending')
            sample.delete_tmp_files(rewriter_output_folder)

        logger_rew.info('%%%%%%%%%%%%%%%%%%%%%%%% Rewriter Finish %%%%%%%%%%%%%%%%%%%%%%%%')
        os.system('touch %s' %REWRITER_EXIT_SIGN)
