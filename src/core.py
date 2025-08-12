import pygame
import math

class Vector2:
    """Simple 2D vector class"""
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
    
    def __str__(self):
        return f"({self.x}, {self.y})"

class Component:
    """Base class for all components"""
    def __init__(self, game_object):
        self.game_object = game_object
    
    def update(self):
        pass
    
    def draw(self, surface):
        pass

class Transform(Component):
    """Transform component for position, rotation, scale"""
    def __init__(self, game_object):
        super().__init__(game_object)
        self.position = Vector2(0, 0)
        self.rotation = 0  # degrees
        self.scale = Vector2(1, 1)
    
    def __str__(self):
        return f"Transform(pos={self.position}, rot={self.rotation}, scale={self.scale})"

class GameObject:
    """Base class for all game objects"""
    def __init__(self, name="GameObject"):
        self.name = name
        self.transform = Transform(self)
        self.components = [self.transform]
        self.selected = False
        self.visible = True
        self.children = []
        self.parent = None
    
    def add_component(self, component):
        self.components.append(component)
    
    def get_component(self, component_type):
        for component in self.components:
            if isinstance(component, component_type):
                return component
        return None
    
    def update(self):
        for component in self.components:
            component.update()
    
    def draw(self, surface):
        if not self.visible:
            return
        
        # Import colors from utils to avoid circular imports
        from utils import Colors
        
        # Calculate scaled radius
        base_radius = 32  # 32px diameter
        scale_factor = max(self.transform.scale.x, self.transform.scale.y)
        scaled_radius = int(base_radius * scale_factor / 2)  # Convert diameter to radius
        
        # Draw selection outline
        if self.selected:
            outline_radius = scaled_radius + 5
            pygame.draw.circle(surface, Colors.SELECTION_COLOR, 
                             (int(self.transform.position.x), int(self.transform.position.y)), 
                             outline_radius, 2)
        
        # For rotation visualization, we'll draw a simple shape that shows rotation
        if self.transform.rotation != 0:
            # Draw a rotated rectangle to show rotation
            rect_width = scaled_radius * 2
            rect_height = scaled_radius * 2
            
            # Create points for a rectangle centered at origin
            points = [
                (-rect_width//2, -rect_height//2),
                (rect_width//2, -rect_height//2),
                (rect_width//2, rect_height//2),
                (-rect_width//2, rect_height//2)
            ]
            
            # Rotate points
            angle_rad = math.radians(self.transform.rotation)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            
            rotated_points = []
            for px, py in points:
                rx = px * cos_a - py * sin_a + self.transform.position.x
                ry = px * sin_a + py * cos_a + self.transform.position.y
                rotated_points.append((int(rx), int(ry)))
            
            # Draw rotated rectangle
            pygame.draw.polygon(surface, Colors.ACCENT_COLOR, rotated_points)
            
            # Draw direction indicator (line from center to front)
            front_x = int(self.transform.position.x + scaled_radius * cos_a)
            front_y = int(self.transform.position.y + scaled_radius * sin_a)
            pygame.draw.line(surface, (255, 255, 255), 
                           (int(self.transform.position.x), int(self.transform.position.y)),
                           (front_x, front_y), 3)
        else:
            # Draw simple circle when no rotation
            pygame.draw.circle(surface, Colors.ACCENT_COLOR, 
                             (int(self.transform.position.x), int(self.transform.position.y)), 
                             scaled_radius)
        
        # Draw center point
        pygame.draw.circle(surface, (255, 255, 255), 
                         (int(self.transform.position.x), int(self.transform.position.y)), 2)
        
        # Draw name
        font = pygame.font.Font(None, 16)
        text = font.render(self.name, True, Colors.TEXT_COLOR)
        text_x = self.transform.position.x - text.get_width() // 2
        text_y = self.transform.position.y + scaled_radius + 5
        surface.blit(text, (int(text_x), int(text_y)))

class Scene:
    """Scene management system"""
    def __init__(self):
        self.game_objects = []
        self.selected_object = None
    
    def add_object(self, game_object):
        self.game_objects.append(game_object)
        return game_object
    
    def select_object(self, game_object):
        # Deselect previous object
        if self.selected_object:
            self.selected_object.selected = False
        
        # Select new object
        self.selected_object = game_object
        if game_object:
            game_object.selected = True
    
    def get_object_at_position(self, x, y):
        """Get object at screen position (ellipse collision considering scale)"""
        for obj in reversed(self.game_objects):  # Check from top to bottom
            if obj.visible:
                # Calculate scaled dimensions  
                base_radius = 32  # 32px diameter
                scale_x = max(0.01, abs(obj.transform.scale.x))
                scale_y = max(0.01, abs(obj.transform.scale.y))
                width = base_radius * scale_x / 2  # Convert diameter to radius for collision
                height = base_radius * scale_y / 2  # Convert diameter to radius for collision
                
                # Check ellipse collision
                dx = (x - obj.transform.position.x) / width
                dy = (y - obj.transform.position.y) / height
                if dx*dx + dy*dy <= 1.0:  # Inside ellipse
                    return obj
        return None
    
    def update(self):
        for obj in self.game_objects:
            obj.update()
    
    def draw(self, surface):
        for obj in self.game_objects:
            obj.draw(surface)
