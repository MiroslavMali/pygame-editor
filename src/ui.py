import pygame
import math
from utils import Colors

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
        color = Colors.HOVER_COLOR if self.hovered else Colors.PANEL_BG
        if self.pressed:
            color = Colors.ACCENT_COLOR
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, Colors.BORDER_COLOR, self.rect, 2)
        
        # Text
        font = pygame.font.Font(None, 20)
        text_surface = font.render(self.text, True, Colors.TEXT_COLOR)
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
        pygame.draw.rect(surface, Colors.PANEL_BG, self.rect)
        pygame.draw.rect(surface, Colors.BORDER_COLOR, self.rect, 2)
        
        # Title
        if self.title:
            font = pygame.font.Font(None, 24)
            text_surface = font.render(self.title, True, Colors.TEXT_COLOR)
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
        text_surface = self.font.render(self.value, True, Colors.TEXT_COLOR)
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
            pygame.draw.line(surface, Colors.TEXT_COLOR, 
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
            color = Colors.TEXT_COLOR  # Normal color
            
        # Draw text
        text_surface = self.font.render(self.text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = self.rect.center
        surface.blit(text_surface, text_rect)

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
            
            # Scale fields - right next to X and Y scale labels
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
        
        # Update existing input field values to reflect current object properties
        if self.scene.selected_object and self.input_fields:
            obj = self.scene.selected_object
            
            # Update position fields
            if len(self.input_fields) >= 2:
                if not self.input_fields[0].is_active:  # Only update if not being edited
                    self.input_fields[0].display_value = f"{obj.transform.position.x:.2f}"
                    self.input_fields[0].value = self.input_fields[0].display_value
                if not self.input_fields[1].is_active:  # Only update if not being edited
                    self.input_fields[1].display_value = f"{obj.transform.position.y:.2f}"
                    self.input_fields[1].value = self.input_fields[1].display_value
            
            # Update rotation field
            if len(self.input_fields) >= 3:
                if not self.input_fields[2].is_active:  # Only update if not being edited
                    self.input_fields[2].display_value = f"{obj.transform.rotation:.2f}"
                    self.input_fields[2].value = self.input_fields[2].display_value
            
            # Update scale fields
            if len(self.input_fields) >= 5:
                if not self.input_fields[3].is_active:  # Only update if not being edited
                    self.input_fields[3].display_value = f"{obj.transform.scale.x:.2f}"
                    self.input_fields[3].value = self.input_fields[3].display_value
                if not self.input_fields[4].is_active:  # Only update if not being edited
                    self.input_fields[4].display_value = f"{obj.transform.scale.y:.2f}"
                    self.input_fields[4].value = self.input_fields[4].display_value

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
        name_text = self.font.render(f"Name: {game_object.name}", True, Colors.TEXT_COLOR)
        surface.blit(name_text, (self.rect.x + 15, start_y))
        
        # Transform section header
        transform_header = self.font.render("Transform", True, Colors.ACCENT_COLOR)
        surface.blit(transform_header, (self.rect.x + 15, start_y + 30))
        
        # Position row
        pos_y = start_y + 70
        pos_text = self.small_font.render("Position", True, Colors.TEXT_COLOR)
        surface.blit(pos_text, (self.rect.x + 20, pos_y))
        
        # X and Y labels are now draggable - removed static ones
        
        # Rotation row
        rot_y = pos_y + row_height
        rot_text = self.small_font.render("Rotation", True, Colors.TEXT_COLOR)
        surface.blit(rot_text, (self.rect.x + 20, rot_y))
        
        # Z label is now draggable - removed static one
        
        # Scale row
        scale_y = rot_y + row_height
        scale_text = self.small_font.render("Scale", True, Colors.TEXT_COLOR)
        surface.blit(scale_text, (self.rect.x + 20, scale_y))
        
        # X and Y scale labels are now draggable - removed static ones

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
            color = Colors.ACCENT_COLOR
        elif self.hovered:
            color = Colors.HOVER_COLOR
        else:
            color = Colors.PANEL_BG
            
        pygame.draw.rect(surface, color, self.rect)
        
        # Object name
        font = pygame.font.Font(None, 18)
        text_surface = font.render(self.game_object.name, True, Colors.TEXT_COLOR)
        surface.blit(text_surface, (self.rect.x + 20, self.rect.y + 5))
        
        # Draw icon (simple circle)
        pygame.draw.circle(surface, Colors.ACCENT_COLOR, (self.rect.x + 10, self.rect.y + self.rect.height // 2), 4)

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
            text_surface = font.render(message, True, Colors.TEXT_COLOR)
            surface.blit(text_surface, (self.rect.x + 10, start_y + i * line_height))
