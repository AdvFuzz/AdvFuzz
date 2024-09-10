import numpy as np
from utils import raycast_to_ground, bezier_point, bezier_derivative
import lgsvl

def cut_in_right(sim,ego,npc, forward, right,num_points,n,m,k):
    """
    生成向右变道路径点。
    n: npc从start_pos直行n个forward到达P0开始变道
    m: P0需要m个forward到达P1控制点
    k: P2需要k个forward到达P3结束点
    """
    waypoints = []
    # 定义贝塞尔曲线的控制点
    P0 = npc.state.position + forward * n
    P1 = P0 + forward * m
    P2 = P1 + right * 3.5
    P3 = P2 + forward * k
    points = [P0, P1, P2, P3]
    last_point = None
    total_distance = n
    # 生成贝塞尔曲线上的路径点
    for i in range(1, num_points + 1):
        t = i / num_points
        current_point = bezier_point(t, *points)
        ground_point = raycast_to_ground(sim, current_point)
        if last_point is not None:
            total_distance += np.linalg.norm(np.array([ground_point.x, ground_point.z]) - np.array([last_point.x, last_point.z]))
        last_point = ground_point
        if i == num_points:
            ground_point = sim.map_point_on_lane(ground_point)
            n_forward = calculate_distance(ground_point, ego, forward)
        # 计算切线方向
        tangent = bezier_derivative(t, *points)
        angle = np.degrees(np.arctan2(tangent.x, tangent.z))
        waypoints.append(lgsvl.DriveWaypoint(ground_point, 0, angle=lgsvl.Vector(0, angle, 0)))  # 初始化速度为0
            # 计算速度并赋值给所有路径点
        
    speed = calculate_velocity(ego, npc, n_forward, total_distance)
    for waypoint in waypoints:
        waypoint.speed = speed

    return waypoints
    
def calculate_distance(final_point, ego, forward):
    final_point = np.array([final_point.position.x, final_point.position.z])
    ego_position = np.array([ego.state.position.x, ego.state.position.z])
    forward = np.array([forward.x, forward.z])
    direction_vector = final_point - ego_position
    dot_product = np.dot(direction_vector, forward)
    forward_magnitude = np.linalg.norm(forward)
    return dot_product / forward_magnitude

def calculate_velocity(ego, npc, n_forward, distance):
    npc_length = npc.bounding_box.max.x - npc.bounding_box.min.x
    t0 = (n_forward - (npc_length / 2)) / max(ego.state.speed+10, 1)
    t1 = (n_forward + (npc_length / 2)) / max(ego.state.speed+10, 1)
    v0 = distance / max(t0, 0.1)
    v1 = distance / max(t1, 0.1)
    return np.random.uniform(v0, v1)