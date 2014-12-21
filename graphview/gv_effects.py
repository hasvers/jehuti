# -*- coding: utf-8 -*-

from gv_globals import *
from scipy import signal, ndimage

'''Visual effects.'''


def glow(surface, sigma=8,mode='np'):
    """This function takes a pygame surface, converts it to a numpy array
    carries out gaussian blur, converts back then returns the pygame surface.
    """
    # Convert to a NumPy array.
    np_array = pg.surfarray.array3d(surface)
    #alpha = pg.surfarray.pixels_alpha(surface)
    # Filter the image
    result = ndimage.filters.gaussian_filter(np_array,
                            sigma=(sigma, sigma, 0),
                            order=0,
                            mode='reflect'
                            )

    #new_alpha = ndimage.filters.gaussian_filter(alpha, sigma=(sigma, sigma), order=0, mode='reflect')
    # Convert back to a surface.
    #surf = pg.surfarray.make_surface(result)#.convert_alpha()
    #pg.surfarray.pixels_alpha(surf)[:] = new_alpha
    surf=surface.copy()
    #pg.surfarray.blit_array(surf,(result+np_array)/2)
    pg.surfarray.blit_array(surf,(result*0.85).astype('int') )
    #surf.fill((200,200,200,250), None, pg.BLEND_MULT)
    del np_array

    #del alpha
    surface.blit( surf,(0,0),None,pg.BLEND_ADD)

def blur(surface, sigma=8,mode='np'):
    """This function takes a pygame surface, converts it to a numpy array
    carries out gaussian blur, converts back then returns the pygame surface.
    """
    # Convert to a NumPy array.
    np_array = pg.surfarray.array3d(surface)
    alpha = pg.surfarray.pixels_alpha(surface)
    # Filter the image
    result = ndimage.filters.gaussian_filter(np_array,
                            sigma=(sigma, sigma, 0),
                            order=0,
                            mode='reflect'
                            )

    #new_alpha = ndimage.filters.gaussian_filter(alpha, sigma=(sigma, sigma), order=0, mode='reflect')
    # Convert back to a surface.
    surf = pg.surfarray.make_surface(result).convert_alpha()
    pg.surfarray.pixels_alpha(surf)[:] = new_alpha
    return surf

def blur_pil(img):
    '''Blurring function using PIL (slower)'''
    pil_string_image = pg.image.tostring(img, "RGBA")
    size=img.get_rect().size
    pil_image = pilImage.fromstring("RGBA",size,pil_string_image)
    #enhancer=pilImageEnhance.Sharpness(pil_image)
    #pil_image=enhancer.enhance(1.2)
    pil_image=pil_image.filter(pilImageFilter.GaussianBlur(radius=3))
    #pil_string_image=pil_image.tostring()
    return pg.image.fromstring(pil_image.tostring(),size,"RGBA")