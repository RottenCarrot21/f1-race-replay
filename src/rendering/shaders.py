"""Shader management system with hot-reloading capabilities."""

import os
import time
from OpenGL.GL import *
from .utils import create_program
import logging

logger = logging.getLogger(__name__)


class ShaderManager:
    """Manages OpenGL shaders with hot-reloading support."""
    
    def __init__(self, shader_dir: str = "src/assets/shaders"):
        self.shader_dir = shader_dir
        self.programs = {}  # name -> program id
        self.file_watches = {}  # program name -> {file paths, last modified times}
        self.needs_reload = set()  # programs that need reloading
        
        # Ensure shader directory exists
        os.makedirs(self.shader_dir, exist_ok=True)
    
    def load_program(self, name: str, vertex_file: str, fragment_file: str, 
                     geometry_file: str = None) -> int:
        """Load a shader program from files."""
        
        # Read shader sources
        try:
            with open(os.path.join(self.shader_dir, vertex_file), 'r') as f:
                vertex_source = f.read()
            
            with open(os.path.join(self.shader_dir, fragment_file), 'r') as f:
                fragment_source = f.read()
            
            geometry_source = None
            if geometry_file:
                with open(os.path.join(self.shader_dir, geometry_file), 'r') as f:
                    geometry_source = f.read()
        except FileNotFoundError as e:
            logger.error(f"Shader file not found: {e}")
            return 0
        
        # Create program
        program = create_program(vertex_source, fragment_source, geometry_source)
        if program == 0:
            logger.error(f"Failed to create shader program: {name}")
            return 0
        
        # Store program and watch files for hot-reloading
        self.programs[name] = program
        
        self.file_watches[name] = {
            'vertex': (os.path.join(self.shader_dir, vertex_file), os.path.getmtime(os.path.join(self.shader_dir, vertex_file))),
            'fragment': (os.path.join(self.shader_dir, fragment_file), os.path.getmtime(os.path.join(self.shader_dir, fragment_file))),
        }
        
        if geometry_file:
            self.file_watches[name]['geometry'] = (
                os.path.join(self.shader_dir, geometry_file),
                os.path.getmtime(os.path.join(self.shader_dir, geometry_file))
            )
        
        return program
    
    def check_hot_reload(self):
        """Check for shader file changes and mark for reload."""
        for program_name, files in self.file_watches.items():
            for file_type, (file_path, last_modified) in files.items():
                if os.path.exists(file_path):
                    current_modified = os.path.getmtime(file_path)
                    if current_modified > last_modified:
                        logger.info(f"Shader file changed: {file_path}")
                        self.file_watches[program_name][file_type] = (file_path, current_modified)
                        self.needs_reload.add(program_name)
    
    def reload_pending(self):
        """Reload any shaders that have been modified."""
        reload_count = 0
        for program_name in list(self.needs_reload):
            if self._reload_program(program_name):
                reload_count += 1
        self.needs_reload.clear()
        return reload_count
    
    def _reload_program(self, name: str) -> bool:
        """Reload a single shader program."""
        if name not in self.file_watches:
            return False
        
        files = self.file_watches[name]
        
        try:
            # Read current sources
            with open(files['vertex'][0], 'r') as f:
                vertex_source = f.read()
            
            with open(files['fragment'][0], 'r') as f:
                fragment_source = f.read()
            
            geometry_source = None
            if 'geometry' in files:
                with open(files['geometry'][0], 'r') as f:
                    geometry_source = f.read()
            
            # Create new program
            new_program = create_program(vertex_source, fragment_source, geometry_source)
            if new_program == 0:
                logger.error(f"Hot reload failed for {name}, keeping old version")
                return False
            
            # Delete old program and replace
            old_program = self.programs[name]
            glDeleteProgram(old_program)
            self.programs[name] = new_program
            
            logger.info(f"Successfully reloaded shader: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error reloading shader {name}: {e}")
            return False
    
    def get_program(self, name: str) -> int:
        """Get a compiled shader program by name."""
        return self.programs.get(name, 0)
    
    def cleanup(self):
        """Delete all shader programs."""
        for program in self.programs.values():
            glDeleteProgram(program)
        self.programs.clear()
        self.file_watches.clear()


# Built-in shader sources for testing and fallback
DEFAULT_VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aColor;

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;

out vec3 vertexColor;

void main() {
    gl_Position = projection * view * model * vec4(aPos, 1.0);
    vertexColor = aColor;
}
"""

DEFAULT_FRAGMENT_SHADER = """
#version 330 core
in vec3 vertexColor;
out vec4 FragColor;

void main() {
    FragColor = vec4(vertexColor, 1.0);
}
"""

DEFAULT_GEOMETRY_SHADER = """
#version 330 core
layout (points) in;
layout (triangle_strip, max_vertices = 4) out;

uniform mat4 projection;
uniform mat4 view;
uniform float size = 0.5;

void main() {
    vec4 center = gl_in[0].gl_Position;
    
    // Generate quad from point
    gl_Position = center + vec4(-size, -size, 0, 0);
    EmitVertex();
    
    gl_Position = center + vec4(size, -size, 0, 0);
    EmitVertex();
    
    gl_Position = center + vec4(-size, size, 0, 0);
    EmitVertex();
    
    gl_Position = center + vec4(size, size, 0, 0);
    EmitVertex();
    
    EndPrimitive();
}
"""
