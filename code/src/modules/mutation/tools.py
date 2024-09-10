import math
                                                                    
def get_similarity_between_npcs(npc1, npc2):
    similarity = 0.0
    
    lane1 = npc1[0]
    forward1 = npc1[1]
    lane2 = npc2[0]
    forward2 = npc2[1]
    
    if lane1 == lane2:
        distance_difference = abs(forward1 - forward2)
        similarity = 1 / (1 + distance_difference)  # The smaller the distance difference, the higher the similarity
    else:
        # If not in the same lane, consider the lane difference
        lane_difference = abs(lane1 - lane2)
        distance_difference = abs(forward1 - forward2)
        # Here, we can design weights according to specific application scenarios
        similarity = 1 / (1 + lane_difference + distance_difference)
    
    return similarity * 100

    


    return similarity

def get_similarity_between_egos(ego1, ego2):
    sim = 0.0
    start1 = ego1[0]
    end1 = ego1[1]
    start2 = ego2[0]
    end2 = ego2[1]
    
    if start1 == start2:
        sim += 50
    if end1 == end2:
        sim +=50
        
    return sim

def get_similarity_between_scenarios(scenario1, scenario2):

    npc_size = len(scenario1[1])

    scenario_sim_total = 0.0
    scenario_sim_ego = 0.0
    scenario_sim_npc = 0.0
    
    ego1 = scenario1[0]
    ego2 = scenario2[0]
    scenario_sim_ego = get_similarity_between_egos(ego1, ego2)
    
    for i in range(npc_size):
        sim_npc = 0.0
        npc = scenario1[1][i]
        for j in range(npc_size):
            sim_npc += get_similarity_between_npcs(npc, scenario2[1][j])
        sim_npc /= npc_size
        scenario_sim_npc += sim_npc
        
    scenario_sim_total = scenario_sim_ego + scenario_sim_npc

    return scenario_sim_total / (npc_size + 1) + 0.0

###################################################################################### 

    
