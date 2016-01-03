# -*- coding: utf-8 -*-

from gv_globals import *
from scipy import signal, ndimage

'''Visual effects.'''


def glow(surface, sigma=8,intens=.85,mode='np',rgba=0):
    newsurf=surface.copy()
    blur(newsurf,sigma,intens)
    if rgba:
        surface.blit( newsurf,(0,0),None,pg.BLEND_RGBA_ADD)
    else:
        surface.blit( newsurf,(0,0),None,pg.BLEND_ADD)


def blur(surface, sigma=8,intens=1,mode='np'):
    """This function takes a pygame surface, converts it to a numpy array
    carries out gaussian blur, converts back then returns the pygame surface.
    """
    np_array = pg.surfarray.array3d(surface)
    result = ndimage.filters.gaussian_filter(np_array,
                            sigma=(sigma, sigma, 0),
                            order=0,
                            mode='reflect'
                            )
    pg.surfarray.blit_array(surface,(result*intens).astype('int') )
    del np_array

def convert_to_greyscale(image,mod=(1,1,1)):
    array = pg.surfarray.pixels3d(image)
    iarray = array.astype(npint)
    # slicing hint from http://dmr.ath.cx/gfx/python/
    r = iarray[:, :, 0]/2
    g = iarray[:, :, 1]/2
    b = iarray[:, :, 2] /2
    # convert to greyscale by luminance
    gray = (30*r+59*g+11*b)/100
    gray = gray.astype(npuint8)
    array[:, :, 0] = gray
    array[:, :, 1] = gray
    array[:, :, 2] = gray
    return image


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



def aboriginize(img):
    #TODO: Make this seriously better
    from math import pi,cos, sin
    rect=img.get_rect()
    center=rect.center#+array((10,-94))
    w,h=rect.size
    rads=[]
    angles=[]
    rad=0
    while rad<max(w,h):
        if not rads:
            r=rnd.randint(48,64)
        else:
            r=rnd.randint(8,16)
        rad+=r
        rads.append(r)
        atot=0
        angles.append([])
        angles[-1].append(0)
        if len(rads)==1:
            continue
        while atot<2*pi*rad-2*r:
            angles[-1].append(r+rnd.randint(6,8) )
            atot+=angles[-1][-1]
    surf=pg.surface.Surface((w,h),pg.SRCALPHA )
    surf.fill((0,0,0,255))
    rad=1
    for c in range(len(rads)):
        r=rads[c]
        if c==0:
            pr=r*2-rads[1]
        else:
            pr=r
        atot=0
        for a in angles[c]:
            atot+=a
            color = tuple((rnd.randint(200,255) for x in range(3) ))
            color+=100,
            pg.draw.circle(surf, color,
                tuple(rint(x) for x in center +
                array((cos(float(atot)/rad),sin(float(atot)/rad)) )*rad),
                    pr/2 )
        rad+=r

    img.blit(surf,(0,0),None,pg.BLEND_MULT)


def make_blur(img,blur_mode=None,use_pil=None):
    #OBSOLETE
    if use_pil is None:
        use_pil=False
        #use_pil=user.use_pil
    if use_pil:
        pil_string_image = pg.image.tostring(img, "RGBA",False)
        pil_image = pilImage.fromstring("RGBA",img.get_rect().size,pil_string_image)

        #enhancer = pilImageEnhance.Contrast(pil_image)
        #pil_image=enhancer.enhance(1.2)
        #enhancer = pilImageEnhance.Brightness(pil_image)
        #pil_image=enhancer.enhance(1.2)
        for i in range(3):
            enhancer = pilImageEnhance.Sharpness(pil_image)
            pil_image=enhancer.enhance(-1.)

        #image=pilImageOps.invert(pil_image)

        mode = pil_image.mode
        size = pil_image.size
        data = pil_image.tostring()
        #print mode
        #assert mode in "RGB", "RGBA"

        return img.blit(  pg.image.fromstring(data, size, mode), (0,0))

    if blur_mode is None:
        blur_mode=graphic_chart['default_blur_mode']
        #(margin, nb of repetitons,flag,total amplitude)
    mrg,nrep,flag,amplitude=[ blur_mode[i] for i in ['margin','repet','flag','amp']]
    if flag=='add':
        flag=pg.BLEND_ADD
    if flag=='mult':
        flag=pg.BLEND_MULT
    w,h=img.get_rect().size
    amplitude=min(1,amplitude/float(nrep+1))
    #imgref=img.copy()
    img.fill(tuple(rint(255*amplitude) for z in range(4)) ,None,pg.BLEND_MULT)
    if 0<mrg<1:
        mrg=rint(mrg*sqrt(w*h) )
    for i in range(1,(nrep+1)/2)+range(-1,-nrep/2,-1):
        nimg=pg.transform.scale(img, tuple(max(2,x-2*mrg*i) for x in (w,h) ))
        nimg.fill(tuple(rint(255*amplitude) for z in range(4)) ,None,pg.BLEND_MULT)
        img.blit(nimg,(mrg*i,mrg*i),None,flag )
    #img2=pg.transform.smoothscale(img, tuple(x-16 for x in array(img.get_rect().size) ))
    #img3=pg.transform.smoothscale(img, tuple(x-32 for x in array(img.get_rect().size) ))
    #img.blit(img2,(8,8),None,pg.BLEND_MULT)
    #img.blit(img3,(16,16),None,pg.BLEND_ADD)
