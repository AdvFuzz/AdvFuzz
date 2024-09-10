# 导入各种行为模块
from behavior_trajectory_solver.cut_in_right import cut_in_right
from behavior_trajectory_solver.cut_in_left import cut_in_left
from behavior_trajectory_solver.follow_lane import follow_lane
from behavior_trajectory_solver.turn_left import turn_left
from behavior_trajectory_solver.turn_right import turn_right


def generate_behavior_trajectory(sim,ego, npc, forward, right, behavior_type, num_points, **kwargs):
    """
    To generate a path point according to the provided behavior type.
    """
    if behavior_type == 'follow_lane':
        action_change_freq = kwargs.get('action_change_freq')
        return follow_lane(sim, ego,npc, forward, num_points,action_change_freq)
    elif behavior_type == 'turn_right':
        return turn_right(sim, npc, forward, right, num_points)
    elif behavior_type == 'turn_left':
        return turn_left(sim, npc, forward, right, num_points)
    elif behavior_type == 'cut_in_right':
        n = kwargs.get('n')
        m = kwargs.get('m')
        k = kwargs.get('k')
        return cut_in_right(sim,ego, npc,forward, right, num_points,n,m,k)
    elif behavior_type == 'cut_in_left':
        n = kwargs.get('n')
        m = kwargs.get('m')
        k = kwargs.get('k')
        return cut_in_left(sim,ego,npc,forward, right, num_points,n,m,k)
    else:
        raise ValueError(f"Unsupported behavior type: {behavior_type}")
