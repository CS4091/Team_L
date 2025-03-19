from direct.showbase.ShowBase import ShowBase
from panda3d.core import TransparencyAttrib
from panda3d.core import NodePath, AmbientLight, DirectionalLight
from panda3d.core import MouseWatcher
from panda3d.core import Shader
from panda3d.core import GeomNode
from panda3d.core import WindowProperties
from panda3d.core import LineSegs

from panda3d.core import ConfigVariableBool
ConfigVariableBool("tk-main-loop").setValue(False)
import math
import sys
from procedural3d.sphere import SphereMaker

import tkinter as tk
from tkinter import ttk

from TSP_Ex import sim_ann_TSP

class Marker:
    altitude = 0.025
    color = (1, 1, 0, 0.5)
    loaded_model = None 
    
    def __init__(self, latitude, longitude):
        if self.loaded_model is None:
            self.loaded_model = loader.loadModel("models/misc/sphere")
        np = self.loaded_model.copyTo(NodePath())
        
        np.setBin("fixed", 0)
        np.setDepthTest(False)
        np.setDepthWrite(False)
        np.setBin("transparent", 0)
        np.setTransparency(TransparencyAttrib.MAlpha)
        np.setColorScale(self.color)
        np.setLightOff(1)
        np.setScale(0.01)  # todo change on zoom?
        self.np = np
        
        self.set_coords(latitude, longitude)
        
    def get_coords(self):
        return self.__coords
        
    def set_coords(self, latitude, longitude):
        self.__coords = (latitude, longitude)
        
        lat_rad = math.radians(latitude) 
        lon_rad = math.radians(longitude) + math.radians(180)
        
        x = (1 + self.altitude) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (1 + self.altitude) * math.cos(lat_rad) * math.sin(lon_rad)
        z = (1 + self.altitude) * math.sin(lat_rad)
        
        self.np.setPos(x, y, z)
        
class GlobeApp(ShowBase):
    def __init__(self, useTk = False):
        if useTk:
            ShowBase.__init__(self, windowType='none')
            self.setup_tk()
        else:
            super().__init__()
            
        self.markers = []
        Marker.parent = self.render
        Marker.group = self.markers
        
        self.disableMouse()

        # Earth, starmap
        segs = {
            "horizontal": 30,
            "vertical": 15
        }
        sphere_geom = SphereMaker(segments=segs).generate()
        self.rotate = self.render.attachNewNode('rotate')
        
        self.earth = self.rotate.attachNewNode(sphere_geom)
        #self.earth.setHpr(, math.radians(180), 0)
        
        self.starmap = self.earth.copy_to(self.rotate)

        texture = self.loader.loadTexture("res/earth.jpg")
        self.earth.setTexture(texture, 1)
        
        texture = self.loader.loadTexture("res/starmap.jpg")
        self.starmap.setTexture(texture, 1)
        self.starmap.setTwoSided(True)
        self.starmap.setScale(1000)
        
        self.earth.setScale(1)

        self.setup_lights()

        # Controls
        self.is_dragging = False
        self.last_mouse_pos = None
        self.rotation_x = 0
        self.rotation_y = 0
        self.zoom = 5

        self.accept("mouse1", self.start_drag)
        self.accept("mouse1-up", self.stop_drag)
        self.taskMgr.add(self.update_camera_rotation, "UpdateRotationTask")
        self.accept("wheel_up", self.zoom_in)
        self.accept("wheel_down", self.zoom_out)
        
        self.markers = []
        
        # Draw paths between the markers
        #self.add_path(self.markers)
        self.do_path_demo()

        
    def do_path_demo(self):
        cities = [
            (40.7128, -74.0060),  # New York City, USA
            (51.5074, -0.1278),   # London, UK
            (48.8566, 2.3522),    # Paris, France
            (35.6762, 139.6503),  # Tokyo, Japan
            (-33.8688, 151.2093), # Sydney, Australia
            (55.7558, 37.6173),   # Moscow, Russia
            (39.9042, 116.4074),  # Beijing, China
            (-22.9068, -43.1729), # Rio de Janeiro, Brazil
            (-33.9249, 18.4241),  # Cape Town, South Africa
            (34.0522, -118.2437), # Los Angeles, USA
            (52.5200, 13.4050),   # Berlin, Germany
            (19.0760, 72.8777),   # Mumbai, India
            (30.0444, 31.2357),   # Cairo, Egypt
            (43.6510, -79.3470),  # Toronto, Canada
            (19.4326, -99.1332),  # Mexico City, Mexico
            (40.7306, -73.9352),  # Brooklyn, USA
            (37.7749, -122.4194), # San Francisco, USA
            (34.0522, -118.2437), # Los Angeles, USA
            (41.9028, 12.4964),   # Rome, Italy
            (55.6761, 12.5683),   # Copenhagen, Denmark
            (59.3293, 18.0686),   # Stockholm, Sweden
            (35.6895, 139.6917),  # Tokyo, Japan
            (37.7749, -122.4194), # San Francisco, USA
            (52.3676, 4.9041),    # Amsterdam, Netherlands
            (28.7041, 77.1025),   # Delhi, India
            (40.7306, -73.9352),  # Brooklyn, USA
            (51.1657, 10.4515)    # Berlin, Germany
        ]
        
        init_temp = 1000
        cool_rate = 0.995
        min_temp = 1e-3
        
        for coord in cities:
            self.add_marker(Marker(coord[0], coord[1]))
            
        path, dist = sim_ann_TSP(cities, init_temp=1000, cool_rate=0.995, min_temp=1e-3)
        print("Path distance:", dist)
        self.add_path(path)
        
    def add_marker(self, marker):
        self.markers.append(marker)
        marker.np.reparentTo(self.render)

    def start_drag(self):
        self.is_dragging = True
        self.last_mouse_pos = None  # Reset tracking

    def stop_drag(self):
        self.is_dragging = False

    def update_camera_rotation(self, task):
        if self.is_dragging and self.mouseWatcherNode.hasMouse():
            mouse_x, mouse_y = self.mouseWatcherNode.getMouseX(), self.mouseWatcherNode.getMouseY()
    
            if self.last_mouse_pos:
                dx = (mouse_x - self.last_mouse_pos[0]) * 10 * self.zoom
                dy = (mouse_y - self.last_mouse_pos[1]) * 10 * self.zoom
    
                # Update the camera's rotation based on mouse movement
                self.rotation_x -= dy
                self.rotation_y += dx
    
                # Apply constraints to prevent flipping
                self.rotation_x = max(-90, min(90, self.rotation_x))  # Limit vertical rotation

            self.last_mouse_pos = (mouse_x, mouse_y)
    
        # Update the camera position based on the calculated rotations
        self.update_camera_position()

        return task.cont

    def update_camera_position(self):
        # Calculate the camera's position using spherical coordinates
        rad_x = math.radians(self.rotation_x)
        rad_y = math.radians(self.rotation_y)

        # Camera's distance from the globe (zoom level)
        distance = self.zoom

        # Convert spherical coordinates to Cartesian coordinates for the camera
        x = distance * math.cos(rad_x) * math.sin(rad_y)
        y = distance * math.cos(rad_x) * math.cos(rad_y)
        z = distance * math.sin(rad_x)

        self.camera.setPos(x, y, z)
        self.camera.lookAt(self.earth)

    def zoom_in(self):
        self.zoom = max(2, self.zoom - 0.3)

    def zoom_out(self):
        self.zoom = min(10, self.zoom + 0.3)
        
    def add_path(self, indices):
        """
        Draws a curved path between the markers by calculating the great-circle route.
        """
        if len(indices) < 2:
            return
        
        path_lines = LineSegs()
        path_lines.setColor(1, 1, 0, 0.75)
        for i in range(len(indices)-1):
            start = self.markers[indices[i]].np.getPos()
            path_lines.moveTo(start)
            end = self.markers[indices[i + 1]].np.getPos()
            
            # Number of intermediate points on the path
            num_points = 50
            for j in range(num_points + 1):
                t = j / num_points  # Parameter between 0 and 1
                point = self.interpolate_great_circle(start, end, t)
                path_lines.drawTo(point)
                #vertex_writer.addData3f(point)
                
        path_lines.drawTo(end)
        lines_np = self.rotate.attachNewNode(path_lines.create())
        #lines_np.setBin("fixed", 0)
        #lines_np.setDepthTest(False)
        #lines_np.setDepthWrite(False)
        
        

    def interpolate_great_circle(self, start, end, t):
        """
        Interpolates between two points on the surface of a sphere.
        t is a parameter between 0 and 1.
        """
        # Normalize the points
        start = start.normalized()
        end = end.normalized()
        
        # Spherical linear interpolation (SLERP)
        cos_theta = start.dot(end)
        if cos_theta > 0.9995:
            result = start + (end - start) * t
            result.normalize()
        else:
            theta = math.acos(cos_theta)
            sin_theta = math.sin(theta)
            a = math.sin((1 - t) * theta) / sin_theta
            b = math.sin(t * theta) / sin_theta
            result = start * a + end * b
        
        # Return the point in Cartesian coordinates
        return result
        
    def add_marker(self, marker):
        marker.np.reparentTo(self.rotate)
        
        self.markers.append(marker)
        
    def setup_tk(self):
        self.startTk()

        self.tk = self.tkRoot
        self.tk.geometry("1920x1080")
        
        # Theme
        self.tk.call('source', '../gui/Azure-ttk-theme-2.1.0/azure.tcl')
        self.tk.call("set_theme", "dark")

        # Main frame for the layout
        self.main_frame = tk.Frame(self.tk)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Sidebar with tabs (left side)
        self.sidebar_frame = tk.Frame(self.main_frame, width=250, bg='#2a2a2a')
        self.sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.tabs = ttk.Notebook(self.sidebar_frame)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        self.tab1 = ttk.Frame(self.tabs)
        self.tabs.add(self.tab1, text="Tab 1")
        self.tab2 = ttk.Frame(self.tabs)
        self.tabs.add(self.tab2, text="Tab 2")
        self.tab3 = ttk.Frame(self.tabs)
        self.tabs.add(self.tab3, text="Tab 3")

        tk.Label(self.tab1, text="This is Tab 1").pack(padx=10, pady=10)
        tk.Label(self.tab2, text="This is Tab 2").pack(padx=10, pady=10)
        tk.Label(self.tab3, text="This is Tab 3").pack(padx=10, pady=10)

        # Frame for the Panda3D viewport (content area)
        self.viewport_frame = tk.Frame(self.main_frame, bg='#111111')
        self.viewport_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.label_frame = tk.LabelFrame(self.viewport_frame, text='Viewport', width=1280, height=720)
        self.label_frame.pack(fill=tk.BOTH, expand=True)

        props = WindowProperties()
        props.set_parent_window(self.label_frame.winfo_id())  # Display within the label frame
        props.set_origin(10, 20)  # Relative to the label frame
        props.set_size(1280, 720)

        self.make_default_pipe()
        self.open_default_window(props=props)
        self.props = props
        
        self.tk.bind("<Configure>", self.on_window_resize)

        # Create the bottom bar (buttons at the bottom of the viewport)
        self.bottom_bar_frame = tk.Frame(self.main_frame, bg='#2a2a2a', height=50)
        self.bottom_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.button1 = tk.Button(self.bottom_bar_frame, text="Button 1", command=self.on_button1_click)
        self.button1.pack(side=tk.LEFT, padx=10)

        self.button2 = tk.Button(self.bottom_bar_frame, text="Button 2", command=self.on_button2_click)
        self.button2.pack(side=tk.LEFT, padx=10)

        self.button3 = tk.Button(self.bottom_bar_frame, text="Button 3", command=self.on_button3_click)
        self.button3.pack(side=tk.LEFT, padx=10)
        
    def on_button1_click(self):
        pass

    def on_button2_click(self):
        pass

    def on_button3_click(self):
        pass
        
    def on_window_resize(self, event):
        # Get the new window size
        window_width = event.width
        window_height = event.height

        # Resize the Panda3D window to match the Tkinter window size
        self.props.set_size(window_width - 50, window_height - 50)  # Adjust for the bottom bar height (50px)
        base.win.request_properties(self.props)

    def setup_lights(self):
        ambient_light = AmbientLight("ambient_light")
        ambient_light.setColor((0.5, 0.5, 0.5, 1))
        self.render.setLight(self.render.attachNewNode(ambient_light))

        directional_light = DirectionalLight("directional_light")
        directional_light.setColor((0.8, 0.8, 0.8, 1))
        dlnp = self.render.attachNewNode(directional_light)
        self.light = dlnp
        dlnp.setHpr(120, -30, 0)
        self.render.setLight(dlnp)
        
if __name__ == "__main__":
    app = GlobeApp()
    base.setFrameRateMeter(True)
    app.run()