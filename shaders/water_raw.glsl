//Slightly modified Hugo Elias shader

/*
This shader is responsible for the generation and propagation of the ripples.
The method is described at http://freespace.virgin.net/hugo.elias/graphics/x_water.htm
*/

uniform sampler2D textureTwoFramesAgo;
uniform sampler2D textureOneFrameAgo;
uniform vec2 mousePosition;
uniform vec2 textureSize;

//const float damping = 1.0;
const float damping = 0.98;

void main()
{
    // pixels position
    vec2 position = gl_TexCoord[0].xy;

    vec4 smoothed =   (texture2D(textureOneFrameAgo, vec2(position.x - 1.0/textureSize.x, position.y)) +
                       texture2D(textureOneFrameAgo, vec2(position.x + 1.0/textureSize.x, position.y)) +
                       texture2D(textureOneFrameAgo, vec2(position.x, position.y + 1.0/textureSize.y)) +
                       texture2D(textureOneFrameAgo, vec2(position.x, position.y - 1.0/textureSize.y))) / 2.0;
     
    smoothed.r -=  smoothed.g; //calculate the effective intensity
    
    float velocity = texture2D(textureTwoFramesAgo, position).r - texture2D(textureTwoFramesAgo, position).g; //calculate the effective velocity
    
    smoothed.r =  smoothed.r - velocity; //[0;1]
    smoothed.r *= damping;
    
    smoothed.g = -smoothed.r; //[0;-1]

    // add new ripples
    if(mousePosition.x > 0.0)
        if(distance(position, mousePosition) < 1.0 / textureSize.x * 5.0)
            smoothed.r = 1.0;

            
    gl_FragColor = vec4(smoothed.r, smoothed.g, 0, 1.0);
} 
