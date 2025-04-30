from panda3d.core import NodePath, TransparencyAttrib, LineSegs, Point3
import math

class Route:
    routes = 0
    
    def __init__(self, name=None):
        self.np = NodePath("route")
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
        marker.route = self
        self.markers.append(marker)
        marker.np.reparentTo(self.np)
        return marker
        
    def remove_airport(self, airport):
        for marker in list(self.markers):
            if marker.airport == airport:
                self.markers.remove(marker)
                self.set_path(None)
                return marker
        
    def get_airports(self):
        return [marker.airport for marker in self.markers]
    
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
    
    def delete(self):
        for marker in list(self.markers):
            marker.delete()
        self.np.removeNode()
        del self
    
    def set_path(self, indices):
        """
        Draws a curved path between the markers by calculating the great-circle route.
        Also rearranges the treeview markers to match the order of the path.
        """

                
        self.path = indices
        
        if self.lines_np:
            self.lines_np.removeNode()
        
        if not indices or len(indices) < 2:
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
            
        self.route = None
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