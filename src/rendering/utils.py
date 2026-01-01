"""OpenGL utility functions for 3D rendering infrastructure."""

from OpenGL.GL import *
import numpy as np
import logging

logger = logging.getLogger(__name__)


def create_shader(shader_type: int, source: str) -> int:
    """Compile a shader from source code."""
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    
    # Check compilation status
    status = glGetShaderiv(shader, GL_COMPILE_STATUS)
    if not status:
        log = glGetShaderInfoLog(shader).decode('utf-8')
        shader_type_str = {
            GL_VERTEX_SHADER: "VERTEX",
            GL_FRAGMENT_SHADER: "FRAGMENT",
            GL_GEOMETRY_SHADER: "GEOMETRY"
        }.get(shader_type, "UNKNOWN")
        
        logger.error(f"{shader_type_str} shader compilation failed:\n{log}")
        logger.error(f"Shader source:\n{source}")
        glDeleteShader(shader)
        return 0
    
    return shader


def create_program(vertex_source: str, fragment_source: str, 
                   geometry_source: str = None) -> int:
    """Create a shader program from vertex and fragment shaders."""
    program = glCreateProgram()
    
    # Compile shaders
    vertex_shader = create_shader(GL_VERTEX_SHADER, vertex_source)
    if not vertex_shader:
        glDeleteProgram(program)
        return 0
    
    fragment_shader = create_shader(GL_FRAGMENT_SHADER, fragment_source)
    if not fragment_shader:
        glDeleteShader(vertex_shader)
        glDeleteProgram(program)
        return 0
    
    geometry_shader = None
    if geometry_source:
        geometry_shader = create_shader(GL_GEOMETRY_SHADER, geometry_source)
        if not geometry_shader:
            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            glDeleteProgram(program)
            return 0
    
    # Attach shaders
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    if geometry_shader:
        glAttachShader(program, geometry_shader)
    
    # Link program
    glLinkProgram(program)
    
    # Check link status
    status = glGetProgramiv(program, GL_LINK_STATUS)
    if not status:
        log = glGetProgramInfoLog(program).decode('utf-8')
        logger.error(f"Shader program linking failed:\n{log}")
        glDeleteProgram(program)
        return 0
    
    # Clean up shaders (they're now linked into the program)
    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)
    if geometry_shader:
        glDeleteShader(geometry_shader)
    
    return program


def create_vao(vertices: np.ndarray, indices: np.ndarray = None, 
               attributes: list = None) -> tuple:
    """
    Create a Vertex Array Object with buffers.
    
    Args:
        vertices: NxM numpy array of vertex data
        indices: Optional index array
        attributes: List of (location, size, offset, stride) tuples
    
    Returns:
        (vao, vbo, ebo) tuple
    """
    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    
    # Setup attributes
    if attributes:
        for location, size, offset, stride in attributes:
            glEnableVertexAttribArray(location)
            glVertexAttribPointer(location, size, GL_FLOAT, GL_FALSE, 
                                stride, ctypes.c_void_p(offset))
    else:
        # Default: assume vertices are 3D positions
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))
    
    ebo = None
    if indices is not None:
        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
    
    glBindVertexArray(0)
    return vao, vbo, ebo


def create_ssbo(data: np.ndarray, binding_point: int) -> int:
    """Create a Shader Storage Buffer Object."""
    ssbo = glGenBuffers(1)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, ssbo)
    glBufferData(GL_SHADER_STORAGE_BUFFER, data.nbytes, data, GL_DYNAMIC_DRAW)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, binding_point, ssbo)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, 0)
    return ssbo


class Framebuffer:
    """Wrapper for OpenGL framebuffer objects."""
    
    def __init__(self, width: int, height: int, 
                 color_format: int = GL_RGBA16F, 
                 depth: bool = True):
        self.width = width
        self.height = height
        self.fbo = glGenFramebuffers(1)
        self.color_texture = None
        self.depth_texture = None
        
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        
        # Create color attachment
        self.color_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.color_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, color_format, width, height, 
                     0, GL_RGBA, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, 
                              GL_TEXTURE_2D, self.color_texture, 0)
        
        # Create depth attachment
        if depth:
            self.depth_texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.depth_texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, width, height, 
                         0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, 
                                  GL_TEXTURE_2D, self.depth_texture, 0)
        
        # Check completeness
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            logger.error(f"Framebuffer incomplete: {status}")
        
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
    
    def bind(self):
        """Bind framebuffer for rendering."""
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glViewport(0, 0, self.width, self.height)
    
    def unbind(self, width: int, height: int):
        """Unbind framebuffer and restore viewport."""
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, width, height)
    
    def bind_color_texture(self, unit: int = 0):
        """Bind color texture for sampling."""
        glActiveTexture(GL_TEXTURE0 + unit)
        glBindTexture(GL_TEXTURE_2D, self.color_texture)
    
    def cleanup(self):
        """Delete OpenGL objects."""
        if self.color_texture:
            glDeleteTextures(1, [self.color_texture])
        if self.depth_texture:
            glDeleteTextures(1, [self.depth_texture])
        if self.fbo:
            glDeleteFramebuffers(1, [self.fbo])


class RingBuffer:
    """Fixed-size circular buffer for efficient trail storage."""
    
    def __init__(self, capacity: int, dtype=np.float32):
        self.capacity = capacity
        self.buffer = np.zeros(capacity, dtype=dtype)
        self.write_pos = 0
        self.filled = False
    
    def append(self, value):
        """Add value to buffer, overwriting oldest if full."""
        self.buffer[self.write_pos] = value
        self.write_pos = (self.write_pos + 1) % self.capacity
        if self.write_pos == 0:
            self.filled = True
    
    def get_data(self):
        """Get buffer data in chronological order."""
        if not self.filled:
            return self.buffer[:self.write_pos]
        else:
            return np.concatenate([
                self.buffer[self.write_pos:], 
                self.buffer[:self.write_pos]
            ])
    
    def __len__(self):
        return self.capacity if self.filled else self.write_pos


def check_gl_error():
    """Check and log OpenGL errors."""
    err = glGetError()
    if err != GL_NO_ERROR:
        error_map = {
            GL_INVALID_ENUM: "INVALID_ENUM",
            GL_INVALID_VALUE: "INVALID_VALUE", 
            GL_INVALID_OPERATION: "INVALID_OPERATION",
            GL_INVALID_FRAMEBUFFER_OPERATION: "INVALID_FRAMEBUFFER_OPERATION",
            GL_OUT_OF_MEMORY: "OUT_OF_MEMORY"
        }
        error_str = error_map.get(err, f"UNKNOWN_ERROR ({err})")
        logger.error(f"OpenGL Error: {error_str}")
        return True
    return False
