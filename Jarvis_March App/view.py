# view.py
# (Owned by the GUI Team)
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont

class ConvexHullView:
    
    # --- Color Palette & Fonts (Defined here for the GUI team) ---
    C_BLACK = "#000000"
    C_NEAR_BLACK = "#1d1d1f"
    C_DARK_GRAY = "#2c2c2e"
    C_MED_GRAY = "#3c3c3e"
    C_LIGHT_GRAY_TEXT = "#a1a1a6"
    C_WHITE_TEXT = "#f5f5f7"
    C_BLUE = "#0071e3"
    C_BLUE_ACTIVE = "#0077ed"
    C_HULL_LINE = "#0071e3"
    C_HULL_FILL = "red"
    C_POINT_BLUE = "#0071e3"
    C_POINT_P = "#f59e0b" # Yellow
    C_LINE_Q = "#10b981"  # Green
    C_LINE_I = "#ef4444"  # Red
    
    FONT_BOLD = ("Inter", 12, "bold")
    FONT_NORMAL = ("Inter", 10)
    
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis March Convex Hull Visualization")
        self.root.configure(bg=self.C_BLACK)
        self.root.state("zoomed")
        
        # --- Canvas/Grid State ---
        self.grid_size = 20
        self.min_grid_size = 4
        self.max_grid_size = 120
        self.origin_x = 0
        self.origin_y = 0
        self._click_job = None
        
        # --- PIL Font ---
        try:
            self.pil_font_bold = ImageFont.truetype("arialbd.ttf", 14)
        except IOError:
            self.pil_font_bold = ImageFont.load_default()

        # --- Setup UI ---
        self._setup_frames()
        self._setup_start_screen()
        self._setup_main_app_screen()
        
        self.show_start_screen()
        self._center_window()

    # --- Public Methods (Called by Controller) ---
    
    def bind_proceed_to_main(self, command):
        self.proceed_button.config(state=tk.NORMAL)
        self.proceed_button.bind("<Button-1>", lambda e: command())
        self.proceed_button.bind("<ButtonRelease-1>", lambda e: self.proceed_button.config(image=self.proceed_button.image_normal))

    def bind_start_animation(self, command):
        self.start_button_command = command
        
    def bind_reset(self, command):
        self.reset_button_command = command

    def bind_pause_resume(self, command):
        self.pause_resume_command = command

    def bind_next_step(self, command):
        self.next_step_command = command
        
    def bind_canvas_events(self, on_press, on_pan, on_release, on_zoom):
        self.canvas.bind("<Button-1>", on_press)
        self.canvas.bind("<B1-Motion>", on_pan)
        self.canvas.bind("<ButtonRelease-1>", on_release)
        self.canvas.bind("<MouseWheel>", on_zoom)
        self.canvas.bind("<Button-4>", on_zoom) # For Linux
        self.canvas.bind("<Button-5>", on_zoom) # For Linux
    
    def bind_resize(self, command):
        self.canvas.bind("<Configure>", command)
        
    def get_speed(self):
        return int(self.speed_scale.get())

    def update_status(self, text):
        self.status_text.set(text)
        
    def update_analysis(self, text):
        self.analysis_text.set(text)
    
    def show_animation_panels(self):
        self.anim_controls_frame.pack(fill=tk.X, pady=(0, 0))
        self.analysis_frame.pack(fill=tk.X, pady=(0, 0))
        
    def hide_results(self):
        self.results_frame.pack_forget()

    def show_results(self, time_text, complexity_text):
        self.time_text.set(time_text)
        self.complexity_text.set(complexity_text)
        self.results_frame.pack(fill=tk.X, pady=(10,0))
    
    def set_button_states(self, start_state, reset_state, pause_text, pause_state, next_state):
        self.start_button.config(state=start_state)
        self.reset_button.config(state=reset_state)
        self.pause_resume_button.config(state=pause_state)
        self.next_step_button.config(state=next_state)
        
        # Update text for pause/resume button
        self._update_button_text(self.pause_resume_button, pause_text)

    def _update_button_text(self, button, text):
        # Re-draw the button with new text
        img_normal = self._draw_button_image(self.C_DARK_GRAY, text)
        img_active = self._draw_button_image(self.C_MED_GRAY, text)
        button.config(image=img_normal)
        button.image_normal = img_normal
        button.image_active = img_active

    def show_main_app(self):
        self.start_frame.pack_forget()
        self.main_app_frame.pack(fill=tk.BOTH, expand=True, padx=32, pady=24)
        
        self.root.update_idletasks()
        self.canvas_width = self.canvas.winfo_width()
        self.canvas_height = self.canvas.winfo_height()
        self.origin_x = self.canvas_width / 2
        self.origin_y = self.canvas_height / 2
        self.draw_all(points=[], hull=[]) # Draw empty grid

    def show_start_screen(self):
        self.main_app_frame.pack_forget()
        self.start_frame.pack(fill=tk.BOTH, expand=True)

    # --- Coordinate Conversion (Belongs to View) ---
    def grid_to_canvas(self, grid_x, grid_y):
        return self.origin_x + grid_x * self.grid_size, self.origin_y - grid_y * self.grid_size
        
    def canvas_to_grid(self, cx, cy):
        return (cx - self.origin_x) / self.grid_size, (self.origin_y - cy) / self.grid_size

    # --- Drawing Methods (All here) ---
    
    def draw_all(self, points, hull, clear=True):
        """Draws the base scene: grid and all points."""
        if clear: self.canvas.delete("all")
        self._draw_axes_and_grid()
        for p in points:
            cx, cy = self.grid_to_canvas(p['grid_x'], p['grid_y'])
            self.canvas.create_oval(cx-4, cy-4, cx+4, cy+4, fill=self.C_POINT_BLUE, outline="", tags="point")
            self.canvas.create_text(cx + 8, cy - 8, text=f"({p['grid_x']},{p['grid_y']})", anchor="sw", fill=self.C_LIGHT_GRAY_TEXT, font=("Inter", 9))
        if hull:
            self._draw_final_hull_shape(hull)

    def draw_animation_step(self, points, p_point, q_point, i_point, hull_so_far):
        """Draws a single step of the animation."""
        self.draw_all(points, hull=None, clear=True) # Redraw base
        
        p_c = self.grid_to_canvas(p_point['grid_x'], p_point['grid_y'])
        q_c = self.grid_to_canvas(q_point['grid_x'], q_point['grid_y'])
        i_c = self.grid_to_canvas(i_point['grid_x'], i_point['grid_y'])
        
        # Highlight P, Q, and I points
        self.canvas.create_oval(p_c[0]-6, p_c[1]-6, p_c[0]+6, p_c[1]+6, fill=self.C_POINT_P, outline="")
        
        # Draw lines
        self.canvas.create_line(p_c, q_c, fill=self.C_LINE_Q, width=2) # Best so far (green)
        self.canvas.create_line(p_c, i_c, fill=self.C_LINE_I, width=1) # Current test (red)
        
        # Draw hull segments found so far
        self._draw_final_hull_shape(hull_so_far, outline_only=True)

    def _draw_final_hull_shape(self, hull, outline_only=False):
        if not hull: return
        hull_coords = [c for p in hull for c in self.grid_to_canvas(p['grid_x'], p['grid_y'])]
        
        if len(hull_coords) >= 6 and not outline_only:
            self.canvas.create_polygon(hull_coords, fill=self.C_HULL_FILL, outline="", stipple="gray25")
        
        if len(hull_coords) >= 4:
            closed_coords = hull_coords + [hull_coords[0], hull_coords[1]]
            self.canvas.create_line(closed_coords, fill=self.C_HULL_LINE, width=3)
            
        for p in hull:
            cx, cy = self.grid_to_canvas(p['grid_x'], p['grid_y'])
            self.canvas.create_oval(cx-6, cy-6, cx+6, cy+6, fill=self.C_HULL_LINE, outline="")

    def _draw_axes_and_grid(self):
        grid_step = self.grid_size
        if self.grid_size < 10: grid_step *= 2
        label_step = 1
        if self.grid_size < 15: label_step = 2
        if self.grid_size < 7: label_step = 5
        if self.grid_size > 40: label_step = 1
        i = 0
        while True:
            x_pos, x_neg = self.origin_x + i * grid_step, self.origin_x - i * grid_step
            if x_pos > self.canvas_width and x_neg < 0: break
            if x_pos <= self.canvas_width:
                self.canvas.create_line(x_pos, 0, x_pos, self.canvas_height, fill=self.C_DARK_GRAY)
                if i > 0 and i % label_step == 0: self.canvas.create_text(x_pos, self.origin_y + 5, text=str(i), anchor="n", fill=self.C_LIGHT_GRAY_TEXT, font=("Inter", 9))
            if i > 0 and x_neg >= 0:
                self.canvas.create_line(x_neg, 0, x_neg, self.canvas_height, fill=self.C_DARK_GRAY)
                if i % label_step == 0: self.canvas.create_text(x_neg, self.origin_y + 5, text=str(-i), anchor="n", fill=self.C_LIGHT_GRAY_TEXT, font=("Inter", 9))
            i += 1
        i = 0
        while True:
            y_pos, y_neg = self.origin_y + i * grid_step, self.origin_y - i * grid_step
            if y_pos > self.canvas_height and y_neg < 0: break
            if y_pos <= self.canvas_height:
                self.canvas.create_line(0, y_pos, self.canvas_width, y_pos, fill=self.C_DARK_GRAY)
                if i > 0 and i % label_step == 0: self.canvas.create_text(self.origin_x - 5, y_pos, text=str(-i), anchor="e", fill=self.C_LIGHT_GRAY_TEXT, font=("Inter", 9))
            if i > 0 and y_neg >= 0:
                self.canvas.create_line(0, y_neg, self.canvas_width, y_neg, fill=self.C_DARK_GRAY)
                if i % label_step == 0: self.canvas.create_text(self.origin_x - 5, y_neg, text=str(i), anchor="e", fill=self.C_LIGHT_GRAY_TEXT, font=("Inter", 9))
            i += 1
        self.canvas.create_line(0, self.origin_y, self.canvas_width, self.origin_y, fill="#888888", width=1)
        self.canvas.create_line(self.origin_x, 0, self.origin_x, self.canvas_height, fill="#888888", width=1)
        self.canvas.create_text(self.origin_x - 5, self.origin_y + 5, text="0", anchor="se", fill=self.C_LIGHT_GRAY_TEXT, font=("Inter", 9, "bold"))


    # --- Internal UI Setup Methods ---
    
    def _center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _setup_frames(self):
        self.start_frame = tk.Frame(self.root, bg=self.C_BLACK)
        self.main_app_frame = tk.Frame(self.root, bg=self.C_BLACK)

    def _setup_start_screen(self):
        try:
            image_path = "startImage.png"
            image = Image.open(image_path)
            image = image.resize((2400, 1600), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(image)
            bg_label = tk.Label(self.start_frame, image=self.bg_photo)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"Error loading background image: {e}. Using a solid color fallback.")
            self.start_frame.config(bg=self.C_BLACK)

        panel_width, panel_height = 750, 450
        panel_image = Image.new("RGBA", (panel_width, panel_height))
        self.panel_photo = ImageTk.PhotoImage(panel_image)
        content_container = tk.Frame(self.start_frame, bg=self.C_BLACK)
        content_container.config(border=100)
        content_container.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(content_container, text="Jarvis March Algorithm", font=("Inter", 48, "bold"), fg=self.C_WHITE_TEXT, bg=self.C_BLACK).pack(pady=(20, 10), padx=50)
        tk.Label(content_container, text="An algorithm for computing the convex hull of a finite set of points.", font=("Inter", 16), fg=self.C_LIGHT_GRAY_TEXT, bg=self.C_BLACK).pack(padx=50)
        description_text = (
            "Also known as the 'gift wrapping' algorithm, Jarvis March simulates wrapping a string around a set of points. "
            "It starts with a point guaranteed to be on the hull (like the bottom-most one) and iteratively finds the next point "
            "that has the smallest polar angle with respect to the current point, effectively 'wrapping' around the set."
        )
        tk.Label(content_container, text=description_text, font=("Inter", 12), fg=self.C_LIGHT_GRAY_TEXT, bg=self.C_BLACK, wraplength=600, justify="center").pack(pady=40, padx=50)
        
        # Note: The command is NOT set here. The controller will bind it.
        self.proceed_button = self._create_rounded_button(content_container, "Proceed to Visualization", None, bg=self.C_BLUE, fg=self.C_WHITE_TEXT, bg_active=self.C_BLUE_ACTIVE, parent_bg=self.C_BLACK)
        self.proceed_button.pack(pady=20)
        self.proceed_button.config(state=tk.DISABLED) # Start disabled until controller binds it

    def _setup_main_app_screen(self):
        content_frame = tk.Frame(self.main_app_frame, bg=self.C_BLACK)
        content_frame.pack(fill=tk.BOTH, expand=True)
        canvas_border_frame = tk.Frame(content_frame, bg=self.C_MED_GRAY, padx=1, pady=1)
        canvas_border_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 24))
        self.canvas = tk.Canvas(canvas_border_frame, bg=self.C_BLACK, highlightthickness=0, borderwidth=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        controls_panel = tk.Frame(content_frame, width=520, bg=self.C_NEAR_BLACK, padx=12, pady=12)
        controls_panel.pack(side=tk.RIGHT, fill=tk.Y)
        controls_panel.pack_propagate(False)
        tk.Label(controls_panel, text="Controls", font=("Inter", 18, "bold"), fg=self.C_WHITE_TEXT, bg=self.C_NEAR_BLACK).pack(anchor="center", pady=(0, 12))
        buttons_row = tk.Frame(controls_panel, bg=self.C_NEAR_BLACK)
        buttons_row.pack(fill=tk.X, pady=(0, 12))
        
        # Commands are proxied to internal handlers
        self.start_button = self._create_rounded_button(buttons_row, "Start", lambda: self.start_button_command(), bg=self.C_BLUE, fg=self.C_WHITE_TEXT, bg_active=self.C_BLUE_ACTIVE, parent_bg=self.C_NEAR_BLACK)
        self.start_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))
        self.reset_button = self._create_rounded_button(buttons_row, "Reset", lambda: self.reset_button_command(), bg=self.C_DARK_GRAY, fg=self.C_WHITE_TEXT, bg_active=self.C_MED_GRAY, parent_bg=self.C_NEAR_BLACK)
        self.reset_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(6, 0))
        
        tk.Frame(controls_panel, height=1, bg=self.C_MED_GRAY).pack(fill=tk.X, pady=10)
        self.anim_controls_frame = tk.Frame(controls_panel, bg=self.C_NEAR_BLACK)
        tk.Label(self.anim_controls_frame, text="Animation", font=("Inter", 16, "bold"), fg=self.C_WHITE_TEXT, bg=self.C_NEAR_BLACK).pack(anchor="w", pady=(0, 20))
        buttons_frame = tk.Frame(self.anim_controls_frame, bg=self.C_NEAR_BLACK)
        buttons_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.pause_resume_button = self._create_rounded_button(buttons_frame, "Pause", lambda: self.pause_resume_command(), bg=self.C_DARK_GRAY, fg=self.C_WHITE_TEXT, bg_active=self.C_MED_GRAY, parent_bg=self.C_NEAR_BLACK)
        self.pause_resume_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.next_step_button = self._create_rounded_button(buttons_frame, "Next Step", lambda: self.next_step_command(), bg=self.C_DARK_GRAY, fg=self.C_WHITE_TEXT, bg_active=self.C_MED_GRAY, parent_bg=self.C_NEAR_BLACK)
        self.next_step_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
        
        speed_frame = tk.Frame(self.anim_controls_frame, bg=self.C_NEAR_BLACK)
        speed_frame.pack(fill=tk.X, pady=(15, 0))
        tk.Label(speed_frame, text="Speed:", font=self.FONT_NORMAL, fg=self.C_LIGHT_GRAY_TEXT, bg=self.C_NEAR_BLACK).pack(side=tk.LEFT)
        style = ttk.Style()
        style.configure("Transparent.Horizontal.TScale", troughcolor=self.C_DARK_GRAY, background=self.C_NEAR_BLACK)
        self.speed_scale = ttk.Scale(speed_frame, from_=800, to=50, orient="horizontal", style="Transparent.Horizontal.TScale")
        self.speed_scale.set(350)
        self.speed_scale.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(10, 0),pady=(0, 5))
        
        self.status_text = tk.StringVar(value="Add at least 3 points to start.")
        status_frame = tk.Frame(controls_panel, bg=self.C_NEAR_BLACK)
        status_frame.pack(fill=tk.X, pady=(5, 5))
        status_row = tk.Frame(status_frame, bg=self.C_DARK_GRAY, padx=10, pady=6)
        status_row.pack(fill=tk.X)
        tk.Label(status_row, text="Status:", font=("Inter", 14, "bold"), fg=self.C_WHITE_TEXT, bg=self.C_DARK_GRAY).pack(side="left", padx=(0, 8))
        tk.Label(status_row, textvariable=self.status_text, font=("Inter", 12), fg=self.C_WHITE_TEXT, bg=self.C_DARK_GRAY, justify="left", wraplength=240, anchor="w").pack(side="left", fill="x", expand=True)

        self.analysis_frame = tk.Frame(controls_panel, bg=self.C_NEAR_BLACK)
        tk.Label(self.analysis_frame, text="Live Analysis", font=("Inter", 15, "bold"), fg=self.C_WHITE_TEXT, bg=self.C_NEAR_BLACK).pack(anchor="w", pady=(0, 4))
        analysis_bg = tk.Frame(self.analysis_frame, bg=self.C_DARK_GRAY, padx=12, pady=10, highlightbackground=self.C_MED_GRAY, highlightthickness=1)
        analysis_bg.pack(fill=tk.X, padx=2)
        accent = tk.Frame(analysis_bg, bg=self.C_BLUE, height=2)
        accent.pack(fill=tk.X, pady=(0, 6))
        self.analysis_text = tk.StringVar(value="Start animation to see calculations.")
        analysis_label = tk.Label(analysis_bg, textvariable=self.analysis_text, font=("Inter", 11), fg=self.C_WHITE_TEXT, bg=self.C_DARK_GRAY, justify="left", wraplength=260, anchor="w")
        analysis_label.pack(anchor="w", fill=tk.X)
        
        self.results_frame = tk.Frame(controls_panel, bg=self.C_NEAR_BLACK)
        tk.Label(self.results_frame, text="Results", font=("Inter", 16, "bold"), fg=self.C_WHITE_TEXT, bg=self.C_NEAR_BLACK).pack(anchor="w", pady=(0, 6))
        results_bg = tk.Frame(self.results_frame, bg=self.C_DARK_GRAY, padx=10, pady=6)
        results_bg.pack(fill=tk.X)
        self.time_text = tk.StringVar(value="Execution Time: —")
        self.complexity_text = tk.StringVar(value="Complexity: —")
        tk.Label(results_bg, textvariable=self.time_text, font=("Inter", 11, "bold"), fg=self.C_WHITE_TEXT, bg=self.C_DARK_GRAY).pack(anchor="w")
        tk.Label(results_bg, textvariable=self.complexity_text, font=("Inter", 11), fg=self.C_WHITE_TEXT, bg=self.C_DARK_GRAY).pack(anchor="w", pady=(2, 0))
        
        # --- Set initial visibility ---
        self.anim_controls_frame.pack_forget()
        self.analysis_frame.pack_forget()
        self.results_frame.pack_forget()

    # --- UI Helpers (Owned by View) ---
    
    def _draw_button_image(self, color, text):
        """Helper to draw a button image."""
        image = Image.new("RGBA", (270, 40), (0, 0, 0, 0)) # Transparent background
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((0, 0, 270, 40), 8, fill=color)
        
        if hasattr(self.pil_font_bold, "getbbox"):
            text_bbox = self.pil_font_bold.getbbox(text)
            text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        else:
            text_width, text_height = draw.textsize(text, font=self.pil_font_bold)

        draw.text(((270 - text_width) / 2, (40 - text_height) / 2 - 2), text, fill=self.C_WHITE_TEXT, font=self.pil_font_bold)
        return ImageTk.PhotoImage(image)

    def _create_rounded_button(self, parent, text, command, bg, fg, bg_active, parent_bg):
        # (Your exact create_rounded_button logic, but adapted)
        img_normal = self._draw_button_image(bg, text)
        img_active = self._draw_button_image(bg_active, text)

        button = tk.Label(parent, image=img_normal, cursor="hand2", bg=parent_bg)
        button.image_normal = img_normal
        button.image_active = img_active
        button['state'] = tk.NORMAL  # Default state
        
        def on_click(event):
            if button['state'] == tk.NORMAL:
                button.config(image=img_active)
                if command:
                    command()

        def on_release(event):
            if button['state'] == tk.NORMAL:
                button.config(image=img_normal)
        
        button.bind("<Button-1>", on_click)
        button.bind("<ButtonRelease-1>", on_release)
        return button