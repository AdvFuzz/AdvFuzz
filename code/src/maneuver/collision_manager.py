# collision_manager.py
import lgsvl

collision_detected = False

def stop_ego_vehicle(ego):
    # Set the speed of the EGO vehicle to 0
    state = ego.state
    state.velocity = lgsvl.Vector(0, 0, 0)
    ego.state = state
    # Apply Brakes
    ego.brake = 1

def stop_npc_vehicle(agent):
    state = agent.state
    state.velocity = lgsvl.Vector(0, 0, 0)
    agent.state = state
    agent.brake = 1


def on_collision(agent1, agent2, contact):
    global collision_detected
    collision_detected = True
    if isinstance(agent1, lgsvl.NpcVehicle):
        stop_npc_vehicle(agent1)
    elif isinstance(agent2, lgsvl.NpcVehicle):
        stop_npc_vehicle(agent2)

def empty_callback(agent1, agent2, contact):
    pass

def reset_collision():
    global collision_detected
    collision_detected = False

def set_collision_callback(ego):
    ego.on_collision(on_collision)

def remove_collision_callback(ego):
    ego.on_collision(empty_callback)

def is_collision_detected():
    global collision_detected
    return collision_detected
