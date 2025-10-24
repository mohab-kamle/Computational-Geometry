import tkinter as tk
from tkinter import ttk
import time
import traceback
import math # Import math for validation
from model import ConvexHullModel
from PIL import Image, ImageTk, ImageDraw, ImageFont

class DualComparisonView:
    """Handles the dual canvas comparison mode interface."""

    # --- Color Palette (STYLES UPDATED) ---
    C_BLACK = "#000000"
    C_NEAR_BLACK = "#1d1d1f"
    C_DARK_GRAY = "#2c2c2e"
    C_MED_GRAY = "#3c3c3e"
    C_LIGHT_GRAY_TEXT = "#a1a1a6"
    C_WHITE_TEXT = "#f5f5f7"
    C_BLUE = "#0071e3"
    C_BLUE_ACTIVE = "#0077ed"
    C_GREEN = "#10b981"
    C_GREEN_ACTIVE = "#059669"

    C_HULL_LINE = "#0071e3"
    C_HULL_FILL = "red"
    C_POINT_BLUE = C_BLUE
    C_POINT_P = "#f59e0b"
    C_LINE_Q = "#10b981"
    C_LINE_I = "#ef4444"
    C_BG_CANVAS = C_BLACK

    FONT_BOLD = ("Inter", 12, "bold")
    FONT_NORMAL = ("Inter", 10)

    def __init__(self, root, main_controller):
        self.root = root
        self.main_controller = main_controller

        # Use separate models for each algorithm
        self.shared_model = main_controller.model # For adding/resetting points
        self.model_jarvis = ConvexHullModel()
        self.model_graham = ConvexHullModel()

        self.grid_size = 20
        self.min_grid_size = 4
        self.max_grid_size = 120

        # Canvas dimensions and origins
        self.origin_x_left = 0
        self.origin_y_left = 0
        self.origin_x_right = 0
        self.origin_y_right = 0
        self.canvas_width = 0
        self.canvas_height = 0

        self.last_pan_x = 0
        self.last_pan_y = 0
        self.is_panning = False

        self._click_job = None
        self.is_running = False
        self.is_paused = False
        self.next_step_requested = False
        self.jarvis_gen = None
        self.graham_gen = None
        self.jarvis_finished = False
        self.graham_finished = False
        self.animation_job = None

        # --- Variables to store the final state ---
        self.final_jarvis_state = None
        self.final_graham_state = None
        # ----------------------------------------

        # Load font for styled buttons
        try:
            # Ensure the font file exists or handle the error
            self.pil_font_bold = ImageFont.truetype("arialbd.ttf", 14)
        except IOError:
            print("Warning: arialbd.ttf not found. Using default font.")
            self.pil_font_bold = ImageFont.load_default()
        except Exception as e:
            print(f"Error loading font: {e}. Using default font.")
            self.pil_font_bold = ImageFont.load_default()


        self._setup_ui()
        # Initial resize called here, will likely call again via Configure binding
        # self.resize_canvases() # Can potentially remove if Configure always triggers

    def _setup_ui(self):
        """Setup the dual comparison interface."""
        self.main_frame = tk.Frame(self.root, bg=self.C_BLACK)

        # Control Panel (right) - Increased width slightly
        control_panel = tk.Frame(self.main_frame, bg=self.C_NEAR_BLACK, width=350, padx=16, pady=16)
        control_panel.pack(side=tk.RIGHT, fill=tk.Y)
        control_panel.pack_propagate(False)

        # Title
        tk.Label(control_panel, text="Dual Comparison", font=("Inter", 18, "bold"),
                 fg=self.C_WHITE_TEXT, bg=self.C_NEAR_BLACK).pack(fill=tk.X, pady=(0, 10))

        # Status Bar
        self.status_text = tk.StringVar(value="Add points to begin.")
        status_bar_frame = tk.Frame(control_panel, bg=self.C_DARK_GRAY, padx=10, pady=6)
        status_bar_frame.pack(fill=tk.X, pady=(5, 15))
        tk.Label(status_bar_frame, text="Status:", font=("Inter", 14, "bold"), fg=self.C_WHITE_TEXT, bg=self.C_DARK_GRAY).pack(side="left", padx=(0, 8))
        tk.Label(status_bar_frame, textvariable=self.status_text, font=("Inter", 12), fg=self.C_WHITE_TEXT, bg=self.C_DARK_GRAY, justify="left", wraplength=200, anchor="w").pack(side="left", fill="x", expand=True)

        # Control Buttons - Stacked Vertically
        main_controls_frame = tk.Frame(control_panel, bg=self.C_NEAR_BLACK, pady=10)
        main_controls_frame.pack(fill=tk.X)

        self.start_button = self._create_rounded_button(
            main_controls_frame, "Start Comparison",
            self._start_comparison,
            bg=self.C_BLUE, fg=self.C_WHITE_TEXT,
            bg_active=self.C_BLUE_ACTIVE, parent_bg=self.C_NEAR_BLACK
        )
        self.start_button.pack(fill=tk.X, pady=(0, 5)) # Added padding between buttons

        self.reset_button = self._create_rounded_button(
            main_controls_frame, "Reset",
            self._reset_comparison,
            bg=self.C_DARK_GRAY, fg=self.C_WHITE_TEXT,
            bg_active=self.C_MED_GRAY, parent_bg=self.C_NEAR_BLACK
        )
        self.reset_button.pack(fill=tk.X, pady=(0, 5)) # Added padding

        self.back_button = self._create_rounded_button(
            main_controls_frame, "Back to Main",
            self._go_back_to_main,
            bg=self.C_MED_GRAY, fg=self.C_WHITE_TEXT,
            bg_active=self.C_DARK_GRAY, parent_bg=self.C_NEAR_BLACK
        )
        self.back_button.pack(fill=tk.X) # No padding after last button

        # Animation Controls Separator
        tk.Frame(control_panel, height=1, bg=self.C_MED_GRAY).pack(fill=tk.X, pady=10)
        self.anim_controls_frame = tk.Frame(control_panel, bg=self.C_NEAR_BLACK, pady=0) # Removed pady

        # Speed Slider
        speed_frame = tk.Frame(self.anim_controls_frame, bg=self.C_NEAR_BLACK)
        tk.Label(speed_frame, text="Speed:", font=self.FONT_NORMAL,
                 fg=self.C_LIGHT_GRAY_TEXT, bg=self.C_NEAR_BLACK).pack(side=tk.LEFT)
        style = ttk.Style()
        style.configure("Transparent.Horizontal.TScale", troughcolor=self.C_DARK_GRAY, background=self.C_NEAR_BLACK)
        self.speed_scale = ttk.Scale(speed_frame, from_=800, to=50, orient="horizontal", style="Transparent.Horizontal.TScale")
        self.speed_scale.set(350)
        self.speed_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        speed_frame.pack(fill=tk.X, pady=(5, 10))

        # Pause/Next buttons - Stacked Vertically
        step_controls_frame = tk.Frame(self.anim_controls_frame, bg=self.C_NEAR_BLACK)
        step_controls_frame.pack(fill=tk.X, pady=10) # Added padding around this frame

        self.pause_resume_button = self._create_rounded_button(
            step_controls_frame, "Pause",
            self._pause_resume,
            bg=self.C_DARK_GRAY, fg=self.C_WHITE_TEXT,
            bg_active=self.C_MED_GRAY, parent_bg=self.C_NEAR_BLACK
        )
        self.pause_resume_button.pack(fill=tk.X, pady=(0, 5)) # Padding below

        self.next_step_button = self._create_rounded_button(
            step_controls_frame, "Next Step",
            self._next_step,
            bg=self.C_DARK_GRAY, fg=self.C_WHITE_TEXT,
            bg_active=self.C_MED_GRAY, parent_bg=self.C_NEAR_BLACK
        )
        self.next_step_button.pack(fill=tk.X) # No padding after last button

        # Analysis Frame
        self.analysis_frame = tk.Frame(control_panel, bg=self.C_NEAR_BLACK, pady=10)
        tk.Label(self.analysis_frame, text="Live Analysis", font=("Inter", 15, "bold"),
                 fg=self.C_WHITE_TEXT, bg=self.C_NEAR_BLACK).pack(fill=tk.X, pady=(0, 5))

        dual_text_frame = tk.Frame(self.analysis_frame, bg=self.C_DARK_GRAY, padx=12, pady=10, highlightbackground=self.C_MED_GRAY, highlightthickness=1)
        dual_text_frame.pack(fill=tk.BOTH, expand=True)

        # Left (Jarvis)
        tk.Label(dual_text_frame, text="Jarvis March:", font=self.FONT_NORMAL,
                 fg=self.C_POINT_P, bg=self.C_DARK_GRAY, anchor="w").pack(fill=tk.X)
        self.analysis_text_left = tk.StringVar(value="Waiting...")
        tk.Label(dual_text_frame, textvariable=self.analysis_text_left, font=("Inter", 10), # Slightly larger font
                 fg=self.C_LIGHT_GRAY_TEXT, bg=self.C_DARK_GRAY, wraplength=260, justify=tk.LEFT,
                 anchor="nw", height=4, padx=0, pady=0).pack(fill=tk.X)

        tk.Frame(dual_text_frame, height=1, bg=self.C_MED_GRAY).pack(fill=tk.X, pady=5)

        # Right (Graham)
        tk.Label(dual_text_frame, text="Graham Scan:", font=self.FONT_NORMAL,
                 fg=self.C_BLUE, bg=self.C_DARK_GRAY, anchor="w").pack(fill=tk.X)
        self.analysis_text_right = tk.StringVar(value="Waiting...")
        tk.Label(dual_text_frame, textvariable=self.analysis_text_right, font=("Inter", 10), # Slightly larger font
                 fg=self.C_LIGHT_GRAY_TEXT, bg=self.C_DARK_GRAY, wraplength=260, justify=tk.LEFT,
                 anchor="nw", height=4, padx=0, pady=0).pack(fill=tk.X)

        # --- Compact Vertical Results Frame ---
        self.results_frame = tk.Frame(control_panel, bg=self.C_NEAR_BLACK, pady=15)
        self.results_frame.pack(fill=tk.X)

        # Title
        tk.Label(
            self.results_frame,
            text="Results Summary",
            font=("Inter", 14, "bold"),
            fg=self.C_WHITE_TEXT,
            bg=self.C_NEAR_BLACK,
            anchor="center"
        ).pack(fill=tk.X, pady=(0, 8))

        # Container (slightly padded background)
        results_bg = tk.Frame(
            self.results_frame,
            bg=self.C_DARK_GRAY,
            padx=12,
            pady=10,
            highlightbackground=self.C_MED_GRAY,
            highlightthickness=1
        )
        results_bg.pack(fill=tk.X, padx=4)

        # Helper for vertically stacked result items
        def create_vertical_result(parent, title, var, accent=None):
            accent = accent or self.C_BLUE_ACTIVE
            frame = tk.Frame(parent, bg=self.C_DARK_GRAY)
            frame.pack(fill=tk.X, pady=6)

            tk.Label(
                frame, text=title, font=("Inter", 12, "bold"),
                fg=accent, bg=self.C_DARK_GRAY, anchor="w"
            ).pack(fill=tk.X)

            tk.Label(
                frame, textvariable=var, font=self.FONT_NORMAL,
                fg=self.C_WHITE_TEXT, bg=self.C_DARK_GRAY,
                anchor="w", wraplength=260, justify="left"
            ).pack(fill=tk.X, pady=(2, 0))

        # --- Result Fields ---
        self.time_text = tk.StringVar(value="—")
        create_vertical_result(results_bg, "Execution Time", self.time_text)

        self.complexity_text = tk.StringVar(value="—")
        create_vertical_result(results_bg, "Algorithm Complexity", self.complexity_text)

        self.status_text = tk.StringVar(value="Waiting for algorithm to start...")
        create_vertical_result(results_bg, "Status", self.status_text, accent=self.C_MED_GRAY)

        # Canvas Area (Right - Dual Canvases)
        self.canvas_container = tk.Frame(self.main_frame, bg=self.C_BLACK)
        self.canvas_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(16,0)) # Added left padding

        # Labels for the dual canvases
        canvas_label_frame = tk.Frame(self.canvas_container, bg=self.C_DARK_GRAY, pady=5)
        canvas_label_frame.pack(fill=tk.X)
        tk.Label(canvas_label_frame, text="Jarvis March (Gift Wrapping)", font=("Inter", 14, "bold"),
                 fg=self.C_POINT_P, bg=self.C_DARK_GRAY).pack(side=tk.LEFT, expand=True)
        tk.Label(canvas_label_frame, text="Graham Scan", font=("Inter", 14, "bold"),
                 fg=self.C_BLUE, bg=self.C_DARK_GRAY).pack(side=tk.LEFT, expand=True)

        # Frame to hold the actual canvas elements side-by-side
        dual_canvas_frame = tk.Frame(self.canvas_container, bg=self.C_BLACK)
        dual_canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Left Canvas (Jarvis) - Added border frame
        canvas_border_left = tk.Frame(dual_canvas_frame, bg=self.C_MED_GRAY, padx=1, pady=1)
        canvas_border_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8)) # Added right padding
        self.canvas_left = tk.Canvas(canvas_border_left, bg=self.C_BG_CANVAS,
                                     highlightthickness=0) # Removed highlight
        self.canvas_left.pack(fill=tk.BOTH, expand=True)
        self.canvas_left.canvas_id = 'left'

        # Right Canvas (Graham) - Added border frame
        canvas_border_right = tk.Frame(dual_canvas_frame, bg=self.C_MED_GRAY, padx=1, pady=1)
        canvas_border_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0)) # Added left padding
        self.canvas_right = tk.Canvas(canvas_border_right, bg=self.C_BG_CANVAS,
                                        highlightthickness=0) # Removed highlight
        self.canvas_right.pack(fill=tk.BOTH, expand=True)
        self.canvas_right.canvas_id = 'right'

        # Bind events
        self._bind_canvas_events()
        # Bind Configure to the container holding both canvases
        self.canvas_container.bind("<Configure>", self.resize_canvases)

        # Initial setup
        self._set_button_states(start_state=tk.DISABLED, reset_state=tk.DISABLED, # Start/Reset disabled initially
                                pause_text="Pause", pause_state=tk.DISABLED,
                                next_state=tk.DISABLED)
        self.hide_animation_controls()
        self.hide_results()
        # Initial draw might happen via resize_canvases called by pack
        # self._redraw_all_canvases() # Can remove if resize handles it

    # --- Coordinate Conversion ---
    def grid_to_canvas(self, canvas_id, grid_x, grid_y):
        if not isinstance(grid_x, (int, float)) or not isinstance(grid_y, (int, float)):
             print(f"Warning: Non-numeric grid coords ({grid_x}, {grid_y})")
             return 0,0 # Fallback
        if canvas_id == 'left':
            origin_x, origin_y = self.origin_x_left, self.origin_y_left
        else:
            origin_x, origin_y = self.origin_x_right, self.origin_y_right
        return origin_x + grid_x * self.grid_size, origin_y - grid_y * self.grid_size

    def canvas_to_grid(self, canvas_id, cx, cy):
        if not isinstance(cx, (int, float)) or not isinstance(cy, (int, float)):
             print(f"Warning: Non-numeric canvas coords ({cx}, {cy})")
             return 0,0 # Fallback
        if self.grid_size == 0: return 0, 0
        if canvas_id == 'left':
            origin_x, origin_y = self.origin_x_left, self.origin_y_left
        else:
            origin_x, origin_y = self.origin_x_right, self.origin_y_right
        return (cx - origin_x) / self.grid_size, (origin_y - cy) / self.grid_size

    # --- Drawing Methods ---
    def draw_all(self, canvas, points, hull, clear=True):
        """Draws the base scene: grid, points, and final hull shape."""
        if not isinstance(canvas, tk.Canvas) or not canvas.winfo_exists(): return
        try:
            if clear: canvas.delete("all")
            self._draw_axes_and_grid(canvas)

            valid_points = [p for p in points if isinstance(p, dict) and 'grid_x' in p and 'grid_y' in p]
            for p in valid_points:
                # Ensure coordinates are numbers before proceeding
                if not all(isinstance(p[k], (int, float)) for k in ['grid_x', 'grid_y']): continue

                cx, cy = self.grid_to_canvas(canvas.canvas_id, p['grid_x'], p['grid_y'])
                if abs(cx) > 1e6 or abs(cy) > 1e6: continue # Skip extreme coords

                canvas.create_oval(cx-4, cy-4, cx+4, cy+4, fill=self.C_POINT_BLUE, outline="", tags="point")
                label_x, label_y = round(p['grid_x']), round(p['grid_y'])
                # Avoid drawing text if coordinates are problematic
                if math.isfinite(cx) and math.isfinite(cy):
                     canvas.create_text(cx + 8, cy - 8, text=f"({label_x},{label_y})", anchor="sw", fill=self.C_LIGHT_GRAY_TEXT, font=("Inter", 9))


            valid_hull = [p for p in hull if isinstance(p, dict) and 'grid_x' in p and 'grid_y' in p]
            if valid_hull and len(valid_hull) >= 2:
                # Determine if hull should be drawn as outline only based on animation state
                is_outline = self.is_running and (
                    (canvas.canvas_id == 'left' and not self.jarvis_finished) or
                    (canvas.canvas_id == 'right' and not self.graham_finished)
                )
                self._draw_final_hull_shape(canvas, valid_hull, outline_only=is_outline)
        except tk.TclError as e:
            print(f"Error in draw_all for canvas {canvas.canvas_id}: {e}")
        except Exception as e:
            print(f"Unexpected error in draw_all: {e}")
            traceback.print_exc()

    # ... (draw_jarvis_step and draw_graham_step remain largely the same, but rely on draw_all) ...
    def draw_jarvis_step(self, canvas, points, p_point, q_point, i_point, hull_so_far):
        if not all(isinstance(pt, dict) and 'grid_x' in pt and 'grid_y' in pt for pt in [p_point, q_point, i_point]): return
        valid_hull = [p for p in hull_so_far if isinstance(p, dict) and 'grid_x' in p and 'grid_y' in p]

        try:
            self.draw_all(canvas, points, hull=None, clear=True) # Draw background

            p_c = self.grid_to_canvas(canvas.canvas_id, p_point['grid_x'], p_point['grid_y'])
            q_c = self.grid_to_canvas(canvas.canvas_id, q_point['grid_x'], q_point['grid_y'])
            i_c = self.grid_to_canvas(canvas.canvas_id, i_point['grid_x'], i_point['grid_y'])

            canvas.create_oval(p_c[0]-6, p_c[1]-6, p_c[0]+6, p_c[1]+6, fill=self.C_POINT_P, outline="", tags="p_point")
            canvas.create_line(p_c, q_c, fill=self.C_LINE_Q, width=2, tags="q_line")
            canvas.create_line(p_c, i_c, fill=self.C_LINE_I, width=1, dash=(3, 3), tags="i_line")
            canvas.create_oval(i_c[0]-4, i_c[1]-4, i_c[0]+4, i_c[1]+4, fill=self.C_LINE_I, outline="", tags="i_point")

            self._draw_final_hull_shape(canvas, valid_hull, outline_only=True) # Always outline during step
        except tk.TclError as e: print(f"Error in draw_jarvis_step: {e}")
        except Exception as e: print(f"Unexpected error in draw_jarvis_step: {e}")


    def draw_graham_step(self, canvas, points, pivot, sorted_points_with_pivot, stack, check_point, status):
        if pivot and not (isinstance(pivot, dict) and 'grid_x' in pivot and 'grid_y' in pivot): return
        valid_stack = [p for p in stack if isinstance(p, dict) and 'grid_x' in p and 'grid_y' in p]
        stack = valid_stack # Use validated stack

        try:
            self.draw_all(canvas, points, hull=None, clear=True)
            canvas_id = canvas.canvas_id

            if pivot:
                p_c = self.grid_to_canvas(canvas_id, pivot['grid_x'], pivot['grid_y'])
                canvas.create_oval(p_c[0]-7, p_c[1]-7, p_c[0]+7, p_c[1]+7, fill=self.C_POINT_P, outline="", tags="pivot")

            if status == 'sorted' and pivot:
                 valid_sorted = [p for p in sorted_points_with_pivot if isinstance(p, dict) and 'grid_x' in p and 'grid_y' in p]
                 sorted_points_with_pivot = valid_sorted
                 for point in sorted_points_with_pivot:
                      if 'id' in point and 'id' in pivot and point['id'] == pivot['id']: continue # More robust check
                      pt_c = self.grid_to_canvas(canvas_id, point['grid_x'], point['grid_y'])
                      canvas.create_line(p_c, pt_c, fill=self.C_MED_GRAY, width=1, dash=(2, 4))


            if len(stack) >= 2: # Use potentially corrected stack
                stack_coords = []
                valid_coords_exist = True
                for p in stack:
                    try:
                         coords = self.grid_to_canvas(canvas_id, p['grid_x'], p['grid_y'])
                         if not all(math.isfinite(c) for c in coords):
                              valid_coords_exist = False; break
                         stack_coords.extend(coords)
                    except KeyError: valid_coords_exist = False; break
                if valid_coords_exist:
                     canvas.create_line(stack_coords, fill=self.C_LINE_Q, width=3, tags="stack_line")


            if status in ['checking', 'popping', 'pushing'] and check_point and len(stack) >= 2:
                 if not (isinstance(check_point, dict) and 'grid_x' in check_point and 'grid_y' in check_point):
                      print(f"Invalid check_point: {check_point}")
                 else:
                      try:
                           top_c = self.grid_to_canvas(canvas_id, stack[-1]['grid_x'], stack[-1]['grid_y'])
                           next_top_c = self.grid_to_canvas(canvas_id, stack[-2]['grid_x'], stack[-2]['grid_y'])
                           check_c = self.grid_to_canvas(canvas_id, check_point['grid_x'], check_point['grid_y'])

                           # Check if coords are valid before drawing
                           if all(math.isfinite(c) for c in top_c + next_top_c + check_c):
                                canvas.create_line(next_top_c, top_c, fill=self.C_LINE_Q, width=4, tags="test_line_1")
                                canvas.create_line(top_c, check_c, fill=self.C_LINE_I, width=2, dash=(4, 4), tags="test_line_2")
                                canvas.create_oval(top_c[0]-5, top_c[1]-5, top_c[0]+5, top_c[1]+5, fill=self.C_LINE_Q, outline="", tags="top_point")
                                canvas.create_oval(check_c[0]-5, check_c[1]-5, check_c[0]+5, check_c[1]+5, fill=self.C_LINE_I, outline="", tags="check_point")
                           else:
                                print("Warning: Skipping drawing check lines due to invalid coordinates.")

                      except IndexError: pass
                      except KeyError: pass
        except tk.TclError as e: print(f"Error in draw_graham_step: {e}")
        except Exception as e: print(f"Unexpected error in draw_graham_step: {e}")


    def _draw_final_hull_shape(self, canvas, hull, outline_only=False):
        # Increased validation
        if not isinstance(hull, list) or not hull: return
        valid_hull = [p for p in hull if isinstance(p, dict) and 'grid_x' in p and 'grid_y' in p]
        if len(valid_hull) < 2: return # Need at least 2 points

        canvas_id = canvas.canvas_id
        hull_coords = []
        try:
             # Generate coords, checking each point
             for p in valid_hull:
                  coords = self.grid_to_canvas(canvas_id, p['grid_x'], p['grid_y'])
                  if not all(isinstance(c, (int, float)) and math.isfinite(c) for c in coords):
                       print(f"Warning: Skipping point {p} due to invalid canvas coords {coords}")
                       continue # Skip points that result in invalid coords
                  hull_coords.extend(coords)

             if not hull_coords or len(hull_coords) < 4: # Need at least 2 valid points (4 coords)
                  return

             # Ensure even number of coordinates after potential skips
             if len(hull_coords) % 2 != 0: hull_coords = hull_coords[:-1]
             if len(hull_coords) < 4: return


        except Exception as e:
             print(f"Error generating hull coordinates: {e}")
             return

        try:
            # Fill only if >= 3 points (6 coords) and not outline_only
            if len(hull_coords) >= 6 and not outline_only:
                canvas.create_polygon(hull_coords, fill=self.C_HULL_FILL, outline="", stipple="gray25", tags="hull_fill")

            # Draw outline if >= 2 points (4 coords)
            if len(hull_coords) >= 4:
                closed_coords = hull_coords + hull_coords[0:2] # Close loop correctly
                canvas.create_line(closed_coords, fill=self.C_HULL_LINE, width=3, tags="hull_line")

            # Draw points on top (only if >= 2 points)
            for p in valid_hull: # Iterate through the valid points again
                 coords = self.grid_to_canvas(canvas_id, p['grid_x'], p['grid_y'])
                 # Check again before drawing oval
                 if all(isinstance(c, (int, float)) and math.isfinite(c) for c in coords):
                      cx, cy = coords
                      if abs(cx) < 1e6 and abs(cy) < 1e6:
                           canvas.create_oval(cx-6, cy-6, cx+6, cy+6, fill=self.C_HULL_LINE, outline="", tags="hull_point")

        except tk.TclError as e:
             print(f"Tkinter Error drawing final hull: {e}")
        except Exception as e:
             print(f"Unexpected error drawing final hull: {e}")


    def _draw_axes_and_grid(self, canvas):
        if not isinstance(canvas, tk.Canvas) or not canvas.winfo_exists(): return
        try:
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            if canvas_width <= 1: canvas_width = getattr(self, 'canvas_width', 500)
            if canvas_height <= 1: canvas_height = getattr(self, 'canvas_height', 300)
        except tk.TclError:
             canvas_width = getattr(self, 'canvas_width', 500)
             canvas_height = getattr(self, 'canvas_height', 300)

        canvas_id = canvas.canvas_id
        origin_x = self.origin_x_left if canvas_id == 'left' else self.origin_x_right
        origin_y = self.origin_y_left if canvas_id == 'left' else self.origin_y_right

        if self.grid_size <= 0: grid_step = 20
        else: grid_step = self.grid_size
        if grid_step < 10: grid_step *= 2

        label_step = 1
        if self.grid_size < 15: label_step = 2
        if self.grid_size < 7: label_step = 5
        if self.grid_size > 40: label_step = 1

        max_iterations = max(int(canvas_width / grid_step * 2), int(canvas_height / grid_step * 2), 500) + 2

        # Vertical
        i = 0
        while i < max_iterations:
            x_pos = origin_x + i * grid_step
            x_neg = origin_x - i * grid_step
            if x_pos > canvas_width + grid_step and x_neg < -grid_step: break
            try:
                if x_pos <= canvas_width + grid_step and math.isfinite(x_pos): # Check finite
                    canvas.create_line(x_pos, 0, x_pos, canvas_height, fill=self.C_DARK_GRAY, tags="grid_v")
                    if i > 0 and i % label_step == 0 and math.isfinite(origin_y): # Check origin_y
                        canvas.create_text(x_pos, origin_y + 5, text=str(i), anchor="n", fill=self.C_LIGHT_GRAY_TEXT, font=("Inter", 9), tags="grid_label")
                if i > 0 and x_neg >= -grid_step and math.isfinite(x_neg): # Check finite
                    canvas.create_line(x_neg, 0, x_neg, canvas_height, fill=self.C_DARK_GRAY, tags="grid_v")
                    if i % label_step == 0 and math.isfinite(origin_y): # Check origin_y
                        canvas.create_text(x_neg, origin_y + 5, text=str(-i), anchor="n", fill=self.C_LIGHT_GRAY_TEXT, font=("Inter", 9), tags="grid_label")
            except tk.TclError: break # Stop on Tkinter error
            except ValueError: break # Stop on math error (e.g., infinity)
            i += 1


        # Horizontal
        i = 0
        while i < max_iterations:
            y_pos = origin_y + i * grid_step
            y_neg = origin_y - i * grid_step
            if y_pos > canvas_height + grid_step and y_neg < -grid_step: break
            try:
                if y_pos <= canvas_height + grid_step and math.isfinite(y_pos): # Check finite
                    canvas.create_line(0, y_pos, canvas_width, y_pos, fill=self.C_DARK_GRAY, tags="grid_h")
                    if i > 0 and i % label_step == 0 and math.isfinite(origin_x): # Check origin_x
                        canvas.create_text(origin_x - 5, y_pos, text=str(-i), anchor="e", fill=self.C_LIGHT_GRAY_TEXT, font=("Inter", 9), tags="grid_label")
                if i > 0 and y_neg >= -grid_step and math.isfinite(y_neg): # Check finite
                    canvas.create_line(0, y_neg, canvas_width, y_neg, fill=self.C_DARK_GRAY, tags="grid_h")
                    if i % label_step == 0 and math.isfinite(origin_x): # Check origin_x
                        canvas.create_text(origin_x - 5, y_neg, text=str(i), anchor="e", fill=self.C_LIGHT_GRAY_TEXT, font=("Inter", 9), tags="grid_label")
            except tk.TclError: break
            except ValueError: break
            i += 1


        # Axes
        try:
             # Check if origins are finite before drawing axes
             if math.isfinite(origin_x) and math.isfinite(origin_y):
                 canvas.create_line(0, origin_y, canvas_width, origin_y, fill="#888888", width=1, tags="axis")
                 canvas.create_line(origin_x, 0, origin_x, canvas_height, fill="#888888", width=1, tags="axis")
                 canvas.create_text(origin_x - 5, origin_y + 5, text="0", anchor="se", fill=self.C_LIGHT_GRAY_TEXT, font=("Inter", 9, "bold"), tags="grid_label")
             else:
                  print("Warning: Skipping axes drawing due to non-finite origin.")

        except tk.TclError: pass # Ignore Tcl errors here, less critical


    # --- Animation Control ---
    def _start_comparison(self):
        if self.shared_model.get_point_count() < 3:
            self.status_text.set("Need at least 3 points to start.")
            return

        self.is_running = True
        self.is_paused = False
        self.next_step_requested = False
        self.final_jarvis_state = None
        self.final_graham_state = None

        # --- FIX: Reset models BEFORE assigning points ---
        self.model_jarvis.reset()
        self.model_graham.reset()
        # -----------------------------------------------

        # --- FIX: Assign points AFTER reset ---
        # Use list() for a shallow copy, deepcopy might be needed if points are modified later
        points_copy = list(self.shared_model.points)
        self.model_jarvis.points = list(points_copy)
        self.model_graham.points = list(points_copy)
        # --- Make sure n is updated after assigning points ---
        self.model_jarvis.n = len(self.model_jarvis.points)
        self.model_graham.n = len(self.model_graham.points)
        # ----------------------------------------------------

        try: # Get generators
            self.jarvis_gen = self.model_jarvis.run_jarvis_march()
            self.graham_gen = self.model_graham.run_graham_scan()
        except Exception as e:
             print(f"Error creating generators: {e}")
             self.is_running = False
             num_points = self.shared_model.get_point_count()
             self._set_button_states(
                 start_state=tk.NORMAL if num_points >= 3 else tk.DISABLED,
                 reset_state=tk.NORMAL if num_points > 0 else tk.DISABLED,
                 pause_text="Pause", pause_state=tk.DISABLED, next_state=tk.DISABLED
             )
             return

        self.jarvis_finished = False
        self.graham_finished = False

        self.status_text.set("Starting Dual Comparison...")
        self._set_button_states(start_state=tk.DISABLED, reset_state=tk.NORMAL,
                                pause_text="Pause", pause_state=tk.NORMAL, next_state=tk.NORMAL)
        self.show_animation_controls()
        self.hide_results()
        self._redraw_all_canvases() # Initial draw

        self._animate_step() # Start the loop

    def _pause_resume(self):
        if not self.is_running: return
        self.is_paused = not self.is_paused
        pause_text = "Resume" if self.is_paused else "Pause"
        next_state = tk.NORMAL if self.is_paused else tk.DISABLED
        self._set_button_states(start_state=tk.DISABLED, reset_state=tk.NORMAL,
                                pause_text=pause_text, pause_state=tk.NORMAL, next_state=next_state)
        if not self.is_paused:
            self.status_text.set("Resuming comparison...")
            self.next_step_requested = False
            if self.animation_job:
                 try: self.root.after_cancel(self.animation_job)
                 except ValueError: pass
                 self.animation_job = None
            self._animate_step()
        else:
            self.status_text.set("Comparison paused.")
            if self.animation_job:
                 try: self.root.after_cancel(self.animation_job)
                 except ValueError: pass
                 self.animation_job = None

    def _next_step(self):
        if self.is_running and self.is_paused:
            self.next_step_requested = True
            if self.animation_job:
                 try: self.root.after_cancel(self.animation_job)
                 except ValueError: pass
                 self.animation_job = None
            self._animate_step()

    def _animate_step(self):
        if not self.is_running: return
        if self.is_paused and not self.next_step_requested: return

        if self.next_step_requested: self.next_step_requested = False

        if self.animation_job:
            try: self.root.after_cancel(self.animation_job)
            except ValueError: pass
            self.animation_job = None

        current_jarvis_state = None
        current_graham_state = None

        # Jarvis Step
        jarvis_advanced = False
        if not self.jarvis_finished:
            try:
                current_jarvis_state = next(self.jarvis_gen)
                jarvis_advanced = True
                self._process_single_state(self.canvas_left, current_jarvis_state, "Jarvis")
                if current_jarvis_state.get('status') == 'finished':
                    self.jarvis_finished = True
                    self.final_jarvis_state = current_jarvis_state
                    # Draw final Jarvis hull immediately when finished
                    final_j_hull = self.final_jarvis_state.get('hull_so_far', [])
                    self.draw_all(self.canvas_left, self.model_jarvis.get_points(), final_j_hull, clear=True)
            except StopIteration:
                self.jarvis_finished = True
                if not self.final_jarvis_state: 
                    self.final_jarvis_state = {'status': 'finished', 'hull_so_far': self.model_jarvis.get_hull(), 'time_ms': self.model_jarvis.time_taken_ms if hasattr(self.model_jarvis, 'time_taken_ms') else 0, 'complexity': 'N/A'}
                # Draw final Jarvis hull immediately
                final_j_hull = self.final_jarvis_state.get('hull_so_far', [])
                self.draw_all(self.canvas_left, self.model_jarvis.get_points(), final_j_hull, clear=True)
            except Exception as e:
                self.jarvis_finished = True; print(f"Jarvis Error: {e}")
                if not self.final_jarvis_state: self.final_jarvis_state = {'status': 'error', 'hull_so_far': [], 'time_ms': 0, 'complexity': 'Error'}

        # Graham Step
        graham_advanced = False
        if not self.graham_finished:
            try:
                current_graham_state = next(self.graham_gen)
                graham_advanced = True
                self._process_single_state(self.canvas_right, current_graham_state, "Graham")
                if current_graham_state.get('status') == 'finished':
                    self.graham_finished = True
                    self.final_graham_state = current_graham_state
                    # Draw final Graham hull immediately when finished
                    final_g_hull = self.final_graham_state.get('hull_so_far', [])
                    self.draw_all(self.canvas_right, self.model_graham.get_points(), final_g_hull, clear=True)
            except StopIteration:
                self.graham_finished = True
                if not self.final_graham_state: 
                    self.final_graham_state = {'status': 'finished', 'hull_so_far': self.model_graham.get_hull(), 'time_ms': self.model_graham.time_taken_ms if hasattr(self.model_graham, 'time_taken_ms') else 0, 'complexity': 'N/A'}
                # Draw final Graham hull immediately
                final_g_hull = self.final_graham_state.get('hull_so_far', [])
                self.draw_all(self.canvas_right, self.model_graham.get_points(), final_g_hull, clear=True)
            except Exception as e:
                self.graham_finished = True; print(f"Graham Error: {e}")
                if not self.final_graham_state: self.final_graham_state = {'status': 'error', 'hull_so_far': [], 'time_ms': 0, 'complexity': 'Error'}

        # Update analysis text
        jarvis_desc = "Finished." if self.jarvis_finished else (current_jarvis_state.get('description', 'Running...') if current_jarvis_state else "Waiting...")
        graham_desc = "Finished." if self.graham_finished else (current_graham_state.get('description', 'Running...') if current_graham_state else "Waiting...")
        self.analysis_text_left.set(jarvis_desc)
        self.analysis_text_right.set(graham_desc)

        # Check completion - but continue animation if either algorithm is still running
        if self.jarvis_finished and self.graham_finished:
            self.is_running = False
            self.status_text.set("Dual Comparison Finished!")
            self._set_button_states(start_state=tk.DISABLED, reset_state=tk.NORMAL,
                                    pause_text="Pause", pause_state=tk.DISABLED, next_state=tk.DISABLED)

            # Final results display
            if self.final_jarvis_state and self.final_graham_state:
                j_comp = self.final_jarvis_state.get('complexity', 'N/A')
                g_comp = self.final_graham_state.get('complexity', 'N/A')
                j_time_val = self.final_jarvis_state.get('time_ms', 0)
                g_time_val = self.final_graham_state.get('time_ms', 0)
                j_time = f"Jarvis: {j_time_val:.2f} ms ({j_comp})"
                g_time = f"Graham: {g_time_val:.2f} ms ({g_comp})"

                self.time_text.set(j_time)
                self.complexity_text.set(g_time)
                self.show_results()
                self.hide_animation_controls()

            return # Stop animation loop

        # Schedule next step if either algorithm is still running AND we're not paused
        if self.is_running and not self.is_paused and (not self.jarvis_finished or not self.graham_finished):
            delay = int(self.speed_scale.get())
            self.animation_job = self.root.after(delay, self._animate_step)


    # ... (rest of _process_single_state, event handlers, UI management, button drawing remain the same) ...
    # ... Make sure all methods below _animate_step are included ...
    def _process_single_state(self, canvas, state, algorithm_type):
        if not isinstance(state, dict): return
        model_to_use = self.model_jarvis if algorithm_type == "Jarvis" else self.model_graham
        points = model_to_use.get_points()
        if not state: return

        state_type = state.get('type')
        status = state.get('status')
        hull_so_far = state.get('hull_so_far', [])
        if not isinstance(hull_so_far, list): hull_so_far = []

        if state_type == 'jarvis':
            if status == 'finished':
                # For final state, ensure we draw the complete hull (not outline_only)
                self.draw_all(canvas, points, hull_so_far, clear=True)
            else:
                p_idx, q_idx, check_idx = state.get('p_idx'), state.get('q_idx'), state.get('check_idx')
                num_points = len(points)
                if not all(idx is not None and 0 <= idx < num_points for idx in [p_idx, q_idx, check_idx]): return
                p, q, i = points[p_idx], points[q_idx], points[check_idx]
                self.draw_jarvis_step(canvas, points, p, q, i, hull_so_far)
        elif state_type == 'graham':
            if status == 'finished':
                # For final state, ensure we draw the complete hull (not outline_only)
                self.draw_all(canvas, points, hull_so_far, clear=True)
            else:
                pivot, sorted_pts, stack = state.get('pivot'), state.get('sorted_points', []), state.get('stack', [])
                check_pt, current_status = state.get('check_point'), state.get('status')
                if not pivot or not isinstance(sorted_pts, list) or not isinstance(stack, list) or not current_status: return
                self.draw_graham_step(canvas, points, pivot, sorted_pts, stack, check_pt, current_status)

    def _bind_canvas_events(self):
        for canvas, canvas_id in [(self.canvas_left, 'left'), (self.canvas_right, 'right')]:
            canvas.bind("<Button-1>", lambda e, cid=canvas_id: self._handle_canvas_press(cid, e))
            canvas.bind("<B1-Motion>", lambda e, cid=canvas_id: self._handle_canvas_pan(cid, e))
            canvas.bind("<ButtonRelease-1>", lambda e, cid=canvas_id: self._handle_canvas_release(cid, e))
            canvas.bind("<MouseWheel>", lambda e, cid=canvas_id: self._handle_canvas_zoom(cid, e))
            canvas.bind("<Button-4>", lambda e, cid=canvas_id: self._handle_canvas_zoom(cid, e, direction=-1))
            canvas.bind("<Button-5>", lambda e, cid=canvas_id: self._handle_canvas_zoom(cid, e, direction=1))

    def _handle_canvas_press(self, canvas_id, event):
        self.last_pan_x, self.last_pan_y = event.x, event.y
        self.is_panning = False
        if self._click_job: self.root.after_cancel(self._click_job)
        self._click_job = self.root.after(200, lambda: self._perform_add_point_click(canvas_id, event))

    def _handle_canvas_pan(self, canvas_id, event):
        if self._click_job: self.root.after_cancel(self._click_job); self._click_job = None
        if not self.is_panning:
             dist_sq = (event.x - self.last_pan_x)**2 + (event.y - self.last_pan_y)**2
             if dist_sq > 4: self.is_panning = True
             else: return
        if self.is_panning:
            dx = event.x - self.last_pan_x; dy = event.y - self.last_pan_y
            self.origin_x_left += dx; self.origin_y_left += dy
            self.origin_x_right += dx; self.origin_y_right += dy
            self._redraw_all_canvases()
            self.last_pan_x, self.last_pan_y = event.x, event.y

    def _handle_canvas_release(self, canvas_id, event):
        if self._click_job and not self.is_panning:
            self.root.after_cancel(self._click_job)
            self._perform_add_point_click(canvas_id, event)
        self.is_panning = False; self._click_job = None

    def _perform_add_point_click(self, canvas_id, event):
         if self.is_running: return
         try:
             grid_x_f, grid_y_f = self.canvas_to_grid(canvas_id, event.x, event.y)
             if not (math.isfinite(grid_x_f) and math.isfinite(grid_y_f)): return
             grid_x, grid_y = round(grid_x_f), round(grid_y_f)
         except Exception as e: print(f"Coord convert error: {e}"); return
         point_added = False
         try: point_added = self.shared_model.add_point(grid_x, grid_y)
         except Exception as e: print(f"Add point error: {e}"); return
         if point_added:
             try:
                  points_list = list(self.shared_model.points) # Create list once
                  self.model_jarvis.points = list(points_list) # Use list() for shallow copy
                  self.model_graham.points = list(points_list)
                  # Update n after setting points
                  self.model_jarvis.n = len(self.model_jarvis.points)
                  self.model_graham.n = len(self.model_graham.points)
             except Exception as e:
                  print(f"Sync error: {e}"); self.shared_model.points.pop(); return
             self.status_text.set(f"Added point ({grid_x}, {grid_y}). Total: {self.shared_model.get_point_count()}")
             self._redraw_all_canvases()
         else: self.status_text.set("Point already exists there.")
         num_points = self.shared_model.get_point_count()
         if not self.is_running:
              start_state = tk.NORMAL if num_points >= 3 else tk.DISABLED
              reset_state = tk.NORMAL if num_points > 0 else tk.DISABLED
              self._set_button_states(start_state=start_state, reset_state=reset_state,
                                      pause_text="Pause", pause_state=tk.DISABLED, next_state=tk.DISABLED)

    def _handle_canvas_zoom(self, canvas_id, event, direction=0):
        if self.is_running: return
        zoom_in = False
        if direction != 0: zoom_in = direction < 0
        elif hasattr(event, 'delta') and event.delta != 0: zoom_in = event.delta > 0
        elif hasattr(event, 'num'): zoom_in = event.num == 4
        else: return
        zoom_factor = 1.1 if zoom_in else (1 / 1.1)
        old_gs = self.grid_size
        new_grid_size = max(self.min_grid_size, min(self.max_grid_size, old_gs * zoom_factor))
        if abs(new_grid_size - old_gs) < 1e-6: return
        try:
             wx, wy = self.canvas_to_grid(canvas_id, event.x, event.y)
             if not (math.isfinite(wx) and math.isfinite(wy)): return
        except Exception as e: print(f"Zoom coord error: {e}"); return
        self.grid_size = new_grid_size
        new_ox = event.x - wx * self.grid_size; new_oy = event.y + wy * self.grid_size
        self.origin_x_left = new_ox; self.origin_y_left = new_oy
        self.origin_x_right = new_ox; self.origin_y_right = new_oy
        self._redraw_all_canvases()

    def resize_canvases(self, event=None):
        try:
             self.root.update_idletasks()
             container_width = self.canvas_container.winfo_width()
             container_height = self.canvas_container.winfo_height()
             if container_width <= 1 or container_height <= 1: return # Widget not ready
        except tk.TclError: return # Widget destroyed

        single_canvas_width = max(1, (container_width - 16) // 2)
        self.canvas_width = single_canvas_width
        self.canvas_height = max(1, container_height)

        if not self.is_panning and not self.is_running:
            self.origin_x_left = self.canvas_width / 2; self.origin_y_left = self.canvas_height / 2
            self.origin_x_right = self.canvas_width / 2; self.origin_y_right = self.canvas_height / 2

        self._redraw_all_canvases() # Redraw after size/origin update

    def _redraw_all_canvases(self):
        points = self.shared_model.get_points()
        # Use get_hull() which returns the current state of the model's hull
        hull_j = self.model_jarvis.get_hull()
        hull_g = self.model_graham.get_hull()
        try:
             self.draw_all(self.canvas_left, points, hull_j, clear=True)
             self.draw_all(self.canvas_right, points, hull_g, clear=True)
        except Exception as e: print(f"Error during redraw: {e}"); traceback.print_exc()


    def _reset_comparison(self):
        if self.animation_job:
            try: self.root.after_cancel(self.animation_job)
            except ValueError: pass
            self.animation_job = None
        self.is_running = False; self.is_paused = False
        self.shared_model.reset(); self.model_jarvis.reset(); self.model_graham.reset()
        self.jarvis_gen = None; self.graham_gen = None
        self.final_jarvis_state = None; self.final_graham_state = None
        self.status_text.set("Comparison reset. Add points to start.")
        self.analysis_text_left.set("Waiting..."); self.analysis_text_right.set("Waiting...")
        self._set_button_states(start_state=tk.DISABLED, reset_state=tk.DISABLED,
                                pause_text="Pause", pause_state=tk.DISABLED, next_state=tk.DISABLED)
        self.hide_animation_controls(); self.hide_results()
        self.is_panning = False
        self.resize_canvases() # Resets origins and redraws empty state
    
    def _go_back_to_main(self):
        self._reset_comparison()
        if hasattr(self, 'main_frame') and self.main_frame.winfo_exists():
            self.main_frame.pack_forget()
        self.main_controller.show_start_screen()


    def _set_button_states(self, start_state, reset_state, pause_text, pause_state, next_state):
        valid={tk.NORMAL, tk.DISABLED}; d=tk.DISABLED
        ss=start_state if start_state in valid else d; rs=reset_state if reset_state in valid else d
        ps=pause_state if pause_state in valid else d; ns=next_state if next_state in valid else d
        try:
             if hasattr(self, 'start_button'): self.start_button.configure(state=ss)
             if hasattr(self, 'reset_button'): self.reset_button.configure(state=rs)
             if hasattr(self, 'pause_resume_button'):
                  self.pause_resume_button.configure(state=ps)
                  if isinstance(pause_text, str): self._update_button_text(self.pause_resume_button, pause_text)
             if hasattr(self, 'next_step_button'): self.next_step_button.configure(state=ns)
        except (tk.TclError, AttributeError) as e: print(f"Btn state error: {e}")

    def show_animation_controls(self):
        if hasattr(self, 'anim_controls_frame'): self.anim_controls_frame.pack(fill=tk.X, pady=(0, 0))
        if hasattr(self, 'analysis_frame'): self.analysis_frame.pack(fill=tk.X, pady=(0, 0))
    def hide_animation_controls(self):
        if hasattr(self, 'anim_controls_frame') and self.anim_controls_frame.winfo_ismapped(): self.anim_controls_frame.pack_forget()
        if hasattr(self, 'analysis_frame') and self.analysis_frame.winfo_ismapped(): self.analysis_frame.pack_forget()
    def show_results(self):
         if hasattr(self, 'results_frame'): self.results_frame.pack(fill=tk.X, pady=(10,0))
    def hide_results(self):
         if hasattr(self, 'results_frame') and self.results_frame.winfo_ismapped(): self.results_frame.pack_forget()

    def _update_button_text(self, button, text):
        if not isinstance(button, tk.Widget) or not isinstance(text, str): return
        if button==self.pause_resume_button or button==self.next_step_button: bg,abg = self.C_DARK_GRAY, self.C_MED_GRAY
        elif button==self.start_button: bg,abg = self.C_BLUE, self.C_BLUE_ACTIVE
        elif button==self.reset_button: bg,abg = self.C_DARK_GRAY, self.C_MED_GRAY
        elif button==self.back_button: bg,abg = self.C_MED_GRAY, self.C_DARK_GRAY
        else: bg,abg = self.C_MED_GRAY, self.C_DARK_GRAY
        try:
             img_normal = self._draw_button_image(bg, text); img_active = self._draw_button_image(abg, text)
             button.config(image=img_normal); button.image_normal = img_normal; button.image_active = img_active
        except Exception as e: print(f"Img update error: {e}")
    def _draw_button_image(self, color, text):
        if not isinstance(color, str) or not color.startswith('#'): color = self.C_MED_GRAY
        if not isinstance(text, str): text = " "
        w, h, r = 270, 40, 8
        try:
             img = Image.new("RGBA", (w, h), (0,0,0,0)); draw = ImageDraw.Draw(img)
             draw.rounded_rectangle((0,0,w,h), r, fill=color)
             font = self.pil_font_bold
             if hasattr(font, "getbbox"):
                 bbox = font.getbbox(text); tw=bbox[2]-bbox[0]; th=bbox[3]-bbox[1]; ty_off=bbox[1]
                 tx=(w-tw)/2; ty=(h-th)/2-ty_off
             else: tw,th = draw.textsize(text, font=font); tx=(w-tw)/2; ty=(h-th)/2-2
             draw.text((tx, ty), text, fill=self.C_WHITE_TEXT, font=font)
             return ImageTk.PhotoImage(img)
        except Exception as e: print(f"Draw img error: {e}"); return ImageTk.PhotoImage(Image.new("RGB", (w, h), color))
    def _create_rounded_button(self, parent, text, command, bg, fg, bg_active, parent_bg):
        if not isinstance(parent, tk.Widget): raise ValueError("Invalid parent")
        try: img_normal = self._draw_button_image(bg, text); img_active = self._draw_button_image(bg_active, text)
        except Exception as e: print(f"Img create error '{text}': {e}"); fb = tk.Button(parent, text=text, command=command, bg=bg, fg=fg, activebackground=bg_active); fb.command = command; return fb
        button = tk.Label(parent, image=img_normal, cursor="hand2", bg=parent_bg)
        button.image_normal = img_normal; button.image_active = img_active
        button.configure(state=tk.NORMAL); button.command = command
        def on_click(event):
            if button.cget('state') == tk.NORMAL:
                button.configure(image=img_active)
                if button.command:
                    try:
                        button.command()
                    except Exception as cmd_e:
                        print(f"Cmd err '{text}': {cmd_e}")
        def on_release(event):
            if button.cget('state') == tk.NORMAL: button.configure(image=img_normal)
        button.bind("<Button-1>", on_click); button.bind("<ButtonRelease-1>", on_release)
        return button
