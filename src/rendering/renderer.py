"""Integration layer between existing data pipeline and 3D rendering system."""

import numpy as np
import logging
import random
from typing import Dict, List, Any
from .window import create_3d_window

logger = logging.getLogger(__name__)


def run_3d_replay(frames, track_statuses, example_lap, drivers, title,
                  playback_speed=1.0, driver_colors=None, circuit_rotation=0.0, 
                  total_laps=None, chart=False):
    """
    Run the 3D F1 race replay with data from existing pipeline.
    
    This function bridges the existing Arcade-based data format with the new 3D rendering system.
    """
    
    logger.info("Starting 3D race replay")
    logger.info(f"Title: {title}")
    logger.info(f"Drivers: {len(drivers)}")
    logger.info(f"Frames: {len(frames)}")
    
    try:
        # Create 3D window
        window = create_3d_window(title=title)
        
        # Load track from example lap
        if example_lap is not None:
            window.load_track_from_example(example_lap)
        else:
            logger.warning("No example lap provided, track will not be rendered")
        
        # Convert frames to format expected by 3D renderer
        # The existing frames are already in a good format, just need to prepare driver colors
        if driver_colors is None:
            driver_colors = {}
            # Generate distinct colors for drivers using HSV to RGB conversion
            for i, driver in enumerate(drivers):
                # Distribute hues evenly across the color wheel
                hue = i / max(len(drivers), 1) * 2.0 * np.pi
                
                # Simple HSV to RGB (full saturation, medium value)
                r = np.clip(np.sin(hue) * 0.7 + 0.3, 0, 1)
                g = np.clip(np.sin(hue + 2.0 * np.pi / 3.0) * 0.7 + 0.3, 0, 1)
                b = np.clip(np.sin(hue + 4.0 * np.pi / 3.0) * 0.7 + 0.3, 0, 1)
                
                driver_colors[driver] = (float(r), float(g), float(b))
        
        # Load race data
        window.load_race_data(frames, driver_colors)
        
        # Set initial playback speed
        window.playback_speed = playback_speed
        
        # Main rendering loop
        while not window.should_close():
            # Poll events
            window.poll_events()
            
            # Render frame
            window.render_frame()
            
            # Swap buffers
            window.swap_buffers()
        
        # Cleanup
        window.close()
        logger.info("3D replay finished")
        
    except Exception as e:
        logger.error(f"Error in 3D replay: {e}")
        raise


class SimpleShaderGenerator:
    """Generate fallback shaders when shader files don't exist yet."""
    
    @staticmethod
    def create_default_shaders():
        """Create minimal working shaders for testing."""
        import os
        shader_dir = "src/assets/shaders"
        os.makedirs(shader_dir, exist_ok=True)
        
        # Simple vertex shader
        if not os.path.exists(f"{shader_dir}/basic.vert.glsl"):
            with open(f"{shader_dir}/basic.vert.glsl", 'w') as f:
                f.write("""#version 330 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aColor;

uniform mat4 mvp;

out vec3 vertexColor;

void main() {
    gl_Position = mvp * vec4(aPos, 1.0);
    vertexColor = aColor;
}
""")
        
        # Simple fragment shader
        if not os.path.exists(f"{shader_dir}/basic.frag.glsl"):
            with open(f"{shader_dir}/basic.frag.glsl", 'w') as f:
                f.write("""#version 330 core
in vec3 vertexColor;
out vec4 FragColor;

void main() {
    FragColor = vec4(vertexColor, 1.0);
}
""")
        
        # Note: track.vert.glsl and track.frag.glsl should already exist
        # from the previous file creation steps


# For backward compatibility with existing code
def run_arcade_replay(*args, **kwargs):
    """Fallback to original arcade replay if 3D is not requested."""
    from ..arcade_replay import run_arcade_replay as original_run
    return original_run(*args, **kwargs)