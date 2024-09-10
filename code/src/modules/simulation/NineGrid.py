import numpy as np
import lgsvl

class NineGrid:
    def __init__(self, npc, forward, right, grid_width=3.5, grid_height=30):
        self.npc = npc
        self.forward = forward
        self.right = right
        self.grid_width = grid_width
        self.grid_height = grid_height

    def get_ego_region(self, ego_position):
        # Use the current position and direction of the npc
        npc_position = self.npc.state.position

        # Calculate relative position
        relative_position = lgsvl.Vector(ego_position.x - npc_position.x,
                                          ego_position.y - npc_position.y,
                                          ego_position.z - npc_position.z)

        # Create matrix A and vector b
        A = np.array([
            [self.forward.x, self.right.x],
            [self.forward.z, self.right.z]
        ])
        b = np.array([relative_position.x, relative_position.z])

        # Solve the linear system to find m and n
        try:
            m, n = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            return None  # If A is irreversible, return None

        # Determine the position of the NineGrid based on the values ​​of m and n
        if abs(m) <= self.grid_height * 1.5 and abs(n) <= self.grid_width * 1.5:
            # Judge column
            if abs(n) <= self.grid_width * 0.5:
                col = 2  # middle
            elif n > self.grid_width * 0.5:
                col = 3  # right
            else:
                col = 1  # left

            # Judge row
            if abs(m) <= self.grid_height * 0.5:
                row = 2  # middle
            elif m > self.grid_height * 0.5:
                row = 1  # upper
            else:
                row = 3  # below
            
            # Determine area number based on row and column
            if row == 3:
                if col == 1:
                    return 5  # Zone L1
                elif col == 2:
                    return 2 # Zone N1
                elif col == 3:
                    return 1 # Zone R1
            elif row == 2:
                if col == 1:
                    return 4    # Zone L2
                elif col == 3:
                    return 3    # Zone R2
                elif col == 2:
                    return 0    # Middle NPC position
            elif row == 1:
                if col == 2:
                    return 6  # Indicates in the upper half of the range
        return None  # If the values ​​of m and n are not in the expected range, None is returned.

