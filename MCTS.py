from numpy.core.fromnumeric import mean
from utils import *
from random import choice, randint
from collections import defaultdict
from bandit import Bandit
import copy
import math

from models import *

classifier_name = Utils.get_classifier_name()
if classifier_name == 'malconv':
    MALCONV_MODEL_PATH = 'models/malconv/malconv.checkpoint'
    model = MalConvModel( MALCONV_MODEL_PATH, thresh=0.5 )
elif classifier_name == 'ember2019':
    EMBER_2019_MODEL_PATH = 'models/ember_2019/ember_model.txt'
    model = EmberModel_2019( EMBER_2019_MODEL_PATH, thresh=0.8336 ) 

class Node:
    def __init__(self, bandit, path):
        self.tup = tuple()
        self.bandit = bandit
        self.path = path
        #self.terminal = terminal

    def find_children(self):
        logger_rew.info('find_children')
        # if self.terminal:  # If the game is finished then no moves can be made
        #    return set()
        # Otherwise, you can make a move in each of the empty spots
        # return {self.make_move(i) for i, value in enumerate(self.tup) if value is None}
        children_set = {self.make_move(copy.deepcopy(arm)) for arm in self.bandit.list_arm}
        return children_set

    def find_random_child(self):
        # if self.terminal:
        #    return None  # If the game is finished then no moves can be made
        #empty_spots = [i for i, value in enumerate(self.tup) if value is None]
        #arm = self.bandit.get_random_arm_norepeat_onceonly(self.popul[i].path)
        arm = self.bandit.get_random_arm(self.path)
        return self.make_move(arm)

    # def reward(self):
    #     if not self.terminal:
    #         raise RuntimeError(f"reward called on nonterminal node {node}")
    #     if self.winner is self.turn:
    #         # It's your turn and you've already won. Should be impossible.
    #         raise RuntimeError(f"reward called on unreachable node {node}")
    #     #if self.turn is (not self.winner):
    #     #    return 0  # Your opponent has just won. Bad.
    #     #if self.winner is None:
    #     #    return 0.5  # Board is a tie
    #     # The winner is neither True, False, nor None
    #     raise RuntimeError(f"node has unknown winner type {node.winner}")

    # def is_terminal(self):
    #    return self.terminal

    def make_move(self, arm):
        output_path = arm.transfer(self.path)
        if model.is_evasive(output_path):
            self.evasive_path = output_path
        return Node(self.bandit, output_path)

    def __str__(self):
        return basename(self.path)


class MCTS:
    "Monte Carlo tree searcher. First rollout the tree then choose a move."

    def __init__(self, bandit, transfer_quota, exploration_weight=1):
        self.scores = defaultdict(list)  # score list of each node
        self.visit_count = defaultdict(int)  # total visit count for each node
        self.children = dict()  # children of each node
        self.exploration_weight = exploration_weight
        self.bandit = bandit
        self.random_path_count = 10
        self.random_path_depth = 5
        self.transfer_quota = transfer_quota

    def choose(self, node):
        "Choose the best successor of node. (Choose a move in the game)"
        logger_rew.info('####### choose')
        # if node.is_terminal():
        #    raise RuntimeError(f"choose called on terminal node {node}")
        if node not in self.children:
            return node.find_random_child()

        def score(n):
            if self.visit_count[n] == 0:
                return float("-inf")  # avoid unseen moves
            return sum(self.scores[n]) / self.visit_count[n]  # average scores

        logger_rew.info('-'*30)
        for x in self.children[node]:
            logger_rew.info('average_score: %s %f' %(x, score(x)))

        logger_rew.info('LOG choose: %s %f\n' %(node, score(node)))
        logger_rew.info('LOG choose: %s %f' %(node, score(node)))
        return min(self.children[node], key=score)

    def do_rollout(self, node):
        "Make the tree one layer better. (Train for one iteration.)"
        logger_rew.info('####### do_rollout')
        logger_rew.info('%s len(children): %d' %(node, len(self.children)))
        path = self._select(node)
        logger_rew.info("path: %d %s" %(len(path), [basename(node.path) for node in path]))
        leaf = path[-1]
        logger_rew.info('leaf: %s' %leaf)
        self._expand(leaf)
        scores, evasive_path = self._simulate(leaf)
        if evasive_path != None:
            logger_rew.info('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Evade')
            return evasive_path, self.transfer_quota
        if self.transfer_quota <= 0:
            logger_rew.info('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Quota remain 0')
            return evasive_path, self.transfer_quota
        logger_rew.info('scores: %s' %scores)
        self._backpropagate(path, scores)
        return None, self.transfer_quota

    def _select(self, node):
        "Find an unexplored descendent of `node`"
        logger_rew.info('####### _select')
        path = []
        while True:
            path.append(node)
            if node not in self.children or not self.children[node]:
                # node is either unexplored or terminal
                return path
            unexplored = self.children[node] - self.children.keys()
            if unexplored:
                logger_rew.info('not all children of node already be expended! unexplored: %d' %len(unexplored))
                logger_rew.info('select unexplored child!')
                n = unexplored.pop()
                path.append(n)
                logger_rew.info('LOG leaf: %s' %basename(n.path))
                logger_rew.info('LOG leaf: %s' %basename(n.path))
                return path
            node = self._uct_select(node)  # descend a layer deeper
            #logger_rew.info('LOG _uct_select: %s' %node)
            #logger_rew.info('LOG _uct_select: %s %f' %(node, model.get_score(node.path)))

    def _expand(self, node):
        "Update the `children` dict with the children of `node`"
        logger_rew.info('####### _expand')
        if node in self.children:
            return  # already expanded
        self.children[node] = node.find_children()
        self._print_children(node)

    def _simulate(self, node):
        "Returns the score for a random simulation (to completion) of `node`"
        logger_rew.info('####### _simulate_simulate on leaf node: %s' %node)
        logger_rew.info('generate %d random paths' %self.random_path_count)
        scores = []
        for _ in range(self.random_path_count):
            input_path = node.path
            depth = randint(1, 5)
            for _ in range(depth):
                #arm = self.bandit.get_random_arm_norepeat_onceonly(input_path)
                arm = self.bandit.get_random_arm(input_path)
                #arm.content = None
                #logger_rew.info(arm, arm.action)
                output_path = arm.transfer(input_path)
                if model.is_evasive(output_path):
                    return [], output_path
                self.transfer_quota -= 1
                logger_rew.info('transfer_quota: %d' %self.transfer_quota)
                if self.transfer_quota <=0:
                    return [], None
                input_path = output_path
            score = model.get_score(output_path)
            logger_rew.info('%s %f' %(basename(output_path), score))
            scores.append(score)
        return scores, None

    def _backpropagate(self, path, scores):
        "Send the score back up to the ancestors of the leaf"
        logger_rew.info('####### _backpropagate')
        for node in reversed(path):
            self.visit_count[node] += len(scores)
            self.scores[node] += scores
        self._print_visit_count()
        self._print_scores()

    def _uct_select(self, node):
        "Select a child of node, balancing exploration & exploitation"
        logger_rew.info('####### _uct_select')

        # All children of node should already be expanded:
        assert all(n in self.children for n in self.children[node])

        log_N_vertex = math.log(self.visit_count[node])

        def uct(n):
            "Upper confidence bound for trees"
            return mean(self.scores[n]) / self.visit_count[n] + self.exploration_weight * math.sqrt(
                log_N_vertex / self.visit_count[n]
            )

        logger_rew.info('%s' %[uct(x) for x in self.children[node]])
        logger_rew.info('select child with max uct')
        return max(self.children[node], key=uct)

    def _uct_approximate_select(self, node):
        "Select a child of node, balancing exploration & exploitation"
        logger_rew.info('####### _uct_approximate_select')

        # All children of node should already be expanded:
        assert all(n in self.children for n in self.children[node])

        log_N_vertex = math.log(self.visit_count[node])

        def uct(n):
            "Upper confidence bound for trees"
            return mean(self.scores[n]) / self.visit_count[n] + self.exploration_weight * math.sqrt(
                log_N_vertex / self.visit_count[n]
            )

        logger_rew.info('%s' %[uct(x) for x in self.children[node]])
        logger_rew.info('select child with max uct')
        return max(self.children[node], key=uct)
    
    def _print_visit_count(self):
        logger_rew.info('------------------------------------------ visit_count')
        for k, v in self.visit_count.items():
            logger_rew.info('%s\t%d' %(k, v))

    def _print_scores(self):
        logger_rew.info('------------------------------------------ scores')
        for k, v in self.scores.items():
            logger_rew.info('%s\t%f %s' %(k, mean(v), v))

    def _print_children(self, node):
        logger_rew.info('------------------------------------------ %s' %node)
        for child in self.children[node]:
            logger_rew.info(child)
