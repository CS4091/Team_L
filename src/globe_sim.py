import sys
import os

lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))
sys.path.append(lib_path)

from direct.showbase.ShowBase import ShowBase
from panda3d.core import Loader, TextureStage, TransparencyAttrib
from panda3d.core import NodePath, AmbientLight, DirectionalLight
from panda3d.core import MouseWatcher
from panda3d.core import Shader
from panda3d.core import GeomNode
from panda3d.core import WindowProperties

import sys
from procedural3d.sphere import SphereMaker
#from ..lib import procedural3d

import tkinter as tk
from tkinter import ttk

class GlobeApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self, windowType='none')
        self.setup_tk()
        
        self.disableMouse()

        # Earth, starmap
        segs = {
            "horizontal": 30,
            "vertical": 15
        }
        sphere_geom = SphereMaker(segments=segs).generate()
        self.earth = self.render.attachNewNode(sphere_geom)
        
        self.starmap = self.earth.copy_to(render)

        texture = self.loader.loadTexture("../res/earth.jpg")
        self.earth.setTexture(texture, 1)
        
        texture = self.loader.loadTexture("../res/starmap.jpg")
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
        self.taskMgr.add(self.update_rotation, "UpdateRotationTask")
        self.accept("wheel_up", self.zoom_in)
        self.accept("wheel_down", self.zoom_out)
        
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
        dlnp.setHpr(45, -30, 0)
        self.render.setLight(dlnp)

    def start_drag(self):
        self.is_dragging = True
        self.last_mouse_pos = None  # Reset tracking

    def stop_drag(self):
        self.is_dragging = False

    def update_rotation(self, task):
        if self.is_dragging and self.mouseWatcherNode.hasMouse():
            mouse_x, mouse_y = self.mouseWatcherNode.getMouseX(), self.mouseWatcherNode.getMouseY()

            if self.last_mouse_pos:
                dx = (mouse_x - self.last_mouse_pos[0]) * 100
                dy = (mouse_y - self.last_mouse_pos[1]) * 100
                self.rotation_y += dx
                self.rotation_x -= dy 

            self.last_mouse_pos = (mouse_x, mouse_y)

        self.earth.setHpr(self.rotation_y, self.rotation_x, 0)
        self.starmap.setHpr(self.rotation_y, self.rotation_x, 0)

        self.camera.setPos(0, -self.zoom, 0)

        return task.cont

    def zoom_in(self):
        self.zoom = max(2, self.zoom - 0.3)

    def zoom_out(self):
        self.zoom = min(10, self.zoom + 0.3)
        
if __name__ == "__main__":
    app = GlobeApp()
    app.run()