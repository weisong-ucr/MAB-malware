from utils import *
import random
import copy
from arm import *
#from lib.common import touch, deepcopy
MAX_SCORE = 65535
from copy import deepcopy
from models import *

classifier_name = Utils.get_classifier_name()
if classifier_name == 'malconv':
    MALCONV_MODEL_PATH = 'models/malconv/malconv.checkpoint'
    model = MalConvModel( MALCONV_MODEL_PATH, thresh=0.5 )
elif classifier_name == 'ember2019':
    EMBER_2019_MODEL_PATH = 'models/ember_2019/ember_model.txt'
    model = EmberModel_2019( EMBER_2019_MODEL_PATH, thresh=0.8336 ) 

class GPRewriter:
    def __init__(self, bandit, samples_manager):
        self.randomize_path = Utils.get_randomized_folder()

        self.bandit = bandit
        self.samples_manager = samples_manager
        self.success_traces = []
        self.promising_traces = []
        self.traces = []
        self.pop_size = 6
        self.max_gen = 10
        self.vid_from_trace = []

    def run(self):
        #self.samples_manager.get_initial_pending_list()
        for sample in self.samples_manager.list_sample:
            sample.status = SAMPLE_STATUS_PENDING

        logger_rew.info(
            '========================================================================')
        count_solve = 0
        count_fail = 0
        succ_count = fail_count = 0
        list_working = self.samples_manager.get_samples_with_status(SAMPLE_STATUS_PENDING)
        logger_rew.info(len(list_working))
        list_success_trace = []
        list_promising_trace = []
        list_pending_sample = self.samples_manager.get_samples_with_status(SAMPLE_STATUS_PENDING)
        count_pending = len(list_pending_sample)
        for sample in list_pending_sample:
            logger_rew.info(
                '========================================================================')
            seed_fitness = model.get_score(sample.path)
            best_score = MAX_SCORE
            logger_rew.info('seed_fitness = %f' % seed_fitness)

            self.fitness_scores = {}

            self.popul = self.initial_population(sample)
            self.generation = 1

            while self.generation <= self.max_gen:
                logger_rew.info("There're %d variants in population at generation %d." % (
                    len(self.popul), self.generation))

                scores = []
                for variant in self.popul:
                    score = model.get_score(variant.current_exe_path)
                    logger_rew.info('%s %f' % (basename(variant.current_exe_path), score))
                    scores.append(score)

                self.fitness_scores[self.generation] = scores

                if min(scores) < model.thresh:
                    best_score = min(scores)
                    logger_rew.info("Already got a low score [%f]>%f variant, break the GP process." % (min(scores), model.thresh))
                    count_solve += 1

                    # backup evasive samples
                    evasive_path = self.popul[scores.index(min(scores))].current_exe_path
                    os.system('cp -p %s %s' % (evasive_path, evasive_folder))

                    logger_rew.info('### Evade! %s (pull_count: %d)' %(evasive_path, (self.generation-1) * self.pop_size + scores.index(min(scores))))
                    print('### Evade! %s (pull_count: %d)' %(evasive_path, (self.generation-1) * self.pop_size + scores.index(min(scores))))

                    # Store the success traces.
                    for i in range(len(scores)):
                        score = scores[i]
                        if score < model.thresh:
                            success_trace = self.popul[i].list_applied_arm
                            if len(success_trace) > 0:
                                self.success_traces.append(success_trace)
                    break

                elif self.generation == self.max_gen:
                    logger_rew.info("Failed at max generation.")
                    count_fail += 1
                    if min(scores) <= seed_fitness:
                        best_gen, best_vid, best_score = self.get_best_variant(1, self.generation)
                        promising_trace = self.load_variant_trace(best_gen, best_vid)
                        logger_rew.info('promising_trace: %s' %promising_trace)
                        logger_rew.info("Save the promising trace %f of %d:%d" % (best_score, best_gen, best_vid))
                        self.promising_traces.append(promising_trace)
                    break

                # Crossover
                # if self.xover_rate > 0:
                #     self.popul = self.select(self.popul, scores, self.pop_size/2)
                #     logger_rew.info("After selecting goods and replacing bads, we have %d variants in population." % len(self.popul))

                #     for p1,p2 in zip(self.popul[0::2], self.popul[1::2]):
                #         c1, c2 = PdfGenome.crossover(p1, p2)
                #         self.popul.append(c1)
                #         self.popul.append(c2)
                #     logger_rew.info("After crossover, we have %d variants in population." % len(self.popul))
                # else: # No Crossover
                #     self.popul = self.select(self.popul, scores, self.pop_size)
                #     logger_rew.info("After selecting goods and replacing bads, we have %d variants in population." % len(self.popul))

                # Mutation
                for i in range(len(self.popul)):
                    if i not in self.vid_from_trace:
                        arm = self.bandit.get_random_arm(self.popul[i].path)
                        output_path = arm.pull(self.popul[i])
                        self.popul[i].set_current_exe_path(output_path)
                        self.popul[i].append_arm(arm)
                    else:
                        logger_rew.info("Keep %d:%d variant from trace." % (self.generation+1, i))

                self.generation = self.generation + 1

            logger_rew.info("Stopped the GP process with min fitness %f." % best_score)
            os.system('rm %s/*' % (rewriter_output_folder))
            logger_rew.info('RESULT total: %d succ: %d, fail: %d' %(count_pending, count_solve, count_fail))
            print('RESULT total: %d succ: %d, fail: %d' %(count_pending, count_solve, count_fail))
        return True

    def initial_population(self, sample):
        logger_rew.info("Getting initial population from existing mutation traces (success: %d, promising: %d)."
                        % (len(self.success_traces), len(self.promising_traces)))
        popul = []

        traces = self.success_traces + self.promising_traces
        logger_rew.info(self.success_traces)
        logger_rew.info(self.promising_traces)
        ##### traces = Trace.get_distinct_traces(traces)
        logger_rew.info("Got %d distinct traces" % len(traces))
        self.traces = traces

        self.remaining_traces_id = list(range(len(traces)))

        if 0 < len(self.remaining_traces_id) <= self.pop_size:
            tid_picked = self.remaining_traces_id
        elif len(self.remaining_traces_id) > self.pop_size:
            tid_picked = random.sample(self.remaining_traces_id, self.pop_size)
            tid_picked.sort()
        else:
            tid_picked = []

        # generate_variants_from_traces
        for i in tid_picked:
            self.remaining_traces_id.remove(i)
            logger_rew.info("Generating variant from existing trace %d." % i)
            trace = traces[i]

            variant = deepcopy(sample)
            output_path = variant.replay_trace(trace)
            new_path = dirname(
                output_path) + '/' + basename(sample.path) + '.T' + str(i)  # str(len(popul))
            os.system('mv %s %s' % (output_path, new_path))
            variant.set_current_exe_path(new_path)
            popul.append(variant)

        if len(popul) < int(self.pop_size):
            logger_rew.info("Getting %d more variants in initial population by random mutation."
                            % (int(self.pop_size) - len(popul)))

        while len(popul) < int(self.pop_size):
            i = len(popul)
            logger_rew.info("Getting variant %d in initial population." % i)
            arm = self.bandit.get_random_arm(sample.path)

            variant = deepcopy(sample)
            output_path = arm.pull(variant)
            variant.set_current_exe_path(output_path)
            variant.append_arm(arm)

            popul.append(variant)
        return popul

    def load_variant_trace(self, gen, vid):
        return self.popul[vid].list_applied_arm[:gen]

    def get_best_variant(self, start_gen, end_gen):
        best_gen = 1
        best_vid = 0
        best_score = MAX_SCORE
        for gen in range(start_gen, end_gen+1):
            scores = self.fitness_scores[gen]
            if min(scores) < best_score:
                best_score = min(scores)
                best_gen = gen
                best_vid = scores.index(best_score)
        return best_gen, best_vid, best_score

    def select(self, orig_list, scores, sel_size):
        # when reverse==False, select variants with lower score, otherwise select higher scores.
        sorted_indices = [i[0] for i in sorted(enumerate(scores), key=lambda x:x[1], reverse=True)]

        ret = []
        self.vid_from_trace = []

        for i in sorted_indices[:sel_size]:
            if scores[i] == MAX_SCORE:
                if len(self.remaining_traces_id) > 0:
                    # TODO: need to label these, not to mutate in next generation.
                    self.vid_from_trace.append(i)
                    tid_picked = random.choice(self.remaining_traces_id)
                    self.remaining_traces_id.remove(tid_picked)
                    logger_rew.info("Ignored a variant with low score, generating from existing trace %d" % tid_picked)
                    trace = self.traces[tid_picked]

                elif self.generation == 1:
                    logger_rew.info("Ignored a variant with low score, replace with original seed.")
                    # ret.append(deepcopy(self.seed_root))
                else:
                    choice = random.choice(
                        ['seed', 'last_gen_best', 'historic_best'])
                    if choice == "seed":
                        logger_rew.info("Ignored a variant with low score, replace with original seed.")
                        # ret.append(deepcopy(self.seed_root))
                    elif choice == "last_gen_best":
                        best_gen, best_vid, best_score = self.get_best_variant(self.generation-1, self.generation-1)
                        best_root = self.load_variant(best_gen, best_vid)
                        ret.append(best_root)
                        logger_rew.info("Ignored a variant with low score, replace with best variant in last generation[%d, %d]." % (best_gen, best_vid))
                    elif choice == "historic_best":
                        best_gen, best_vid, best_score = self.get_best_variant(1, self.generation-1)
                        best_root = self.load_variant(best_gen, best_vid)
                        ret.append(best_root)
                        logger_rew.info("Ignored a variant with low score, replace with best variant in historic generation[%d, %d]." % (best_gen, best_vid))
            else:
                logger_rew.info("Selected a file with score %f" % scores[i])
                ret.append(orig_list[i])
        return ret
