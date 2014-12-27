//test
uniform float time;
uniform vec2 resolution;
uniform sampler2D texture;
uniform vec2 mousepos;

void main( void ) {
    float z;
    float sigma=.01;
    vec2 posdrop=vec2(sin(time/10.),.3);
    vec4 in_Point=gl_TexCoord[0];
    vec4 dot=vec4(0.,0.,0.,0.);

    float u_Theta = 6.28*mousepos.x;
    float dist=length(in_Point.xy-posdrop) ;
    dot.z=exp(-dist*dist/2./sigma/sigma);

    z = sqrt(1.0 - in_Point.x * in_Point.x - in_Point.y * in_Point.y);
    float a = 1.0 / (z * tan(u_Theta * 0.5));
    //gl_FragColor = texture2D(texture, (in_Point.xy ) * 2.0 /a);
    gl_FragColor = texture2D(texture,in_Point.xy) +dot;

    // Channelswap to deal with RGBA/BGRA conversion with pygame
	vec2 aux=gl_FragColor.xy;
	gl_FragColor.x=gl_FragColor.z;
	gl_FragColor.z=aux.x;
}
