from bandit import *
import threading

if __name__ == '__main__':

    logger_rew.info('============= Start ============')

    bandit = Bandit()
    samples_manager = SamplesManager(Utils.get_malware_folder(), bandit)

    rewriter = Rewriter(bandit, samples_manager)
    rewriter.run_once()

    print("Done!")
