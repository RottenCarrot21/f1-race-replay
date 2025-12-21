"""
Shader Management System
Provides a centralized way to manage and compile GLSL shaders for different rendering techniques
"""

import moderngl
from typing import Dict, Optional, List
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ShaderConfig:
    """Configuration for shader compilation"""
    vertex_shader: str
    fragment_shader: str
    geometry_shader: Optional[str] = None
    tessellation_shaders: Optional[List[str]] = None
    defines: Optional[Dict[str, str]] = None


class Shader:
    """Represents a compiled shader program"""
    
    def __init__(self, program: moderngl.Program, name: str):
        self.program = program
        self.name = name
        
    def use(self):
        """Activate this shader program"""
        self.program.use()
        
    def __getitem__(self, uniform_name):
        """Get a uniform variable from the shader"""
        return self.program[uniform_name]


class ShaderManager:
    """Manages shader compilation, caching, and uniform management"""
    
    def __init__(self):
        self.shaders: Dict[str, Shader] = {}
        self.shader_configs: Dict[str, ShaderConfig] = {}
        self._load_default_shaders()
        
    def _load_default_shaders(self):
        """Load default shader configurations"""
        
        # Basic lighting shader with Phong reflection model
        self.shader_configs['basic_lighting'] = ShaderConfig(
            vertex_shader="""
                #version 330
                
                in vec3 in_position;
                in vec3 in_normal;
                in vec2 in_uv;
                
                uniform mat4 model_matrix;
                uniform mat4 view_matrix;
                uniform mat4 projection_matrix;
                
                out vec3 v_normal;
                out vec2 v_uv;
                out vec3 v_world_pos;
                
                void main() {
                    vec4 world_pos = model_matrix * vec4(in_position, 1.0);
                    v_world_pos = world_pos.xyz;
                    
                    // Calculate normal (inverse transpose of model matrix for proper lighting)
                    mat3 normal_matrix = transpose(inverse(mat3(model_matrix)));
                    v_normal = normalize(normal_matrix * in_normal);
                    
                    v_uv = in_uv;
                    
                    gl_Position = projection_matrix * view_matrix * world_pos;
                }
            """,
            fragment_shader="""
                #version 330
                
                in vec3 v_normal;
                in vec2 v_uv;
                in vec3 v_world_pos;
                
                uniform vec4 object_color;
                uniform float ambient_light_intensity;
                uniform vec3 ambient_light_color;
                
                // Material properties
                uniform float material_shininess;
                uniform float material_specular_strength;
                uniform vec3 material_specular_color;
                
                // Directional lights
                #define MAX_DIR_LIGHTS 4
                uniform int num_directional_lights;
                uniform struct {
                    vec3 direction;
                    float intensity;
                    vec3 color;
                } directional_lights[MAX_DIR_LIGHTS];
                
                // Point lights
                #define MAX_POINT_LIGHTS 4
                uniform int num_point_lights;
                uniform struct {
                    vec3 position;
                    float intensity;
                    vec3 color;
                } point_lights[MAX_POINT_LIGHTS];
                
                out vec4 fragColor;
                
                void main() {
                    vec3 normal = normalize(v_normal);
                    vec3 view_dir = normalize(-v_world_pos); // Assuming camera at origin for now
                    
                    vec3 lighting = ambient_light_color * ambient_light_intensity;
                    
                    // Directional lights
                    for (int i = 0; i < num_directional_lights && i < MAX_DIR_LIGHTS; i++) {
                        vec3 light_dir = normalize(-directional_lights[i].direction);
                        
                        // Diffuse component
                        float diff = max(dot(normal, light_dir), 0.0);
                        
                        // Specular component (Phong)
                        vec3 reflect_dir = reflect(-light_dir, normal);
                        float spec = pow(max(dot(view_dir, reflect_dir), 0.0), material_shininess);
                        vec3 specular = material_specular_strength * spec * material_specular_color * directional_lights[i].color;
                        
                        lighting += directional_lights[i].color * (diff + specular) * directional_lights[i].intensity;
                    }
                    
                    // Point lights
                    for (int i = 0; i < num_point_lights && i < MAX_POINT_LIGHTS; i++) {
                        vec3 light_dir = normalize(point_lights[i].position - v_world_pos);
                        float distance = length(point_lights[i].position - v_world_pos);
                        
                        // Diffuse component
                        float diff = max(dot(normal, light_dir), 0.0);
                        
                        // Specular component (Phong)
                        vec3 reflect_dir = reflect(-light_dir, normal);
                        float spec = pow(max(dot(view_dir, reflect_dir), 0.0), material_shininess);
                        vec3 specular = material_specular_strength * spec * material_specular_color * point_lights[i].color;
                        
                        // Attenuation
                        float attenuation = 1.0 / (1.0 + 0.1 * distance + 0.01 * distance * distance);
                        
                        lighting += point_lights[i].color * (diff + specular) * point_lights[i].intensity * attenuation;
                    }
                    
                    vec3 final_color = object_color.rgb * lighting;
                    fragColor = vec4(final_color, object_color.a);
                }
            """
        )
        
        # PBR (Physically Based Rendering) shader
        self.shader_configs['pbr_lighting'] = ShaderConfig(
            vertex_shader="""
                #version 330
                
                in vec3 in_position;
                in vec3 in_normal;
                in vec2 in_uv;
                
                uniform mat4 model_matrix;
                uniform mat4 view_matrix;
                uniform mat4 projection_matrix;
                
                out vec3 v_normal;
                out vec2 v_uv;
                out vec3 v_world_pos;
                out vec3 v_view_pos;
                
                void main() {
                    vec4 world_pos = model_matrix * vec4(in_position, 1.0);
                    v_world_pos = world_pos.xyz;
                    
                    // Calculate normal (inverse transpose of model matrix for proper lighting)
                    mat3 normal_matrix = transpose(inverse(mat3(model_matrix)));
                    v_normal = normalize(normal_matrix * in_normal);
                    
                    v_uv = in_uv;
                    
                    v_view_pos = (view_matrix * world_pos).xyz;
                    
                    gl_Position = projection_matrix * view_matrix * world_pos;
                }
            """,
            fragment_shader="""
                #version 330
                
                in vec3 v_normal;
                in vec2 v_uv;
                in vec3 v_world_pos;
                in vec3 v_view_pos;
                
                uniform vec4 object_color;
                uniform float ambient_light_intensity;
                uniform vec3 ambient_light_color;
                
                // PBR Material properties
                uniform float metallic;
                uniform float roughness;
                uniform vec3 albedo;
                
                // Directional lights
                #define MAX_DIR_LIGHTS 4
                uniform int num_directional_lights;
                uniform struct {
                    vec3 direction;
                    float intensity;
                    vec3 color;
                } directional_lights[MAX_DIR_LIGHTS];
                
                // Point lights
                #define MAX_POINT_LIGHTS 4
                uniform int num_point_lights;
                uniform struct {
                    vec3 position;
                    float intensity;
                    vec3 color;
                } point_lights[MAX_POINT_LIGHTS];
                
                out vec4 fragColor;
                
                // PBR functions
                float DistributionGGX(vec3 N, vec3 H, float roughness) {
                    float a = roughness * roughness;
                    float a2 = a * a;
                    float NdotH = max(dot(N, H), 0.0);
                    float NdotH2 = NdotH * NdotH;
                    
                    float num = a2;
                    float denom = (NdotH2 * (a2 - 1.0) + 1.0);
                    denom = 3.14159265 * denom * denom;
                    
                    return num / denom;
                }
                
                float GeometrySchlickGGX(float NdotV, float roughness) {
                    float r = (roughness + 1.0);
                    float k = (r * r) / 8.0;
                    
                    float num = NdotV;
                    float denom = NdotV * (1.0 - k) + k;
                    
                    return num / denom;
                }
                
                float GeometrySmith(vec3 N, vec3 V, vec3 L, float roughness) {
                    float NdotV = max(dot(N, V), 0.0);
                    float NdotL = max(dot(N, L), 0.0);
                    float ggx2 = GeometrySchlickGGX(NdotV, roughness);
                    float ggx1 = GeometrySchlickGGX(NdotL, roughness);
                    
                    return ggx1 * ggx2;
                }
                
                vec3 FresnelSchlick(float cosTheta, vec3 F0) {
                    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
                }
                
                vec3 getLightColor(vec3 L, vec3 V, vec3 N, vec3 lightDir, vec3 lightColor, float intensity) {
                    vec3 H = normalize(V + L);
                    float distance = length(lightDir);
                    
                    // Attenuation
                    float attenuation = 1.0 / (distance * distance);
                    
                    // Radiance
                    vec3 radiance = lightColor * intensity * attenuation;
                    
                    // Cook-Torrance BRDF
                    float NDF = DistributionGGX(N, H, roughness);
                    float G = GeometrySmith(N, V, L, roughness);
                    vec3 F = FresnelSchlick(max(dot(H, V), 0.0), F0);
                    
                    vec3 numerator = NDF * G * F;
                    float denominator = 4.0 * max(dot(N, V), 0.0) * max(dot(N, L), 0.0) + 0.001;
                    vec3 specular = numerator / denominator;
                    
                    vec3 kS = F;
                    vec3 kD = vec3(1.0) - kS;
                    kD *= 1.0 - metallic;
                    
                    float NdotL = max(dot(N, L), 0.0);
                    return (kD * albedo / 3.14159265 + specular) * radiance * NdotL;
                }
                
                void main() {
                    vec3 normal = normalize(v_normal);
                    vec3 view_dir = normalize(-v_view_pos);
                    
                    // Calculate reflectance at normal incidence
                    vec3 F0 = vec3(0.04);
                    F0 = mix(F0, albedo, metallic);
                    
                    vec3 lighting = ambient_light_color * ambient_light_intensity;
                    
                    // Directional lights
                    for (int i = 0; i < num_directional_lights && i < MAX_DIR_LIGHTS; i++) {
                        vec3 L = normalize(-directional_lights[i].direction);
                        lighting += getLightColor(L, view_dir, normal, directional_lights[i].direction, 
                                                directional_lights[i].color, directional_lights[i].intensity);
                    }
                    
                    // Point lights
                    for (int i = 0; i < num_point_lights && i < MAX_POINT_LIGHTS; i++) {
                        vec3 L = normalize(point_lights[i].position - v_world_pos);
                        lighting += getLightColor(L, view_dir, normal, point_lights[i].position - v_world_pos,
                                                point_lights[i].color, point_lights[i].intensity);
                    }
                    
                    vec3 final_color = lighting * object_color.rgb;
                    fragColor = vec4(final_color, object_color.a);
                }
            """
        )
        
        # Unlit shader for debugging and simple shapes
        self.shader_configs['unlit'] = ShaderConfig(
            vertex_shader="""
                #version 330
                
                in vec3 in_position;
                in vec3 in_normal;
                in vec2 in_uv;
                
                uniform mat4 model_matrix;
                uniform mat4 view_matrix;
                uniform mat4 projection_matrix;
                
                void main() {
                    gl_Position = projection_matrix * view_matrix * model_matrix * vec4(in_position, 1.0);
                }
            """,
            fragment_shader="""
                #version 330
                
                uniform vec4 object_color;
                
                out vec4 fragColor;
                
                void main() {
                    fragColor = object_color;
                }
            """
        )
        
        # Wireframe shader for debugging
        self.shader_configs['wireframe'] = ShaderConfig(
            vertex_shader="""
                #version 330
                
                in vec3 in_position;
                
                uniform mat4 model_matrix;
                uniform mat4 view_matrix;
                uniform mat4 projection_matrix;
                
                void main() {
                    gl_Position = projection_matrix * view_matrix * model_matrix * vec4(in_position, 1.0);
                }
            """,
            fragment_shader="""
                #version 330
                
                uniform vec4 wireframe_color;
                
                out vec4 fragColor;
                
                void main() {
                    fragColor = wireframe_color;
                }
            """
        )
        
        # Instanced rendering shader for efficiency
        self.shader_configs['instanced'] = ShaderConfig(
            vertex_shader="""
                #version 330
                
                in vec3 in_position;
                in vec3 in_normal;
                in vec2 in_uv;
                
                // Instance attributes
                in vec3 instance_position;
                in vec3 instance_rotation;
                in vec3 instance_scale;
                in vec4 instance_color;
                
                uniform mat4 view_matrix;
                uniform mat4 projection_matrix;
                
                out vec3 v_normal;
                out vec2 v_uv;
                out vec4 v_color;
                
                mat4 getModelMatrix(vec3 position, vec3 rotation, vec3 scale) {
                    mat4 translation = mat4(
                        1, 0, 0, 0,
                        0, 1, 0, 0,
                        0, 0, 1, 0,
                        position[0], position[1], position[2], 1
                    );
                    
                    float cX = cos(rotation[0]), sX = sin(rotation[0]);
                    float cY = cos(rotation[1]), sY = sin(rotation[1]);
                    float cZ = cos(rotation[2]), sZ = sin(rotation[2]);
                    
                    mat4 rotationX = mat4(
                        1, 0, 0, 0,
                        0, cX, sX, 0,
                        0, -sX, cX, 0,
                        0, 0, 0, 1
                    );
                    
                    mat4 rotationY = mat4(
                        cY, 0, -sY, 0,
                        0, 1, 0, 0,
                        sY, 0, cY, 0,
                        0, 0, 0, 1
                    );
                    
                    mat4 rotationZ = mat4(
                        cZ, sZ, 0, 0,
                        -sZ, cZ, 0, 0,
                        0, 0, 1, 0,
                        0, 0, 0, 1
                    );
                    
                    mat4 scale_mat = mat4(
                        scale[0], 0, 0, 0,
                        0, scale[1], 0, 0,
                        0, 0, scale[2], 0,
                        0, 0, 0, 1
                    );
                    
                    return translation * rotationZ * rotationY * rotationX * scale_mat;
                }
                
                void main() {
                    mat4 model_matrix = getModelMatrix(instance_position, instance_rotation, instance_scale);
                    vec4 world_pos = model_matrix * vec4(in_position, 1.0);
                    
                    // Calculate normal
                    mat3 normal_matrix = transpose(inverse(mat3(model_matrix)));
                    v_normal = normalize(normal_matrix * in_normal);
                    
                    v_uv = in_uv;
                    v_color = instance_color;
                    
                    gl_Position = projection_matrix * view_matrix * world_pos;
                }
            """,
            fragment_shader="""
                #version 330
                
                in vec3 v_normal;
                in vec2 v_uv;
                in vec4 v_color;
                
                uniform vec3 light_direction;
                uniform float ambient_intensity;
                
                out vec4 fragColor;
                
                void main() {
                    vec3 normal = normalize(v_normal);
                    float diff = max(dot(normal, normalize(-light_direction)), 0.0);
                    float lighting = ambient_intensity + diff * (1.0 - ambient_intensity);
                    
                    fragColor = vec4(v_color.rgb * lighting, v_color.a);
                }
            """
        )
        
    def compile_shader(self, ctx: moderngl.Context, name: str, config: ShaderConfig) -> Shader:
        """Compile a shader from configuration"""
        try:
            # Apply defines if present
            vertex_source = config.vertex_shader
            fragment_source = config.fragment_shader
            
            if config.defines:
                for define_name, define_value in config.defines.items():
                    define_line = f"#define {define_name} {define_value}\\n"
                    vertex_source = define_line + vertex_source
                    fragment_source = define_line + fragment_source
            
            # Compile shader program
            program = ctx.program(
                vertex_shader=vertex_source,
                fragment_shader=fragment_source,
                geometry_shader=config.geometry_shader
            )
            
            shader = Shader(program, name)
            return shader
            
        except Exception as e:
            print(f"Error compiling shader '{name}': {e}")
            return None
            
    def get_shader(self, name: str, ctx: Optional[moderngl.Context] = None) -> Optional[Shader]:
        """Get a compiled shader by name"""
        if name in self.shaders:
            return self.shaders[name]
            
        # Try to compile if not found
        if name in self.shader_configs and ctx:
            shader_config = self.shader_configs[name]
            shader = self.compile_shader(ctx, name, shader_config)
            if shader:
                self.shaders[name] = shader
                return shader
                
        return None
        
    def load_shader_from_file(self, ctx: moderngl.Context, name: str, vertex_path: str, fragment_path: str) -> Optional[Shader]:
        """Load shader from file paths"""
        try:
            with open(vertex_path, 'r') as f:
                vertex_source = f.read()
                
            with open(fragment_path, 'r') as f:
                fragment_source = f.read()
                
            config = ShaderConfig(vertex_source, fragment_source)
            shader = self.compile_shader(ctx, name, config)
            
            if shader:
                self.shaders[name] = shader
                
            return shader
            
        except Exception as e:
            print(f"Error loading shader from files '{name}': {e}")
            return None
            
    def add_custom_shader(self, name: str, config: ShaderConfig):
        """Add a custom shader configuration"""
        self.shader_configs[name] = config
        
    def list_shaders(self) -> List[str]:
        """List all available shader names"""
        return list(self.shader_configs.keys())
        
    def cleanup(self):
        """Cleanup shader resources"""
        for shader in self.shaders.values():
            shader.program.release()
        self.shaders.clear()