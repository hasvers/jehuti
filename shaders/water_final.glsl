//Slightly modified Hugo Elias shader

/*
Further reading:
 http://habibs.wordpress.com/lake/
 http://habibs.wordpress.com/water-mathematics/
 http://www.gamedev.net/page/resources/_/technical/graphics-programming-and-theory/the-water-effect-explained-r915
*/

uniform sampler2D rippleMapTex; 	// input from the ripple generation shader
uniform sampler2D backgroundTex; 	// background texture
uniform sampler2D wavesTex; 		// normal map

uniform vec2 textureSize;
uniform vec2 moveVec ;
uniform float time;

const float rIndex = 2.0; 			// refraction index of water
const float specAmp = 150.0; 			// amplification of the specular color
const vec4 specColor = vec4(0.7,0.8,0.99,0.6);	// color of the light reflected by the waves

const float rippleWeight = 1.7;
const float waveMapWeight = 1.1;

const vec3 eyeVector = vec3(0.0,0.72,1.0);
uniform vec3 lightVector ;
const vec3 surfaceNormal = vec3(1.0,0.0,0.0);

void main()
{
    vec2 pos = vec2(gl_TexCoord[0].x, gl_TexCoord[0].y);
    vec2 waveMapPos = pos + moveVec * time;
    
    vec2 diff = rippleWeight*vec2(texture2D(rippleMapTex,pos + vec2(1.0/textureSize.x,0.0)).r - texture2D(rippleMapTex,pos + vec2(1.0/textureSize.x,0.0)).g - (texture2D(rippleMapTex,pos).r + texture2D(rippleMapTex,pos).g),
				  texture2D(rippleMapTex,pos + vec2(0.0,1.0/textureSize.y)).r - texture2D(rippleMapTex,pos + vec2(0.0,1.0/textureSize.y)).g - (texture2D(rippleMapTex,pos).r + texture2D(rippleMapTex,pos).g));
    
    vec2 waveMapNormal = vec2(texture2D(wavesTex,pos).r-0.5,texture2D(wavesTex,pos).g-0.5)+vec2(texture2D(wavesTex,waveMapPos).r-0.5,texture2D(wavesTex,waveMapPos).g-0.5);
    
    diff += waveMapNormal*waveMapWeight;
    
    //refraction
    vec2 angle = atan(diff);
    vec2 refraction = asin(sin(angle)/rIndex);
    vec2 displace = tan(refraction) * diff;
    pos.y = 1.-pos.y ;
    vec4 refractionColor = texture2D(backgroundTex,pos + sign(diff) * displace);
    
    //reflection
    vec3 waterNormal = vec3(displace.x,displace.y,0)*specAmp;
    vec3 halfvec = normalize(eyeVector+lightVector+waterNormal);

    vec4 specColor = specColor*pow(dot(halfvec,surfaceNormal),2);
    specColor = vec4(specColor.x*specColor.w,specColor.y*specColor.w,specColor.z*specColor.w,0);
    
    gl_FragColor = refractionColor + specColor;

    // Channelswap to deal with RGBA/BGRA conversion with pygame
	diff=gl_FragColor.xy;
	gl_FragColor.x=gl_FragColor.z;
	gl_FragColor.z=diff.x;
} 
