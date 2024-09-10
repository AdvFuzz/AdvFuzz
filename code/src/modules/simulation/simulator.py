import os
import pickle
import lgsvl
import time
import json
from environs import Env
import random

import modules.simulation.utils as util
import modules.simulation.liability as liability

from datetime import datetime
from loguru import logger

from modules.simulation.NineGrid import NineGrid
from modules.simulation.handle_zones import handle_zone_L1, handle_zone_N1, handle_zone_R1, handle_zone_L2, handle_zone_R2
class Simulator(object):

    def __init__(self, default_record_folder, target_record_folder, total_sim_time, data_prime, target_status_folder, target_collision_folder, lgsvl_map = 'Highway101GLE', apollo_map = 'Highway101GLE'):
        
        self.default_record_folder = default_record_folder
        self.target_record_folder = target_record_folder
        self.target_status_foldef = target_status_folder
        self.target_collision_foldef = target_collision_folder
        ################################################################
        self.total_sim_time = total_sim_time
        self.destination = None
        ################################################################
        self.sim = None
        self.data_prime = data_prime
        self.dv = None
        self.lgsvl_map = lgsvl_map
        self.apollo_map = apollo_map
        self.ego = None
        self.mutated_npc_list = [] # The list contains all the npc added
        self.fixed_npc_list = []
        self.yellow_lines = None
        self.cross_lines = None
        self.edge_lines = None

        self.connect_lgsvl()
        self.load_map(self.lgsvl_map)
        self.isEgoFault = False
        self.isHit = False
        
        
        # self.maxint = 130
        # self.egoFaultDeltaD = 0

        self.modules = [
            'Localization',
            'Transform',
            'Routing',
            'Prediction',
            'Planning',
            'Control',
            'Perception',
        ]
        self.dy_modules = [
            'Recorder',
        ]
        # self.init_environment()

    def connect_lgsvl(self):
        env = Env()
        logger.info("Connecting to the Simulator")
        SIMULATOR_HOST = os.environ.get("LGSVL__SIMULATOR_HOST", lgsvl.wise.SimulatorSettings.simulator_host)
        SIMULATOR_PORT = os.environ.get("LGSVL__SIMULATOR_PORT", lgsvl.wise.SimulatorSettings.simulator_port)
        try:
            sim = lgsvl.Simulator(SIMULATOR_HOST, SIMULATOR_PORT) 
            self.sim = sim
        except Exception as e:
            logger.error('Connect LGSVL wrong: ' + '127.0.0.1:8181')
            logger.error(e.message)
        logger.info('Connected LGSVL 127.0.0.1:8181')

    def load_map(self, mapName="SanFrancisco_correct"):
        if self.sim.current_scene == mapName:
           self.sim.reset()
        else:
           self.sim.load(self.lgsvl_map)
        logger.info('Loaded map: ' + mapName)

    def set_ego(self, sim, start_pos):
        ego_state = lgsvl.AgentState()
        start_pos = self.raycast_to_ground( start_pos)
        ego_state.transform.position = start_pos
        ego_state.transform = sim.map_point_on_lane(start_pos)
        ego = sim.add_agent(os.environ.get(
            "LGSVL__VEHICLE_0", lgsvl.wise.DefaultAssets.ego_lincoln2017mkz_apollo5), lgsvl.AgentType.EGO, ego_state)
        return ego    

    def set_npc(self, name, start_pos, is_light):
        npc_state = lgsvl.AgentState()
        start_pos = self.raycast_to_ground(start_pos)
        npc_state.transform.position = start_pos
        npc_state.transform = self.sim.map_point_on_lane(start_pos)
        npc = self.sim.add_agent(name, lgsvl.AgentType.NPC, npc_state)
        logger.info("Set {} at start_pos.", name)
        if is_light:
            logger.info("Set npc lights on because of night.")
            c = lgsvl.NPCControl()
            c.headlights = 2
            npc.apply_control(c)
        return npc
    
    def raycast_to_ground(self, position):
        start_height = 100
        start_point = lgsvl.Vector(
            position.x, position.y + start_height, position.z)
        hit = self.sim.raycast(start_point, lgsvl.Vector(0, -1, 0), layer_mask=1 << 0)
        if hit:
            return hit.point
        else:
            return position



    def init_environment(self, scenario_obj):
        
        self.isEgoFault = False
        self.isHit = False

        self.mutated_npc_list = []
        self.fixed_npc_list = []
        
        # load environments 
        rain_rate = scenario_obj[2][0]
        fog_rate = scenario_obj[2][1]
        wetness_rate = scenario_obj[2][2]
        cloudiness_rate = scenario_obj[2][3]
        self.sim.weather = lgsvl.WeatherState(
            rain=rain_rate,
            fog=fog_rate,
            wetness=wetness_rate,
            cloudiness=cloudiness_rate,
        )
        daytime = scenario_obj[2][4]
        night = True if daytime > 17 else False
        self.sim.set_time_of_day(daytime)

        # load ego start pos
        ego_data = self.data_prime['agents']['ego']
        ego_start_pos = scenario_obj[0][0]
        ego_position = ego_data['position'][ego_start_pos]
        ego_pos_vector = lgsvl.Vector(x=ego_position['x'], y=ego_position['y'], z=ego_position['z'])
        ego_state = lgsvl.AgentState()
        ego_state.transform = self.sim.map_point_on_lane(ego_pos_vector)
        self.forward = lgsvl.utils.transform_to_forward(ego_state.transform)
        self.right = lgsvl.utils.transform_to_right(ego_state.transform)
        self.ego = self.sim.add_agent(os.environ.get("LGSVL__VEHICLE_0",lgsvl.wise.DefaultAssets.ego_test), lgsvl.AgentType.EGO, ego_state)
        logger.info("Set ego at start_pos.")
        
        ## load ego destination
        ego_end_pos = scenario_obj[0][1]
        des_method = ego_data['destination']['method']
        if des_method == 'xyz':
            x = ego_data['destination']['value'][ego_end_pos]['v1']
            y = ego_data['destination']['value'][ego_end_pos]['v2']
            z = ego_data['destination']['value'][ego_end_pos]['v3']
            self.destination = lgsvl.Vector(x, y, z)
        else:
            raise RuntimeError('Unmatched destination method')

        # load mutated npc
        npcs = self.data_prime['agents']['npcs']
        bubble = self.data_prime['bubble']['scope']
        index = 0
        for m_npc in npcs:
            lane_num = scenario_obj[1][index][0]
            npc_type = m_npc['type']
            npc_goal = m_npc['goal']
            forward_num = scenario_obj[1][index][1]
            npc_pos_x = bubble[lane_num][0][0]
            npc_pos_y = 0
            npc_pos_z = bubble[lane_num][0][1]
            npc_pos = lgsvl.Vector(x=npc_pos_x, y=npc_pos_y, z=npc_pos_z)
            npc_state = lgsvl.AgentState()
            npc_state.transform.position = npc_pos
            npc_pos = npc_state.transform.position + forward_num * self.forward
            npc = self.set_npc(npc_type, npc_pos, is_light=night)
            if npc_goal == 'fixed':
                self.fixed_npc_list.append(npc)
            elif npc_goal == 'mutated':
                self.mutated_npc_list.append(npc)
            else:
                raise RuntimeError('Wrong npc goal. Only support fixed or mutated.')
            index += 1
            
        # load lines
        # yellow line
        self.yellow_lines = self.data_prime['lines']['yellow_lines']
        self.cross_lines = self.data_prime['lines']['cross_lines']
        self.edge_lines = self.data_prime['lines']['edge_lines']

    def runSimulation(self, scenario_obj, json_file, case_id):

        #exit_handler()
        now = datetime.now()
        date_time = now.strftime("%m-%d-%Y-%H-%M-%S")
        logger.info(' === Simulation Start:  ['  + date_time + '] ===')
        # self.sim.reset()
        self.init_environment(scenario_obj)







        time_slice_size = len(scenario_obj[0])
        mutated_npc_num = len(scenario_obj[1])

        assert mutated_npc_num == len(self.mutated_npc_list)

        # simulation info
        simulation_recording = {
            'bbox': {
                'ego' : self.ego.bounding_box
            },
            'frames': {

            }
        }
        for npc_i in range(mutated_npc_num):
            simulation_recording['bbox']['npc_' + str(npc_i)] = self.mutated_npc_list[npc_i].bounding_box
        
        
       
        
        global collision_info
        global accident_happen
        global time_index
        
        collision_info = None
        accident_happen = False
        # TODO 其他判断方法
        def on_collision(agent1, agent2, contact):
            global accident_happen
            global collision_info
            global time_index

            accident_happen = True
            collision_info = {}

            name1 = "STATIC OBSTACLE" if agent1 is None else agent1.name
            name2 = "STATIC OBSTACLE" if agent2 is None else agent2.name
            logger.error(str(name1) + " collided with " + str(name2) + " at " + str(contact))

            agent1_info = [agent1.state, agent1.bounding_box]
                        
            if not agent2:
                agent2_info = [None, None]
            else:
                agent2_info = [agent2.state, agent2.bounding_box]
            
            if contact:
                contact_loc = [contact.x, contact.y, contact.z]
            
            collision_info['time'] = time_index
            collision_info['ego'] = agent1_info
            collision_info['npc'] = agent2_info
            # contact为None
            collision_info['contact'] = contact_loc

            self.sim.stop()
        
        # INIT apollo      
        BRIDGE_HOST = os.environ.get("BRIDGE_HOST", "127.0.0.1")
        BRIDGE_PORT = int(os.environ.get("BRIDGE_PORT", 9090))
        self.ego.connect_bridge(BRIDGE_HOST, BRIDGE_PORT) #address, port
        self.ego.on_collision(on_collision)
        
        times = 0
        success = False
        while times < 3:
            try:
                dv = lgsvl.dreamview.Connection(self.sim, self.ego, os.environ.get("BRIDGE_HOST", "127.0.0.1"))
                dv.set_hd_map(self.apollo_map)
                dv.set_vehicle('Lincoln2017MKZ_LGSVL')
                dv.setup_apollo(self.destination.x, self.destination.z, self.modules, default_timeout=30)
                success = True
                break
            except:
                logger.warning('Fail to connect with apollo, try again!')
                times += 1
        if not success:
            raise RuntimeError('Fail to connect with apollo')

        if self.default_record_folder:
            util.disnable_modules(dv, self.dy_modules)
            time.sleep(1)
            util.enable_modules(dv, self.dy_modules)
        
        dv.set_destination(self.destination.x, self.destination.z)
        logger.info(' --- Set ego_destination: ' + str(self.destination.x) + ',' + str(self.destination.z))
        
        delay_t = 3
        time.sleep(delay_t)
        
        # record start
        simulation_recording['frames'][time_index] = {
            'ego': self.ego.state
        }

        for npc_i in range(mutated_npc_num):
            simulation_recording['frames'][time_index]['npc_' + str(npc_i)] = self.mutated_npc_list[npc_i].state

        # TODO

        for npc in self.mutated_npc_list:
            npc.follow_closest_lane(True, 0)

        # for npc in self.fixed_npc_list:
        #     npc.follow_closest_lane(True, 13.4)

    #TODO 执行npc行为

        spawns = self.sim.get_spawn()
        forward = lgsvl.utils.transform_to_forward(spawns[0])
        right = lgsvl.utils.transform_to_right(spawns[0])

        # Frequency of action change of NPCs
        total_sim_time = self.total_sim_time # 25
        action_change_freq = 5 # 完成动作需要的时间
        time_index = 0
        # 初始化每个 NPC的标记为True,列表为ninegrid_flags,waypoints_flags
        # ninegrid_flags用来标记是否还需要判定九宫格
        # waypoints_flags用来标记是否已经生成过一次路径
        ninegrid_flags = [True for i in range(len(self.mutated_npc_list))]
        waypoints_flags = [True for i in range(len(self.mutated_npc_list))]
        action_timers = [5.0 for _ in self.mutated_npc_list]  # 为每个 NPC 添加计时器

        # 假设总仿真时间为25s，每一帧为0.1s，每次run 0.1s并检查当前ego和npc的位置，根据位置执行相应的行为
        # 需要去除外面时间片的概念
        for j in range(total_sim_time):
            for index,npc in enumerate(self.mutated_npc_list):  # 遍历所有npc 
                nine_grid = NineGrid(npc, forward, right) #创建实例
                if ninegrid_flags[index]: # 如果需要判定九宫格
                    region = nine_grid.get_ego_region(self.ego.state.position)
                    if region == 5:  # 如果ego在npc的左后方
                        handle_zone_L1(self, npc, forward, right, index, ninegrid_flags, waypoints_flags, action_change_freq)
                    elif region == 2: # ego在npc的正后方
                        handle_zone_N1(self, npc, forward, right, index, ninegrid_flags, waypoints_flags, action_change_freq)
                    elif region == 1: # ego在npc的右后方
                        handle_zone_R1(self, npc, forward, right, index, ninegrid_flags, waypoints_flags, action_change_freq)
                    elif region == 4: # ego在npc的左测
                        handle_zone_L2(self, npc, forward, right, index, ninegrid_flags, waypoints_flags, action_change_freq)
                    elif region == 3: # ego在npc的右侧
                        handle_zone_R2(self, npc, forward, right, index, ninegrid_flags, waypoints_flags, action_change_freq)
                    elif region == 0: # ego在npc的后侧
                        npc.follow_closest_lane(True, npc.state.speed)
                    elif region == None: 
                        # npc静止   
                        npc.follow_closest_lane(True, 0)
                else:
                    action_timers[index] -= 0.1
                    if action_timers[index] <= 0:
                        ninegrid_flags[index] = True
                        waypoints_flags[index] = True
                        action_timers[index] = 5.0  
            self.sim.run(0.1)                 

            # check module_status
            module_status_mark = True
            while module_status_mark:
                module_status_mark = False
                module_status = dv.get_module_status()
                for module, status in module_status.items():
                    if (not status) and (module in self.modules):
                        logger.warning('$$Simulator$$ Module is closed: ' + module + ' ==> restart')
                        dv.enable_module(module)
                        time.sleep(0.5)
                        module_status_mark = True
            time_index += 1
            # self.sim.run(0.1)

            simulation_recording['frames'][time_index] = {
                'ego': self.ego.state
            }

            for npc_i in range(len(self.mutated_npc_list)):
                simulation_recording['frames'][time_index]['npc_' + str(npc_i)] = self.mutated_npc_list[npc_i].state

    
        if self.default_record_folder:
            util.disnable_modules(dv, self.dy_modules)
            time.sleep(0.5)

        # check new folder and move -> save folder
        if self.default_record_folder:
            util.check_rename_record(self.default_record_folder, self.target_record_folder, case_id)

        
        
        
        
        # compute fitness score & check other bugs such as line cross or else
        '''
        

        global collision_info
        global accident_happen
        
        collision_info = None
        accident_happen = False
        
        '''
        # Step 1 obtain time
        simulation_slices = max(simulation_recording['frames'].keys())

        '''
        simulation_recording[time_index] = {
                    'ego': self.ego.transform,
                    'npc': []
                }
        '''
        fault = []
        max_fitness = -1111
        # Step 2 compute distance and check line error and filter npc_fault
        for t in range(simulation_slices):
            simulation_frame = simulation_recording['frames'][t]
            ego_info = {
                'state': simulation_frame['ego'],
                'bbox': simulation_recording['bbox']['ego']
            }            
            # compute distance
            for npc_i in range(len(self.mutated_npc_list)):
                npc_id = 'npc_' + str(npc_i)
                npc_info = {
                    'state': simulation_frame[npc_id],
                    'bbox': simulation_recording['bbox'][npc_id]
                }
                
                npc_ego_fitness = liability.compute_danger_fitness(ego_info, npc_info, yellow_line, False)
                
                if npc_ego_fitness > max_fitness:
                    max_fitness = npc_ego_fitness
            
            # check line
            for yellow_line in self.yellow_lines:
                hit_yellow_line = liability.ego_yellow_line_fault(ego_info, yellow_line)
                if hit_yellow_line:
                    fault.append('hit_yellow_line')
            
            for edge_line in self.edge_lines:
                hit_edge_line = liability.ego_edge_line_fault(ego_info, edge_line)
                if hit_edge_line:
                    fault.append('hit_edge_line')
            
        # Step 3 if collision, check is npc fault
        '''
        agent1_info = [agent1.transform, agent1.state]
                        
            if not agent2:
                agent2_info = [None, None]
            else:
                agent2_info = [agent2.transform, agent2.state]
            
            if contact:
                contact_loc = [contact.x, contact.y, contact.z]
            
            collision_info['time'] = time_index
            collision_info['ego'] = agent1_info
            collision_info['npc'] = agent2_info
            collision_info['contact'] = contact_loc

        '''
        if collision_info is not None:
            ego_info = {
                'state': collision_info['ego'][0],
                'bbox': collision_info['ego'][1]
            }

            npc_info = {
                'state': collision_info['npc'][0],
                'bbox': collision_info['npc'][1]
            }
            
            ego_fault = liability.ego_collision_fault(ego_info, npc_info, self.cross_lines)
            if ego_fault:
                fault.append('ego_fault')
            else:
                fault.append('npc_fault')
            
            fitness = liability.compute_danger_fitness(ego_info, npc_info, yellow_line, True)
            # if fitness < max_fitness:
            if fitness <= max_fitness:
                logger.error('Please increase K in liability.compute_danger_fitness: Collision - ' + str(fitness) + 'No Collision - ' + str(max_fitness))
                raise RuntimeError('liability.compute_danger_fitness parameter setting is not right.')
            else:
                max_fitness = fitness

        if len(fault) == 0:
            fault.append('normal')
        
        #fitness_score = self.findFitness(deltaDList, dList, self.isHit, hit_time)
        
        result_dict = {}
        result_dict['fitness'] = max_fitness
        #(fitness_score + self.maxint) / float(len(self.mutated_npc_list) - 1 ) # Try to make sure it is positive
        
        
                # save simulation info
        simulation_file = os.path.join(self.target_status_foldef, case_id + '.obj')
        if os.path.isfile(simulation_file):
            os.system("rm " + simulation_file)
        with open(simulation_file, 'wb') as f_f:
            pickle.dump(simulation_recording, f_f)

        collision_file = os.path.join(self.target_collision_foldef, case_id + '.obj')
        if os.path.isfile(collision_file):
            os.system("rm " + collision_file)
        with open(simulation_file, 'wb') as f_f1:
            pickle.dump(collision_info, f_f1)
            
        result_dict['fault'] = fault
        
        logger.info(' === Simulation End === ')

        return result_dict