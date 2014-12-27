//
precision mediump float;

varying vec2 surfacePosition;
uniform float time;

void main(void) {
	vec3 light_color = vec3(0.9, 0.3, 0.1); // RGB, proportional values, higher increases intensity
	float master_scale = 0.1; // Change the size of the effect
	float c = master_scale/(length(surfacePosition+0.0));
	
	gl_FragColor = smoothstep(0.95,1.05,c) * vec4(1.0) + vec4(vec3(c) * light_color, 1.0);
}
