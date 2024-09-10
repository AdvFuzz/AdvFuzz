import os
import shutil
import time
import numpy as np
import lgsvl

from loguru import logger

def check_rename_record(default_path, target_path, case_id):
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    folders = os.listdir(default_path)
    folders = sorted(folders)
    if len(folders) > 0:
        original_folder = folders[-1]
        original_fpath = os.path.join(default_path, original_folder)
        target_fpath = os.path.join(target_path, case_id)
        shutil.move(original_fpath, target_fpath)
        logger.info(' --- Move: ' + original_fpath + ' ==> ' + target_fpath)

def enable_modules(dv, modules):
    # try 5 times
    not_all = True
    while not_all:
        not_all = False
        module_status = dv.get_module_status()
        for module, status in module_status.items():
            if (not status) and (module in modules):
                dv.enable_module(module)
                not_all = True
        time.sleep(1)

def disnable_modules(dv, modules):
    not_all = True
    while not_all:
        not_all = False
        module_status = dv.get_module_status()
        for module, status in module_status.items():
            if status and (module in modules):
                dv.disable_module(module)
                not_all = True
        time.sleep(1)

def raycast_to_ground(sim, position):
    start_height = 5
    start_point = lgsvl.Vector(
        position.x, position.y + start_height, position.z)
    hit = sim.raycast(start_point, lgsvl.Vector(0, -1, 0), layer_mask=1 << 0)
    if hit:
        return hit.point
    else:
        return position


# Bezier curve
def bezier_point(t, P0, P1, P2, P3):
    """ Calculate the cubic Bezier curve point at t """
    return (1 - t) ** 3 * P0 + 3 * (1 - t) ** 2 * t * P1 + 3 * (1 - t) * t ** 2 * P2 + t ** 3 * P3


def calculate_curvature(point1, point2, point3):
    """ Calculates the curvature defined by three points """
    if np.array_equal(point1, point2) or np.array_equal(point2, point3):
        return 0
    k = 0.5 * (point1.x * (point2.y - point3.y) - point2.x * (point1.y - point3.y) + point3.x * (point1.y - point2.y)) / \
        (point1.x * point2.x + point2.y * point3.y + point3.x * point1.y -
         point1.y * point2.x - point2.y * point3.x - point3.y * point1.x)
    return k

def bezier_derivative(t, P0, P1, P2, P3):
    """Calculate the derivative of a cubic Bezier curve at parameter t."""
    P0, P1, P2, P3 = np.array(P0), np.array(P1), np.array(P2), np.array(P3)
    return (-3 * (1 - t)**2 * P0
            + 3 * (1 - 4*t + 3*t**2) * P1
            + 3 * (2*t - 3*t**2) * P2
            + 3 * t**2 * P3)

def calculate_angle(prev_point, current_point):
    delta_x = current_point.x - prev_point.x
    delta_z = current_point.z - prev_point.z
    angle = np.arctan2(delta_z, delta_x)  # The returned angle is between -π and π.
    return np.degrees(angle)  


def calculate_distance(pos1, pos2):
    return ((pos1.x - pos2.x) ** 2 + (pos1.z - pos2.z) ** 2) ** 0.5