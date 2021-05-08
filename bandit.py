import copy
from scipy.stats import beta
from utils import *
from arm import *


class Bandit:
    def __init__(self):
        #self.arm_limit = get_max_working_arm_count()

        self.samples_manager = None
        #self.samples_used_to_increase_alpha = set()

        self.list_arm = []
        self.list_arm.append(ArmOA(0))
        self.list_arm.append(ArmSA(1))
        self.list_arm.append(ArmSP(2))
        self.list_arm.append(ArmSR(3))
        self.list_arm.append(ArmRD(4))
        self.list_arm.append(ArmRC(5))
        self.list_arm.append(ArmBC(6))
        self.list_arm.append(ArmCR(7))
        #self.list_arm.append(ArmOA(8, content=bytes([1])))    # OA1
        #self.list_arm.append(ArmSA(9, content=bytes([1])))    # SA1
        #self.list_arm.append(ArmSP(10, content=bytes([1])))   # SP1
        #self.list_arm.append(ArmSR(11, mutate_one_byte=True)) # SR1
        #self.list_arm.append(ArmCP1(12))                                                            # CP1
        self.idx_to_ori_idx = {}

        # Bayesian UCB
        #self.counts = [0] * len(self.list_arm)
        self.c = 3
        self._as = [1] * len(self.list_arm)
        self._bs = [1] * len(self.list_arm)
        # logger_rew.info(self.list_arm)
        
        # used ONCE_ONLY arm
        self.used_once_only_arm_idxs = set()
        self.random_arm_count = 0

    def get_random_arm(self, path):           # for GP and MCTS only, not for MAB
        idx = None
        if self.random_arm_count == 0:
            cr_path = Utils.get_randomized_folder() + Utils.get_ori_name(path) + '.CR'
            if os.path.exists(cr_path):
                self.random_arm_count += 1
                idx = 7
        if not idx:
            idx = random.randint(0, 6)
        arm = copy.deepcopy(self.list_arm[idx])
        self.random_arm_count += 1
        return arm
    
    def get_random_arm_norepeat_onceonly(self, path):           # for GP and MCTS only, not for MAB
        idx = None
        if self.random_arm_count == 0:
            cr_path = Utils.get_randomized_folder() + Utils.get_ori_name(path) + '.CR'
            if os.path.exists(cr_path):
                self.random_arm_count += 1
                idx = 7
        if not idx:
            idx = random.randint(0, 6)
            while idx in self.used_once_only_arm_idxs:
                #print('select once_only arm %s, reselect ...' %arm.action)
                idx = random.randint(0, 6)
        #print('finally got %s' %arm.action)
        if idx in [4,5,6,7]:
            self.used_once_only_arm_idxs.add(idx)
            #print('select once_only arm %s' %arm.action)
        arm = copy.deepcopy(self.list_arm[idx])
        self.random_arm_count += 1
        return arm
    
    def get_next_arm(self, sample, list_action, rand=False):
        # Bayesian UCB
        # list_value = [self._as[x] / float(self._as[x] + self._bs[x]) + beta.std(
        #        self._as[x], self._bs[x]) * self.c for x in range(len(self.list_arm))]
        #
        # logger_rew.info(list_value)
        #max_value = max(list_value)
        #list_max_value_idx = []
        # for idx, i in enumerate(list_value):
        #    if i == max_value:
        #        list_max_value_idx.append(idx)
        #idx = random.choice(list_max_value_idx)

        #print('list_action:', list_action)
        cr_path = Utils.get_randomized_folder() + Utils.get_ori_name(sample.path) + '.CR'
        if len(list_action) == 0 and os.path.exists(cr_path) and random.randint(0, 1) == 1: # 50% chance to use CR action if .CR exists for the first action 
            idx = 7
        else:
            if rand:
                idx = random.randint(0, 6)
            else:
                while True:
                    # Tompson Sampling
                    samples = [np.random.beta(self._as[x], self._bs[x]) for x in range(len(self.list_arm))]
                    idx = max(range(len(self.list_arm)), key=lambda x: samples[x])
                    if idx not in [4, 5, 6, 7] \
                            or (idx == 4 and 'RD' not in list_action) \
                            or (idx == 5 and 'RC' not in list_action) \
                            or (idx == 6 and 'BC' not in list_action):
                        break

        arm = copy.deepcopy(self.list_arm[idx])
        return arm

    def update_reward_with_alpha_beta(self, idx, alpha, beta):
        logger_rew.info('update_reward_with_alpha_beta: update %d with alpha: %d beta: %d' % (idx, alpha, beta))
        if Utils.is_thompson_sampling() == False:
            return

        # Bayesian UCB
        # Update Gaussian posterior
        if idx >= len(self._as): #TODO
            print(idx, len(self._as))
        self._as[idx] += alpha
        self._bs[idx] += beta

        if Utils.get_update_parent():
            # if child succ, give ori reward too!
            if alpha == 1:
                if idx in self.idx_to_ori_idx:
                    ori_idx = self.idx_to_ori_idx[idx]
                    self._as[ori_idx] += alpha

    def add_new_arm(self, new_arm):
        if Utils.is_thompson_sampling() == False:
            return
        ori_idx = new_arm.idx
        new_arm.idx = len(self.list_arm)

        self.idx_to_ori_idx[new_arm.idx] = ori_idx

        # find existing arm
        new_arm.update_description()
        for idx, arm in enumerate(self.list_arm):
            if arm.description == new_arm.description:    # arm already exist, update existing arm
                logger_rew.info('no need to add a new arm, update existing arm')
                self._as[idx] += 1
                return

        # add a new arm, append _as _bs
        self.list_arm.append(new_arm)
        # Bayesian UCB
        # self._as.append(self._as[ori_idx])
        # self._bs.append(self._bs[ori_idx])
        self._as.append(1)
        self._bs.append(1)
