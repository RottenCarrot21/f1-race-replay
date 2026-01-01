#version 330 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec2 aTexCoord;

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;

uniform vec3 cameraPos;
uniform float time;

out vec3 FragPos;
out vec3 Normal;
out vec2 TexCoord;
out vec3 ViewDir;
out float DistanceFromCenter;

void main()
{
    vec3 position = aPos;
    
    // Add subtle vertex animation for wet surface effect
    // This creates small ripples on wet track surfaces
    if (time > 0.0) {
        float wave = sin(position.x * 10.0 + time * 2.0) * 0.001;
        wave += cos(position.z * 15.0 + time * 1.5) * 0.0005;
        position.y += wave;
    }
    
    FragPos = vec3(model * vec4(position, 1.0));
    Normal = mat3(transpose(inverse(model))) * aNormal;
    TexCoord = aTexCoord;
    ViewDir = cameraPos - FragPos;
    DistanceFromCenter = length(position.xz);
    
    gl_Position = projection * view * vec4(FragPos, 1.0);
}