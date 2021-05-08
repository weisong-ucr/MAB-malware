from bandit import Bandit
from minimizer import Minimizer
from rewriter_MAB import MABRewriter
from rewriter_GP import GPRewriter
from rewriter_MCTS import MCTSRewriter
from samples_manager import SamplesManager
from utils import *
import random
import threading
from classifier import Classifier

random.seed(10)

if __name__ == '__main__':
    logger_rew.info('============= Start ============')
    logger_min.info('============= Start ============')
    Utils.print_configure()
    Utils.create_folders()

    bandit = Bandit()
    samples_manager = SamplesManager(Utils.get_malware_folder(), bandit)

    print('\n### Log can be found in the log/ folder ###\n')
    if Utils.get_classifier_scan_type() == SCAN_TYPE_MODEL:
        classifier = Classifier(Utils.get_classifier_name())
        classifier_thread = threading.Thread(target=classifier.run)
        print('start classifier...')
        classifier_thread.start()

    rewriter_type = Utils.get_rewriter_type()
    if rewriter_type == 'MAB':
        rewriter = MABRewriter(bandit, samples_manager)
        minimizer = Minimizer(samples_manager)

        rewriter_thread = threading.Thread(target=rewriter.run)
        minimizer_thread = threading.Thread(target=minimizer.run)

        print('start rewriter...')
        rewriter_thread.start()
        print('start minimizer...')
        minimizer_thread.start()

        rewriter_thread.join()
        minimizer_thread.join()
    elif rewriter_type == 'GP':
        rewriter = GPRewriter(bandit, samples_manager)
        rewriter.run()
    elif rewriter_type == 'MCTS':
        rewriter = MCTSRewriter(bandit, samples_manager)
        rewriter.run()
    elif rewriter_type == 'RAND':
        rewriter = MABRewriter(bandit, samples_manager, rand=True)
        rewriter.run()

    if Utils.get_classifier_scan_type() == SCAN_TYPE_MODEL:
        classifier_thread.join()
    print("Done!")
