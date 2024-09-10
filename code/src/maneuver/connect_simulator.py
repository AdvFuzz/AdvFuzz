import os
import time
import lgsvl
from loguru import logger
from environs import Env

def connect_svl():
    env = Env()
    
    SIMULATOR_HOST = env.str("LGSVL__SIMULATOR_HOST", lgsvl.wise.SimulatorSettings.simulator_host)
    SIMULATOR_PORT = env.int("LGSVL__SIMULATOR_PORT", lgsvl.wise.SimulatorSettings.simulator_port)
    logger.info("Connecting to the Simulator")
    # Connects to the simulator instance at the ip defined by LGSVL__SIMULATOR_HOST, default is localhost or 127.0.0.1
    
    sim = lgsvl.Simulator(SIMULATOR_HOST, SIMULATOR_PORT)
    
    logger.info("Connect to simulator successfully, Version =", sim.version)
    return sim

def bridgeApollo(sim, ego, ego_destination):
    BRIDGE_HOST = os.environ.get("BRIDGE_HOST", "127.0.0.1")
    BRIDGE_PORT = int(os.environ.get("BRIDGE_PORT", 9090))
    ego.connect_bridge(BRIDGE_HOST, BRIDGE_PORT)
    dv = lgsvl.dreamview.Connection(sim, ego, BRIDGE_HOST)
    # env = Env()
    # ego.connect_bridge(
    # env.str("LGSVL__AUTOPILOT_0_HOST", lgsvl.wise.SimulatorSettings.bridge_host),
    # env.int("LGSVL__AUTOPILOT_0_PORT", lgsvl.wise.SimulatorSettings.bridge_port)
    # )
    # dv = lgsvl.dreamview.Connection(sim, ego, env.str("LGSVL__AUTOPILOT_0_HOST", "127.0.0.1"))
    dv.set_hd_map('Highway101GLE')
    dv.set_vehicle('Lincoln2017MKZ')
    modules = [
        'Localization',
        'Perception',
        'Transform',
        'Routing',
        'Prediction',
        'Planning',
        'Control'
    ]
    dv.disable_apollo()
    dv.setup_apollo(ego_destination[0], ego_destination[1], modules)
    time.sleep(5)

if __name__ == '__main__':
    connect_svl()