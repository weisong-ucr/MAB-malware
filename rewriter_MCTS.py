from utils import *
from MCTS import MCTS, Node

class MCTSRewriter:
    def __init__(self, bandit, samples_manager):
        self.bandit = bandit
        self.samples_manager = samples_manager
        self.transformation = 36
        self.transfer_quota = 60

    def run(self):
        #self.samples_manager.get_initial_pending_list()
        for sample in self.samples_manager.list_sample:
            sample.status = SAMPLE_STATUS_PENDING

        # trial_amount = self.samples_manager.get_count_with_status(SAMPLE_STATUS_PENDING) * Utils.get_max_pull()
        # logger_rew.info('trial_amount: %d' %trial_amount)

        total_pull_count = 0
        logger_rew.info('===========================================')
        process_count = 0
        count_skip = 0
        count_solve = 0
        count_fail = 0
        count_need = 0
        # while(total_pull_count < trial_amount):
        list_pending_sample = self.samples_manager.get_samples_with_status(SAMPLE_STATUS_PENDING)
        count_pending = len(list_pending_sample)
        for sample in list_pending_sample:
            logger_min.info('==========================================================')
            logger_min.info(sample.path)
            evasive_path = None
            
            tree = MCTS(self.bandit, self.transfer_quota)
            node = Node(self.bandit, sample.path)
            while True:
                finish = False
                for idx in range(self.transformation):
                    # print('-'*30)
                    # print('do_rollout:', idx)
                    evasive_path, transfer_quota = tree.do_rollout(node)
                    if evasive_path != None:
                        # print('Success! Evasive Path: ', evasive_path)

                        logger_rew.info('### Evade! %s (pull_count: %d)' %(evasive_path, 60 - transfer_quota))
                        print('### Evade! %s (pull_count: %d)' %(evasive_path, 60 - transfer_quota))

                        os.system('cp -p %s %s' %(evasive_path, evasive_folder))
                        os.system('rm %s/*' %(rewriter_output_folder))
                        count_solve += 1
                        finish = True
                        break
                    # print('transfer_quota:', transfer_quota)
                    if transfer_quota == 0:
                        # print('Fail! transfer_quota is empty')
                        os.system('rm %s/*' %(rewriter_output_folder))
                        finish = True
                        count_fail += 1
                        break                        
                if finish:
                    break
                node = tree.choose(node)
                # print('='*30)
            logger_rew.info('RESULT total: %d succ: %d, fail: %d' %(count_pending, count_solve, count_fail))
            print('RESULT total: %d succ: %d, fail: %d' %(count_pending, count_solve, count_fail))
        logger_rew.info('%%%%%%%%%%%%%%%%%%%%%%%% Rewriter Finish %%%%%%%%%%%%%%%%%%%%%%%%')
        exit()
