from utils import *

class Minimizer:
    def __init__(self, samples_manager):
        self.samples_manager = samples_manager

    def run(self):
        while True:
            count_evasive = self.samples_manager.get_count_with_status(SAMPLE_STATUS_EVASIVE)
            count_minimal = self.samples_manager.get_count_with_status(SAMPLE_STATUS_MINIMAL)
            
            if count_evasive == 0:
                logger_min.info('No evasive samples, sleep...')
                time.sleep(5)
            else:
                self.samples_manager.minimize_evasive_sample()
                self.samples_manager.update_evasive_list()
                if Utils.is_cuckoo_enable():
                    self.samples_manager.update_minimal_list()

            if ( Utils.is_cuckoo_enable() and count_evasive + count_minimal == 0 ) or (not Utils.is_cuckoo_enable() and count_evasive == 0):
                if os.path.exists(REWRITER_EXIT_SIGN):
                    logger_min.info('%%%%%%%%%%%%%%%%%%%%%%%% Minimizer Finish %%%%%%%%%%%%%%%%%%%%%%%%')
                    exit()

            time.sleep(0.5)
