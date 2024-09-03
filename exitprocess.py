from tkinter import *
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sys
import subprocess
import results
import widgets

def poweroff():
    try:
        shutdown = messagebox.askquestion("Confirm", "Do you want to shutdown?", parent=None)
        if shutdown == 'yes':
            subprocess.run(["sudo", "shutdown", "-h", "now"])
        else:
            print('Shutdown canceled')
    except Exception as e:
        widgets.error(None,str(e))
        results.usesummary(str(e))

def restart():
    try:
        restartans = messagebox.askquestion("Confirm", "Do you want to restart?",parent=None)
        if restartans == 'yes':
            subprocess.run(["sudo", "shutdown", "-r", "now"])
        else:
            print('Restart canceled')
    except Exception as e:
        widgets.error(None,str(e))
        results.usesummary(str(e))
