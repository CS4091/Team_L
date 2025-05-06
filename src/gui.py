import tkinter as tk
from tkinter import ttk

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
        self.value_label.config(text=f"{self.value:.4f}")
        
    @property
    def value(self):
        return self.value_slider.get()

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
        
    def remove_item(self, item):
        self.treeview.delete(self.object_to_id[item])
        item_id = self.object_to_id[item]
        del self.object_to_id[item]
        del self.id_to_object[item_id]

    def add_route(self, route):
        self.add_item("", route, route.name)
        for marker in route.markers:
            self.add_marker(route, marker)
    
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
                if marker not in self.object_to_id:
                    self.add_marker(route, marker)
    
    def get_prev_route(self, route):
        items = self.treeview.get_children('')
        if len(items) == 1:
            return None
        prev_index = items.index(self.object_to_id[route])-1
        return self.id_to_object[items[prev_index]]

    def get_selected_item(self):
        selection = self.treeview.selection()
        if selection:
            selected = selection[-1]
            return self.id_to_object.get(selected)

class DictView:
    def __init__(self, parent, title):
        self.entries = {}
        self.info_frame = tk.LabelFrame(parent, text=title, bg='#2a2a2a')
        self.info_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        self.first_called = False
        
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
            
        def remove(self):
            self.key_label.pack_forget()
            self.value_label.pack_forget()
            
        def reshow(self):
            self.key_label.pack(side=tk.LEFT, padx=5)
            self.value_label.pack(side=tk.RIGHT, padx=5)

    def view_dict(self, dictionary):
        for key, value in dictionary.items():
            if key in self.entries:
                self.entries[key].set_value(value)
            else:
                entry = self.DictViewEntry(self.info_frame, key, value)
                self.entries[key] = entry
                
    def close_dict(self):
        #for k in self.entries.keys():
        #    self.entries[k].remove()
        self.info_frame.pack_forget()
        self.first_called = True
    
    def reshow(self):
        self.info_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        


                
                

class GlobeSimUI:
    def __init__(self, root):
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Sidebar with tabs (left side)
        right_sidebar_frame = tk.Frame(main_frame, width=250, bg='#2a2a2a')
        right_sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y)

        tabs_right = ttk.Notebook(right_sidebar_frame)
        tabs_right.pack(fill=tk.BOTH, expand=True)

        tab_airports = tk.Frame(tabs_right)
        tabs_right.add(tab_airports, text="Airports")
        
        left_sidebar_frame = tk.Frame(main_frame, width=250, bg='#2a2a2a')
        left_sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        tabs_left = ttk.Notebook(left_sidebar_frame)
        tabs_left.pack(fill=tk.BOTH, expand=True)

        tab_routes = tk.Frame(tabs_left)
        tabs_left.add(tab_routes, text="Routes")

        menu_bar = tk.Menu(root)
        root.config(menu=menu_bar)
        
        # Create File menu
        self.file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=self.file_menu)
        #file_menu.add_separator()
        #file_menu.add_command(label="Exit", command=root.quit)

        # Frame for the Panda3D viewport (content area)
        self.viewport_frame = tk.Frame(main_frame, bg='#111111')
        self.viewport_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.label_frame = tk.LabelFrame(self.viewport_frame, text='Viewport', width=1280, height=720)
        self.label_frame.pack(fill=tk.BOTH, expand=True)

        # Create the bottom bar (buttons at the bottom of the viewport)
        bottom_bar_frame = tk.Frame(main_frame, bg='#2a2a2a', height=50)
        bottom_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Add checkbox to show all airports
        var = tk.IntVar()
        self.show_airports_var = var
        self.show_airports_checkbutton = ttk.Checkbutton(tab_airports, text="Show All", variable=var, onvalue=1, offvalue=0)
        self.show_airports_checkbutton.pack(side=tk.TOP)

        # Search box
        search_frame = tk.LabelFrame(tab_airports, bg='#2a2a2a')
        search_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        
        row_frame = tk.Frame(search_frame)
        row_frame.pack(fill=tk.X, pady=5, padx=5)
        
        search_label = tk.Label(row_frame, text="Search")
        search_label.pack(side=tk.LEFT, pady=5, padx=5)
        
        self.search_box = tk.Entry(row_frame, width=20)
        self.search_box.pack(side=tk.RIGHT, padx=5)
        self.search_box.bind("<Button-1>", lambda e: self.search_box.focus_force())
        
        self.result_listbox = tk.Listbox(search_frame, height=7)
        self.result_listbox.pack(fill=tk.X, padx=10, pady=(0, 8))
        
        # Create a new section in the sidebar for Airport Information
        self.airport_info_view = DictView(tab_airports, "Airport Info")

        # Add a new section in the sidebar for Weather Information
        self.weather_info_view = DictView(tab_airports, "Weather")
        
        self.show_weather_var = tk.IntVar()
        self.show_weather_checkbutton = ttk.Checkbutton(tab_airports, text="Show Weather", variable=self.show_weather_var, onvalue=1, offvalue=0)
        self.show_weather_checkbutton.pack(side=tk.TOP, padx=5)
        
        row_frame = tk.Frame(self.airport_info_view.info_frame)
        row_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=5)

        self.add_airport_button = ttk.Button(row_frame, text="Add To Route")
        self.add_airport_button.pack(side=tk.LEFT, padx=10)

        self.remove_airport_button = ttk.Button(row_frame, text="Remove From Route")
        self.remove_airport_button.pack(side=tk.RIGHT, padx=10)
        
        # Add section in left to view routes and markers
        self.route_tree = RouteTree(tab_routes, "Route List")
        
        # Add route new/delete buttons
        row_frame = tk.Frame(tab_routes)
        row_frame.pack(fill=tk.X, pady=5, padx=10)
        self.copy_route_button = ttk.Button(row_frame, text="Copy Current Route")
        self.copy_route_button.pack(side=tk.LEFT)
        self.new_route_button = ttk.Button(row_frame, text="New Route")
        self.new_route_button.pack(side=tk.LEFT)
        self.delete_route_button = ttk.Button(row_frame, text="Delete Route")
        self.delete_route_button.pack(side=tk.LEFT)
        
        #row_frame = tk.Frame(tab_routes)
        #row_frame.pack(fill=tk.X, pady=5, padx=10)
        #self.import_route_button = ttk.Button(row_frame, text="Import")
        #self.import_route_button.pack(side=tk.LEFT)
        #self.export_route_button = ttk.Button(row_frame, text="Export")
        #self.export_route_button.pack(side=tk.LEFT)
            
        # Add a "Compute Route" section to the routes tab
        compute_route_frame = tk.LabelFrame(tab_routes, text="Find Shortest Path", bg='#2a2a2a', padx=10, pady=10)
        compute_route_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        
        annealing_frame = tk.LabelFrame(compute_route_frame, text="Options", bg='#2a2a2a', padx=10, pady=10)
        annealing_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        
        self.heuristic_options = {
            "Annealing": annealing_frame,
            "Nearest Neighbor": None,
            "Brute Force": None
        }
        
        self.selected_heuristic = tk.StringVar()
        self.selected_heuristic.set("Annealing")
        self.heuristic_dropdown = ttk.Combobox(compute_route_frame, textvariable=self.selected_heuristic, values=list(self.heuristic_options.keys()))
        self.heuristic_dropdown.pack(pady=10)
        self.heuristic_dropdown.bind("<<ComboboxSelected>>", self.set_heuristic)

         
        self.init_temp_input = ParamSlider(annealing_frame, "Initial Temperature:", 1, 10000, 1000)
        self.cool_rate_input = ParamSlider(annealing_frame, "Cooling Rate:", 0.9, 0.9999, 0.995)
        self.min_temp_input  = ParamSlider(annealing_frame, "Minimum Temperature:", 1e-5, 1e-2, 1e-3)

        # Compute Route Button
        self.compute_route_button = ttk.Button(compute_route_frame, text="Compute Route")
        self.compute_route_button.pack(side=tk.TOP, pady=10)
        
        # Route Stats
        self.route_stats_view = DictView(tab_routes, "Route Stats")
        
    def search_airports(self, airports):
        query = self.search_box.get().lower().strip()

    
        self.result_listbox.delete(0, tk.END)  # Clear previous results
        self.search_results = []  # Store matches for later use
        
        if len(query) < 2:
            return
    
        for airport in airports.values():
            if (query in airport['icao'].lower() or
                query in airport['iata'].lower() or
                query in airport['name'].lower() or
                query in airport['city'].lower()):
                display_text = f"{airport['icao']} - {airport['name']} ({airport['city']})"
                self.result_listbox.insert(tk.END, display_text)
                self.search_results.append(airport)
                if len(self.search_results) > 100:
                    return
        
        if not self.search_results:
            self.result_listbox.insert(tk.END, "No results found.")
            
    def get_selected_search(self):
        selection = self.result_listbox.curselection()
        if not selection:
            return None
        index = selection[0]
        if index >= len(self.search_results):
            return None
        return self.search_results[index]
        
    def set_heuristic(self, event):
        for panel in self.heuristic_options.values():
            if panel:
                panel.pack_forget()
        new_options = self.heuristic_options[self.selected_heuristic.get()]
        if new_options:
            new_options.pack(fill=tk.BOTH, padx=10, pady=10)
            
            
        
    def update_route_info(self, route):
        self.route_stats_view.view_dict(route.get_stats())
        self.route_tree.update_route_list(route)
