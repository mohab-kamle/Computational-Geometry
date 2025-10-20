# model.py
# (Owned by the Logic/Algorithm Team)
# --- NO TKINTER OR PIL IMPORTS ---
import math
import time

class JarvisMarchModel:
    def __init__(self):
        self.points = []
        self.hull = []
        self.n = 0
        self.h = 0
        self.start_time = 0

    def add_point(self, grid_x, grid_y):
        """Adds a new unique point to the list."""
        if not any(p['grid_x'] == grid_x and p['grid_y'] == grid_y for p in self.points):
            self.points.append({'grid_x': grid_x, 'grid_y': grid_y})
            return True
        return False

    def get_points(self):
        return self.points

    def get_hull(self):
        return self.hull

    def get_point_count(self):
        return len(self.points)

    def reset(self):
        self.points.clear()
        self.hull.clear()

    # --- Static Math Helpers ---
    @staticmethod
    def _distance_sq(p1, p2):
        return (p1['grid_x'] - p2['grid_x'])**2 + (p1['grid_y'] - p2['grid_y'])**2

    @staticmethod
    def _orientation(p, q, r):
        val = (q['grid_x'] - p['grid_x']) * (r['grid_y'] - p['grid_y']) - \
              (q['grid_y'] - p['grid_y']) * (r['grid_x'] - p['grid_x'])
        if math.isclose(val, 0): return 0, val
        return (1, val) if val > 0 else (2, val)

    # --- Core Algorithm as a Generator ---
    
    def run_algorithm(self):
        """
        This is the new algorithm logic. It's a generator that
        'yields' the state at each step, instead of calling root.after().
        The Controller will be responsible for looping through this.
        """
        self.start_time = time.perf_counter()
        self.hull = []
        self.n = len(self.points)
        if self.n < 3:
            return  # Stop the generator if not enough points

        # 1. Find the starting point (bottom-most, then left-most)
        start_idx = min(range(self.n), key=lambda i: (self.points[i]['grid_y'], self.points[i]['grid_x']))
        p_idx = start_idx
        
        while True:
            self.hull.append(self.points[p_idx])
            
            # Find the first valid 'next' point (q)
            q_idx = -1
            for i in range(self.n):
                if i != p_idx:
                    q_idx = i
                    break
            if q_idx == -1: break # Should not happen if n >= 2

            # This is the 'find_next_hull_point' logic
            p = self.points[p_idx]
            q = self.points[q_idx]

            # Now, iterate through all other points to find the real 'q'
            # This is the 'check_candidate_point' loop
            for check_idx in range(self.n):
                if check_idx == p_idx or check_idx == q_idx:
                    continue
                
                r = self.points[check_idx]
                o, val = self._orientation(p, q, r)
                
                desc = (f"P: ({p['grid_x']},{p['grid_y']}), Q (best): ({q['grid_x']},{q['grid_y']}), I (test): ({r['grid_x']},{r['grid_y']})\n\n"
                        f"Checking orientation of (P, Q, I).\nResult: {val:.1f}\n\n")

                if o == 2:  # Counter-clockwise
                    desc += "Result is negative -> Counter-clockwise.\nI is 'more left' than Q. New Q = I."
                    q_idx = check_idx
                    q = self.points[q_idx] # Update q for next comparison
                elif o == 0:  # Collinear
                    desc += "Result is zero -> Collinear.\n"
                    dist_pi = self._distance_sq(p, r)
                    dist_pq = self._distance_sq(p, q)
                    if dist_pi > dist_pq:
                        desc += f"I is farther than Q. New Q = I."
                        q_idx = check_idx
                        q = self.points[q_idx] # Update q
                    else:
                        desc += "Q is farther or equal. Q remains."
                else: # Clockwise
                    desc += "Result is positive -> Clockwise.\nQ remains the best candidate."
                
                # --- THIS IS THE KEY ---
                # Yield the current state to the controller to draw
                yield {
                    'p_idx': p_idx,
                    'q_idx': q_idx,
                    'check_idx': check_idx,
                    'description': desc,
                    'hull_so_far': self.hull
                }

            # Loop finished, we found the next hull point
            p_idx = q_idx
            
            # Check if we're back at the start
            if p_idx == start_idx:
                break
        
        # --- Algorithm Finished ---
        end_time = time.perf_counter()
        self.h = len(self.hull)
        self.time_taken_ms = (end_time - self.start_time) * 1000
        
        # Yield a final 'finished' state
        yield {
            'status': 'finished',
            'hull_so_far': self.hull,
            'time_ms': self.time_taken_ms,
            'n': self.n,
            'h': self.h,
            'complexity': f"O(nh): {self.n} * {self.h} = {self.n * self.h} ops"
        }