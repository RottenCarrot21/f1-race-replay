#version 330 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aColor;
layout (location = 2) in float aAge;

out vec3 vertexColor;
out float vertexAge;
out vec3 vertexPosition;

uniform mat4 view;
uniform mat4 projection;

void main()
{
    vertexPosition = aPos;
    vertexColor = aColor;
    vertexAge = aAge;
    
    // Transform to view space (geometry shader will handle final output)
    gl_Position = view * vec4(aPos, 1.0);
}