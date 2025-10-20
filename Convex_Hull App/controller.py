# controller.py
# (Owned by integration/lead developer)
import tkinter as tk
# --- RENAMED MODEL ---
from model import ConvexHullModel
from view import ConvexHullView

class ConvexHullController:
    def __init__(self, root):
        self.root = root
        # --- RENAMED MODEL ---
        self.model = ConvexHullModel()
        self.view = ConvexHullView(root)
        
        # --- Animation State ---
        self.is_running = False
        self.is_paused = False
        self.next_step_requested = False
        self.animation_job = None
        self.algorithm_generator = None
        self.current_algorithm_name = None # NEW: To track which algo is running
        
        # ... (Canvas Pan/Click State is unchanged) ...
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
    
    # ... (show_main_app, on_resize, on_canvas_press, on_pan, 
    #      on_pan_release, _perform_add_point, on_zoom are unchanged) ...
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
        self._click_job = self.root.after(200, self._perform_add_point, event)
    def on_pan(self, event):
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
        if self._click_job:
            self.root.after_cancel(self._click_job)
            self._perform_add_point(event)
        self.is_panning = False
    def _perform_add_point(self, event):
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

    # --- Control Logic (UPDATED) ---
    
    def start_animation(self):
        if self.is_running or self.model.get_point_count() < 3:
            return
            
        self.is_running = True
        self.is_paused = False
        self.view.show_animation_panels()
        self.view.hide_results()
        
        # --- NEW: Check which algorithm is selected ---
        self.current_algorithm_name = self.view.get_selected_algorithm()
        
        if self.current_algorithm_name == "Jarvis March":
            self.algorithm_generator = self.model.run_jarvis_march()
        elif self.current_algorithm_name == "Graham Scan":
            self.algorithm_generator = self.model.run_graham_scan()
        else:
            # Fallback
            print(f"Unknown algorithm: {self.current_algorithm_name}")
            self.is_running = False
            return
            
        self._run_animation_step()

    def _run_animation_step(self):
        """This is the main animation loop, controlled by the Controller."""
        if not self.is_running:
            return
            
        if self.is_paused and not self.next_step_requested:
            return
            
        self.next_step_requested = False
        
        try:
            update_data = next(self.algorithm_generator)
            
            if update_data.get('status') == 'finished':
                self._animation_finished(update_data)
                return

            self.view.update_analysis(update_data['description'])
            
            # --- NEW: Route to the correct drawing function ---
            
            if update_data.get('type') == 'jarvis':
                p = self.model.points[update_data['p_idx']]
                q = self.model.points[update_data['q_idx']]
                i = self.model.points[update_data['check_idx']]
                self.view.draw_jarvis_step(
                    self.model.get_points(),
                    p, q, i,
                    update_data['hull_so_far']
                )
                
            elif update_data.get('type') == 'graham':
                check_point = None
                if update_data.get('check_point_id') is not None:
                     # Find the check point by its unique ID
                     check_point = next((p for p in self.model.points if p['id'] == update_data['check_point_id']), None)

                self.view.draw_graham_step(
                    self.model.get_points(),
                    update_data['pivot'],
                    update_data['sorted_points'],
                    update_data['stack'],
                    check_point,
                    update_data['status']
                )

            # Schedule the next step
            if not self.is_paused:
                delay = self.view.get_speed()
                self.animation_job = self.root.after(delay, self._run_animation_step)
                
        except StopIteration:
            self._animation_finished(None)
        except Exception as e:
            print(f"Error during animation: {e}")
            import traceback
            traceback.print_exc()
            self.reset()
            
    def _animation_finished(self, final_data):
        self.is_running = False
        self.is_paused = False
        self.algorithm_generator = None
        self.current_algorithm_name = None # Clear current algo
        
        if final_data:
            self.view.update_status("Convex hull complete!")
            self.view.update_analysis("Algorithm finished. The final convex hull is shown.")
            self.view.show_results(
                time_text=f"Time: {final_data['time_ms']:.2f} ms",
                # The complexity string now comes from the model
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
        self.current_algorithm_name = None # Clear current algo
        
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
            self.view.update_status(f"Resuming {self.current_algorithm_name}...")
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
            combo_state = "disabled" # Can't change algo while running
            
            if not self.is_paused:
                self.view.update_status(f"{self.current_algorithm_name} is running...")

        else: # Not running
            start_state = tk.NORMAL if num_points >= 3 else tk.DISABLED
            reset_state = tk.NORMAL
            pause_state = tk.DISABLED
            pause_text = "Pause"
            next_state = tk.DISABLED
            combo_state = "readonly" # Can change algo
            
            if num_points < 3:
                self.view.update_status(f"Add {3 - num_points} more point(s).")
            else:
                self.view.update_status("Ready to visualize.")
        
        self.view.set_button_states(
            start_state=start_state,
            reset_state=reset_state,
            pause_text=pause_text,
            pause_state=pause_state,
            next_state=next_state,
            combo_state=combo_state
        )