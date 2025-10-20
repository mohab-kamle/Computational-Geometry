# model.py
# (Owned by the Logic/Algorithm Team)
# --- NO TKINTER OR PIL IMPORTS ---
import math
import time
from functools import cmp_to_key

# --- RENAMED CLASS ---
class ConvexHullModel:
    def __init__(self):
        self.points = []
        self.hull = []
        self.n = 0
        self.h = 0
        self.start_time = 0
        self.pivot = None # For Graham Scan

    def add_point(self, grid_x, grid_y):
        """Adds a new unique point to the list."""
        if not any(p['grid_x'] == grid_x and p['grid_y'] == grid_y for p in self.points):
            self.points.append({'grid_x': grid_x, 'grid_y': grid_y, 'id': len(self.points)})
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
        self.pivot = None

    # --- Static Math Helpers ---
    @staticmethod
    def _distance_sq(p1, p2):
        return (p1['grid_x'] - p2['grid_x'])**2 + (p1['grid_y'] - p2['grid_y'])**2

    @staticmethod
    def _orientation(p, q, r):
        # 0 -> Collinear
        # 1 -> Clockwise
        # 2 -> Counterclockwise
        val = (q['grid_x'] - p['grid_x']) * (r['grid_y'] - p['grid_y']) - \
              (q['grid_y'] - p['grid_y']) * (r['grid_x'] - p['grid_x'])
              
        if math.isclose(val, 0): return 0, val
        return (1, val) if val > 0 else (2, val)

    # --- Jarvis March Algorithm ---
    
    def run_jarvis_march(self):
        """
        Generator for Jarvis March (Gift Wrapping) Algorithm.
        Yields the state at each check.
        """
        self.start_time = time.perf_counter()
        self.hull = []
        self.n = len(self.points)
        if self.n < 3:
            return

        # 1. Find the starting point
        start_idx = min(range(self.n), key=lambda i: (self.points[i]['grid_y'], self.points[i]['grid_x']))
        p_idx = start_idx
        
        while True:
            self.hull.append(self.points[p_idx])
            
            # Find the first valid 'next' point (q)
            q_idx = (p_idx + 1) % self.n

            # This is the 'find_next_hull_point' logic
            p = self.points[p_idx]

            # Iterate through all other points
            for check_idx in range(self.n):
                if check_idx == p_idx:
                    continue
                
                q = self.points[q_idx]
                r = self.points[check_idx]
                o, val = self._orientation(p, q, r)
                
                desc = (f"P: ({p['grid_x']},{p['grid_y']}), Q (best): ({q['grid_x']},{q['grid_y']}), I (test): ({r['grid_x']},{r['grid_y']})\n\n"
                        f"Checking orientation of (P, Q, I).\nResult: {val:.1f}\n\n")

                if o == 2:  # Counter-clockwise
                    desc += "Result is negative -> Counter-clockwise.\nI is 'more left' than Q. New Q = I."
                    q_idx = check_idx
                elif o == 0:  # Collinear
                    desc += "Result is zero -> Collinear.\n"
                    dist_pi = self._distance_sq(p, r)
                    dist_pq = self._distance_sq(p, q)
                    if dist_pi > dist_pq:
                        desc += f"I is farther than Q. New Q = I."
                        q_idx = check_idx
                    else:
                        desc += "Q is farther or equal. Q remains."
                else: # Clockwise
                    desc += "Result is positive -> Clockwise.\nQ remains the best candidate."
                
                yield {
                    'type': 'jarvis',
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
        
        yield {
            'status': 'finished',
            'hull_so_far': self.hull,
            'time_ms': self.time_taken_ms,
            'complexity': f"Jarvis March: O(nh) = {self.n} * {self.h} ops"
        }

    # --- NEW: Graham Scan Algorithm ---

    def _get_pivot_and_sort_points(self):
        """Helper for Graham Scan: finds pivot and sorts remaining points by polar angle."""
        if self.n < 3:
            return None, None
            
        # 1. Find pivot (bottom-most, then left-most)
        pivot_idx = min(range(self.n), key=lambda i: (self.points[i]['grid_y'], self.points[i]['grid_x']))
        self.pivot = self.points[pivot_idx]
        
        # 2. Create list of other points
        other_points = [p for i, p in enumerate(self.points) if i != pivot_idx]
        
        # 3. Define a comparison function for sorting
        def compare(p1, p2):
            o, _ = self._orientation(self.pivot, p1, p2)
            
            if o == 0: # Collinear
                # Keep the farthest point
                if self._distance_sq(self.pivot, p1) < self._distance_sq(self.pivot, p2):
                    return -1 # p2 is farther, so it comes "after" p1
                else:
                    return 1  # p1 is farther or equal, so it comes "after" p2
            
            # Not collinear, sort by angle
            return 1 if o == 1 else -1 # 1 = Clockwise (p2 is "after"), -1 = CCW (p1 is "after")

        # 4. Sort points based on polar angle
        sorted_points = sorted(other_points, key=cmp_to_key(compare))
        
        # 5. Handle collinear points removal (keep only farthest)
        # We iterate backwards and remove any point that is collinear with its *next* point
        # (since the farthest one will be at the end of any collinear group)
        final_sorted = []
        i = 0
        while i < len(sorted_points):
            final_sorted.append(sorted_points[i])
            j = i + 1
            # Skip all collinear points
            while j < len(sorted_points):
                o, _ = self._orientation(self.pivot, sorted_points[i], sorted_points[j])
                if o != 0:
                    break
                j += 1
            i = j

        return self.pivot, final_sorted

    def run_graham_scan(self):
        """
        Generator for Graham Scan Algorithm.
        Yields the state at each stack operation.
        """
        self.start_time = time.perf_counter()
        self.hull = []
        self.n = len(self.points)
        if self.n < 3:
            return

        # --- Step 1 & 2: Find Pivot and Sort ---
        pivot, sorted_points = self._get_pivot_and_sort_points()
        
        if not pivot or len(sorted_points) < 2:
            return # Not enough unique points to form a hull

        yield {
            'type': 'graham',
            'status': 'sorted',
            'pivot': pivot,
            'sorted_points': [pivot] + sorted_points, # Show lines from pivot
            'stack': [],
            'check_idx': -1,
            'description': f"Found pivot P: ({pivot['grid_x']},{pivot['grid_y']}).\nSorted all other points by polar angle."
        }

        # --- Step 3: Main Algorithm ---
        stack = [pivot, sorted_points[0], sorted_points[1]]
        
        # We start checking from the 3rd sorted point
        for i in range(2, len(sorted_points)):
            current_point = sorted_points[i]
            
            # Yield the 'checking' state
            yield {
                'type': 'graham',
                'status': 'checking',
                'pivot': pivot,
                'sorted_points': [pivot] + sorted_points,
                'stack': stack,
                'check_point_id': current_point['id'],
                'description': f"Checking point I: ({current_point['grid_x']},{current_point['grid_y']})\nAgainst stack top: ({stack[-1]['grid_x']},{stack[-1]['grid_y']})"
            }

            # --- Step 4: Pop from stack if not CCW ---
            # stack[-2] = next-to-top, stack[-1] = top
            o, val = self._orientation(stack[-2], stack[-1], current_point)
            
            while o != 2: # While not counter-clockwise (i.e., clockwise or collinear)
                popped = stack.pop()
                
                yield {
                    'type': 'graham',
                    'status': 'popping',
                    'pivot': pivot,
                    'sorted_points': [pivot] + sorted_points,
                    'stack': stack,
                    'check_point_id': current_point['id'],
                    'description': f"({stack[-1]['grid_x']},{stack[-1]['grid_y']}) -> ({popped['grid_x']},{popped['grid_y']}) -> ({current_point['grid_x']},{current_point['grid_y']}) is a 'right turn'.\nPopping ({popped['grid_x']},{popped['grid_y']}) from stack."
                }
                
                # Re-check with new stack top
                o, val = self._orientation(stack[-2], stack[-1], current_point)

            # --- Step 5: Push to stack ---
            stack.append(current_point)
            yield {
                'type': 'graham',
                'status': 'pushing',
                'pivot': pivot,
                'sorted_points': [pivot] + sorted_points,
                'stack': stack,
                'check_point_id': current_point['id'],
                'description': f"({stack[-2]['grid_x']},{stack[-2]['grid_y']}) -> ({stack[-1]['grid_x']},{stack[-1]['grid_y']}) is a 'left turn'.\nPushing ({current_point['grid_x']},{current_point['grid_y']}) to stack."
            }

        # --- Algorithm Finished ---
        self.hull = stack
        end_time = time.perf_counter()
        self.h = len(self.hull)
        self.time_taken_ms = (end_time - self.start_time) * 1000
        
        yield {
            'status': 'finished',
            'hull_so_far': self.hull,
            'time_ms': self.time_taken_ms,
            'complexity': f"Graham Scan: O(n log n) = {self.n} * {math.log(self.n, 2):.1f} ops (for sorting)"
        }