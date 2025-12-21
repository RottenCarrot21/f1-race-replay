"""
Core 3D Engine - Window and Context Management
Provides a foundation for 3D rendering using ModernGL and pyglet
"""

import pyglet
from pyglet.window import key
import moderngl
import numpy as np
from typing import Tuple, Optional, Callable, Dict, Any
from .camera import Camera3D
from .graphics import Renderer3D, BatchRenderer3D
import time


class Window3D(pyglet.window.Window):
    """
    3D Window wrapper using ModernGL for rendering and pyglet for windowing.
    Provides a migration path from Arcade to full 3D capabilities.
    """
    
    def __init__(self, 
                 width: int = 1920, 
                 height: int = 1200,
                 title: str = "F1 3D Engine",
                 resizable: bool = True,
                 vsync: bool = True):
        
        # Initialize pyglet window
        super().__init__(width, height, title, resizable=resizable, vsync=vsync)
        
        # Initialize ModernGL context
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        
        # Set clear color (dark blue for F1 simulation)
        self.ctx.clear(0.05, 0.1, 0.2, 1.0)
        
        # Core components
        self.camera = Camera3D(aspect_ratio=width/height)
        self.renderer = Renderer3D(self.ctx)
        self.batch_renderer = BatchRenderer3D(self.ctx)
        
        # State management
        self.paused = False
        self.playback_speed = 1.0
        self.last_frame_time = time.time()
        self.frame_index = 0.0
        
        # 3D to 2D scaling factors (migration helper)
        self.world_scale = 1.0
        self.tx = 0.0
        self.ty = 0.0
        
        # Legacy compatibility (for migration)
        self.left_ui_margin = 340
        self.right_ui_margin = 260
        self.circuit_rotation = 0.0
        self._rot_rad = 0.0
        self._cos_rot = 1.0
        self._sin_rot = 0.0
        
        # Input handling
        self.setup_event_handlers()
        
    def setup_event_handlers(self):
        """Setup keyboard and mouse event handlers"""
        self.push_handlers(self)
        
    def on_draw(self):
        """Main render loop - called every frame"""
        # Clear the screen
        self.ctx.clear(0.05, 0.1, 0.2, 1.0)
        
        # Update camera
        self.camera.update()
        
        # Render 3D scene
        self.renderer.render(self.camera)
        
        # Render UI elements (2D overlay)
        self._render_ui()
        
    def _render_ui(self):
        """Render UI elements using pyglet's 2D graphics"""
        # Draw a simple border around the 3D viewport
        if hasattr(self, 'viewport_rect'):
            x, y, w, h = self.viewport_rect
            # Draw border lines
            pyglet.graphics.draw(4, pyglet.gl.GL_LINES, 
                ('v2f', [x, y, x+w, y, x+w, y, x+w, y+h, x+w, y+h, x, y+h, x, y+h, x, y])
            )
    
    def on_update(self, dt):
        """Update simulation - called every frame"""
        if self.paused:
            return
        
        # Update frame index for F1 telemetry playback
        from src.f1_data import FPS
        self.frame_index += dt * FPS * self.playback_speed
        
        # Update camera (for smooth transitions)
        self.camera.update()
        
    def on_resize(self, width, height):
        """Handle window resize"""
        super().on_resize(width, height)
        
        # Update viewport
        self.ctx.viewport = (0, 0, width, height)
        
        # Update camera aspect ratio
        self.camera.set_aspect_ratio(width / height)
        
        # Update 2D scaling factors for migration compatibility
        self.update_scaling(width, height)
        
    def update_scaling(self, screen_w, screen_h):
        """Update world-to-screen scaling (legacy compatibility)"""
        # Reserve margins for UI
        inner_w = max(1.0, screen_w - self.left_ui_margin - self.right_ui_margin)
        
        # For now, maintain the same scaling logic as the original
        # TODO: Replace with proper 3D camera-based projection
        screen_cx = self.left_ui_margin + inner_w / 2
        screen_cy = screen_h / 2
        
        self.tx = screen_cx
        self.ty = screen_cy
        self.world_scale = min(inner_w / 2000.0, screen_h / 1000.0)  # Default scale
        
    def set_circuit_rotation(self, rotation_degrees: float):
        """Set circuit rotation (legacy compatibility)"""
        self.circuit_rotation = rotation_degrees
        self._rot_rad = float(np.deg2rad(rotation_degrees))
        self._cos_rot = float(np.cos(self._rot_rad))
        self._sin_rot = float(np.sin(self._rot_rad))
        
    def world_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """Convert world coordinates to screen coordinates (legacy compatibility)"""
        # Apply rotation around center
        world_cx, world_cy = 0.0, 0.0  # Default world center
        
        if self._rot_rad:
            tx = x - world_cx
            ty = y - world_cy
            rx = tx * self._cos_rot - ty * self._sin_rot
            ry = tx * self._sin_rot + ty * self._cos_rot
            x, y = rx + world_cx, ry + world_cy
            
        # Scale and translate
        sx = self.world_scale * x + self.tx
        sy = self.world_scale * y + self.ty
        return sx, sy
        
    def set_paused(self, paused: bool):
        """Set pause state"""
        self.paused = paused
        
    def set_playback_speed(self, speed: float):
        """Set playback speed"""
        self.playback_speed = speed
        
    def set_frame_index(self, frame_index: float):
        """Set current frame index"""
        self.frame_index = frame_index
        
    def get_frame_index(self) -> float:
        """Get current frame index"""
        return self.frame_index
        
    def is_paused(self) -> bool:
        """Get pause state"""
        return self.paused
        
    def get_playback_speed(self) -> float:
        """Get playback speed"""
        return self.playback_speed
        
    # Event handlers
    def on_key_press(self, symbol, modifiers):
        """Handle key press events"""
        if symbol == key.SPACE:
            self.paused = not self.paused
        elif symbol == key.RIGHT:
            self.frame_index = min(self.frame_index + 10.0, 1000.0)  # Max frame
        elif symbol == key.LEFT:
            self.frame_index = max(self.frame_index - 10.0, 0.0)
        elif symbol == key.UP:
            self.playback_speed *= 2.0
        elif symbol == key.DOWN:
            self.playback_speed = max(0.1, self.playback_speed / 2.0)
        elif symbol == key.KEY_1:
            self.playback_speed = 0.5
        elif symbol == key.KEY_2:
            self.playback_speed = 1.0
        elif symbol == key.KEY_3:
            self.playback_speed = 2.0
        elif symbol == key.KEY_4:
            self.playback_speed = 4.0
        elif symbol == key.R:
            self.frame_index = 0.0
            self.playback_speed = 1.0
            
    def on_mouse_press(self, x, y, button, modifiers):
        """Handle mouse press events"""
        pass
        
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """Handle mouse drag for camera control"""
        if buttons & pyglet.window.mouse.LEFT:
            # Rotate camera with left mouse drag
            self.camera.rotate_around_target(dx * 0.01, dy * 0.01)
        elif buttons & pyglet.window.mouse.RIGHT:
            # Pan camera with right mouse drag
            self.camera.pan(dx, dy)
            
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Handle mouse scroll for zoom control"""
        self.camera.zoom(scroll_y * 0.1)
        
    def run(self):
        """Start the 3D application"""
        pyglet.clock.schedule(self.on_update)
        pyglet.app.run()