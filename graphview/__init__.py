from gv_gui import *
from extender import *

def canvasinit(**params):
        canvas=Canvas(**params)
        try :
            fin=fopen('editor.log','r')
            for i in fin :
                j = i.split(':')
                if j[0]=='current_graph':
                    canvas.set_graph_from_file(j[1])

            fin.close()
        except :
            canvas.graph.make()
            canvas.set_graph(canvas.graph)
        return canvas



def mainlaunch():
    try :
        user.screen = pg.display.set_mode(graphic_chart['screen_size'])
        user.music=MusicMaster()
        pg.display.set_caption('Graphview')
        pg.init()
        size = width, height = 640, 480
        background=image_load(database['image_path']+database['default_bg']).convert()
        canvas=canvasinit(bg=background)
        user.set_ui(EditorUI(None,canvas))
        pg.key.set_repeat(300,30)
        pg.time.set_timer(30,int(round(1000/ergonomy['animation_fps'])))# Animation pulse: event type 30
        while 1:
            for event in pgevent.get():
                #screen.fill((200,200,200,255))
                user.ui.event(event)
                if event.type == pg.QUIT:
                    pg.quit()
                    return 1
                user.ui.update()
            user.ui.paint()
            clock.tick(140)
            pg.display.update()
            pg.display.set_caption('Graphview  %d fps' % clock.get_fps())
    except :
        print traceback.print_tb(sys.exc_info()[2])
        print sys.exc_info()
    finally :
        pg.quit()
        return 0

if __name__ in '__main__':
    import sys, traceback
    mainlaunch()
    '''cProfile.run('mainlaunch()')'''
