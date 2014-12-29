//attributes from vertex shader
//varying vec4 vColor;
//varying vec2 vTexCoord;

//our texture samplers
uniform sampler2D texture;   //diffuse map
uniform sampler2D normals;   //normal map

//values used for shading algorithm...
uniform vec2 Resolution;      //resolution of screen
uniform vec3 LightPos;        //light position, normalized
uniform vec4 LightColor;      //light RGBA -- alpha is intensity
uniform vec4 AmbientColor;    //ambient RGBA -- alpha is intensity 
uniform vec3 Falloff;         //attenuation coefficients

void main() {
    vec2 vTexCoord= gl_TexCoord[0].xy;
    //RGBA of our diffuse color
    vec4 DiffuseColor = texture2D(texture, vTexCoord);

    //RGB of our normal map
    vec3 NormalMap = texture2D(normals, vTexCoord).rgb;

    //The delta position of light
    vec3 LightDir = vec3(LightPos.xy - (gl_FragCoord.xy / Resolution.xy), LightPos.z);

    //Correct for aspect ratio
    LightDir.x *= Resolution.x / Resolution.y;

    //Determine distance (used for attenuation) BEFORE we normalize our LightDir
    float D = length(LightDir);

    //normalize our vectors
    vec3 N = normalize(NormalMap * 2.0 - 1.0);
    vec3 L = normalize(LightDir);

    //Pre-multiply light color with intensity
    //Then perform "N dot L" to determine our diffuse term
    vec3 Diffuse = (LightColor.rgb * LightColor.a) * max(dot(N, L), 0.0);

    //pre-multiply ambient color with intensity
    vec3 Ambient = AmbientColor.rgb * AmbientColor.a;

    //calculate attenuation
    float Attenuation = 1.0 / ( Falloff.x + (Falloff.y*D) + (Falloff.z*D*D) );

    //the calculation which brings it all together
    vec3 Intensity = Ambient + Diffuse * Attenuation;
    vec3 FinalColor = DiffuseColor.rgb * Intensity;
    gl_FragColor =  vec4(FinalColor, DiffuseColor.a);
    //gl_FragColor =  texture2D(normals,gl_TexCoord[0].st);//vColor * vec4(FinalColor, DiffuseColor.a);

	//Channelswap to deal with RGBA/BGRA conversion with pygame
	vec2 aux=gl_FragColor.xy;
	gl_FragColor.x=gl_FragColor.z;
	gl_FragColor.z=aux.x;
}
