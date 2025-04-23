import math

class GlobeSimCam:
    def __init__(self):
        self.is_dragging = False
        self.last_mouse_pos = None
        self.rotation_x = 0
        self.rotation_y = 0
        self.zoom = 5
    
    def start_drag(self):
        self.is_dragging = True
        self.last_mouse_pos = None  # Reset tracking
        
    def stop_drag(self):
        self.is_dragging = False

    def get_pos(self, mouse_x, mouse_y):
        if self.is_dragging and mouse_x:
            if self.last_mouse_pos:
                dx = (mouse_x - self.last_mouse_pos[0]) * 10 * (self.zoom + 1)
                dy = (mouse_y - self.last_mouse_pos[1]) * 10 * (self.zoom + 1)
                
                #if dy or dx:
                #    self.dragged = True
    
                # Update the camera's rotation based on mouse movement
                self.rotation_x -= dy
                self.rotation_y += dx
    
                # Apply constraints to prevent flipping
                self.rotation_x = max(-90, min(90, self.rotation_x))  # Limit vertical rotation

            self.last_mouse_pos = (mouse_x, mouse_y)
    
        # Update the camera position based on the calculated rotations
        rad_x = math.radians(self.rotation_x)
        rad_y = math.radians(self.rotation_y)

        # Camera's distance from the globe (zoom level)
        distance = self.zoom + 1
        # Convert spherical coordinates to Cartesian coordinates for the camera
        x = distance * math.cos(rad_x) * math.sin(rad_y)
        y = distance * math.cos(rad_x) * math.cos(rad_y)
        z = distance * math.sin(rad_x)
        
        return (x, y, z)
        
    def get_zoom_step(self):
        # Example: step shrinks as zoom increases
        return max(0.05, 0.5 * self.zoom)
    
    def zoom_in(self):
        self.zoom = max(0.001, self.zoom - self.get_zoom_step())
    
    def zoom_out(self):
        self.zoom = min(10, self.zoom + self.get_zoom_step())