import pygame
import sys
import os
import math

# --- Constants ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
DARK_GRAY = (30, 30, 30)
PANEL_BG = (40, 40, 40)
BORDER_COLOR = (60, 60, 60)
TEXT_COLOR = (220, 220, 220)
ACCENT_COLOR = (100, 150, 255)
HOVER_COLOR = (80, 80, 80)
SELECTION_COLOR = (255, 255, 0)

# Layout
PROJECT_WIDTH = 250
INSPECTOR_WIDTH = 300
CONSOLE_HEIGHT = 150
MENU_HEIGHT = 40

# --- Core Game Systems ---

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
        
        # Draw selection outline
        if self.selected:
            pygame.draw.circle(surface, SELECTION_COLOR, 
                             (int(self.transform.position.x), int(self.transform.position.y)), 
                             25, 2)
        
        # Draw the object (simple circle for now)
        pygame.draw.circle(surface, ACCENT_COLOR, 
                         (int(self.transform.position.x), int(self.transform.position.y)), 
                         20)
        
        # Draw name
        font = pygame.font.Font(None, 16)
        text = font.render(self.name, True, TEXT_COLOR)
        surface.blit(text, (self.transform.position.x - 30, self.transform.position.y + 25))

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
        """Get object at screen position (simple circle collision)"""
        for obj in reversed(self.game_objects):  # Check from top to bottom
            if obj.visible:
                distance = math.sqrt((x - obj.transform.position.x)**2 + (y - obj.transform.position.y)**2)
                if distance <= 20:  # Object radius
                    return obj
        return None
    
    def update(self):
        for obj in self.game_objects:
            obj.update()
    
    def draw(self, surface):
        for obj in self.game_objects:
            obj.draw(surface)

# --- UI System ---

class UIElement:
    """Base class for all UI elements"""
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.hovered = False
        self.focused = False
        
    def handle_event(self, event):
        return False
        
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        
    def draw(self, surface):
        pass

class Button(UIElement):
    """Simple button with text"""
    def __init__(self, x, y, width, height, text, action=None):
        super().__init__(x, y, width, height)
        self.text = text
        self.action = action
        self.pressed = False
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            self.pressed = True
            return True
        elif event.type == pygame.MOUSEBUTTONUP and self.pressed:
            self.pressed = False
            if self.action:
                self.action()
            return True
        return False
        
    def draw(self, surface):
        # Background
        color = HOVER_COLOR if self.hovered else PANEL_BG
        if self.pressed:
            color = ACCENT_COLOR
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BORDER_COLOR, self.rect, 2)
        
        # Text
        font = pygame.font.Font(None, 20)
        text_surface = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

class Panel(UIElement):
    """Panel container for UI elements"""
    def __init__(self, x, y, width, height, title=""):
        super().__init__(x, y, width, height)
        self.title = title
        self.elements = []
        
    def add_element(self, element):
        self.elements.append(element)
        
    def handle_event(self, event):
        for element in self.elements:
            if element.handle_event(event):
                return True
        return False
        
    def update(self, mouse_pos):
        super().update(mouse_pos)
        for element in self.elements:
            element.update(mouse_pos)
            
    def draw(self, surface):
        # Panel background
        pygame.draw.rect(surface, PANEL_BG, self.rect)
        pygame.draw.rect(surface, BORDER_COLOR, self.rect, 2)
        
        # Title
        if self.title:
            font = pygame.font.Font(None, 24)
            text_surface = font.render(self.title, True, TEXT_COLOR)
            surface.blit(text_surface, (self.rect.x + 10, self.rect.y + 10))
            
        # Draw elements
        for element in self.elements:
            element.draw(surface)

class InspectorPanel(Panel):
    """Inspector panel that shows properties of selected objects"""
    def __init__(self, x, y, width, height, scene):
        super().__init__(x, y, width, height, "Inspector")
        self.scene = scene
        self.font = pygame.font.Font(None, 18)
        self.small_font = pygame.font.Font(None, 16)
        
    def draw(self, surface):
        # Draw panel background and title
        super().draw(surface)
        
        # Check if we have a selected object
        if self.scene.selected_object:
            self.draw_object_inspector(surface, self.scene.selected_object)
        else:
            self.draw_no_selection(surface)
            
    def draw_no_selection(self, surface):
        """Draw message when no object is selected"""
        text = self.font.render("No object selected", True, (120, 120, 120))
        surface.blit(text, (self.rect.x + 15, self.rect.y + 50))
        
    def draw_object_inspector(self, surface, game_object):
        """Draw inspector for the selected game object"""
        y_offset = 50
        line_height = 25
        
        # Object name
        name_text = self.font.render(f"Name: {game_object.name}", True, TEXT_COLOR)
        surface.blit(name_text, (self.rect.x + 15, self.rect.y + y_offset))
        y_offset += line_height + 10
        
        # Transform section header
        transform_header = self.font.render("Transform", True, ACCENT_COLOR)
        surface.blit(transform_header, (self.rect.x + 15, self.rect.y + y_offset))
        y_offset += line_height
        
        # Draw separator line
        pygame.draw.line(surface, BORDER_COLOR, 
                        (self.rect.x + 15, self.rect.y + y_offset - 5),
                        (self.rect.x + self.rect.width - 15, self.rect.y + y_offset - 5))
        
        # Position
        pos_text = self.small_font.render("Position:", True, TEXT_COLOR)
        surface.blit(pos_text, (self.rect.x + 20, self.rect.y + y_offset))
        y_offset += 20
        
        pos_x_text = self.small_font.render(f"X: {game_object.transform.position.x:.1f}", True, (200, 200, 200))
        pos_y_text = self.small_font.render(f"Y: {game_object.transform.position.y:.1f}", True, (200, 200, 200))
        surface.blit(pos_x_text, (self.rect.x + 25, self.rect.y + y_offset))
        surface.blit(pos_y_text, (self.rect.x + 140, self.rect.y + y_offset))
        y_offset += line_height
        
        # Rotation
        rot_text = self.small_font.render("Rotation:", True, TEXT_COLOR)
        surface.blit(rot_text, (self.rect.x + 20, self.rect.y + y_offset))
        y_offset += 20
        
        rot_value_text = self.small_font.render(f"Z: {game_object.transform.rotation:.1f}°", True, (200, 200, 200))
        surface.blit(rot_value_text, (self.rect.x + 25, self.rect.y + y_offset))
        y_offset += line_height
        
        # Scale
        scale_text = self.small_font.render("Scale:", True, TEXT_COLOR)
        surface.blit(scale_text, (self.rect.x + 20, self.rect.y + y_offset))
        y_offset += 20
        
        scale_x_text = self.small_font.render(f"X: {game_object.transform.scale.x:.2f}", True, (200, 200, 200))
        scale_y_text = self.small_font.render(f"Y: {game_object.transform.scale.y:.2f}", True, (200, 200, 200))
        surface.blit(scale_x_text, (self.rect.x + 25, self.rect.y + y_offset))
        surface.blit(scale_y_text, (self.rect.x + 140, self.rect.y + y_offset))

class Console:
    """Console system for displaying messages"""
    def __init__(self):
        self.messages = []
        self.max_messages = 20
        
    def log(self, message):
        """Add a message to the console"""
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
        print(message)  # Also print to terminal for debugging
        
    def clear(self):
        """Clear all messages"""
        self.messages.clear()
        
    def get_messages(self):
        """Get all messages"""
        return self.messages

class HierarchyItem:
    """Individual item in the hierarchy list"""
    def __init__(self, game_object, x, y, width, height):
        self.game_object = game_object
        self.rect = pygame.Rect(x, y, width, height)
        self.hovered = False
        self.selected = False
        
    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(mouse_pos):
            return True
        return False
        
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        self.selected = self.game_object.selected
        
    def draw(self, surface):
        # Background color based on state
        if self.selected:
            color = ACCENT_COLOR
        elif self.hovered:
            color = HOVER_COLOR
        else:
            color = PANEL_BG
            
        pygame.draw.rect(surface, color, self.rect)
        
        # Object name
        font = pygame.font.Font(None, 18)
        text_surface = font.render(self.game_object.name, True, TEXT_COLOR)
        surface.blit(text_surface, (self.rect.x + 20, self.rect.y + 5))
        
        # Draw icon (simple circle)
        pygame.draw.circle(surface, ACCENT_COLOR, (self.rect.x + 10, self.rect.y + self.rect.height // 2), 4)

class HierarchyPanel(Panel):
    """Hierarchy panel that shows all scene objects in a list"""
    def __init__(self, x, y, width, height, scene):
        super().__init__(x, y, width, height, "Hierarchy")
        self.scene = scene
        self.items = []
        self.item_height = 25
        self.scroll_offset = 0
        
    def update_items(self):
        """Update the hierarchy items list"""
        self.items.clear()
        start_y = self.rect.y + 35  # Below title
        
        for i, game_object in enumerate(self.scene.game_objects):
            item_y = start_y + i * self.item_height
            item = HierarchyItem(game_object, self.rect.x + 5, item_y, 
                               self.rect.width - 10, self.item_height)
            self.items.append(item)
            
    def handle_event(self, event):
        # Handle parent panel events first
        if super().handle_event(event):
            return True
            
        # Handle hierarchy item clicks
        mouse_pos = pygame.mouse.get_pos()
        for item in self.items:
            if item.handle_event(event, mouse_pos):
                self.scene.select_object(item.game_object)
                return True
        return False
        
    def update(self, mouse_pos):
        super().update(mouse_pos)
        self.update_items()  # Update items every frame
        
        for item in self.items:
            item.update(mouse_pos)
            
    def draw(self, surface):
        # Draw panel background and title
        super().draw(surface)
        
        # Draw hierarchy items
        for item in self.items:
            # Only draw items that are visible in the panel
            if item.rect.y >= self.rect.y and item.rect.y <= self.rect.y + self.rect.height:
                item.draw(surface)

class ConsolePanel(Panel):
    """Console panel that displays console messages"""
    def __init__(self, x, y, width, height, console):
        super().__init__(x, y, width, height, "Console")
        self.console = console
        self.scroll_offset = 0
        
    def draw(self, surface):
        # Draw panel background and title
        super().draw(surface)
        
        # Draw console messages
        font = pygame.font.Font(None, 18)
        line_height = 20
        start_y = self.rect.y + 35  # Below title
        
        messages = self.console.get_messages()
        for i, message in enumerate(messages[-10:]):  # Show last 10 messages
            text_surface = font.render(message, True, TEXT_COLOR)
            surface.blit(text_surface, (self.rect.x + 10, start_y + i * line_height))

class SceneView(UIElement):
    """Main scene view where the game is rendered"""
    def __init__(self, x, y, width, height, scene):
        super().__init__(x, y, width, height)
        self.surface = pygame.Surface((width, height))
        self.scene = scene
        self.camera_x = 0
        self.camera_y = 0
        self.grid_size = 20
        self.show_grid = True
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            # Convert screen coordinates to scene coordinates
            mouse_x, mouse_y = pygame.mouse.get_pos()
            scene_x = mouse_x - self.rect.x
            scene_y = mouse_y - self.rect.y
            
            # Try to select object at mouse position
            clicked_object = self.scene.get_object_at_position(scene_x, scene_y)
            self.scene.select_object(clicked_object)
            return True
        return False
        
    def draw(self, surface):
        # Clear scene surface
        self.surface.fill(DARK_GRAY)
        
        # Draw grid
        if self.show_grid:
            self.draw_grid()
            
        # Draw scene objects
        self.scene.draw(self.surface)
        
        # Draw border
        pygame.draw.rect(self.surface, BORDER_COLOR, (0, 0, self.rect.width, self.rect.height), 2)
        
        # Blit to main surface
        surface.blit(self.surface, self.rect)
        
    def draw_grid(self):
        """Draw grid lines"""
        for x in range(0, self.rect.width, self.grid_size):
            pygame.draw.line(self.surface, (50, 50, 50), (x, 0), (x, self.rect.height))
        for y in range(0, self.rect.height, self.grid_size):
            pygame.draw.line(self.surface, (50, 50, 50), (0, y), (self.rect.width, y))

class PygameEditor:
    """Main editor class"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pygame Editor")
        self.clock = pygame.time.Clock()
        
        # Create console system
        self.console = Console()
        
        # Create scene
        self.scene = Scene()
        
        # Create panels
        self.create_panels()
        
        # Editor state
        self.running = True
        self.object_counter = 1
        
        # Add some sample objects
        self.create_sample_objects()
        
        # Log startup message
        self.console.log("Pygame Editor started")
        
    def create_panels(self):
        """Create and setup all UI panels"""
        # Hierarchy Panel (instead of Project Explorer)
        self.hierarchy_panel = HierarchyPanel(0, MENU_HEIGHT, PROJECT_WIDTH, 
                                            SCREEN_HEIGHT - MENU_HEIGHT - CONSOLE_HEIGHT, self.scene)
        
        # Scene View
        scene_x = PROJECT_WIDTH
        scene_y = MENU_HEIGHT
        scene_width = SCREEN_WIDTH - PROJECT_WIDTH - INSPECTOR_WIDTH
        scene_height = SCREEN_HEIGHT - MENU_HEIGHT - CONSOLE_HEIGHT
        self.scene_view = SceneView(scene_x, scene_y, scene_width, scene_height, self.scene)
        
        # Inspector Panel
        inspector_x = SCREEN_WIDTH - INSPECTOR_WIDTH
        inspector_y = MENU_HEIGHT
        inspector_width = INSPECTOR_WIDTH
        inspector_height = SCREEN_HEIGHT - MENU_HEIGHT - CONSOLE_HEIGHT
        self.inspector_panel = InspectorPanel(inspector_x, inspector_y, inspector_width, 
                                            inspector_height, self.scene)
        
        # Console Panel
        self.console_panel = ConsolePanel(0, SCREEN_HEIGHT - CONSOLE_HEIGHT, 
                                         SCREEN_WIDTH, CONSOLE_HEIGHT, self.console)
        
        # Add plus button to menu bar
        self.add_button = Button(150, 5, 30, 30, "+", self.add_object)
        
    def create_sample_objects(self):
        """Create some sample objects for testing"""
        # Create a few sample objects
        obj1 = GameObject("Player")
        obj1.transform.position = Vector2(200, 200)
        self.scene.add_object(obj1)
        
        obj2 = GameObject("Enemy")
        obj2.transform.position = Vector2(400, 300)
        self.scene.add_object(obj2)
        
        obj3 = GameObject("Item")
        obj3.transform.position = Vector2(300, 150)
        self.scene.add_object(obj3)
        
    def new_scene(self):
        """Create a new scene"""
        self.console.log("Creating new scene...")
        
    def save_scene(self):
        """Save current scene"""
        self.console.log("Saving scene...")
        
    def add_object(self):
        """Add new object to scene"""
        new_obj = GameObject(f"GameObject_{self.object_counter}")
        new_obj.transform.position = Vector2(100, 100)
        self.scene.add_object(new_obj)
        self.object_counter += 1
        self.console.log(f"Added {new_obj.name}")
        
    def delete_object(self):
        """Delete selected object"""
        if self.scene.selected_object:
            obj_name = self.scene.selected_object.name
            self.scene.game_objects.remove(self.scene.selected_object)
            self.scene.select_object(None)
            self.console.log(f"Deleted {obj_name}")
        else:
            self.console.log("No object selected")
        
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_DELETE:
                    # Delete selected object with Delete key
                    self.delete_object()
                    
            # Handle UI events
            mouse_pos = pygame.mouse.get_pos()
            self.add_button.handle_event(event)  # Handle add button in menu bar
            self.hierarchy_panel.handle_event(event)  # Handle hierarchy clicks
            self.scene_view.handle_event(event)  # Handle scene view clicks
            self.inspector_panel.handle_event(event)
            self.console_panel.handle_event(event)
            
    def update(self):
        """Update editor state"""
        mouse_pos = pygame.mouse.get_pos()
        self.add_button.update(mouse_pos)  # Update add button
        self.hierarchy_panel.update(mouse_pos)
        self.scene_view.update(mouse_pos)
        self.inspector_panel.update(mouse_pos)
        self.console_panel.update(mouse_pos)
        
        # Update scene
        self.scene.update()
        
    def draw(self):
        """Draw the editor"""
        # Clear screen
        self.screen.fill(DARK_GRAY)
        
        # Draw menu bar
        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, SCREEN_WIDTH, MENU_HEIGHT))
        pygame.draw.rect(self.screen, BORDER_COLOR, (0, 0, SCREEN_WIDTH, MENU_HEIGHT), 2)
        
        # Draw menu text
        font = pygame.font.Font(None, 24)
        text = font.render("Pygame Editor", True, TEXT_COLOR)
        self.screen.blit(text, (10, 10))
        
        # Draw add button in menu bar
        self.add_button.draw(self.screen)
        
        # Draw panels
        self.hierarchy_panel.draw(self.screen)
        self.scene_view.draw(self.screen)
        self.inspector_panel.draw(self.screen)
        self.console_panel.draw(self.screen)
        
        # Update display
        pygame.display.flip()
        
    def run(self):
        """Main editor loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    editor = PygameEditor()
    editor.run()
