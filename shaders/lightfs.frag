//attributes from vertex shader
uniform vec2 lightpos;
uniform vec3 lightColor;
uniform float screenHeight;
uniform vec3 lightAttenuation;
uniform float radius;

uniform sampler2D texture;

void main()
{		
	vec2 pixel=gl_FragCoord.xy;		
	
	pixel.y=screenHeight-pixel.y;	
	
	vec2 aux=lightpos-pixel;
	
	float distance=length(aux);
	
	float attenuation=1.0/(lightAttenuation.x+lightAttenuation.y*distance+lightAttenuation.z*distance*distance);	
	
	vec4 color=vec4(attenuation,attenuation,attenuation,1.0)*vec4(lightColor,0.3);	
	
	gl_FragColor = color*.3+(vec4(1,1,1,.7)+color)*texture2D(texture,gl_TexCoord[0].st);
	

	//Channelswap to deal with RGBA/BGRA conversion with pygame
	aux=gl_FragColor.xy;
	
	gl_FragColor.x=gl_FragColor.z;
	
	gl_FragColor.z=aux.x;
	
}
