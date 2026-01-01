#version 330 core

out vec4 FragColor;

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;
in vec3 ViewDir;
in float DistanceFromCenter;

// Material properties
uniform vec3 albedo;
uniform float metallic;
uniform float roughness;
uniform float ao;

// Weather and condition uniforms
uniform float time;
uniform float trackWetness;
uniform float rainIntensity;
uniform vec3 lightDir;
uniform vec3 lightColor;
uniform vec3 ambientColor;
uniform vec3 cameraPos;

// Track surface type (0 = asphalt, 1 = curb, 2 = grass, 3 = barrier)
uniform int surfaceType;

// Lighting calculation
vec3 CalculateLighting(vec3 N, vec3 V, vec3 L, vec3 albedo, float metallic, float roughness)
{
    vec3 H = normalize(V + L);
    
    float NDF = DistributionGGX(N, H, roughness);
    float G = GeometrySmith(N, V, L, roughness);
    vec3 F = FresnelSchlick(max(dot(H, V), 0.0), mix(vec3(0.04), albedo, metallic));
    
    vec3 kS = F;
    vec3 kD = vec3(1.0) - kS;
    kD *= 1.0 - metallic;
    
    vec3 numerator = NDF * G * F;
    float denominator = 4.0 * max(dot(N, V), 0.0) * max(dot(N, L), 0.0) + 0.001;
    vec3 specular = numerator / denominator;
    
    float NdotL = max(dot(N, L), 0.0);
    return (kD * albedo / 3.14159 + specular) * NdotL;
}

// Normal Distribution Function
float DistributionGGX(vec3 N, vec3 H, float roughness)
{
    float a = roughness * roughness;
    float a2 = a * a;
    float NdotH = max(dot(N, H), 0.0);
    float NdotH2 = NdotH * NdotH;
    
    float num = a2;
    float denom = (NdotH2 * (a2 - 1.0) + 1.0);
    denom = 3.14159 * denom * denom;
    
    return num / denom;
}

// Geometry Function
float GeometrySchlickGGX(float NdotV, float roughness)
{
    float r = roughness + 1.0;
    float k = (r * r) / 8.0;
    
    float num = NdotV;
    float denom = NdotV * (1.0 - k) + k;
    
    return num / denom;
}

float GeometrySmith(vec3 N, vec3 V, vec3 L, float roughness)
{
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);
    float ggx2 = GeometrySchlickGGX(NdotV, roughness);
    float ggx1 = GeometrySchlickGGX(NdotL, roughness);
    
    return ggx1 * ggx2;
}

// Fresnel
vec3 FresnelSchlick(float cosTheta, vec3 F0)
{
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

void main()
{
    vec3 N = normalize(Normal);
    vec3 V = normalize(ViewDir);
    vec3 L = normalize(-lightDir);
    
    // Surface-specific material properties
    vec3 surfaceAlbedo = albedo;
    float surfaceMetallic = metallic;
    float surfaceRoughness = roughness;
    
    switch(surfaceType) {
        case 0: // Asphalt
            surfaceAlbedo = vec3(0.08, 0.08, 0.10);
            surfaceMetallic = 0.0;
            surfaceRoughness = 0.95;
            break;
        case 1: // Curb (Yellow/Red)
            surfaceAlbedo = vec3(0.9, 0.7, 0.0);
            surfaceMetallic = 0.1;
            surfaceRoughness = 0.7;
            break;
        case 2: // Grass
            surfaceAlbedo = vec3(0.1, 0.3, 0.05);
            surfaceMetallic = 0.0;
            surfaceRoughness = 0.99;
            break;
        case 3: // Barrier/Wall
            surfaceAlbedo = vec3(0.6, 0.6, 0.7);
            surfaceMetallic = 0.8;
            surfaceRoughness = 0.3;
            break;
    }
    
    // Modify properties based on wetness
    if (trackWetness > 0.0) {
        surfaceAlbedo = mix(surfaceAlbedo, surfaceAlbedo * 0.4, trackWetness);
        surfaceRoughness = mix(surfaceRoughness, 0.05, trackWetness);
        surfaceMetallic = mix(surfaceMetallic, 0.2, trackWetness);
    }
    
    // Main lighting
    vec3 Lo = CalculateLighting(N, V, L, surfaceAlbedo, surfaceMetallic, surfaceRoughness);
    
    // Ambient lighting with sky color
    vec3 ambient = ambientColor * surfaceAlbedo * ao;
    
    // Add rim lighting for dramatic effect
    float rim = 1.0 - max(dot(N, V), 0.0);
    rim = pow(rim, 3.0);
    vec3 rimColor = lightColor * rim * 0.3;
    
    vec3 color = ambient + Lo + rimColor;
    
    // Wet surface reflections (screen-space approximation)
    if (trackWetness > 0.5) {
        float reflectionFactor = (trackWetness - 0.5) * 2.0;
        vec3 reflectedDir = reflect(-V, N);
        
        // Fake reflection with sky color
        float skyReflection = max(dot(reflectedDir, vec3(0, 1, 0)), 0.0);
        vec3 skyColor = vec3(0.4, 0.5, 0.8);
        color += skyColor * skyReflection * reflectionFactor * 0.5;
    }
    
    // Add some procedural detail
    // float grimeNoise = texture(noiseTexture, TexCoord * 50.0).r * 0.1;
    // float skidMarks = texture(skidTexture, TexCoord).r * 0.2;
    // color -= vec3(grimeNoise + skidMarks);
    
    // Distance-based atmospheric perspective
    float distance = length(FragPos - cameraPos);
    float fogFactor = exp(-distance * 0.0005);
    color = mix(ambientColor, color, fogFactor);
    
    // HDR tonemapping
    color = color / (color + vec3(1.0));
    // Exposure adjustment
    color = pow(color, vec3(1.0/2.2)); // gamma correction
    
    FragColor = vec4(color, 1.0);
}