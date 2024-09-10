import lgsvl
import numpy as np
from z3 import *


def follow_lane(sim, ego, npc, forward, num_points=10, action_change_freq=5):
    """
    Generate path points that follow the lanes, ensuring each waypoint is on the road.
    Adjusts waypoints based on dynamic velocity calculations.
    """
    start_pos = npc.state
    waypoints = []
    layer_mask = 1 << 0  # Layer for the road
    
    n_forward = calculate_distance(start_pos,ego,forward)
    # Calculate acceleration and target distance
    acceleration, target_distance = calculate_velocity(ego, npc, n_forward, action_change_freq)                              

    total_time = action_change_freq
    time_step = total_time / num_points
    t_accelerate = 4   # 加速时间
    t_decelerate = total_time - t_accelerate  # 减速时间
    current_position = np.array([start_pos.position.x, start_pos.position.y, start_pos.position.z])
    forward_np = np.array([forward.x, 0, forward.z])

    for i in range(num_points):
        # Time at current step
        t = (i + 1) * time_step
        
        if t <= t_accelerate:
            # 加速阶段
            new_speed = acceleration * t
            distance = 0.5 * acceleration * (t ** 2)

        else:
            # 减速阶段
            t_dec = t - t_accelerate
            new_speed = max(0, acceleration * t_accelerate - acceleration * t_dec)  # 保证速度不会小于0
            if new_speed > 0:
                distance = (0.5 * acceleration * (t_accelerate ** 2)) + (acceleration * t_accelerate * t_dec - 0.5 * acceleration * (t_dec ** 2))
            else:
                # 当速度降至0，停止计算新的距离，保持当前距离不变
                max_t_dec = acceleration * t_accelerate / max(1,acceleration)  # 计算减速到0需要的时间
                max_distance = (0.5 * acceleration * (t_accelerate ** 2)) + (acceleration * t_accelerate * max_t_dec - 0.5 * acceleration * (max_t_dec ** 2))
                distance = max_distance  # 保持在减速到0时的最终距离
        # Convert distance to a position
        new_position_vector = current_position + forward_np * distance
        new_position = lgsvl.Vector(new_position_vector[0], new_position_vector[1], new_position_vector[2])
        
        raycast_start_point = lgsvl.Vector(new_position.x, new_position.y + 10, new_position.z)
        # Perform a raycast to ensure the waypoint is placed correctly on the road surface
        hit = sim.raycast(raycast_start_point, lgsvl.Vector(0, -1, 0), layer_mask)
        if hit:
            # Create a waypoint at the hit point with calculated speed and no additional idle time
            wp = lgsvl.DriveWaypoint(hit.point, new_speed, angle=start_pos.rotation, idle=0)
            waypoints.append(wp)
        else:
            print(f"Raycast did not hit any object at waypoint {i+1}, skipping this waypoint.")
    
    return waypoints

def calculate_distance(final_point, ego, forward):
    final_point = np.array([final_point.position.x, final_point.position.z])
    ego_position = np.array([ego.state.position.x, ego.state.position.z])
    forward = np.array([forward.x, forward.z])
    direction_vector = final_point - ego_position
    dot_product = np.dot(direction_vector, forward)
    forward_magnitude = np.linalg.norm(forward)
    return dot_product / forward_magnitude

def calculate_velocity(ego, npc, n_forward,total_time=5):
    npc_length = npc.bounding_box.max.x - npc.bounding_box.min.x
    initial_npc_speed = npc.state.speed
    initial_ego_speed = ego.state.speed
    
    # 计算 ego 初始到达 npc 的时间
    distance_to_npc = n_forward - (npc_length / 2)
    time_to_reach_npc = distance_to_npc / max(1,initial_ego_speed)

    # 计算碰撞时间
    max_collision_time = total_time - time_to_reach_npc

    # 碰撞时间内ego最大行驶距离
    max_distance = max_collision_time * initial_ego_speed

    # 根据 npc 的初始速度决定速度
    if initial_npc_speed == 0:
        # 如果 NPC 从静止开始，计算在 5 秒内发生碰撞需要的 ego 速度
        # 假设 NPC 先匀加速后匀减速，最大碰撞距离为 max_distance
        # v-t图的面积小于等于 max_distance
        # 生成目标距离
        # target_distance = np.random.uniform(0.75*max_distance, max_distance)
        target_distance = max_distance  
        
        # 定义加速度和时间变量
        a1 = Real('a1')  # 加速阶段的加速度
        a2 = Real('a2')  # 减速阶段的加速度
        t1 = Real('t1')  # 加速时间
        t2 = Real('t2')  # 减速时间，总时间减去加速时间
        
        # 创建求解器实例
        solver = Solver()
        
        # 添加时间约束
        solver.add(t1 == total_time/2)  # 加速时间
        solver.add(t2 == total_time - t1)  # 减速时间为总时间减去加速时间

        #加速和减速度相同
        solver.add(a1 == a2)

        # 添加位移方程：匀加速位移 + 匀减速位移 = target_distance
        # 匀加速位移: (1/2) * a1 * t1^2
        # 匀减速位移: (1/2) * a2 * t2^2
        solver.add(0.5 * a1 * t1**2 + 0.5 * a2 * t2**2 == target_distance)

        # 求解方程
        if solver.check() == sat:
            model = solver.model()
            acceleration1 = model[a1].as_decimal(5)  # 加速度 a1
            cleaned_string = acceleration1.replace('?', '')
            acceleration = float(cleaned_string)
            if acceleration == 0:
                acceleration = 10  # 如果计算出的加速度为0，则赋值为10
            return acceleration, target_distance
        else:
            return "No solution", "No solution", target_distance

        
    

    else:
        # NPC 已经在移动，执行匀减速直到碰撞
        # deceleration_distance = np.random.uniform(0.75*max_distance, max_distance)
        deceleration_distance = max_distance
        
        # 计算匀减速所需的减速度
        if deceleration_distance > 0:
            deceleration = (initial_npc_speed ** 2) / (2 * deceleration_distance)
        else:
            deceleration = 0


    return deceleration, deceleration_distance

            

 
        
