from panda3d.core import CollisionNode, CollisionHandlerQueue, CollisionSphere, CollisionRay, CollisionNode, CollisionTraverser
from panda3d.core import BitMask32, NodePath, Point3
from panda3d.core import GeomNode, Geom, GeomVertexData, GeomVertexWriter, GeomPoints, GeomVertexFormat, Shader
from panda3d.core import AmbientLight, DirectionalLight

from lib.procedural3d.sphere import SphereMaker

import math

class GlobeSimWorld:
    def __init__(self):
        segs = {
            "horizontal": 60,
            "vertical": 30
        }
        self.np = NodePath("world")
        
        sphere_geom = SphereMaker(segments=segs).generate()
        #self.rotate = self.render.attachNewNode('rotate')
        
        self.earth = self.np.attachNewNode(sphere_geom)
        #self.earth.setHpr(, math.radians(180), 0)
        
        self.starmap = self.earth.copy_to(self.np)
        
        self.earth.setScale(1)

        self.starmap.setTwoSided(True)
        self.starmap.setScale(1000)
        
        self.airport_positions = {}
        
        self.collision_handler = CollisionHandlerQueue()
        self.collision_traverser = CollisionTraverser()
        
        self.mouse_ray = CollisionRay()

        # Set up a CollisionNode for the ray
        self.mouse_ray_node = CollisionNode('mouse_ray')
        self.mouse_ray_node.addSolid(self.mouse_ray)
        self.mouse_ray_node.setFromCollideMask(BitMask32.bit(1))
        self.mouse_ray_node_path = NodePath(self.mouse_ray_node)
        
        self.collision_traverser.addCollider(self.mouse_ray_node_path, self.collision_handler)
        
        collision_sphere = CollisionSphere(0, 0, 0, 1.0)  # 1.0 is the radius of the sphere
        
        collision_node = CollisionNode("earth")
        collision_node.addSolid(collision_sphere)
        
        collision_node.setIntoCollideMask(BitMask32.bit(1))
        collision_node.setFromCollideMask(BitMask32.allOff())  # Only collide with ray

        # Create a NodePath for the CollisionNode and attach it to the scene graph
        collision_node_path = self.earth.attachNewNode(collision_node)
        self.collision_traverser.addCollider(collision_node_path, self.collision_handler)
        
        #ambient_light = AmbientLight("ambient_light")
        #ambient_light.setColor((0.5, 0.5, 0.5, 1))
        #self.np.setLight(self.np.attachNewNode(ambient_light))
        #
        #directional_light = DirectionalLight("directional_light")
        #directional_light.setColor((0.8, 0.8, 0.8, 1))
        #dlnp = self.np.attachNewNode(directional_light)
        #self.light = dlnp
        #dlnp.setHpr(120, -30, 0)
        #
        #self.np.setLight(dlnp)

        
    def create_points(self, airports):
        def world_to_3d(latitude, longitude, elevation):
            lat_rad = math.radians(latitude) 
            lon_rad = math.radians(longitude) + math.radians(180)
            
            x = (1 + elevation) * math.cos(lat_rad) * math.cos(lon_rad)
            y = (1 + elevation) * math.cos(lat_rad) * math.sin(lon_rad)
            z = (1 + elevation) * math.sin(lat_rad)
            
            return Point3(x, y, z)
        
        vertex_data = GeomVertexData('points', GeomVertexFormat.get_v3(), Geom.UH_static)
        vertex_writer = GeomVertexWriter(vertex_data, 'vertex')
        for airport in airports.values():
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
        self.airports_np.reparent_to(self.np)
        
    def find_airport(self):
        # Traverse the collision space
        self.collision_traverser.traverse(self.np)

        # Check if there are any collisions
        if self.collision_handler.getNumEntries() > 0:
            entry = self.collision_handler.getEntry(0)
            col_point = entry.getSurfacePoint(self.np)  # Get the point of collision
            closest_point = min(self.airport_positions.keys(), key=lambda point: (point - col_point).lengthSquared())
            
            return self.airport_positions[closest_point]
        else:
            return None
        