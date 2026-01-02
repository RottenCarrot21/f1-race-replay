#version 330 core

in vec3 fragColor;
in vec2 fragTexCoord;
in float fragAge;

out vec4 FragColor;

void main()
{
    // Fade out with age
    float alpha = 1.0 - fragAge;
    alpha = max(alpha, 0.0);
    
    // Smooth easing for fade
    alpha = alpha * alpha;  // Quadratic falloff
    
    // Ensure minimum visibility
    alpha = max(alpha, 0.05);
    
    FragColor = vec4(fragColor, alpha);
    
    // Premultiply alpha
    FragColor.rgb *= FragColor.a;
}