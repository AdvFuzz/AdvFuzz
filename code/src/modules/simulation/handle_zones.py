from maneuver.generate_behavior_trajectory import generate_behavior_trajectory
import random
from modules.simulation.NineGrid import NineGrid


def on_waypoint(agent, index, waypoints):
    total_waypoints = len(waypoints)
    # Check if it is the last point in the waypoint list
    if index == total_waypoints - 1:
        # Continue driving at final speed
        agent.follow_closest_lane(follow=True, max_speed=waypoints[-1].speed)


def handle_zone_L1(self, npc, forward, right, index, ninegrid_flags, waypoints_flags, action_change_freq):
    if random.random() < 0.5:
        if waypoints_flags[index]:
            waypoints = generate_behavior_trajectory(
                self.sim, self.ego, npc, forward, right, 'cut_in_left', num_points=10, n=10, m=3, k=3)
            waypoints_flags[index] = False
            ninegrid_flags[index] = False
            npc.follow(waypoints, loop=False)
            npc.on_waypoint_reached(lambda agent, index: on_waypoint(
                agent, index, waypoints))
    else:
        # NPC
        npc.follow_closest_lane(True, npc.state.speed)


def handle_zone_N1(self, npc, forward, right, index, ninegrid_flags, waypoints_flags, action_change_freq):
    # Slow down follow lane
    if random.random() < 0.5:
        if waypoints_flags[index]:
            waypoints = generate_behavior_trajectory(
                self.sim, self.ego, npc, forward, right, 'follow_lane', num_points=10, action_change_freq=action_change_freq)
            waypoints_flags[index] = False
            ninegrid_flags[index] = False
            npc.follow(waypoints, loop=False)
            npc.on_waypoint_reached(lambda agent, index: on_waypoint(
                agent, index, waypoints))
    else:
        #NPC stops immediately
        npc.follow_closest_lane(True, npc.state.speed)


def handle_zone_R2(self, npc, forward, right, index, ninegrid_flags, waypoints_flags, action_change_freq):
    # Turn right
    if waypoints_flags[index]:
        waypoints = generate_behavior_trajectory(
            self.sim, self.ego, npc, forward, right, 'cut_in_right', num_points=10, n=10, m=3, k=3)
        waypoints_flags[index] = False
        ninegrid_flags[index] = False
        npc.follow(waypoints, loop=False)
        npc.on_waypoint_reached(lambda agent, index: on_waypoint(
            agent, index, waypoints))


def handle_zone_L2(self, npc, forward, right, index, ninegrid_flags, waypoints_flags, action_change_freq):
    # Turn left
    if waypoints_flags[index]:
        waypoints = generate_behavior_trajectory(
            self.sim, self.ego, npc, forward, right, 'cut_in_left', num_points=10, n=10, m=3, k=3)
        waypoints_flags[index] = False
        ninegrid_flags[index] = False
        npc.follow(waypoints, loop=False)
        npc.on_waypoint_reached(lambda agent, index: on_waypoint(
            agent, index, waypoints))


def handle_zone_R1(self, npc, forward, right, index, ninegrid_flags, waypoints_flags, action_change_freq):
    if random.random() < 0.5:
        # Change lane right
        if waypoints_flags[index]:
            waypoints = generate_behavior_trajectory(
                self.sim, self.ego, npc, forward, right, 'cut_in_right', num_points=10, n=10, m=3, k=3)
            waypoints_flags[index] = False
            ninegrid_flags[index] = False
            npc.follow(waypoints, loop=False)
            npc.on_waypoint_reached(lambda agent, index: on_waypoint(
                agent, index, waypoints))
    else:
        # NPC stops immediately
        npc.follow_closest_lane(True, npc.state.speed)
