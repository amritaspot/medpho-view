import datetime as dt

menufont   = "Helvetica 20"
buttonfont = "Helvetica 16"
smallfont = "Helvetica 14"
labelfont = "Helvetica 14"
titlefont = "Helvetica 22"


def screen_config(parent):
    parent.title('Main')
    parent.geometry('800x480')
    parent.config(bg='#ffffff')
    parent.attributes('-fullscreen', True)

def widget_config(parent):
    parent.title('Widget')
    parent.geometry('800x480')
    parent.config(bg='#ffffff')
    parent.attributes('-fullscreen', True)
   
def kill_previous(prevscreen):
    for screen in prevscreen:
        screen.destroy()
    