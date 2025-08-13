import pygame
import sys
from core import Vector2, Scene, GameObject
from ui import Button, HierarchyPanel, InspectorPanel, ConsolePanel
from systems import Console
from utils import Colors, SCREEN_WIDTH, SCREEN_HEIGHT, FPS, PROJECT_WIDTH, INSPECTOR_WIDTH, CONSOLE_HEIGHT, MENU_HEIGHT

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
    
    def reset_zoom(self):
        """Reset zoom to 1.0 while keeping camera position"""
        self.zoom = 1.0

class SceneView:
    """Main scene view where the game is rendered"""
    def __init__(self, x, y, width, height, scene):
        self.rect = pygame.Rect(x, y, width, height)
        self.surface = pygame.Surface((width, height))
        self.scene = scene
        self.camera = EditorCamera(width, height)

        self.show_grid = True
        self.show_origin = True
        
        # Pan/zoom interaction state
        self.is_panning = False
        self.last_mouse_pos = Vector2(0, 0)
        self.hovered = False
        
        # Drag and drop state
        self.is_dragging_object = False
        self.dragged_object = None
        self.drag_start_pos = Vector2(0, 0)
        
        # Play mode state (will be set by editor)
        self.is_playing = False
        
    def handle_event(self, event):
        if not self.hovered:
            return False
            
        mouse_x, mouse_y = pygame.mouse.get_pos()
        local_mouse_x = mouse_x - self.rect.x
        local_mouse_y = mouse_y - self.rect.y
        local_mouse_pos = Vector2(local_mouse_x, local_mouse_y)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check if clicking on zoom text
                if self.is_click_on_zoom_text(local_mouse_pos):
                    self.camera.reset_zoom()
                    return True
                
                # Check if clicking on camera position text
                if self.is_click_on_camera_text(local_mouse_pos):
                    self.camera.reset_view()
                    return True
                
                # Object selection and drag start (only in edit mode)
                world_pos = self.camera.screen_to_world(local_mouse_pos)
                clicked_object = self.scene.get_object_at_position(world_pos.x, world_pos.y)
                self.scene.select_object(clicked_object)
                
                # Start dragging if we clicked on an object (only in edit mode)
                if clicked_object and not self.is_playing:
                    self.is_dragging_object = True
                    self.dragged_object = clicked_object
                    self.drag_start_pos = world_pos
                
                return True
            elif event.button == 2:  # Middle click - start panning
                self.is_panning = True
                self.last_mouse_pos = local_mouse_pos
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left click release - stop dragging
                if self.is_dragging_object:
                    self.is_dragging_object = False
                    self.dragged_object = None
                    return True
            elif event.button == 2:  # Middle click release - stop panning
                self.is_panning = False
                return True
                
        elif event.type == pygame.MOUSEMOTION:
            if self.is_panning:
                # Pan the camera
                delta_x = local_mouse_pos.x - self.last_mouse_pos.x
                delta_y = local_mouse_pos.y - self.last_mouse_pos.y
                self.camera.pan(delta_x, delta_y)
                self.last_mouse_pos = local_mouse_pos
                return True
            elif self.is_dragging_object and self.dragged_object and not self.is_playing:
                # Drag the object (only in edit mode)
                world_pos = self.camera.screen_to_world(local_mouse_pos)
                self.dragged_object.transform.position = world_pos
                return True
            
        elif event.type == pygame.MOUSEWHEEL and self.hovered:
            # Zoom at mouse position
            zoom_factor = 1.1 if event.y > 0 else 0.9
            self.camera.zoom_at_point(local_mouse_pos, zoom_factor)
            return True
            
        return False
    
    def is_click_on_zoom_text(self, local_mouse_pos):
        """Check if mouse click is on the zoom text overlay"""
        font = pygame.font.Font(None, 20)
        zoom_text = f"Zoom: {self.camera.zoom:.1f}x"
        zoom_surface = font.render(zoom_text, True, Colors.TEXT_COLOR)
        
        # Create a rectangle for the zoom text area
        zoom_rect = pygame.Rect(10, 10, zoom_surface.get_width(), zoom_surface.get_height())
        return zoom_rect.collidepoint(local_mouse_pos.x, local_mouse_pos.y)
    
    def is_click_on_camera_text(self, local_mouse_pos):
        """Check if mouse click is on the camera position text overlay"""
        font = pygame.font.Font(None, 20)
        pos_text = f"Camera: ({self.camera.position.x:.1f}, {self.camera.position.y:.1f})"
        pos_surface = font.render(pos_text, True, Colors.TEXT_COLOR)
        
        # Create a rectangle for the camera text area
        camera_rect = pygame.Rect(10, 30, pos_surface.get_width(), pos_surface.get_height())
        return camera_rect.collidepoint(local_mouse_pos.x, local_mouse_pos.y)
    
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        # Check if middle mouse button is still pressed globally
        # This fixes the issue where releasing MMB outside the scene view doesn't stop panning
        if self.is_panning and not pygame.mouse.get_pressed()[1]:  # Index 1 is middle mouse button
            self.is_panning = False
        
        # Check if left mouse button is still pressed globally (for dragging)
        if self.is_dragging_object and not pygame.mouse.get_pressed()[0]:  # Index 0 is left mouse button
            self.is_dragging_object = False
            self.dragged_object = None
    
    def draw(self, surface):
        # Clear scene surface
        self.surface.fill(Colors.DARK_GRAY)
        
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
        pygame.draw.rect(self.surface, Colors.BORDER_COLOR, (0, 0, self.rect.width, self.rect.height), 2)
        
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
                    pygame.draw.ellipse(self.surface, Colors.SELECTION_COLOR, selection_rect, 2)
                
                # Choose object color based on state
                if self.is_dragging_object and obj == self.dragged_object:
                    object_color = (255, 200, 100)  # Orange when dragging
                else:
                    object_color = Colors.ACCENT_COLOR  # Normal color
                
                # Draw the object as ellipse (proper X/Y scaling)
                object_rect = pygame.Rect(
                    int(screen_pos.x - scaled_width/2), 
                    int(screen_pos.y - scaled_height/2),
                    scaled_width, 
                    scaled_height
                )
                pygame.draw.ellipse(self.surface, object_color, object_rect)
                
                # Draw name (only if zoom is high enough)
                if self.camera.zoom >= 0.5:
                    font_size = max(12, int(16 * self.camera.zoom))
                    font = pygame.font.Font(None, font_size)
                    text = font.render(obj.name, True, Colors.TEXT_COLOR)
                    text_pos = (screen_pos.x - text.get_width() // 2, 
                               screen_pos.y + scaled_radius + 5)
                    self.surface.blit(text, text_pos)
    
    def draw_ui_overlays(self):
        """Draw UI overlays like zoom level and coordinates"""
        font = pygame.font.Font(None, 20)
        
        # Get current mouse position for hover detection
        mouse_x, mouse_y = pygame.mouse.get_pos()
        local_mouse_x = mouse_x - self.rect.x
        local_mouse_y = mouse_y - self.rect.y
        
        # Zoom level
        zoom_text = f"Zoom: {self.camera.zoom:.1f}x"
        zoom_surface = font.render(zoom_text, True, Colors.TEXT_COLOR)
        
        # Check if hovering over zoom text
        zoom_rect = pygame.Rect(10, 10, zoom_surface.get_width(), zoom_surface.get_height())
        zoom_hovered = zoom_rect.collidepoint(local_mouse_x, local_mouse_y)
        
        # Draw zoom text with hover effect
        zoom_color = Colors.ACCENT_COLOR if zoom_hovered else Colors.TEXT_COLOR
        zoom_surface = font.render(zoom_text, True, zoom_color)
        self.surface.blit(zoom_surface, (10, 10))
        
        # Add underline if hovered
        if zoom_hovered:
            pygame.draw.line(self.surface, zoom_color, (10, 10 + zoom_surface.get_height()), 
                           (10 + zoom_surface.get_width(), 10 + zoom_surface.get_height()), 1)
        
        # Camera position
        pos_text = f"Camera: ({self.camera.position.x:.1f}, {self.camera.position.y:.1f})"
        pos_surface = font.render(pos_text, True, Colors.TEXT_COLOR)
        
        # Check if hovering over camera text
        camera_rect = pygame.Rect(10, 30, pos_surface.get_width(), pos_surface.get_height())
        camera_hovered = camera_rect.collidepoint(local_mouse_x, local_mouse_y)
        
        # Draw camera text with hover effect
        camera_color = Colors.ACCENT_COLOR if camera_hovered else Colors.TEXT_COLOR
        pos_surface = font.render(pos_text, True, camera_color)
        self.surface.blit(pos_surface, (10, 30))
        
        # Add underline if hovered
        if camera_hovered:
            pygame.draw.line(self.surface, camera_color, (10, 30 + pos_surface.get_height()), 
                           (10 + pos_surface.get_width(), 30 + pos_surface.get_height()), 1)

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
        
        # Play mode state
        self.is_playing = False
        self.play_speed = 5  # Movement speed for play mode
        
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
        
        # Add play button to menu bar
        self.play_button = Button(190, 5, 60, 30, "Play", self.toggle_play_mode)
        
        # Add code generation button
        self.code_button = Button(260, 5, 60, 30, "Code", self.show_generated_code)
        
    def show_generated_code(self):
        """Show generated Pygame code in console"""
        code = self.generate_pygame_code()
        self.console.log("Generated Pygame Code:")
        self.console.log("=" * 50)
        for line in code.split('\n'):
            if line.strip():
                self.console.log(line)
        self.console.log("=" * 50)
    
    def toggle_play_mode(self):
        """Toggle between edit and play mode"""
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.enter_play_mode()
        else:
            self.exit_play_mode()
    
    def enter_play_mode(self):
        """Enter play mode"""
        self.console.log("Entering Play Mode")
        # Select the first object as default player
        if self.scene.game_objects:
            self.scene.select_object(self.scene.game_objects[0])
    
    def exit_play_mode(self):
        """Exit play mode"""
        self.console.log("Exiting Play Mode")
        # Deselect all objects
        self.scene.select_object(None)
    
    def generate_pygame_code(self):
        """Generate Pygame code from current scene"""
        code = """import pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# Game objects generated from editor
"""
        
        for i, obj in enumerate(self.scene.game_objects):
            code += f"""
# {obj.name}
{obj.name.lower()}_pos = [{obj.transform.position.x}, {obj.transform.position.y}]
{obj.name.lower()}_speed = 5
"""
        
        code += """
# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Handle input
    keys = pygame.key.get_pressed()
"""
        
        # Add movement for the first object (player)
        if self.scene.game_objects:
            player = self.scene.game_objects[0]
            code += f"""
    # Move {player.name}
    if keys[pygame.K_LEFT]:
        {player.name.lower()}_pos[0] -= {player.name.lower()}_speed
    if keys[pygame.K_RIGHT]:
        {player.name.lower()}_pos[0] += {player.name.lower()}_speed
    if keys[pygame.K_UP]:
        {player.name.lower()}_pos[1] -= {player.name.lower()}_speed
    if keys[pygame.K_DOWN]:
        {player.name.lower()}_pos[1] += {player.name.lower()}_speed
"""
        
        code += """
    # Clear screen
    screen.fill((50, 50, 50))
    
    # Draw objects
"""
        
        for obj in self.scene.game_objects:
            code += f"""    pygame.draw.circle(screen, (255, 0, 0), {obj.name.lower()}_pos, 20)
"""
        
        code += """
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
"""
        
        return code
        
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
                elif event.key == pygame.K_SPACE and not self.is_playing:
                    # Toggle play mode with spacebar (only when not playing)
                    self.toggle_play_mode()
                    
            # Handle UI events
            mouse_pos = pygame.mouse.get_pos()
            self.add_button.handle_event(event)  # Handle add button in menu bar
            self.play_button.handle_event(event)  # Handle play button in menu bar
            self.code_button.handle_event(event)  # Handle code button in menu bar
            self.hierarchy_panel.handle_event(event)  # Handle hierarchy clicks
            self.scene_view.handle_event(event)  # Handle scene view clicks
            self.inspector_panel.handle_event(event)
            self.console_panel.handle_event(event)
            
    def update(self):
        """Update editor state"""
        mouse_pos = pygame.mouse.get_pos()
        self.add_button.update(mouse_pos)  # Update add button
        self.play_button.update(mouse_pos)  # Update play button
        self.code_button.update(mouse_pos)  # Update code button
        self.hierarchy_panel.update(mouse_pos)
        
        # Update scene view with play mode state
        self.scene_view.is_playing = self.is_playing
        self.scene_view.update(mouse_pos)
        
        self.inspector_panel.update(mouse_pos)
        self.console_panel.update(mouse_pos)
        
        # Handle play mode input
        if self.is_playing:
            self.handle_play_input()
        
        # Update scene
        self.scene.update()
    
    def handle_play_input(self):
        """Handle input during play mode"""
        keys = pygame.key.get_pressed()
        if self.scene.selected_object:
            # Move selected object with arrow keys
            if keys[pygame.K_LEFT]:
                self.scene.selected_object.transform.position.x -= self.play_speed
            if keys[pygame.K_RIGHT]:
                self.scene.selected_object.transform.position.x += self.play_speed
            if keys[pygame.K_UP]:
                self.scene.selected_object.transform.position.y -= self.play_speed
            if keys[pygame.K_DOWN]:
                self.scene.selected_object.transform.position.y += self.play_speed
        
    def draw(self):
        """Draw the editor"""
        # Clear screen
        self.screen.fill(Colors.DARK_GRAY)
        
        # Draw menu bar
        pygame.draw.rect(self.screen, Colors.PANEL_BG, (0, 0, SCREEN_WIDTH, MENU_HEIGHT))
        pygame.draw.rect(self.screen, Colors.BORDER_COLOR, (0, 0, SCREEN_WIDTH, MENU_HEIGHT), 2)
        
        # Draw menu text
        font = pygame.font.Font(None, 24)
        text = font.render("Pygame Editor", True, Colors.TEXT_COLOR)
        self.screen.blit(text, (10, 10))
        
        # Update play button text based on mode
        if self.is_playing:
            self.play_button.text = "Stop"
        else:
            self.play_button.text = "Play"
        
        # Draw add button in menu bar
        self.add_button.draw(self.screen)
        self.play_button.draw(self.screen)
        self.code_button.draw(self.screen)
        
        # Draw play mode indicator
        if self.is_playing:
            mode_text = font.render("PLAY MODE", True, (255, 255, 0))  # Yellow text
            self.screen.blit(mode_text, (SCREEN_WIDTH - 150, 10))
        
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
