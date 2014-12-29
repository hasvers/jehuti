
//http://stackoverflow.com/questions/13538216/normal-mapping-specular-mapping-and-ambient-mapping

// My variant

uniform sampler2D texture;
uniform sampler2D normals;
uniform sampler2D specular;
//uniform sampler2D ambient;
uniform vec3 LightPos;
uniform vec3 eyeDirection;

uniform vec2 Resolution;      //resolution of screen
uniform vec4 LightColor;      //light RGBA -- alpha is intensity
uniform vec4 AmbientColor;    //ambient RGBA -- alpha is intensity 
uniform vec3 Falloff;         //attenuation coefficients

void main() {
    vec2 texcoord= gl_TexCoord[0].xy;

    // Eye vector (towards the camera)
    vec3 E = normalize(eyeDirection);
    
    // Material properties 
    vec4 Diffuse = texture2D(texture, texcoord);
    vec3 Ambient=AmbientColor.rgb *AmbientColor.a ;
    //vec3 Ambient = texture2D(ambientTextureSampler, texcoord).rgb;
    vec3 Specular = texture2D(specular, texcoord).rgb ;

    // Local normal, in tangent space.
    vec3 n = normalize(texture2D(normals, texcoord).rgb*2.0 - 1.0);

    // Direction of the light (from the fragment to the light)
    vec3 LightDir = vec3(LightPos.xy - (gl_FragCoord.xy / Resolution.xy), LightPos.z);

    //Correct for aspect ratio
    LightDir.x *= Resolution.x / Resolution.y;

    //Determine distance (used for attenuation) BEFORE we normalize our LightDir
    float D = length(LightDir);
    vec3 l = normalize(LightDir);

    // Cosine of the angle between the normal and the light direction, 
    // clamped above 0
    //  - light is normal to the surface -> 1
    //  - light is tangent to the surface -> 0
    //  - light is behind the surface -> 0
    float cosTheta = clamp(dot(n,l),0,1);

    // Direction in which the texture reflects the light
    vec3 R = reflect(-l,n);

    // Cosine of the angle between the Eye vector and the Reflect vector,
    // clamped to 0
    //  - Looking into the reflection -> 1
    //  - Looking elsewhere -> < 1
    float cosAlpha = clamp(dot(E,R),0,1);

    //calculate attenuation
    float Attenuation = 1.0 / ( Falloff.x + (Falloff.y*D) + (Falloff.z*D*D) );
    
    vec3 Light=LightColor.rgb*LightColor.a*Attenuation;
    
    vec3 FinalColor = Ambient*Diffuse.rgb +  // Ambient : simulates indirect lighting
        Diffuse.rgb * Light  * cosTheta  + // Diffuse : "color" of the object      
        Specular * Light * pow(cosAlpha,5);  //Specular
        
    gl_FragColor =  vec4(FinalColor, Diffuse.a);

    //Channelswap to deal with RGBA/BGRA conversion with pygame
    vec2 aux=gl_FragColor.xy;
    gl_FragColor.x=gl_FragColor.z;
    gl_FragColor.z=aux.x;
}
