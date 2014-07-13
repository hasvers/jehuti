from gam_import import *
import graphview as gv


class LinkTypeField(WindowField):
    #Game specific
    def __init__(self,parent,**kwargs):
        gv.WindowField.__init__(self,parent,**kwargs)
        color=[graphic_chart['icon_node_fill_colors'][i] for i in self.val]
        self.image.blit(gradients.horizontal(self.rect.size, *color),(0,0))

    def set_val(self,val=None):
        if val != self.val :
            size= self.rect.size
            self.val= val
            colors=graphic_chart['icon_node_fill_colors']
            self.image.blit(gradients.horizontal(size, *[colors[i] for i in val[:2]]),(0,0))
            if val[2] or val[3]:
                marksize=size[1]/3,size[1]/3
                mark=pgsurface.Surface(marksize)
            if val[2]:
                mark.fill(colors[1-val[0]])
                self.image.blit(mark,marksize)
            if val[3]:
                mark.fill(colors[1-val[1]])
                self.image.blit(mark,(size[0]-2*marksize[0],marksize[1]))


    def event(self,event,**kwargs):
        if event.type == pg.MOUSEBUTTONDOWN:
            v=array(self.val)
            if event.button ==1 :
                if self.parent.mousepos(self)[0]- self.width/2 > 0:
                    v[1]=1-v[1]
                else :
                    v[0]=1-v[0]
            if event.button ==3 :
                if self.parent.mousepos(self)[0]- self.width/2 > 0:
                    v[3]=1-v[3]
                else :
                    v[2]=1-v[2]
            if event.button==2:
                return False
            self.set_val( tuple(v) )
            self.output()
            return True
        return False




def gam_FCadd(oldadd,self,field,**kwargs):
    if isinstance(field,basestring):
        if field == 'ltyp':
            field =LinkTypeField(self,**kwargs)
    return oldadd(self,field,**kwargs)

extend_method(FieldContainer,'add',gam_FCadd)

