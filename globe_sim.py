from direct.showbase.ShowBase import ShowBase
from panda3d.core import TransparencyAttrib
from panda3d.core import NodePath, AmbientLight, DirectionalLight
from panda3d.core import MouseWatcher
from panda3d.core import Shader
from panda3d.core import CollisionNode, CollisionHandlerQueue, CollisionSphere, CollisionRay, CollisionNode, CollisionTraverser, BitMask32
from panda3d.core import GeomNode, Geom, GeomVertexData, GeomVertexWriter, GeomPoints, GeomVertexFormat, Shader
from panda3d.core import WindowProperties
from panda3d.core import LineSegs
from panda3d.core import Point3

from panda3d.core import ConfigVariableBool
ConfigVariableBool("tk-main-loop").setValue(False)
import math
import sys
from procedural3d.sphere import SphereMaker

import tkinter as tk
from tkinter import ttk

import airportsdata
import time

from TSP_Ex import sim_ann_TSP

#todo: need this outside?

    
class Route:
    app = None #todo
    routes = 0
    
    def __init__(self, name=None):
        self.np = self.app.render.attachNewNode('route')
        self.markers = []
        self.lines_np = None
        self.distance = None
        if not name:
            name = f"Route {self.routes+1}"
        self.name = name
        Route.routes += 1
        
        self.treeview_id = None
        
        
    def remove_markers(self):
        for marker in list(self.markers):
            marker.delete()
        self.markers = []
        
    def add_airport(self, airport):
        #todo: don't add duplicate airports
        marker = Marker(airport)
        self.markers.append(marker)
        marker.np.reparentTo(self.np)
        return marker
    
    def compute_path(self, alg):
        #todo
        points = []
        for marker in self.markers:
            points.append((marker.airport['lon'], marker.airport['lat']))
        if alg['type'] == "Annealing":
            path, dist = sim_ann_TSP(points, init_temp=alg['init_temp'], cool_rate=alg['cool_rate'], min_temp=alg['min_temp'], globe=True)
        else:
            return
        #print("Path distance:", dist, "km")
        self.distance = dist
        
        self.set_path(path)
        
    def copy(self):
        route = Route()
        for marker in self.markers:
            route.add_airport(marker.airport)
        route.set_path(self.path)
        return route
    
    def set_path(self, indices):
        """
        Draws a curved path between the markers by calculating the great-circle route.
        Also rearranges the treeview markers to match the order of the path.
        """

                
        self.path = indices
        
        if self.lines_np:
            self.lines_np.removeNode()
        
        if len(indices) < 2:
            return
        
        path_lines = LineSegs()
        #path_lines.setColor(1, 1, 0, 0.75)
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
        self.lines_np = self.np.attachNewNode(path_lines.create())
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

class Marker:
    altitude = 0.025
    color = (1, 1, 0, 0.5)
    select_color = (0, 1, 1, 0.75)
    loaded_model = None 
    
    #def __init__(self, latitude, longitude):
    def __init__(self, airport):
        if self.loaded_model is None:
            self.loaded_model = loader.loadModel("models/misc/sphere")
            
        self.airport = airport
        np = self.loaded_model.instanceTo(NodePath())
        
        np.setBin("fixed", 0)
        np.setDepthTest(False)
        np.setDepthWrite(False)
        np.setBin("transparent", 0)
        np.setTransparency(TransparencyAttrib.MAlpha)
        np.setColorScale(self.color)
        np.setLightOff(1)
        np.setScale(0.005)  # todo change on zoom?
        self.np = np
        
        self.np.setPos(self.airport['xyz'])
        
        path_lines = LineSegs()
        path_lines.setColor(1, 1, 0, 0.75)
        start = self.np.getPos()
        end = Point3(0, 0, 0)
        path_lines.moveTo(start)
        path_lines.drawTo(end)

        self.lines_np = self.np.attachNewNode(path_lines.create())
        
        self.treeview_id = None
        #self.set_coords(latitude, longitude)
        
    # def get_coords(self):
        # return self.__coords
        
    #def set_coords(self, latitude, longitude):
    #    #self.__coords = (latitude, longitude)
    #    #self.np.setPos(world_to_3d(latitude, longitude, self.altitude))
        
    
    def delete(self):
        self.np.removeNode()
        del self
        
class GlobeApp(ShowBase):
    def __init__(self, useTk = False):
        if useTk:
            ShowBase.__init__(self, windowType='none')
            self.setup_tk()
        else:
            super().__init__()

        Marker.app = self #todo
        Route.app = self
        


        self.setup_controls()

        self.airports = airportsdata.load()
        self.airport_positions = {}

        self.setup_world()
        self.setup_collision()
        self.setup_lights()
        self.create_all_airports_points()
        
        self.current_route = None
        self.routes = []
        self.tree_objects = {} #todo refactor by making a new tree view class?
        self.create_new_route()
        
        
        #todo: merge these
        self.selected_airport_marker = None
        self.selected_airport = None
        
        self.update_airport_info(self.airports[next(iter(self.airports))]) #todo, just using the first airport as setup here
        
        base.win.request_properties(self.props)
        
    def setup_controls(self):
        self.disableMouse()
        self.cam.node().getLens().setNear(0.01)
        
        self.is_dragging = False
        self.last_mouse_pos = None
        self.rotation_x = 0
        self.rotation_y = 0
        self.zoom = 5
        
        self.accept("mouse1", self.start_drag)
        self.accept("mouse1-up", self.stop_drag)
        self.accept("mouse3", self.check_collision)
        self.taskMgr.add(self.update_camera_rotation, "UpdateRotationTask")
        self.accept("wheel_up", self.zoom_in)
        self.accept("wheel_down", self.zoom_out)
        #self.accept("e", self.do_path_demo)
    
    def setup_world(self):
        # Earth, starmap
        segs = {
            "horizontal": 60,
            "vertical": 30
        }
        sphere_geom = SphereMaker(segments=segs).generate()
        #self.rotate = self.render.attachNewNode('rotate')
        
        self.earth = self.render.attachNewNode(sphere_geom)
        #self.earth.setHpr(, math.radians(180), 0)
        
        self.starmap = self.earth.copy_to(self.render)
        
        self.earth.setScale(1)
        
        texture = self.loader.loadTexture("res/earth.jpg")
        self.earth.setTexture(texture, 1)
        
        texture = self.loader.loadTexture("res/starmap.jpg")
        self.starmap.setTexture(texture, 1)
        self.starmap.setTwoSided(True)
        self.starmap.setScale(1000)
        
    def setup_collision(self):
        self.collision_handler = CollisionHandlerQueue()
        self.collision_traverser = CollisionTraverser()
        
        self.mouse_ray = CollisionRay()
        self.mouse_ray.setFromLens(self.camNode, 0, 0)  # From the camera through the mouse position
        #self.mouse_ray.setInto(render)  # Set the target for the ray

        # Set up a CollisionNode for the ray
        self.mouse_ray_node = CollisionNode('mouse_ray')
        self.mouse_ray_node.addSolid(self.mouse_ray)
        self.mouse_ray_node.setFromCollideMask(BitMask32.bit(1))
        self.mouse_ray_node_path = self.cam.attachNewNode(self.mouse_ray_node)
        
        self.collision_traverser.addCollider(self.mouse_ray_node_path, self.collision_handler)
        
        collision_sphere = CollisionSphere(0, 0, 0, 1.0)  # 1.0 is the radius of the sphere
        
        collision_node = CollisionNode("earth")
        collision_node.addSolid(collision_sphere)
        
        collision_node.setIntoCollideMask(BitMask32.bit(1))
        collision_node.setFromCollideMask(BitMask32.allOff())  # Only collide with ray

        # Create a NodePath for the CollisionNode and attach it to the scene graph
        collision_node_path = self.earth.attachNewNode(collision_node)
        self.collision_traverser.addCollider(collision_node_path, self.collision_handler)
        
    def check_collision(self):
        # Update the ray position to follow the mouse
        mouse_pos = self.mouseWatcherNode.getMouse()
        if mouse_pos != (0, 0):  # Ensure the mouse is inside the window
            self.mouse_ray.setFromLens(self.camNode, mouse_pos[0], mouse_pos[1])

        # Traverse the collision space
        self.collision_traverser.traverse(self.render)

        # Check if there are any collisions
        if self.collision_handler.getNumEntries() > 0:
            entry = self.collision_handler.getEntry(0)
            col_point = entry.getSurfacePoint(self.render)  # Get the point of collision
            #print(f"Collision at: {col_point}")
            closest_point = min(self.airport_positions.keys(), key=lambda point: (point - col_point).lengthSquared())
            #print(self.airport_positions[closest_point])
            self.update_airport_info(self.airport_positions[closest_point])

    def create_all_airports_points(self):
        def world_to_3d(latitude, longitude, elevation):
            lat_rad = math.radians(latitude) 
            lon_rad = math.radians(longitude) + math.radians(180)
            
            x = (1 + elevation) * math.cos(lat_rad) * math.cos(lon_rad)
            y = (1 + elevation) * math.cos(lat_rad) * math.sin(lon_rad)
            z = (1 + elevation) * math.sin(lat_rad)
            
            return Point3(x, y, z)
        
        vertex_data = GeomVertexData('points', GeomVertexFormat.get_v3(), Geom.UH_static)
        vertex_writer = GeomVertexWriter(vertex_data, 'vertex')
        for airport in self.airports.values():
            #elev = airport['elevation'] / 2.093e+7
            #writer = vertex_writer_large if airport['iata'] else vertex_writer_small
            world_coord = world_to_3d(airport['lat'], airport['lon'], 0.001)
            airport['xyz'] = world_coord
            self.airport_positions[world_coord] = airport
            vertex_writer.add_data3(world_coord)
                
        points_geom = Geom(vertex_data)
        points_prim = GeomPoints(Geom.UH_static)
        
        for i in range(vertex_writer.get_write_row()):
            points_prim.add_vertex(i)
            
        points_prim.close_primitive()
        points_geom.add_primitive(points_prim)
        
        points_node = GeomNode('points')
        points_node.add_geom(points_geom)
        
        points_np = render.attach_new_node(points_node)
        points_np.set_color(0.8, 0.8, 1, 1)
        points_np.set_render_mode_thickness(2)
        points_np.hide()
        
        self.airports_np = points_np


    def start_drag(self):
        self.is_dragging = True
        self.last_mouse_pos = None  # Reset tracking

    def stop_drag(self):
        self.is_dragging = False

    def update_camera_rotation(self, task):
        if self.is_dragging and self.mouseWatcherNode.hasMouse():
            mouse_x, mouse_y = self.mouseWatcherNode.getMouseX(), self.mouseWatcherNode.getMouseY()
    
            if self.last_mouse_pos:
                dx = (mouse_x - self.last_mouse_pos[0]) * 10 * (self.zoom + 1)
                dy = (mouse_y - self.last_mouse_pos[1]) * 10 * (self.zoom + 1)
    
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
        distance = self.zoom + 1
        # Convert spherical coordinates to Cartesian coordinates for the camera
        x = distance * math.cos(rad_x) * math.sin(rad_y)
        y = distance * math.cos(rad_x) * math.cos(rad_y)
        z = distance * math.sin(rad_x)

        self.camera.setPos(x, y, z)
        self.camera.lookAt(self.earth)

    def get_zoom_step(self):
        # Example: step shrinks as zoom increases
        return max(0.05, 0.5 * self.zoom)
    
    def zoom_in(self):
        #print(self.zoom)
        self.zoom = max(0.001, self.zoom - self.get_zoom_step())
    
    def zoom_out(self):
        self.zoom = min(10, self.zoom + self.get_zoom_step())
        
        
    def setup_tk(self):
        self.startTk()

        self.tk = self.tkRoot
        self.tk.geometry("1920x1080")
        
        # Theme
        self.tk.call('source', 'gui/Azure-ttk-theme-2.1.0/azure.tcl')
        self.tk.call("set_theme", "dark")

        # Main frame for the layout
        self.main_frame = tk.Frame(self.tk)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Sidebar with tabs (left side)
        self.right_sidebar_frame = tk.Frame(self.main_frame, width=250, bg='#2a2a2a')
        self.right_sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.tabs_right = ttk.Notebook(self.right_sidebar_frame)
        self.tabs_right.pack(fill=tk.BOTH, expand=True)

        self.tab_airports = tk.Frame(self.tabs_right)
        self.tabs_right.add(self.tab_airports, text="Airports")
        
        self.left_sidebar_frame = tk.Frame(self.main_frame, width=250, bg='#2a2a2a')
        self.left_sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.tabs_left = ttk.Notebook(self.left_sidebar_frame)
        self.tabs_left.pack(fill=tk.BOTH, expand=True)

        self.tab_routes = tk.Frame(self.tabs_left)
        self.tabs_left.add(self.tab_routes, text="Routes")

        # Frame for the Panda3D viewport (content area)
        self.viewport_frame = tk.Frame(self.main_frame, bg='#111111')
        self.viewport_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.label_frame = tk.LabelFrame(self.viewport_frame, text='Viewport', width=1280, height=720)
        self.label_frame.pack(fill=tk.BOTH, expand=True)

        # Create the bottom bar (buttons at the bottom of the viewport)
        self.bottom_bar_frame = tk.Frame(self.main_frame, bg='#2a2a2a', height=50)
        self.bottom_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        var = tk.IntVar()
        self.show_airports_var = var
        show_airports_checkbutton = ttk.Checkbutton(self.tab_airports, text="Show All", variable=var, command=self.show_all_airports, onvalue=1, offvalue=0)
        show_airports_checkbutton.pack(side=tk.TOP)
        
        # Create a new section in the sidebar for Airport Information
        self.airport_info_labels = {}
        self.airport_info_frame = tk.LabelFrame(self.tab_airports, text="Airport Info", bg='#2a2a2a')
        self.airport_info_frame.pack(fill=tk.BOTH, padx=10, pady=10)

        add_airport_button = ttk.Button(self.airport_info_frame, text="Add To Route", command=self.add_selected_airport)
        add_airport_button.pack(side=tk.BOTTOM, padx=10)
        
        self.route_tree = ttk.Treeview(self.tab_routes)
        self.route_tree.heading('#0', text="Route List")
        self.route_tree.pack()
        self.route_tree.bind("<<TreeviewSelect>>", self.treeview_select)
        
        #todo: buttons for new route, copy current route
        def update_value_label(slider, label):
            value = slider.get()  # Get the current value of the slider
            label.config(text=f"{value:.3f}")  # Update the label text with the value
            
        # Add a "Compute Route" section to the routes tab
        self.compute_route_frame = tk.LabelFrame(self.tab_routes, text="Find Shortest Path", bg='#2a2a2a', padx=10, pady=10)
        self.compute_route_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        
        heuristic_options = ["Annealing"]
        self.selected_heuristic = tk.StringVar()
        self.selected_heuristic.set(heuristic_options[0])
        self.heuristic_dropdown = ttk.Combobox(self.compute_route_frame, textvariable=self.selected_heuristic, values=heuristic_options)
        self.heuristic_dropdown.pack(pady=10)
        self.heuristic_dropdown.bind("<<ComboboxSelected>>", self.heuristic_changed)
        
        #todo: we need to refactor this, setting up sliders and labels programatically based on each heuristic
        
    
        # Initial Temperature Slider
        self.init_temp_label = tk.Label(self.compute_route_frame, text="Initial Temperature:")
        self.init_temp_label.pack(side=tk.TOP, anchor='w')
        self.init_temp_value_label = tk.Label(self.compute_route_frame, text="1000.000")  # Initial value label
        self.init_temp_value_label.pack(side=tk.TOP, anchor='w')
        self.init_temp_slider = ttk.Scale(self.compute_route_frame, from_=1, to=2000, orient="horizontal",
                                        command=lambda e: update_value_label(self.init_temp_slider, self.init_temp_value_label))
        self.init_temp_slider.set(1000)  # Default value
        self.init_temp_slider.pack(side=tk.TOP, fill=tk.X)
        
        # Cool Rate Slider
        self.cool_rate_label = tk.Label(self.compute_route_frame, text="Cooling Rate:")
        self.cool_rate_label.pack(side=tk.TOP, anchor='w')
        self.cool_rate_value_label = tk.Label(self.compute_route_frame, text="0.995")  # Initial value label
        self.cool_rate_value_label.pack(side=tk.TOP, anchor='w')
        self.cool_rate_slider = ttk.Scale(self.compute_route_frame, from_=0.9, to=0.999, orient="horizontal",
                                        command=lambda e: update_value_label(self.cool_rate_slider, self.cool_rate_value_label))
        self.cool_rate_slider.set(0.995)  # Default value
        self.cool_rate_slider.pack(side=tk.TOP, fill=tk.X)
        
        # Minimum Temperature Slider
        self.min_temp_label = tk.Label(self.compute_route_frame, text="Minimum Temperature:")
        self.min_temp_label.pack(side=tk.TOP, anchor='w')
        self.min_temp_value_label = tk.Label(self.compute_route_frame, text="0.001")  # Initial value label
        self.min_temp_value_label.pack(side=tk.TOP, anchor='w')
        self.min_temp_slider = ttk.Scale(self.compute_route_frame, from_=1e-5, to=1e-2, orient="horizontal",
                                        command=lambda e: update_value_label(self.min_temp_slider, self.min_temp_value_label))
        self.min_temp_slider.set(1e-3)  # Default value
        self.min_temp_slider.pack(side=tk.TOP, fill=tk.X)
        
        
    
        # Compute Route Button
        self.compute_route_button = ttk.Button(self.compute_route_frame, text="Compute Route", command=self.compute_route)
        self.compute_route_button.pack(side=tk.TOP, pady=10)
        
     
        #  Route stats
        # todo: abstract this type of frame. Also done in the airport info
        self.route_stats_frame = tk.LabelFrame(self.tab_routes, text="Route Stats", bg='#2a2a2a', padx=10, pady=10)
        self.route_stats_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        row_frame = tk.Frame(self.route_stats_frame, bg='#2a2a2a')
        row_frame.pack(fill=tk.X, pady=5)
        key_label = tk.Label(row_frame, text="Distance", anchor='w', width=15, bg='#2a2a2a', fg='white')
        key_label.pack(side=tk.LEFT, padx=5)
        self.distance_value_label = tk.Label(row_frame, text="", anchor='e', width=25, bg='#2a2a2a', fg='white')
        self.distance_value_label.pack(side=tk.RIGHT, padx=5)
        
        
        self.copy_route_button = ttk.Button(self.tab_routes, text="Copy Current Route", command=self.copy_current_route)
        self.copy_route_button.pack(side=tk.TOP, pady=10)
        self.new_route_button = ttk.Button(self.tab_routes, text="New Route", command=self.create_new_route)
        self.new_route_button.pack(side=tk.TOP, pady=10)

        props = WindowProperties()
        props.set_parent_window(self.label_frame.winfo_id())  # Display within the label frame
        props.set_origin(10, 20)  # Relative to the label frame
        props.set_size(1280, 720)

        self.make_default_pipe()
        self.open_default_window(props=props)
        self.props = props
        
        self.tk.bind("<Configure>", self.on_window_resize)
    
    # def on_route_select(self, event):
        # sel_index = self.route_tree.curselection()
        # if sel_index:
            # self.set_current_route(self.route_tree.get(sel_index))
            
    def treeview_select(self, event):
        selected = self.route_tree.selection()
        for item_id in selected:
            data = self.tree_objects.get(item_id)
            if isinstance(data, Route):
                self.set_current_route(data)
            elif isinstance(data, Marker):
                self.update_airport_info(data.airport)
                #todo: select color, no "add to route" button
            
    def create_new_route(self):
        self.add_route(Route())        
            
    def copy_current_route(self):
        self.add_route(self.current_route.copy())
        
    def heuristic_changed(self):
        pass
        
    def compute_route(self):
        alg = {}
        alg['type'] = self.selected_heuristic.get()
        if alg['type'] == "Annealing":
            alg['init_temp'] = self.init_temp_slider.get()
            alg['cool_rate'] = self.cool_rate_slider.get()
            alg['min_temp'] = self.min_temp_slider.get()
        
        self.current_route.compute_path(alg)
        # Rearrange treeview markers to match the new order
        if self.current_route.treeview_id:
            # Remove all the old markers from the treeview
            for marker in self.current_route.markers:
                self.route_tree.delete(marker.treeview_id)
            
            # Reinsert markers based on the new order in the indices list
            for index in self.current_route.path:
                marker = self.current_route.markers[index]
                marker.treeview_id = self.route_tree.insert(self.current_route.treeview_id, "end", text=marker.airport['name'])
                
        
        self.distance_value_label.config(text=self.current_route.distance)
    
    
    # def add_to_tree(self, parent, obj):
        # self.tree_objects[obj.treeview_id] = obj
        # obj.treeview_id = self.route_tree.insert(parent, 
    
    #todo also add delete
    def add_route(self, route):
        self.routes.append(route)
        route.treeview_id = self.route_tree.insert("", "end", text=route.name, open=True, values=route)
        self.tree_objects[route.treeview_id] = route
        #self.route_tree.tag_bind(id(route), function=lambda: self.set_current_route(route))
        for marker in route.markers:
            marker.treeview_id = self.route_tree.insert(route.treeview_id, "end", text=marker.airport['name']) #todo also called in add selected airport
        self.set_current_route(route)
    
    def set_current_route(self, route):
        if self.current_route:
            self.current_route.np.hide()
        self.current_route = route
        self.distance_value_label.config(text=self.current_route.distance) #todo: we should make an update info method (also called in compute_route)
        route.np.show()
    
    def add_selected_airport(self):
        self.selected_airport_marker.delete()
        self.selected_airport_marker = None
        marker = self.current_route.add_airport(self.selected_airport)
        marker.treeview_id = self.route_tree.insert(self.current_route.treeview_id, "end", text=marker.airport['name']) #todo figure out where to add markers to the tree view
        
    def show_all_airports(self):
        if self.show_airports_var.get():
            self.airports_np.show()
        else:
            self.airports_np.hide()
        
    def update_airport_info(self, airport: dict):
        # Update the labels with the new data (instead of destroying and recreating)

        if self.selected_airport == airport:
            self.add_selected_airport()
        else:
            self.selected_airport = airport
        if self.selected_airport_marker:
            self.selected_airport_marker.delete()
        self.selected_airport_marker = Marker(self.selected_airport)
        self.selected_airport_marker.np.setColorScale(Marker.select_color)
        self.selected_airport_marker.np.reparentTo(render)
        
        for key, value in airport.items():
            if key in self.airport_info_labels:
                # If the label already exists, just update the text
                self.airport_info_labels[key][1].config(text=str(value))
            else:
                # If the label doesn't exist, create new ones
                row_frame = tk.Frame(self.airport_info_frame, bg='#2a2a2a')
                row_frame.pack(fill=tk.X, pady=5)

                key_label = tk.Label(row_frame, text=key, anchor='w', width=15, bg='#2a2a2a', fg='white')
                key_label.pack(side=tk.LEFT, padx=5)

                value_label = tk.Label(row_frame, text=str(value), anchor='e', width=25, bg='#2a2a2a', fg='white')
                value_label.pack(side=tk.RIGHT, padx=5)

                # Store the reference to the key-value pair labels
                self.airport_info_labels[key] = (key_label, value_label)
        
    def on_window_resize(self, event):
        #print(event, "resizing")
        window_width = event.width
        window_height = event.height
        
        #todo have some timer 
        if base.win.getXSize() != window_width-50 or base.win.getYSize() != window_height-50:
            #print("resized")
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
    app = GlobeApp(useTk=True)
    base.setFrameRateMeter(True)
    app.run()