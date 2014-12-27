//http://stackoverflow.com/questions/13538216/normal-mapping-specular-mapping-and-ambient-mapping

// Interpolated values from the vertex shaders
in vec2 texcoord;
in vec3 worldPosition;
in vec3 cameraLightDirection;

in vec3 lightDirectionTangent;
in vec3 eyeDirectionTangent;

// Ouput data
out vec3 color;

// Values that stay constant for the whole mesh.
uniform sampler2D diffuseTextureSampler;
uniform sampler2D normalTextureSampler;
uniform sampler2D specularTextureSampler;
uniform sampler2D ambientTextureSampler;
uniform mat4 V;
uniform mat4 M;
uniform mat3 MVR;
uniform vec3 worldLightPosition;

uniform float LightPower;
uniform vec3 LightColor;

void main() {
    vec3 cameraEyeDirection = (0.,0.,1.) ;
    vec2 texCoord= gl_TexCoord[0].xy;

    // Light emission properties
    // You probably want to put them as uniforms

    // Material properties 
    vec3 MaterialDiffuseColor = texture2D(diffuseTextureSampler, texcoord).rgb;
    vec3 MaterialAmbientColor = texture2D(ambientTextureSampler, texcoord).rgb * MaterialDiffuseColor;
    vec3 MaterialSpecularColor = texture2D(specularTextureSampler, texcoord).rgb * 0.3;

    // Local normal, in tangent space.
    vec3 tangentTextureNormal = normalize(texture2D(normalTextureSampler, texcoord).rgb*2.0 - 1.0);

    // Distance to the light
    float distanceBetween = length(worldLightPosition - worldPosition);

    // Normal of the computed fragment, in camera space
    vec3 n = tangentTextureNormal;

    // Direction of the light (from the fragment to the light)
    vec3 l = normalize(lightDirectionTangent);

    // Cosine of the angle between the normal and the light direction, 
    // clamped above 0
    //  - light is at the vertical of the triangle -> 1
    //  - light is perpendicular to the triangle -> 0
    //  - light is behind the triangle -> 0
    float cosTheta = clamp(dot(n,l),0,1);

    // Eye vector (towards the camera)
    vec3 E = normalize(eyeDirectionTangent);

    // Direction in which the triangle reflects the light
    vec3 R = reflect(-l,n);

    // Cosine of the angle between the Eye vector and the Reflect vector,
    // clamped to 0
    //  - Looking into the reflection -> 1
    //  - Looking elsewhere -> < 1
    float cosAlpha = clamp(dot(E,R),0,1);

    color = MaterialAmbientColor +  // Ambient : simulates indirect lighting
        MaterialDiffuseColor * LightColor * LightPower * cosTheta / (distanceBetween*distanceBetween) + // Diffuse : "color" of the object      
        MaterialSpecularColor * LightColor * LightPower * pow(cosAlpha,5) / (distanceBetween*distanceBetween);  //Specular


	//Channelswap to deal with RGBA/BGRA conversion with pygame
	vec2 aux=gl_FragColor.xy;
	gl_FragColor.x=gl_FragColor.z;
	gl_FragColor.z=aux.x;
}
