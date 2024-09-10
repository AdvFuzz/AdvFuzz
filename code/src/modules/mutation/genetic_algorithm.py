import os
import copy
import random
import pickle
import shutil

from datetime import datetime
from loguru import logger

from modules.corpus.corpus import CorpusElement
from modules.mutation.local_genetic_algorithm import LocalGeneticMutator
from modules.mutation import restart

class GeneticMutator(object):
    def __init__(self, runner, selection, output_path, scenario_name, bounds, pm, pc, pop_size, NPC_size, time_size, max_gen):
        self.pop = []
        self.bounds = bounds                # The value ranges of the inner most elements
        self.pm = pm
        self.pc = pc
        self.pop_size = pop_size            # Number of scenarios in the population
        self.NPC_size = NPC_size            # Number of NPC in each scenario
        self.time_size = time_size          # Number of time slides in each NPC
        self.max_gen = max_gen
        self.bests = [0] * max_gen
        self.bestIndex = 0
        self.g_best = None
        self.touched_chs = []             # Record which chromosomes have been touched in each generation

        self.minLisGen = 2                  # Min gen to start LIS
        self.numOfGenInLis = 5              # Number of gens in LIS
        self.hasRestarted = False
        self.lastRestartGen = 0
        self.bestYAfterRestart = 0

        self.runner = runner
        self.selection = selection
        self.scenario_name = scenario_name
        self.output_path = output_path
        self.ga_checkpoints_path = os.path.join(self.output_path, 'logs/checkpoints_ga')

        if os.path.exists(self.ga_checkpoints_path):
            shutil.rmtree(self.ga_checkpoints_path)
        os.makedirs(self.ga_checkpoints_path)

        self.ga_log = os.path.join(self.output_path, 'logs/ga.log')
        if os.path.exists(self.ga_log):
            os.remove(self.ga_log)
        
        self.progress_log = os.path.join(self.output_path, 'logs/progress.log')
        if os.path.exists(self.progress_log):
            os.remove(self.progress_log)
    
    def take_checkpoint(self, obj, ck_name):
        ck_file = os.path.join(self.ga_checkpoints_path, ck_name)
        with open(ck_file, 'wb') as ck_f:
            pickle.dump(obj, ck_f)

    def cross(self):
        # Implementation of random crossover

        for i in range(int(self.pop_size / 2.0)):
            # Check crossover probability
            if self.pc > random.random():
            # randomly select 2 chromosomes(scenarios) in pops
                i = 0
                j = 0
                while i == j:
                    i = random.randint(0, self.pop_size-1)
                    j = random.randint(0, self.pop_size-1)
                pop_i = self.pop[i]
                pop_j = self.pop[j]

                # Record which chromosomes have been touched
                self.touched_chs.append(i)
                self.touched_chs.append(j)

                # Every time we only switch one NPC or ego between scenarios
                # select cross index
                
                if random.random() < 0.5:
                    swap_index = random.randint(0, self.NPC_size - 1)
                    temp = copy.deepcopy(pop_j.scenario[1][swap_index])
                    pop_j.scenario[1][swap_index] = copy.deepcopy(pop_i.scenario[1][swap_index])
                    pop_i.scenario[1][swap_index] = temp
                    # keep lane
                    # temp = copy.deepcopy(pop_j.scenario[1][swap_index][1])
                    # pop_j.scenario[1][swap_index][1] = copy.deepcopy(pop_i.scenario[1][swap_index][1])
                    # pop_i.scenario[1][swap_index][1] = temp

                else:
                    temp = copy.deepcopy(pop_j.scenario[0])
                    pop_j.scenario[0] = copy.deepcopy(pop_i.scenario[0])
                    pop_i.scenario[0] = temp
        

    def mutation(self, ga_iter):

        i = 0
        while i < len(self.pop) :
            eachChs = self.pop[i]
            
            if self.pm >= random.random():
                # Record which chromosomes have been touched
                self.touched_chs.append(i)
                # select mutation part
                actionIndex = random.randint(0, 2)
                
                if actionIndex == 0:
                    # Change ego state
                    egoAction = random.randint(0, 1)
                    if egoAction == 0:
                        eachChs.scenario[0][0] = random.randrange(self.bounds[0][0][0], self.bounds[0][0][1])
                    elif egoAction ==1 :
                        eachChs.scenario[0][1] = random.randrange(self.bounds[0][1][0], self.bounds[0][1][1])
                        
                elif actionIndex == 1:
                    # Change npc state
                    npc_index = random.randint(0, self.NPC_size - 1)
                    npcAction = random.randint(0, 1)
                    if npcAction == 0:
                        #Change npc lane
                        eachChs.scenario[1][npc_index][0] = random.randrange(self.bounds[1][0][0], self.bounds[1][0][1])
                    elif npcAction == 1:
                        #Change npc forward
                         eachChs.scenario[1][npc_index][1] = random.randrange(self.bounds[1][1][0], self.bounds[1][1][1])
                elif actionIndex == 2:
                    # Change weather
                    rain_rate = 0 if random.random()<0.5 else random.uniform(self.bounds[2][0][0], self.bounds[2][0][1])
                    fog_rate = 0 if random.random()<0.5 else random.uniform(self.bounds[2][0][0], self.bounds[2][0][1])
                    wetness_rate = 0 if random.random()<0.5 else random.uniform(self.bounds[2][0][0], self.bounds[2][0][1])
                    cloudiness_rate = 0 if random.random()<0.5 else random.uniform(self.bounds[2][0][0], self.bounds[2][0][1])
                    daytime = random.randint(self.bounds[2][1][0], self.bounds[2][1][1])
                    eachChs.scenario[2] = [rain_rate, fog_rate, wetness_rate, cloudiness_rate, daytime]
            i = i + 1
            
        logger.info('Generate ' + str(len(self.touched_chs)) + ' mutated scenarios')
        # Only run simulation for the chromosomes that are touched in this generation
        self.touched_chs = set(self.touched_chs)
        for i in self.touched_chs:
            eachChs = self.pop[i]
            before_fitness = eachChs.fitness
            # 1. run simulator for each modified elements
            fitness, scenario_id = self.runner.run(eachChs.scenario)
            # 2. creat new elements or update fitness_score and coverage feat
            eachChs.fitness = fitness
            eachChs.scenario_id = scenario_id
            after_fitness = eachChs.fitness
            
            with open(self.ga_log, 'a') as f:
                f.write('global_' + str(ga_iter))
                f.write(',')
                f.write(scenario_id)
                f.write(',')
                f.write('before run:' + str(before_fitness))
                f.write(',')
                f.write('after run:' + str(after_fitness))
                f.write('\n')
    
    def select_roulette(self):

        sum_f = 0
        for i in range(0, self.pop_size):
            if self.pop[i].fitness == 0:
                self.pop[i].fitness = 0.001

        ############################################################
        min_fitness = self.pop[0].fitness
        for k in range(0, self.pop_size):
            if self.pop[k].fitness < min_fitness:
                min_fitness = self.pop[k].fitness
        if min_fitness < 0:
            for l in range(0, self.pop_size):
                self.pop[l].fitness = self.pop[l].fitness + (-1) * min_fitness

        # roulette
        for i in range(0, self.pop_size):
            sum_f += self.pop[i].fitness
        p = [0] * self.pop_size
        for i in range(0, self.pop_size):
            if sum_f == 0:
                sum_f = 1
            p[i] = self.pop[i].fitness / sum_f
        q = [0] * self.pop_size
        q[0] = 0
        for i in range(0, self.pop_size):
            s = 0
            for j in range(0, i+1):
                s += p[j]
            q[i] = s

        # start roulette
        v = []
        for i in range(0, self.pop_size):
            r = random.random()
            if r < q[0]:
                v.append(copy.deepcopy(self.pop[0]))
            for j in range(1, self.pop_size):
                if q[j - 1] < r <= q[j]:
                    v.append(copy.deepcopy(self.pop[j]))
        self.pop = copy.deepcopy(v)

    def select_top2(self):
        maxFitness = 0
        v = []
        for i in range(0, self.pop_size):
            if self.pop[i].fitness > maxFitness:
                maxFitness = self.pop[i].fitness

        for i in range(0, self.pop_size):
            if self.pop[i].fitness == maxFitness:
                for j in range(int(self.pop_size / 2.0)):
                    v.append(copy.deepcopy(self.pop[i]))
                break

        max2Fitness = 0
        for i in range(0, self.pop_size):
            if self.pop[i].fitness > max2Fitness and self.pop[i].fitness != maxFitness:
                max2Fitness = self.pop[i].fitness

        for i in range(0, self.pop_size):
            if self.pop[i].fitness == max2Fitness:
                for j in range(int(self.pop_size / 2.0)):
                    v.append(copy.deepcopy(self.pop[i]))
                break

        self.pop = copy.deepcopy(v)

    def find_best(self):
        logger.debug(self.pop)
        best = copy.deepcopy(self.pop[0]) # element object
        bestIndex = 0
        for i in range(self.pop_size):
            if best.fitness < self.pop[i].fitness:
                best = copy.deepcopy(self.pop[i])
                bestIndex = i
        return best, bestIndex
    
    def init_pop(self):
        for i in range(self.pop_size):
        # 1. init scenario data  [[ego_start,ego_end],[[npc_start,forward],[npc_start,forward]...],[[rain],[fog],[wet],[cloudiness],[daytime]]]
            scenario_data = [[], [], []]
            ego_start_pos = random.randrange(self.bounds[0][0][0], self.bounds[0][0][1])
            ego_end_pos = random.randrange(self.bounds[0][1][0], self.bounds[0][1][1])
            scenario_data[0].append(ego_start_pos)
            scenario_data[0].append(ego_end_pos)
            
            # set npc at per lane
            for _ in range(self.NPC_size):
                forward_num = random.randint(self.bounds[1][1][0], self.bounds[1][1][1])
                npc_pos = [_, forward_num]
                scenario_data[1].append(npc_pos)
                
            if random.random() <0.5:
                rain_rate = 0 
                fog_rate = 0 
                wetness_rate = 0
                cloudiness_rate = 0 
            else:
                rain_rate = 0 if random.random()<0.5 else random.uniform(self.bounds[2][0][0], self.bounds[2][0][1])
                fog_rate = 0 if random.random()<0.5 else random.uniform(self.bounds[2][0][0], self.bounds[2][0][1])
                wetness_rate = 0 if random.random()<0.5 else random.uniform(self.bounds[2][0][0], self.bounds[2][0][1])
                cloudiness_rate = 0 if random.random()<0.5 else random.uniform(self.bounds[2][0][0], self.bounds[2][0][1])
            scenario_data[2].append(rain_rate)
            scenario_data[2].append(fog_rate)
            scenario_data[2].append(wetness_rate)
            scenario_data[2].append(cloudiness_rate)
        
            daytime = random.randint(self.bounds[2][1][0], self.bounds[2][1][1])
            scenario_data[2].append(daytime)


            # 2. run simulator -> get outputs
            fitness_score, scenario_id = self.runner.run(scenario_data)
            # 3. generate new elements
            new_element = CorpusElement(scenario_id, scenario_data, fitness_score)
            self.pop.append(new_element)
            with open(self.ga_log, 'a') as f:
                f.write('init_' + str(i))
                f.write(',')
                f.write(scenario_id)
                f.write('\n')
    
    def process(self):
        
        best, bestIndex = self.find_best()
        self.g_best = copy.deepcopy(best)

        with open(self.progress_log, 'a') as f:
            f.write('name' + " " + "best_fitness" + " " + "global_best_fitness" + " " + "similarity" + " " + "datatime" + "\n")
        
        now = datetime.now()
        date_time = now.strftime("%m-%d-%Y-%H-%M-%S")
        with open(self.progress_log, 'a') as f:
            f.write('initialization' + " " + str(best.fitness) + " " + str(self.g_best.fitness) + " " + "0000" + " " + date_time + "\n")


        # Start evolution
        for i in range(self.max_gen):                       # i th generation.
            # util.print_debug(" \n\n*** " + str(i) + "th generation ***")
            logger.info("    *** " + str(i) + "th generation ***    ")
            
            # Make sure we clear touched_chs history book every gen
            # TODO: select 方法

            self.touched_chs = []
            self.cross()
            self.mutation(i)
            
            
            if self.selection == 'top':
                self.select_top2()
            elif self.selection == 'roulette':
                self.select_roulette()
            else:
                raise RuntimeError('Selection methods require: top or roulette.')      

            best, bestIndex = self.find_best()                     # Find the scenario with the best fitness score in current generation 
            self.bests[i] = best                        # Record the scenario with the best fitness score in i th generation

            ########### Update noprogressCounter #########              
            noprogress = False
            ave = 0
            if i >= self.lastRestartGen + 5:
                for j in range(i - 5, i):
                    ave +=  self.bests[j].fitness
                ave /= 5
                if ave >= best.fitness:
                    self.lastRestarGen = i
                    noprogress = True

            if self.g_best.fitness < best.fitness:                  # Record the best fitness score across all generations
                self.g_best = copy.deepcopy(best)

            N_generation = self.pop
            N_b = self.g_best                           # Record the scenario with the best score over all generations

            # Update the checkpoint of the best scenario so far
            self.take_checkpoint(N_b, 'best_scenario.obj')                       

            # Checkpoint this generation
            self.take_checkpoint(N_generation, 'last_gen.obj')

            # Checkpoint every generation
            now = datetime.now()
            date_time = now.strftime("%m-%d-%Y-%H-%M-%S")
            self.take_checkpoint(N_generation, 'generation-' + str(i) + '-at-' + date_time)

            #################### Start the Restart Process ################### 
            if noprogress:
                logger.info("    ### Restart Based on Generation: " + str(i) + " ###    ")
                oldCkName = self.ga_checkpoints_path
                newPop = restart.generate_restart_scenarios(self.runner, self.ga_log, i, oldCkName, 1000, self.bounds)
                self.pop = copy.deepcopy(newPop)
                self.hasRestarted = True
                best, self.bestIndex = self.find_best()
                self.bestYAfterRestart = best.fitness
                self.lastRestartGen = i
                 # Log fitness etc
                with open(self.progress_log, 'a') as f:
                    f.write('global_' + str(i) + '_restart' + " " + str(best.fitness) + " " + str(self.g_best.fitness) + " " + str(simiSum/float(self.pop_size)) + " " + date_time + "\n")

            #################### End the Restart Process ################### 

            if os.path.exists(self.ga_checkpoints_path) == True:
                prePopPool = restart.get_all_checkpoints(self.ga_checkpoints_path) 
                simiSum = 0
                for eachChs in self.pop:
                    eachSimilarity =  restart.get_similarity_scenario_vs_pre_pop(eachChs, prePopPool)
                    simiSum += eachSimilarity
                logger.debug(" ==== Similarity compared with all prior generations: " + str(simiSum/float(self.pop_size)))

            # Log fitness etc
            with open(self.progress_log, 'a') as f:
                f.write('global_' + str(i) + " " + str(best.fitness) + " " + str(self.g_best.fitness) + " " + str(simiSum/float(self.pop_size)) + " " + date_time + "\n")

            if best.fitness > self.bestYAfterRestart:
                self.bestYAfterRestart = best.fitness
                if i > (self.lastRestartGen + self.minLisGen): # Only allow one level of recursion
                    ################## Start LIS #################
                    logger.debug(" === Start of Local Iterative Search === ")
                    # Increase mutation rate a little bit to jump out of local maxima
                    local_output_path = os.path.join(self.output_path, 'local_ga', 'local_' + str(i))
                    lis = LocalGeneticMutator(self.runner, self.selection, local_output_path, i, self.ga_log, self.progress_log, self.scenario_name, self.bounds, self.pm * 1.5, self.pc, self.pop_size, self.NPC_size, self.time_size, self.numOfGenInLis)
                    lis.setLisPop(self.g_best)
                    lisBestChs = lis.process(i)
                    logger.debug(" --- Best fitness in LIS: " + str(lisBestChs.fitness))
                    if lisBestChs.fitness > self.g_best.fitness:
                        # Let's replace this
                        self.pop[bestIndex] = copy.deepcopy(lisBestChs)
                        logger.info(" --- Find better scenario in LIS: LIS->" + str(lisBestChs.fitness) + ", original->" + str(self.g_best.fitness))
                    else:
                        logger.debug(" --- LIS does not find any better scenarios")
                    logger.info(' === End of Local Iterative Search === ')

        return self.g_best
 