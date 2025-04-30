from direct.showbase.ShowBase import ShowBase
from panda3d.core import MouseWatcher
from panda3d.core import WindowProperties

from panda3d.core import ConfigVariableBool
ConfigVariableBool("tk-main-loop").setValue(False)
import math
import sys

from src.gui import GlobeSimUI
from src.camera import GlobeSimCam
from src.world import GlobeSimWorld
from src.route import Route, Marker
from src.heuristic import TSPHeuristic

from tkinter import filedialog
import os

import airportsdata
import time
import xml.etree.ElementTree as ET

class GlobeSim(ShowBase):
    def __init__(self):
        ShowBase.__init__(self, windowType='none')
        
        # Setup the ui
        self.startTk()
        
        self.tkRoot.geometry("1920x1080")
        self.tkRoot.call('source', 'themes/Azure-ttk-theme-2.1.0/azure.tcl')
        self.tkRoot.call("set_theme", "dark")
        
        ui = GlobeSimUI(self.tkRoot)
        
        ui.file_menu.add_command(label="Import", command=self.dlg_import)
        ui.file_menu.add_command(label="Export", command=self.dlg_export)
        
        ui.show_airports_checkbutton.configure(command=self.show_all_airports)
        ui.add_airport_button.configure(command=self.add_selected_airport)
        ui.remove_airport_button.configure(command=self.remove_selected_airport)
        
        ui.route_tree.treeview.bind("<<TreeviewSelect>>", self.on_treeview_select)
        ui.copy_route_button.configure(command=self.copy_current_route)
        ui.new_route_button.configure(command=self.create_new_route)
        ui.delete_route_button.configure(command=self.delete_current_route)
        
        ui.compute_route_button.configure(command=self.compute_route)
        
        ui.result_listbox.bind("<<ListboxSelect>>", self.on_search_select)
        ui.search_box.bind("<KeyRelease>", self.search_airports)
        
        
        self.ui = ui

        props = WindowProperties()
        props.set_parent_window(ui.label_frame.winfo_id())
        props.set_origin(10, 20) 
        props.set_size(1280, 720)

        self.make_default_pipe()
        self.open_default_window(props=props)
        self.props = props
        
        self.tkRoot.bind("<Configure>", self.on_window_resize)
        self.tkRoot.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Setup the controls
        self.disableMouse()
        self.camera_control = GlobeSimCam()
        self.cam.node().getLens().setNear(0.01)
        self.accept("mouse3", self.camera_control.start_drag)
        self.accept("mouse3-up", self.camera_control.stop_drag)
        self.accept("mouse1", self.mouse_click)
        self.taskMgr.add(self.update_camera, "UpdateRotationTask")
        self.accept("wheel_up", self.camera_control.zoom_in)
        self.accept("wheel_down", self.camera_control.zoom_out)
        self.selected_airport_marker = None
        self.selected_airport = None
        
        # Load airports
        self.airports = airportsdata.load()

        # Setup the 3d objects
        self.world = GlobeSimWorld()
        self.world.create_points(self.airports)
        self.world.earth.setTexture(self.loader.loadTexture("res/earth_2.jpg"))
        self.world.starmap.setTexture(self.loader.loadTexture("res/starmap.jpg"))
        self.world.np.reparentTo(render)
        self.world.mouse_ray_node_path.reparentTo(self.cam)
        
        # Initial ui
        self.routes = []
        self.current_route = None
        self.create_new_route()
        self.update_airport_info(self.airports[next(iter(self.airports))]) #todo, just using the first airport as setup here
        
        
        
    def update_camera(self, task):
        """ Update the camera each frame """
        x, y = None, None
        if self.mouseWatcherNode.hasMouse():
            x, y = self.mouseWatcherNode.getMouseX(), self.mouseWatcherNode.getMouseY()
        pos = self.camera_control.get_pos(x, y)
        self.camera.setPos(pos)
        self.camera.lookAt(self.world.earth)
        return task.cont
        
    def do_airport_select(self): # Demo function
        """ Find closest airport to mouse and make it the current selection """
        mouse_pos = self.mouseWatcherNode.getMouse()
        if mouse_pos != (0, 0):
            self.world.mouse_ray.setFromLens(self.camNode, mouse_pos[0], mouse_pos[1])
            nearest = self.world.find_airport()
            if nearest:
                self.update_airport_info(nearest)
    
    def mouse_click(self):
        airport = self.selected_airport
        self.do_airport_select()
        if airport == self.selected_airport:
            self.add_selected_airport()
            
    def on_treeview_select(self, event):
        item = self.ui.route_tree.get_selected_item()
        if isinstance(item, Route):
            self.set_current_route(item)
        elif isinstance(item, Marker):
            self.set_current_route(item.route)
            self.update_airport_info(item.airport)
            
    def search_airports(self, event):
        self.ui.search_airports(self.airports)
            
    def on_search_select(self, event):
        self.update_airport_info(self.ui.get_selected_search())
        
    def compute_route(self):
        """ Updates the route based on the selected heuristic in the dropdown """
        route = self.current_route
        
        if not route.markers:
            return
            
        cities = route.get_points()
        
        if len(cities) < 2:
            return
        
        match self.ui.selected_heuristic.get():
            case "Annealing":
                path, dist = TSPHeuristic.sim_ann_TSP(
                    cities=route.get_points(), 
                    init_temp=self.ui.init_temp_input.value, 
                    cool_rate=self.ui.cool_rate_input.value, 
                    min_temp=self.ui.min_temp_input.value
                )
            case "Nearest Neighbor":
                path, dist = TSPHeuristic.nearest_neighbor(cities)
            case "Brute Force":
                path, dist = TSPHeuristic.brute_force(cities)
        
        route.distance = dist
        route.set_path(path)

        self.ui.update_route_info(self.current_route)
        
    def create_new_route(self):
        self.add_route(Route())     
            
    def copy_current_route(self):
        self.add_route(self.current_route.copy())
        
    def add_route(self, route): #TODO we need to update the route tree so its not storing the routes, should store them in globe sim
        # We could simplify stuff by passing the route list to the route tree each time so that it can update
        self.ui.route_tree.add_route(route)
        route.np.reparentTo(self.world.np)
        self.routes.append(route)
        self.set_current_route(route)
        
    def delete_current_route(self):
        if self.current_route:
            to_del = self.current_route
            new = self.ui.route_tree.get_prev_route(self.current_route)
            self.set_current_route(new)
            self.delete_route(to_del)
            if not new:
                self.create_new_route()
        
    def delete_route(self, route):
        if route == self.current_route:
            self.current_route = None
        self.ui.route_tree.remove_item(route)
        self.routes.remove(route)
        route.delete()
    
    def set_current_route(self, route):
        if self.current_route:
            self.current_route.np.hide()
        self.current_route = route
        if route:
            self.ui.route_stats_view.view_dict(route.get_stats()) #TODO
            route.np.show()
            
    def remove_selection_marker(self):
        if self.selected_airport_marker:
            self.selected_airport_marker.delete()
            self.selected_airport_marker = None
    
    def add_selected_airport(self):
        if self.selected_airport in self.current_route.get_airports():
            return
        self.remove_selection_marker()
        marker = self.current_route.add_airport(self.selected_airport)
        self.ui.route_tree.add_marker(self.current_route, marker)
        
    def remove_selected_airport(self):
        self.remove_selection_marker()
        marker = self.current_route.remove_airport(self.selected_airport)
        if marker:
            self.ui.route_tree.remove_item(marker)
            marker.delete()

    def show_all_airports(self):
        if self.ui.show_airports_var.get():
            self.world.airports_np.show()
        else:
            self.world.airports_np.hide()
        
    def update_airport_info(self, airport: dict):
        if not airport:
            return #TODO
        self.selected_airport = airport
        if self.selected_airport_marker:
            self.selected_airport_marker.delete()
        self.selected_airport_marker = Marker(self.selected_airport)
        self.selected_airport_marker.np.setColorScale(Marker.select_color)
        self.selected_airport_marker.np.reparentTo(render)
        
        self.ui.airport_info_view.view_dict(airport)

    #todo: reduce lag
    def on_window_resize(self, event):
        width = self.ui.viewport_frame.winfo_width()
        height = self.ui.viewport_frame.winfo_height()
        self.props.set_size(width-20, height-40)
        base.win.request_properties(self.props)
        
    def on_closing(self):
        self.taskMgr.stop()
        
    def dlg_import(self):
        folder_path = os.path.join(os.getcwd(), "saved")
    
        file_path = filedialog.askopenfilename(
            initialdir=folder_path,
            title="Select a routes file",
            filetypes=[("XML files", "*.xml")]
        )
        if file_path:
            self.import_file(file_path)
            
    def dlg_export(self):
        folder_path = os.path.join(os.getcwd(), "saved")
    
        file_path = filedialog.asksaveasfilename(
            initialdir=folder_path,
            title="Save a routes file",
            defaultextension=".xml",
            filetypes=[("XML files", "*.xml")]
        )
    
        if file_path:
            self.export_file(file_path)
        
    def import_file(self, path):
        for route in list(self.routes):
            self.delete_route(route)
        tree = ET.parse(path)
        for route_elem in tree.getroot():
            self.add_route(Route.from_element(route_elem, self.airports))
        
    def export_file(self, path):
        root = ET.Element("Routes")
        for route in self.routes:
            root.append(route.to_element())
        tree = ET.ElementTree(root)
        ET.indent(tree, space="    ", level=0)
        tree.write(path, encoding="utf-8", xml_declaration=True)
        