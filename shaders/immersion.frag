//Simple immersion/emersion test shader

uniform sampler2D texture;
uniform sampler2D depth; //depth map of the texture
uniform sampler2D poke;

//uniform vec2 resolution;      //resolution of screen
uniform float z;      //depth of the bg


void main() {
    vec2 texcoord= gl_TexCoord[0].xy;

    vec4 Poke = texture2D(poke, texcoord);
    vec4 Texture=texture2D(texture, texcoord);
    vec4 Depth=texture2D(depth, texcoord);
    float zdif= smoothstep(-.1,.1,z-Depth.r);

    gl_FragColor =  Texture*zdif+Poke*(1.-zdif);

    //Channelswap to deal with RGBA/BGRA conversion with pygame
    vec2 aux=gl_FragColor.xy;
    gl_FragColor.x=gl_FragColor.z;
    gl_FragColor.z=aux.x;
}
