import random
import lgsvl
from utils import raycast_to_ground

def generate_random_position(bubble, lane_index, forward_index, sim, forward):
    """
    lane_index: 0, 1, 2, 3
    region_range: value in the range of 0-150
    """

    # Get the lane range from the bubble
    lane_scope = bubble["scope"][lane_index]
    
    # Each lane is divided into three areas
    x_min = lane_scope[0][0]
    x_max = lane_scope[1][0]
    z_min = lane_scope[0][1]
    z_max = lane_scope[1][1]
    
    # Lane width is 3.5 meters
    lane_width = 3.5

    position_start = lgsvl.Vector(x_min, 0, z_min)
    
    # Starting position + number of forwards
    position_end = position_start + forward_index * forward
    
    ground_position = raycast_to_ground(sim, position_end)
    
    return ground_position

    