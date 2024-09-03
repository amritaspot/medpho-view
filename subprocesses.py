from tkinter import *
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk
import sys
import subprocess

def poweroff():
    shutdown = tk.messagebox.askquestion("Confirm","Do you want to shutdown?")
    if shutdown == 'no':print('no')
    else:subprocess.run(["sudo", "shutdown", "-h", "now"])
    #else:subprocess.run(['sudo', 'shutdown', '-h', 'now'])

def restart():
    restart = tk.messagebox.askquestion("Confirm","Do you want to restart?")
    if restart == 'no':print('no')
    else:subprocess.run(["sudo", "shutdown", "-r", "now"])

