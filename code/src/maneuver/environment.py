import lgsvl
import os
from utils import raycast_to_ground


def initial_scene(sim):
    if sim.current_scene == lgsvl.wise.DefaultAssets.map_sanfrancisco:
        sim.reset()
    else:
        sim.load(lgsvl.wise.DefaultAssets.map_sanfrancisco)
    print("Successfully loaded map!")
    return sim


def set_weather(sim):
    sim.set_time_of_day(17)
    sim.weather = lgsvl.WeatherState(
        rain=0, fog=0, wetness=0, cloudiness=0, damage=0)
    return sim


def set_ego(sim, start_pos):
    ego_state = lgsvl.AgentState()
    start_pos = raycast_to_ground(sim, start_pos)
    ego_state.transform.position = start_pos
    ego_state.transform = sim.map_point_on_lane(start_pos)
    forward = lgsvl.utils.transform_to_forward(ego_state.transform)
    ego_state.velocity = 30 * forward
    ego = sim.add_agent(os.environ.get(
        "LGSVL__VEHICLE_0", lgsvl.wise.DefaultAssets.ego_lincoln2017mkz_apollo5), lgsvl.AgentType.EGO, ego_state)
    return ego


def set_npc(sim,  name, start_pos, is_light):
    npc_state = lgsvl.AgentState()
    npc_state.transform.position = start_pos
    npc_state.transform = sim.map_point_on_lane(start_pos)
    npc = sim.add_agent(name, lgsvl.AgentType.NPC, npc_state)
    return npc
