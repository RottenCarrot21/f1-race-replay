#version 330 core

layout (points) in;
layout (triangle_strip, max_vertices = 4) out;

in vec3 vertexColor[];
in float vertexAge[];
in vec3 vertexPosition[];

out vec3 fragColor;
out vec2 fragTexCoord;
out float fragAge;

uniform mat4 projection;

void main()
{
    // Camera properties (simulated - in real implementation would be uniforms)
    vec3 view_dir = vec3(0, 0, 1);  // View direction (simplified)
    vec3 up = vec3(0, 1, 0);        // World up
    
    // Calculate right vector from view direction and up
    vec3 right = normalize(cross(view_dir, up));
    
    // Trail segment width (thicker for recent trails, thinner for old)
    float width = 0.3 * (1.0 - vertexAge[0]);
    width = max(width, 0.05);  // Minimum width
    
    if (width < 0.01) {
        return;  // Don't render very thin trails
    }
    
    // Convert input point to trail quad
    vec4 center = gl_in[0].gl_Position;
    
    // Fade color with age
    vec3 color = vertexColor[0] * (1.0 - vertexAge[0] * 0.5);
    
    // Generate quad vertices (view-facing)
    vec4 offset_right = vec4(right * width, 0.0);
    vec4 offset_up = vec4(up * width * 0.3, 0.0);  // Thin in vertical direction
    
    // Vertex 1: bottom-left
    gl_Position = projection * (center - offset_right - offset_up);
    fragColor = color;
    fragTexCoord = vec2(0.0, 0.0);
    fragAge = vertexAge[0];
    EmitVertex();
    
    // Vertex 2: bottom-right
    gl_Position = projection * (center + offset_right - offset_up);
    fragColor = color;
    fragTexCoord = vec2(1.0, 0.0);
    fragAge = vertexAge[0];
    EmitVertex();
    
    // Vertex 3: top-left
    gl_Position = projection * (center - offset_right + offset_up);
    fragColor = color;
    fragTexCoord = vec2(0.0, 1.0);
    fragAge = vertexAge[0];
    EmitVertex();
    
    // Vertex 4: top-right
    gl_Position = projection * (center + offset_right + offset_up);
    fragColor = color;
    fragTexCoord = vec2(1.0, 1.0);
    fragAge = vertexAge[0];
    EmitVertex();
    
    EndPrimitive();
}