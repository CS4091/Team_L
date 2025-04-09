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

class Route:
    app = None #todo
    routes = 0
    
    def __init__(self, name=None):
        self.np = self.app.render.attachNewNode('route')
        self.markers = []
        self.lines_np = None
        self.distance = None
        self.path = []
        if not name:
            name = f"Route {self.routes+1}"
        self.name = name
        Route.routes += 1
        
        
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
    
    def get_points(self):
        return [(marker.airport['lon'], marker.airport['lat']) for marker in self.markers]
        
    def get_stats(self):
        return {
            "Distance:": self.distance
        }
        
    def copy(self):
        route = Route()
        for marker in self.markers:
            route.add_airport(marker.airport)
        if self.path:
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
        
        self.accept("mouse3", self.start_drag)
        self.accept("mouse3-up", self.stop_drag)
        self.accept("mouse1", self.marker_check)
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
            closest_point = min(self.airport_positions.keys(), key=lambda point: (point - col_point).lengthSquared())
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


    def marker_check(self):
        airport = self.selected_airport
        self.check_collision()
        if airport == self.selected_airport:
            self.add_selected_airport()

    def start_drag(self):
        #self.set_window()
        
        self.is_dragging = True
        #self.dragged = False
        self.last_mouse_pos = None  # Reset tracking
        

    def stop_drag(self):
        self.is_dragging = False
        # if not self.dragged:
            # airport = self.selected_airport
            # self.check_collision()
            # if airport == self.selected_airport:
                # self.add_selected_airport()

    def update_camera_rotation(self, task):
        if self.is_dragging and self.mouseWatcherNode.hasMouse():
            mouse_x, mouse_y = self.mouseWatcherNode.getMouseX(), self.mouseWatcherNode.getMouseY()
    
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
        
        # Add checkbox to show all airports
        var = tk.IntVar()
        self.show_airports_var = var
        show_airports_checkbutton = ttk.Checkbutton(self.tab_airports, text="Show All", variable=var, command=self.show_all_airports, onvalue=1, offvalue=0)
        show_airports_checkbutton.pack(side=tk.TOP)

        #todo: search box
        row_frame = tk.Frame(self.tab_airports, bg='#2a2a2a')
        row_frame.pack(fill=tk.X, pady=5, padx=5)
        
        search_label = tk.Label(row_frame, text="Search (todo)")
        search_label.pack(side=tk.LEFT, pady=5, padx=5)
        
        self.search_box = tk.Text(row_frame, height=1, width=15)
        self.search_box.pack(side=tk.RIGHT, padx=5)
        
        class DictView:
            def __init__(self, parent, title):
                self.entries = {}
                self.info_frame = tk.LabelFrame(parent, text=title, bg='#2a2a2a')
                self.info_frame.pack(fill=tk.BOTH, padx=10, pady=10)
                
            class DictViewEntry:
                def __init__(self, parent, key, value):
                    row_frame = tk.Frame(parent, bg='#2a2a2a')
                    row_frame.pack(fill=tk.X, pady=5)
                    
                    self.key_label = tk.Label(row_frame, text=str(key), anchor='w', width=15, bg='#2a2a2a', fg='white')
                    self.key_label.pack(side=tk.LEFT, padx=5)
                    
                    self.value_label = tk.Label(row_frame, text=str(value), anchor='e', width=25, bg='#2a2a2a', fg='white')
                    self.value_label.pack(side=tk.RIGHT, padx=5)
                    
                def set_value(self, value):
                    self.value_label.config(text=str(value))
                
            def view_dict(self, dictionary):
                for key, value in dictionary.items():
                    if key in self.entries:
                        self.entries[key].set_value(value)
                    else:
                        entry = self.DictViewEntry(self.info_frame, key, value)
                        self.entries[key] = entry
        
        # Create a new section in the sidebar for Airport Information
        self.airport_info_view = DictView(self.tab_airports, "Airport Info")

        add_airport_button = ttk.Button(self.airport_info_view.info_frame, text="Add To Route", command=self.add_selected_airport)
        add_airport_button.pack(side=tk.BOTTOM, padx=10)
        
        class RouteTree: #todo maybe abstract to ItemTree?
            def __init__(self, parent, title):
                self.id_to_object = {}
                self.object_to_id = {} 
                self.treeview = ttk.Treeview(parent)
                self.treeview.heading('#0', text=title)
                self.treeview.pack(fill=tk.X, pady=5, padx=10)
        
            def add_item(self, parent_id, item, name):
                tree_id = self.treeview.insert(parent_id, "end", text=name, open=True)
                self.id_to_object[tree_id] = item
                self.object_to_id[item] = tree_id
        
            def add_route(self, route):
                self.add_item("", route, route.name)
                for marker in route.markers:
                    self.add_marker(route, marker)
        
            def delete_item(self, item):
                pass
            
            def add_marker(self, route, marker):
                parent_id = self.object_to_id[route]
                self.add_item(parent_id, marker, marker.airport['name'])
        
            def update_route_list(self, route):
                route_id = self.object_to_id.get(route)
                if route_id:
                    for marker in route.markers:
                        marker_id = self.object_to_id.get(marker)
                        if marker_id:
                            self.treeview.delete(marker_id)
                            del self.id_to_object[marker_id]
                            del self.object_to_id[marker]
        
                    for index in route.path:
                        marker = route.markers[index]
                        self.add_marker(route, marker)
        
            @property
            def selected_item(self):
                selection = self.treeview.selection()
                if selection:
                    selected = selection[-1]
                    return self.id_to_object.get(selected)
        
        # Add section in left to view routes and markers
        self.route_tree = RouteTree(self.tab_routes, "Route List")
        self.route_tree.treeview.bind("<<TreeviewSelect>>", self.on_treeview_select)
        
        # Add route new/delete buttons
        row_frame = tk.Frame(self.tab_routes)
        row_frame.pack(fill=tk.X, pady=5, padx=10)
        self.copy_route_button = ttk.Button(row_frame, text="Copy Current Route", command=self.copy_current_route)
        self.copy_route_button.pack(side=tk.LEFT)
        self.new_route_button = ttk.Button(row_frame, text="New Route", command=self.create_new_route)
        self.new_route_button.pack(side=tk.LEFT)
        self.new_route_button = ttk.Button(row_frame, text="Delete Route", command=self.delete_route)
        self.new_route_button.pack(side=tk.LEFT)
            
        # Add a "Compute Route" section to the routes tab
        self.compute_route_frame = tk.LabelFrame(self.tab_routes, text="Find Shortest Path", bg='#2a2a2a', padx=10, pady=10)
        self.compute_route_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        
        heuristic_options = ["Annealing"]
        self.selected_heuristic = tk.StringVar()
        self.selected_heuristic.set(heuristic_options[0])
        self.heuristic_dropdown = ttk.Combobox(self.compute_route_frame, textvariable=self.selected_heuristic, values=heuristic_options)
        self.heuristic_dropdown.pack(pady=10)
        self.heuristic_dropdown.bind("<<ComboboxSelected>>", self.heuristic_changed)
        
        
        class ParamSlider:
            def __init__(self, parent, text, from_val, to_val, default_val):
                self.label = tk.Label(parent, text=text)
                self.label.pack(side=tk.TOP, anchor='w')
                self.value_label = tk.Label(parent)
                self.value_label.pack(side=tk.TOP, anchor='w')
                self.value_slider = ttk.Scale(
                    parent, from_=from_val, 
                    to=to_val, 
                    orient="horizontal", 
                    command=lambda e: self.update_value_label()
                )
                self.value_slider.set(default_val)
                self.value_slider.pack(side=tk.TOP, fill=tk.X)
            
            def update_value_label(self):
                self.value_label.config(text=f"{self.value:.3f}")
                
            @property
            def value(self):
                return self.value_slider.get()
                
        self.init_temp_input = ParamSlider(self.compute_route_frame, "Initial Temperature:", 1, 2000, 1000)
        self.cool_rate_input = ParamSlider(self.compute_route_frame, "Cooling Rate:", 0.9, 0.999, 0.995)
        self.min_temp_input  = ParamSlider(self.compute_route_frame, "Minimum Temperature:", 1e-5, 1e-2, 1e-3)

        # Compute Route Button
        self.compute_route_button = ttk.Button(self.compute_route_frame, text="Compute Route", command=self.compute_route)
        self.compute_route_button.pack(side=tk.TOP, pady=10)
        
        # Route Stats
        self.route_stats_view = DictView(self.tab_routes, "Route Stats")
        
        #todo: move these to be underneath the tree view


        props = WindowProperties()
        props.set_parent_window(self.label_frame.winfo_id())  # Display within the label frame
        props.set_origin(10, 20)  # Relative to the label frame
        props.set_size(1280, 720)

        self.make_default_pipe()
        self.open_default_window(props=props)
        self.props = props
        
        self.tk.bind("<Configure>", self.on_window_resize)
        self.tkRoot.protocol("WM_DELETE_WINDOW", self.on_closing)
            
    def on_treeview_select(self, event):
        item = self.route_tree.selected_item
        if isinstance(item, Route):
            self.set_current_route(item)
        elif isinstance(item, Marker):
            self.update_airport_info(item.airport)
            #todo: select color, no "add to route" button
            
    def create_new_route(self):
        self.add_route(Route())        
            
    def copy_current_route(self):
        self.add_route(self.current_route.copy())
        
    def heuristic_changed(self):
        print("Change not implemented")
        pass
        
    def delete_route(self):
        print("Delete not implemented")
        pass
        
    def compute_route(self):
        route = self.current_route
        
        if not route.markers:
            return
            
        match self.selected_heuristic.get():
            case "Annealing":
                path, dist = sim_ann_TSP(
                    cities=route.get_points(), 
                    init_temp=self.init_temp_input.value, 
                    cool_rate=self.cool_rate_input.value, 
                    min_temp=self.min_temp_input.value, 
                    globe=True
                )
        
        route.distance = dist
        route.set_path(path)

        self.update_route_info()


    def update_route_info(self):
        self.route_stats_view.view_dict(self.current_route.get_stats())
        self.route_tree.update_route_list(self.current_route)
        
    #todo also add delete
    def add_route(self, route):
        self.route_tree.add_route(route)
        self.set_current_route(route)
    
    def set_current_route(self, route):
        if self.current_route:
            self.current_route.np.hide()
        self.current_route = route
        self.update_route_info()
        route.np.show()
    
    
    def add_selected_airport(self):
        if self.selected_airport_marker:
            self.selected_airport_marker.delete()
            self.selected_airport_marker = None
        marker = self.current_route.add_airport(self.selected_airport)
        self.route_tree.add_marker(self.current_route, marker)
        
    def show_all_airports(self):
        if self.show_airports_var.get():
            self.airports_np.show()
        else:
            self.airports_np.hide()
        
    def update_airport_info(self, airport: dict):
        # Update the labels with the new data (instead of destroying and recreating)

        self.selected_airport = airport
        if self.selected_airport_marker:
            self.selected_airport_marker.delete()
        self.selected_airport_marker = Marker(self.selected_airport)
        self.selected_airport_marker.np.setColorScale(Marker.select_color)
        self.selected_airport_marker.np.reparentTo(render)
        
        self.airport_info_view.view_dict(airport)
    
    #todo: reduce lag
    def on_window_resize(self, event):
        width = self.viewport_frame.winfo_width()
        height = self.viewport_frame.winfo_height()
        self.props.set_size(width, height)
        base.win.request_properties(self.props)
        
    def on_closing(self):
        self.taskMgr.stop()

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
    
    
#todo: need this outside?

    
