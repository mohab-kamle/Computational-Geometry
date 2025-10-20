# controller.py
# (Owned by integration/lead developer)
import tkinter as tk
from model import JarvisMarchModel
from view import ConvexHullView

class ConvexHullController:
    def __init__(self, root):
        self.root = root
        self.model = JarvisMarchModel()
        self.view = ConvexHullView(root)
        
        # --- Animation State ---
        self.is_running = False
        self.is_paused = False
        self.next_step_requested = False
        self.animation_job = None
        self.algorithm_generator = None
        
        # --- Canvas Pan/Click State ---
        self.is_panning = False
        self.last_pan_x = 0
        self.last_pan_y = 0
        self._click_job = None
        
        # --- Bind View Events to Controller Methods ---
        self.view.bind_proceed_to_main(self.show_main_app)
        self.view.bind_start_animation(self.start_animation)
        self.view.bind_reset(self.reset)
        self.view.bind_pause_resume(self.toggle_pause_resume)
        self.view.bind_next_step(self.next_step)
        
        self.view.bind_canvas_events(
            self.on_canvas_press,
            self.on_pan,
            self.on_pan_release,
            self.on_zoom
        )
        self.view.bind_resize(self.on_resize)
        
        self._update_ui_states()

    # --- Event Handlers (Called by View) ---

    def show_main_app(self):
        self.view.show_main_app()
        self.view.draw_all(self.model.get_points(), self.model.get_hull())
        
    def on_resize(self, event):
        self.view.canvas_width = event.width
        self.view.canvas_height = event.height
        if not self.is_panning:
            self.view.origin_x = event.width / 2
            self.view.origin_y = event.height / 2
        self.view.draw_all(self.model.get_points(), self.model.get_hull())

    def on_canvas_press(self, event):
        if self.is_running: return
        self.last_pan_x, self.last_pan_y = event.x, event.y
        # Start a timer to see if this is a click or a pan
        self._click_job = self.root.after(200, self._perform_add_point, event)

    def on_pan(self, event):
        # If we start panning, cancel the 'add point' job
        if self._click_job:
            self.root.after_cancel(self._click_job)
            self._click_job = None
            
        self.is_panning = True
        dx = event.x - self.last_pan_x
        dy = event.y - self.last_pan_y
        self.view.origin_x += dx
        self.view.origin_y += dy
        self.last_pan_x, self.last_pan_y = event.x, event.y
        self.view.draw_all(self.model.get_points(), self.model.get_hull())

    def on_pan_release(self, event):
        # If we release *without* cancelling the click job, it was a click
        if self._click_job:
            self.root.after_cancel(self._click_job)
            self._perform_add_point(event)
        self.is_panning = False

    def _perform_add_point(self, event):
        """Internal: Add a point from a click event."""
        grid_x_f, grid_y_f = self.view.canvas_to_grid(event.x, event.y)
        grid_x, grid_y = round(grid_x_f), round(grid_y_f)
        
        if self.model.add_point(grid_x, grid_y):
            self.view.draw_all(self.model.get_points(), self.model.get_hull())
            self._update_ui_states()
            
    def on_zoom(self, event):
        zoom_factor = 1.1 if event.num == 4 or event.delta > 0 else 0.9
        new_grid_size = self.view.grid_size * zoom_factor
        
        if self.view.min_grid_size <= new_grid_size <= self.view.max_grid_size:
            wx, wy = self.view.canvas_to_grid(event.x, event.y)
            self.view.grid_size = new_grid_size
            self.view.origin_x = event.x - wx * self.view.grid_size
            self.view.origin_y = event.y - wy * self.view.grid_size
            self.view.draw_all(self.model.get_points(), self.model.get_hull())

    # --- Control Logic ---
    
    def start_animation(self):
        if self.is_running or self.model.get_point_count() < 3:
            return
            
        self.is_running = True
        self.is_paused = False
        self.view.show_animation_panels()
        self.view.hide_results()
        
        # Create the algorithm generator
        self.algorithm_generator = self.model.run_algorithm()
        self._run_animation_step()

    def _run_animation_step(self):
        """This is the main animation loop, controlled by the Controller."""
        if not self.is_running:
            return
            
        if self.is_paused and not self.next_step_requested:
            return
            
        self.next_step_requested = False
        
        try:
            # Get the next step from the Model's generator
            update_data = next(self.algorithm_generator)
            
            if update_data.get('status') == 'finished':
                self._animation_finished(update_data)
                return

            # --- Tell the View to draw the step ---
            p = self.model.points[update_data['p_idx']]
            q = self.model.points[update_data['q_idx']]
            i = self.model.points[update_data['check_idx']]
            
            self.view.draw_animation_step(
                self.model.get_points(),
                p, q, i,
                update_data['hull_so_far']
            )
            self.view.update_analysis(update_data['description'])
            
            # Schedule the next step
            if not self.is_paused:
                delay = self.view.get_speed()
                self.animation_job = self.root.after(delay, self._run_animation_step)
                
        except StopIteration:
            # Generator finished unexpectedly (e.g., < 3 points)
            self._animation_finished(None)
        except Exception as e:
            print(f"Error during animation: {e}")
            self.reset()
            
    def _animation_finished(self, final_data):
        self.is_running = False
        self.is_paused = False
        self.algorithm_generator = None
        
        if final_data:
            self.view.update_status("Convex hull complete!")
            self.view.update_analysis("Algorithm finished. The final convex hull is shown.")
            self.view.show_results(
                time_text=f"Time: {final_data['time_ms']:.2f} ms",
                complexity_text=final_data['complexity']
            )
            self.view.draw_all(self.model.get_points(), self.model.get_hull())
        else:
            self.view.update_status("Algorithm finished (or not needed).")
            
        self._update_ui_states()

    def reset(self):
        if self.animation_job:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None
            
        self.is_running = False
        self.is_paused = False
        self.algorithm_generator = None
        
        self.model.reset()
        
        self.view.anim_controls_frame.pack_forget()
        self.view.analysis_frame.pack_forget()
        self.view.results_frame.pack_forget()
        
        self.view.draw_all(self.model.get_points(), self.model.get_hull())
        self._update_ui_states()

    def toggle_pause_resume(self):
        if not self.is_running:
            return
            
        self.is_paused = not self.is_paused
        
        if not self.is_paused:
            # Resuming, so kick off the loop again
            self.view.update_status("Resuming...")
            self._run_animation_step()
        else:
            self.view.update_status("Animation paused.")
            
        self._update_ui_states()

    def next_step(self):
        if self.is_running and self.is_paused:
            self.next_step_requested = True
            self._run_animation_step()

    def _update_ui_states(self):
        """Central place to update all button states."""
        num_points = self.model.get_point_count()
        
        if self.is_running:
            start_state = tk.DISABLED
            reset_state = tk.DISABLED
            pause_state = tk.NORMAL
            pause_text = "Resume" if self.is_paused else "Pause"
            next_state = tk.NORMAL if self.is_paused else tk.DISABLED
            
            if not self.is_paused:
                self.view.update_status("Algorithm is running...")

        else: # Not running
            start_state = tk.NORMAL if num_points >= 3 else tk.DISABLED
            reset_state = tk.NORMAL
            pause_state = tk.DISABLED
            pause_text = "Pause"
            next_state = tk.DISABLED
            
            if num_points < 3:
                self.view.update_status(f"Add {3 - num_points} more point(s).")
            else:
                self.view.update_status("Ready to visualize.")
        
        self.view.set_button_states(
            start_state=start_state,
            reset_state=reset_state,
            pause_text=pause_text,
            pause_state=pause_state,
            next_state=next_state
        )