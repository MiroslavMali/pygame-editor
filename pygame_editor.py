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

class EditorCamera:
    """Camera system for the scene view with pan and zoom capabilities"""
    def __init__(self, viewport_width, viewport_height):
        self.position = Vector2(0, 0)  # Camera world position
        self.zoom = 1.0               # Zoom level (1.0 = normal, 2.0 = 2x zoom)
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.viewport_center = Vector2(viewport_width / 2, viewport_height / 2)
        self.viewport_size = Vector2(viewport_width, viewport_height)
        
    def world_to_screen(self, world_pos):
        """Convert world coordinates to screen coordinates"""
        # Calculate relative position from camera
        relative_x = world_pos.x - self.position.x
        relative_y = world_pos.y - self.position.y
        
        # Apply zoom and translate to screen center
        screen_x = relative_x * self.zoom + self.viewport_center.x
        screen_y = relative_y * self.zoom + self.viewport_center.y
        
        return Vector2(screen_x, screen_y)
    
    def screen_to_world(self, screen_pos):
        """Convert screen coordinates to world coordinates"""
        # Calculate relative position from screen center
        relative_x = (screen_pos.x - self.viewport_center.x) / self.zoom
        relative_y = (screen_pos.y - self.viewport_center.y) / self.zoom
        
        # Add camera position to get world coordinates
        world_x = relative_x + self.position.x
        world_y = relative_y + self.position.y
        
        return Vector2(world_x, world_y)
    
    def pan(self, delta_x, delta_y):
        """Pan the camera by screen pixels"""
        # Convert screen delta to world delta
        world_delta_x = delta_x / self.zoom
        world_delta_y = delta_y / self.zoom
        
        self.position.x -= world_delta_x
        self.position.y -= world_delta_y
    
    def zoom_at_point(self, screen_point, zoom_factor):
        """Zoom in/out while keeping the screen point at the same position"""
        # Get world position before zoom
        world_point_before = self.screen_to_world(screen_point)
        
        # Apply zoom (with limits)
        new_zoom = self.zoom * zoom_factor
        self.zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
        
        # Get world position after zoom
        world_point_after = self.screen_to_world(screen_point)
        
        # Adjust camera position to keep the point in the same place
        # (Reversed the direction to fix the inverted zoom behavior)
        self.position.x -= world_point_after.x - world_point_before.x
        self.position.y -= world_point_after.y - world_point_before.y
    
    def reset_view(self):
        """Reset camera to origin with normal zoom"""
        self.position = Vector2(0, 0)
        self.zoom = 1.0

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
        
        # Calculate scaled radius
        base_radius = 32  # 32px diameter
        scale_factor = max(self.transform.scale.x, self.transform.scale.y)
        scaled_radius = int(base_radius * scale_factor / 2)  # Convert diameter to radius
        
        # Draw selection outline
        if self.selected:
            outline_radius = scaled_radius + 5
            pygame.draw.circle(surface, SELECTION_COLOR, 
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
            import math
            angle_rad = math.radians(self.transform.rotation)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            
            rotated_points = []
            for px, py in points:
                rx = px * cos_a - py * sin_a + self.transform.position.x
                ry = px * sin_a + py * cos_a + self.transform.position.y
                rotated_points.append((int(rx), int(ry)))
            
            # Draw rotated rectangle
            pygame.draw.polygon(surface, ACCENT_COLOR, rotated_points)
            
            # Draw direction indicator (line from center to front)
            front_x = int(self.transform.position.x + scaled_radius * cos_a)
            front_y = int(self.transform.position.y + scaled_radius * sin_a)
            pygame.draw.line(surface, (255, 255, 255), 
                           (int(self.transform.position.x), int(self.transform.position.y)),
                           (front_x, front_y), 3)
        else:
            # Draw simple circle when no rotation
            pygame.draw.circle(surface, ACCENT_COLOR, 
                             (int(self.transform.position.x), int(self.transform.position.y)), 
                             scaled_radius)
        
        # Draw center point
        pygame.draw.circle(surface, (255, 255, 255), 
                         (int(self.transform.position.x), int(self.transform.position.y)), 2)
        
        # Draw name
        font = pygame.font.Font(None, 16)
        text = font.render(self.name, True, TEXT_COLOR)
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

class TextInput:
    """Text input field with click-to-activate, pulsing, and Enter/Escape handling"""
    def __init__(self, x, y, width, height, initial_value, callback, property_path):
        self.rect = pygame.Rect(x, y, width, height)
        self.value = str(initial_value)
        self.display_value = self.value
        self.callback = callback
        self.property_path = property_path
        self.is_active = False
        self.cursor_pos = len(self.value)
        self.selection_start = 0
        self.selection_end = 0
        self.pulse_time = 0.0
        self.blink_time = 0.0
        self.font = pygame.font.Font(None, 16)
        self.hovered = False
        
    def activate(self):
        """Activate input field and select all text"""
        self.is_active = True
        self.selection_start = 0
        self.selection_end = len(self.value)
        self.cursor_pos = len(self.value)
        
    def deactivate(self):
        """Deactivate input field"""
        self.is_active = False
        self.selection_start = 0
        self.selection_end = 0
        
    def confirm_value(self):
        """Confirm the current value and call callback"""
        try:
            # Try to convert to float for numeric values
            numeric_value = float(self.value)
            self.callback(self.property_path, numeric_value)
            self.display_value = self.value
            self.deactivate()
            return True
        except ValueError:
            # Invalid numeric input, revert to display value
            self.value = self.display_value
            self.cursor_pos = len(self.value)
            return False
            
    def cancel_input(self):
        """Cancel input and revert to original value"""
        self.value = self.display_value
        self.cursor_pos = len(self.value)
        self.deactivate()
        
    def handle_event(self, event):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_x, mouse_y)
        
        if not self.hovered and event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_active:
                self.deactivate()
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hovered:
            self.activate()
            return True
            
        if self.is_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                self.confirm_value()
                return True
            elif event.key == pygame.K_ESCAPE:
                self.cancel_input()
                return True
            elif event.key == pygame.K_BACKSPACE:
                if self.selection_start != self.selection_end:
                    # Delete selection
                    start = min(self.selection_start, self.selection_end)
                    end = max(self.selection_start, self.selection_end)
                    self.value = self.value[:start] + self.value[end:]
                    self.cursor_pos = start
                    self.selection_start = self.selection_end = start
                elif self.cursor_pos > 0:
                    # Delete character before cursor
                    self.value = self.value[:self.cursor_pos-1] + self.value[self.cursor_pos:]
                    self.cursor_pos -= 1
                return True
            elif event.key == pygame.K_DELETE:
                if self.selection_start != self.selection_end:
                    # Delete selection
                    start = min(self.selection_start, self.selection_end)
                    end = max(self.selection_start, self.selection_end)
                    self.value = self.value[:start] + self.value[end:]
                    self.cursor_pos = start
                    self.selection_start = self.selection_end = start
                elif self.cursor_pos < len(self.value):
                    # Delete character after cursor
                    self.value = self.value[:self.cursor_pos] + self.value[self.cursor_pos+1:]
                return True
            elif event.key == pygame.K_LEFT:
                if event.mod & pygame.KMOD_SHIFT:
                    # Extend selection
                    if self.selection_start == self.selection_end:
                        self.selection_start = self.cursor_pos
                    self.cursor_pos = max(0, self.cursor_pos - 1)
                    self.selection_end = self.cursor_pos
                else:
                    # Move cursor
                    self.cursor_pos = max(0, self.cursor_pos - 1)
                    self.selection_start = self.selection_end = self.cursor_pos
                return True
            elif event.key == pygame.K_RIGHT:
                if event.mod & pygame.KMOD_SHIFT:
                    # Extend selection
                    if self.selection_start == self.selection_end:
                        self.selection_start = self.cursor_pos
                    self.cursor_pos = min(len(self.value), self.cursor_pos + 1)
                    self.selection_end = self.cursor_pos
                else:
                    # Move cursor
                    self.cursor_pos = min(len(self.value), self.cursor_pos + 1)
                    self.selection_start = self.selection_end = self.cursor_pos
                return True
            elif event.key == pygame.K_HOME:
                if event.mod & pygame.KMOD_SHIFT:
                    if self.selection_start == self.selection_end:
                        self.selection_start = self.cursor_pos
                    self.cursor_pos = 0
                    self.selection_end = self.cursor_pos
                else:
                    self.cursor_pos = 0
                    self.selection_start = self.selection_end = self.cursor_pos
                return True
            elif event.key == pygame.K_END:
                if event.mod & pygame.KMOD_SHIFT:
                    if self.selection_start == self.selection_end:
                        self.selection_start = self.cursor_pos
                    self.cursor_pos = len(self.value)
                    self.selection_end = self.cursor_pos
                else:
                    self.cursor_pos = len(self.value)
                    self.selection_start = self.selection_end = self.cursor_pos
                return True
            elif event.key == pygame.K_a and event.mod & pygame.KMOD_CTRL:
                # Select all
                self.selection_start = 0
                self.selection_end = len(self.value)
                self.cursor_pos = len(self.value)
                return True
            elif event.unicode and event.unicode.isprintable():
                # Insert character
                if self.selection_start != self.selection_end:
                    # Replace selection
                    start = min(self.selection_start, self.selection_end)
                    end = max(self.selection_start, self.selection_end)
                    self.value = self.value[:start] + event.unicode + self.value[end:]
                    self.cursor_pos = start + 1
                    self.selection_start = self.selection_end = self.cursor_pos
                else:
                    # Insert at cursor
                    self.value = self.value[:self.cursor_pos] + event.unicode + self.value[self.cursor_pos:]
                    self.cursor_pos += 1
                return True
                
        return False
        
    def update(self, dt):
        """Update pulsing and blinking effects"""
        if self.is_active:
            self.pulse_time += dt
            self.blink_time += dt
            
    def draw(self, surface):
        # Calculate colors based on state
        if self.is_active:
            # Pulsing effect when active
            pulse_intensity = 0.5 + 0.5 * math.sin(self.pulse_time * 8)
            bg_color = (int(40 + pulse_intensity * 20), int(60 + pulse_intensity * 30), int(100 + pulse_intensity * 40))
            border_color = (100, 150, 255)
        elif self.hovered:
            bg_color = (50, 50, 50)
            border_color = (120, 120, 120)
        else:
            bg_color = (35, 35, 35)
            border_color = (80, 80, 80)
            
        # Draw background
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 1)
        
        # Draw text
        text_surface = self.font.render(self.value, True, TEXT_COLOR)
        text_rect = text_surface.get_rect()
        text_rect.centery = self.rect.centery
        text_rect.x = self.rect.x + 5
        
        # Clip text to input area
        clip_rect = pygame.Rect(self.rect.x + 3, self.rect.y + 1, self.rect.width - 6, self.rect.height - 2)
        surface.set_clip(clip_rect)
        
        # Draw selection background
        if self.is_active and self.selection_start != self.selection_end:
            start_pos = min(self.selection_start, self.selection_end)
            end_pos = max(self.selection_start, self.selection_end)
            
            # Calculate pixel positions
            before_text = self.value[:start_pos]
            selection_text = self.value[start_pos:end_pos]
            
            before_width = self.font.size(before_text)[0] if before_text else 0
            selection_width = self.font.size(selection_text)[0] if selection_text else 0
            
            selection_rect = pygame.Rect(
                text_rect.x + before_width,
                text_rect.y,
                selection_width,
                text_rect.height
            )
            pygame.draw.rect(surface, (100, 100, 200), selection_rect)
            
        # Draw text
        surface.blit(text_surface, text_rect)
        
        # Draw cursor
        if self.is_active and (self.blink_time % 1.0) < 0.5:
            cursor_text = self.value[:self.cursor_pos]
            cursor_width = self.font.size(cursor_text)[0] if cursor_text else 0
            cursor_x = text_rect.x + cursor_width
            pygame.draw.line(surface, TEXT_COLOR, 
                           (cursor_x, text_rect.y + 2), 
                           (cursor_x, text_rect.y + text_rect.height - 2), 1)
        
        surface.set_clip(None)

class DragLabel:
    """Draggable label for quick value adjustments"""
    def __init__(self, x, y, width, height, text, callback, property_path, scene, step=1.0):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.property_path = property_path
        self.scene = scene
        self.step = step
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_value = 0.0
        self.hovered = False
        self.font = pygame.font.Font(None, 16)
        
    def handle_event(self, event):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_x, mouse_y)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hovered:
            self.is_dragging = True
            self.drag_start_x = mouse_x
            self.drag_start_value = self.get_current_value()
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEWE)
            return True
            
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging:
                self.is_dragging = False
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                return True
                
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            total_distance = mouse_x - self.drag_start_x
            new_value = self.drag_start_value + (total_distance * self.step)
            
            # Hard limit for scale values
            if "scale" in self.property_path.lower():
                new_value = max(0.01, new_value)
                
            self.callback(self.property_path, new_value)
            return True
            
        return False
        
    def get_current_value(self):
        """Get current value from the object"""
        if self.scene.selected_object:
            try:
                obj = self.scene.selected_object
                path_parts = self.property_path.split('.')
                target = obj
                for part in path_parts:
                    target = getattr(target, part)
                return float(target)
            except:
                return 0.0
        return 0.0
        
    def draw(self, surface):
        # Change cursor on hover
        if self.hovered and not self.is_dragging:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEWE)
        elif not self.hovered and not self.is_dragging:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            
        # Color based on state
        if self.is_dragging:
            color = (100, 150, 255)  # Blue when dragging
        elif self.hovered:
            color = (180, 180, 180)  # Light gray on hover
        else:
            color = TEXT_COLOR  # Normal color
            
        # Draw text
        text_surface = self.font.render(self.text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = self.rect.center
        surface.blit(text_surface, text_rect)

class DragField:
    """Draggable value field for the inspector"""
    def __init__(self, x, y, width, height, label, game_object, property_path, step=1.0):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.game_object = game_object
        self.property_path = property_path  # e.g., "transform.position.x"
        self.step = step
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_value = 0.0
        self.hovered = False
        
    def get_value(self):
        """Get value using property path"""
        try:
            obj = self.game_object
            for prop in self.property_path.split('.'):
                obj = getattr(obj, prop)
            return obj
        except:
            return 0.0
            
    def set_value(self, value):
        """Set value using property path"""
        try:
            obj = self.game_object
            props = self.property_path.split('.')
            for prop in props[:-1]:
                obj = getattr(obj, prop)
            setattr(obj, props[-1], value)
        except Exception as e:
            print(f"Error setting {self.property_path} to {value}: {e}")
        
    def handle_event(self, event, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            if event.button == 1:  # Left click
                # Store initial state when drag starts
                self.is_dragging = True
                self.drag_start_x = mouse_pos[0]
                self.drag_start_value = self.get_value()
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_dragging:
                self.is_dragging = False
                
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            # Calculate total distance from start
            total_distance = mouse_pos[0] - self.drag_start_x
            # Convert distance to value change
            value_change = total_distance * self.step
            # Apply to original value
            new_value = self.drag_start_value + value_change
            
            # Hard limits for scale values
            if "scale" in self.property_path.lower():
                new_value = max(0.01, new_value)  # Minimum scale of 0.01
            
            self.set_value(new_value)
            return True
            
        return False
        
    def draw(self, surface):
        # Draw background box like Unity
        box_color = (60, 60, 60)  # Dark gray background
        border_color = (100, 100, 100)  # Lighter border
        
        if self.is_dragging:
            border_color = (150, 150, 255)  # Blue border when dragging
        elif self.hovered:
            border_color = (120, 120, 120)  # Lighter border when hovered
            
        # Draw the box
        pygame.draw.rect(surface, box_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 1)
        
        # Draw the value text centered in the box
        font = pygame.font.Font(None, 16)
        text_color = (255, 255, 255)  # White text
            
        # Format value
        if self.label == "Rotation":
            value_text = f"{self.get_value():.1f}"
        else:
            value_text = f"{self.get_value():.1f}"
            
        text_surface = font.render(value_text, True, text_color)
        
        # Center the text in the box
        text_x = self.rect.x + (self.rect.width - text_surface.get_width()) // 2
        text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
        surface.blit(text_surface, (text_x, text_y))


class InspectorPanel(Panel):
    """Inspector panel that shows properties of selected objects"""
    def __init__(self, x, y, width, height, scene):
        super().__init__(x, y, width, height, "Inspector")
        self.scene = scene
        self.font = pygame.font.Font(None, 18)
        self.small_font = pygame.font.Font(None, 16)
        self.input_fields = []
        self.drag_labels = []
        self.current_object = None  # Track which object we have fields for
        
    def on_value_change(self, property_path, value):
        """Callback when input field value changes"""
        if self.scene.selected_object:
            obj = self.scene.selected_object
            try:
                # Navigate to the property and set it
                path_parts = property_path.split('.')
                target = obj
                for part in path_parts[:-1]:
                    target = getattr(target, part)
                setattr(target, path_parts[-1], value)
                
                # Update corresponding input field display values
                for field in self.input_fields:
                    if field.property_path == property_path:
                        field.display_value = f"{value:.2f}"
                        if not field.is_active:  # Only update if not currently being edited
                            field.value = field.display_value
                        
            except Exception as e:
                print(f"Error setting property {property_path}: {e}")
        
    def handle_event(self, event):
        # Handle parent panel events first
        if super().handle_event(event):
            return True
            
        # Handle input field events
        for field in self.input_fields:
            if field.handle_event(event):
                return True
        
        # Handle drag label events
        for label in self.drag_labels:
            if label.handle_event(event):
                return True
        
        return False
        
    def update(self, mouse_pos):
        super().update(mouse_pos)
        # Update input fields based on selected object
        self.update_input_fields()
        # Update input field timings
        for field in self.input_fields:
            field.update(1/60)
        
    def update_input_fields(self):
        """Create/update input fields based on selected object"""
        # Only recreate fields if selected object changed
        if self.current_object != self.scene.selected_object:
            self.input_fields.clear()
            self.drag_labels.clear()
            self.current_object = self.scene.selected_object
        
        if self.scene.selected_object and not self.input_fields:
            obj = self.scene.selected_object
            start_y = self.rect.y + 130  # Match draw_object_inspector
            row_height = 35
            box_width = 60
            box_height = 20
            
            # Position fields - right next to X and Y labels  
            pos_y = start_y
            pos_x_field = TextInput(
                self.rect.x + 130, pos_y,  # Right after X label
                box_width, box_height,
                f"{obj.transform.position.x:.2f}",
                self.on_value_change, "transform.position.x"
            )
            self.input_fields.append(pos_x_field)
            
            pos_y_field = TextInput(
                self.rect.x + 230, pos_y,  # Right after Y label with more spacing
                box_width, box_height,
                f"{obj.transform.position.y:.2f}",
                self.on_value_change, "transform.position.y"
            )
            self.input_fields.append(pos_y_field)
            
            # Rotation field - right next to Z label
            rot_y = pos_y + row_height
            rot_field = TextInput(
                self.rect.x + 130, rot_y,  # Right after Z label
                box_width, box_height,
                f"{obj.transform.rotation:.2f}",
                self.on_value_change, "transform.rotation"
            )
            self.input_fields.append(rot_field)
            
            # Scale fields - right next to X and Y labels
            scale_y = rot_y + row_height
            scale_x_field = TextInput(
                self.rect.x + 130, scale_y,  # Right after X label
                box_width, box_height,
                f"{obj.transform.scale.x:.2f}",
                self.on_value_change, "transform.scale.x"
            )
            self.input_fields.append(scale_x_field)
            
            scale_y_field = TextInput(
                self.rect.x + 230, scale_y,  # Right after Y label with more spacing
                box_width, box_height,
                f"{obj.transform.scale.y:.2f}",
                self.on_value_change, "transform.scale.y"
            )
            self.input_fields.append(scale_y_field)
            
            # Create drag labels for X/Y/Z labels
            # Position X/Y labels
            pos_x_label = DragLabel(
                self.rect.x + 105, pos_y,  # X label position
                20, box_height, "X", 
                self.on_value_change, "transform.position.x", self.scene, step=1.0
            )
            self.drag_labels.append(pos_x_label)
            
            pos_y_label = DragLabel(
                self.rect.x + 205, pos_y,  # Y label position with more spacing
                20, box_height, "Y",
                self.on_value_change, "transform.position.y", self.scene, step=1.0
            )
            self.drag_labels.append(pos_y_label)
            
            # Rotation Z label
            rot_z_label = DragLabel(
                self.rect.x + 105, rot_y,  # Z label position
                20, box_height, "Z",
                self.on_value_change, "transform.rotation", self.scene, step=2.0
            )
            self.drag_labels.append(rot_z_label)
            
            # Scale X/Y labels
            scale_x_label = DragLabel(
                self.rect.x + 105, scale_y,  # X label position  
                20, box_height, "X",
                self.on_value_change, "transform.scale.x", self.scene, step=0.01
            )
            self.drag_labels.append(scale_x_label)
            
            scale_y_label = DragLabel(
                self.rect.x + 205, scale_y,  # Y label position with more spacing
                20, box_height, "Y", 
                self.on_value_change, "transform.scale.y", self.scene, step=0.01
            )
            self.drag_labels.append(scale_y_label)

    def draw(self, surface):
        # Draw panel background and title
        super().draw(surface)
        
        # Check if we have a selected object
        if self.scene.selected_object:
            self.draw_object_inspector(surface, self.scene.selected_object)
            # Draw interactive input fields
            for field in self.input_fields:
                field.draw(surface)
                
            # Draw drag labels (on top so they're interactive)
            for label in self.drag_labels:
                label.draw(surface)
        else:
            self.draw_no_selection(surface)
            
    def draw_no_selection(self, surface):
        """Draw message when no object is selected"""
        text = self.font.render("No object selected", True, (120, 120, 120))
        surface.blit(text, (self.rect.x + 15, self.rect.y + 50))
        
    def draw_object_inspector(self, surface, game_object):
        """Draw inspector for the selected game object in Unity style"""
        start_y = self.rect.y + 60
        row_height = 35
        
        # Object name
        name_text = self.font.render(f"Name: {game_object.name}", True, TEXT_COLOR)
        surface.blit(name_text, (self.rect.x + 15, start_y))
        
        # Transform section header
        transform_header = self.font.render("Transform", True, ACCENT_COLOR)
        surface.blit(transform_header, (self.rect.x + 15, start_y + 30))
        
        # Position row
        pos_y = start_y + 70
        pos_text = self.small_font.render("Position", True, TEXT_COLOR)
        surface.blit(pos_text, (self.rect.x + 20, pos_y))
        
        # X and Y labels are now draggable - removed static ones
        
        # Rotation row
        rot_y = pos_y + row_height
        rot_text = self.small_font.render("Rotation", True, TEXT_COLOR)
        surface.blit(rot_text, (self.rect.x + 20, rot_y))
        
        # Z label is now draggable - removed static one
        
        # Scale row
        scale_y = rot_y + row_height
        scale_text = self.small_font.render("Scale", True, TEXT_COLOR)
        surface.blit(scale_text, (self.rect.x + 20, scale_y))
        
        # X and Y scale labels are now draggable - removed static ones

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
        self.camera = EditorCamera(width, height)
        self.grid_size = 20
        self.show_grid = True
        self.show_origin = True
        
        # Pan/zoom interaction state
        self.is_panning = False
        self.last_mouse_pos = Vector2(0, 0)
        
    def handle_event(self, event):
        if not self.hovered:
            return False
            
        mouse_x, mouse_y = pygame.mouse.get_pos()
        local_mouse_x = mouse_x - self.rect.x
        local_mouse_y = mouse_y - self.rect.y
        local_mouse_pos = Vector2(local_mouse_x, local_mouse_y)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click - object selection
                # Convert screen coordinates to world coordinates
                world_pos = self.camera.screen_to_world(local_mouse_pos)
                clicked_object = self.scene.get_object_at_position(world_pos.x, world_pos.y)
                self.scene.select_object(clicked_object)
                return True
            elif event.button == 2:  # Middle click - start panning
                self.is_panning = True
                self.last_mouse_pos = local_mouse_pos
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:  # Middle click release - stop panning
                self.is_panning = False
                return True
                
        elif event.type == pygame.MOUSEMOTION and self.is_panning:
            # Pan the camera
            delta_x = local_mouse_pos.x - self.last_mouse_pos.x
            delta_y = local_mouse_pos.y - self.last_mouse_pos.y
            self.camera.pan(delta_x, delta_y)
            self.last_mouse_pos = local_mouse_pos
            return True
            
        elif event.type == pygame.MOUSEWHEEL and self.hovered:
            # Zoom at mouse position
            zoom_factor = 1.1 if event.y > 0 else 0.9
            self.camera.zoom_at_point(local_mouse_pos, zoom_factor)
            return True
            
        return False
        
    def draw(self, surface):
        # Clear scene surface
        self.surface.fill(DARK_GRAY)
        
        # Draw grid
        if self.show_grid:
            self.draw_grid()
            
        # Draw origin indicator
        if self.show_origin:
            self.draw_origin()
            
        # Draw scene objects with camera transformation
        self.draw_scene_objects()
        
        # Draw UI overlays
        self.draw_ui_overlays()
        
        # Draw border
        pygame.draw.rect(self.surface, BORDER_COLOR, (0, 0, self.rect.width, self.rect.height), 2)
        
        # Blit to main surface
        surface.blit(self.surface, self.rect)
        
    def draw_grid(self):
        """Draw grid lines with smart scaling like professional editors"""
        # Smart grid scaling: choose appropriate grid size based on zoom
        base_size = 32  # Base grid size in pixels (32px = common pixel art standard)
        
        # Calculate multiple levels of grid detail
        if self.camera.zoom >= 4.0:
            world_grid_size = base_size / 4  # Fine grid when zoomed in
        elif self.camera.zoom >= 2.0:
            world_grid_size = base_size / 2  # Medium grid
        elif self.camera.zoom >= 0.5:
            world_grid_size = base_size      # Normal grid
        elif self.camera.zoom >= 0.25:
            world_grid_size = base_size * 2  # Coarse grid when zoomed out
        else:
            world_grid_size = base_size * 4  # Very coarse grid
            
        # Convert world grid size to screen pixels
        screen_grid_size = world_grid_size * self.camera.zoom
        
        # Don't draw grid if too small or too large
        if screen_grid_size < 8 or screen_grid_size > 200:
            return
            
        # Calculate world coordinates of the viewport corners
        top_left_world = self.camera.screen_to_world(Vector2(0, 0))
        bottom_right_world = self.camera.screen_to_world(Vector2(self.rect.width, self.rect.height))
        
        # Find grid lines that intersect the viewport
        # Start from grid line before viewport and end after viewport
        start_x = int(top_left_world.x / world_grid_size) * world_grid_size
        end_x = int(bottom_right_world.x / world_grid_size + 1) * world_grid_size
        start_y = int(top_left_world.y / world_grid_size) * world_grid_size  
        end_y = int(bottom_right_world.y / world_grid_size + 1) * world_grid_size
        
        # Draw vertical lines
        current_x = start_x
        while current_x <= end_x:
            screen_pos = self.camera.world_to_screen(Vector2(current_x, 0))
            if 0 <= screen_pos.x <= self.rect.width:
                pygame.draw.line(self.surface, (50, 50, 50), 
                               (int(screen_pos.x), 0), 
                               (int(screen_pos.x), self.rect.height))
            current_x += world_grid_size
            
        # Draw horizontal lines  
        current_y = start_y
        while current_y <= end_y:
            screen_pos = self.camera.world_to_screen(Vector2(0, current_y))
            if 0 <= screen_pos.y <= self.rect.height:
                pygame.draw.line(self.surface, (50, 50, 50),
                               (0, int(screen_pos.y)), 
                               (self.rect.width, int(screen_pos.y)))
            current_y += world_grid_size
    
    def draw_origin(self):
        """Draw origin (0,0) crosshairs"""
        origin_screen = self.camera.world_to_screen(Vector2(0, 0))
        
        # Only draw if origin is visible
        if (0 <= origin_screen.x <= self.rect.width and 
            0 <= origin_screen.y <= self.rect.height):
            
            # Draw crosshairs
            cross_size = 20
            origin_color = (100, 255, 100)  # Green
            
            # Horizontal line
            pygame.draw.line(self.surface, origin_color,
                           (origin_screen.x - cross_size, origin_screen.y),
                           (origin_screen.x + cross_size, origin_screen.y), 2)
            
            # Vertical line
            pygame.draw.line(self.surface, origin_color,
                           (origin_screen.x, origin_screen.y - cross_size),
                           (origin_screen.x, origin_screen.y + cross_size), 2)
            
            # Center dot
            pygame.draw.circle(self.surface, origin_color, 
                             (int(origin_screen.x), int(origin_screen.y)), 3)
    
    def draw_scene_objects(self):
        """Draw all scene objects using camera transformation"""
        for obj in self.scene.game_objects:
            if not obj.visible:
                continue
                
            # Convert world position to screen position
            screen_pos = self.camera.world_to_screen(obj.transform.position)
            
            # Only draw if object is visible on screen (with some margin)
            margin = 50
            if (-margin <= screen_pos.x <= self.rect.width + margin and
                -margin <= screen_pos.y <= self.rect.height + margin):
                
                # Calculate scaled dimensions based on zoom AND object scale  
                base_radius = 32  # 32px diameter (fits grid perfectly)
                scale_x = max(0.01, abs(obj.transform.scale.x))  # Hard limit: minimum 0.01
                scale_y = max(0.01, abs(obj.transform.scale.y))  # Hard limit: minimum 0.01
                
                # Calculate width and height separately for proper X/Y scaling
                scaled_width = max(1, int(base_radius * self.camera.zoom * scale_x))
                scaled_height = max(1, int(base_radius * self.camera.zoom * scale_y))
                
                # For circular objects, we'll draw an ellipse
                scaled_radius = max(scaled_width, scaled_height)  # For selection outline
                
                # Draw selection outline (ellipse for proper X/Y scaling)
                if obj.selected:
                    selection_width = scaled_width + 10
                    selection_height = scaled_height + 10
                    selection_rect = pygame.Rect(
                        int(screen_pos.x - selection_width/2), 
                        int(screen_pos.y - selection_height/2),
                        selection_width, 
                        selection_height
                    )
                    pygame.draw.ellipse(self.surface, SELECTION_COLOR, selection_rect, 2)
                
                # Draw the object as ellipse (proper X/Y scaling)
                object_rect = pygame.Rect(
                    int(screen_pos.x - scaled_width/2), 
                    int(screen_pos.y - scaled_height/2),
                    scaled_width, 
                    scaled_height
                )
                pygame.draw.ellipse(self.surface, ACCENT_COLOR, object_rect)
                
                # Draw name (only if zoom is high enough)
                if self.camera.zoom >= 0.5:
                    font_size = max(12, int(16 * self.camera.zoom))
                    font = pygame.font.Font(None, font_size)
                    text = font.render(obj.name, True, TEXT_COLOR)
                    text_pos = (screen_pos.x - text.get_width() // 2, 
                               screen_pos.y + scaled_radius + 5)
                    self.surface.blit(text, text_pos)
    
    def draw_ui_overlays(self):
        """Draw UI overlays like zoom level and coordinates"""
        font = pygame.font.Font(None, 20)
        
        # Zoom level
        zoom_text = f"Zoom: {self.camera.zoom:.1f}x"
        zoom_surface = font.render(zoom_text, True, TEXT_COLOR)
        self.surface.blit(zoom_surface, (10, 10))
        
        # Camera position
        pos_text = f"Camera: ({self.camera.position.x:.1f}, {self.camera.position.y:.1f})"
        pos_surface = font.render(pos_text, True, TEXT_COLOR)
        self.surface.blit(pos_surface, (10, 30))

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
        # Create a few sample objects positioned around the world origin
        obj1 = GameObject("Player")
        obj1.transform.position = Vector2(0, 0)  # At world origin
        self.scene.add_object(obj1)
        
        obj2 = GameObject("Enemy")
        obj2.transform.position = Vector2(100, -50)  # To the right and up
        self.scene.add_object(obj2)
        
        obj3 = GameObject("Item")
        obj3.transform.position = Vector2(-80, 60)  # To the left and down
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
