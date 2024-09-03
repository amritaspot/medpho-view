import tkinter as tk
from tkinter import Label, Button, Entry, Menu, LabelFrame, messagebox
from tkinter import StringVar
from tkinter import CENTER, TOP, LEFT, FLAT, NO, BOTTOM, X
from tkinter import ttk, Tk, Toplevel

import os
import csv
import numpy as np

from tinydb import TinyDB, Query
from PIL import Image, ImageTk
from datetime import datetime

import matplotlib.pyplot as plt
import webbrowser
import qrcode

from scipy.optimize import curve_fit

import deviceinfo
import imagepro
import widgets
import hardwaretest
import exitprocess
import screen_config
import utils
import results
import printer
# Initialize TinyDB databases for results and analytes
db = TinyDB(deviceinfo.path + 'results/results.json')
analytedb = TinyDB(deviceinfo.path + 'analytes.json')

# Define a query object for querying the databases
Sample = Query()

# Initialize a global array for storing general calibration data
global gencal_array
gencal_array = [""] * 9  # Array with 9 empty string elements

# results.json format
# {"_default": {"1": {"sampleid": "1", "analyte": "", "calid": "","caldate": "","expdate": "","measl": "","measu": "", "result": "","unit": "" "date": "21/01/2023", "name": "b/o a", "gender": "female", "age": "3"}}

# analytes.json format
# {"_default": {"1": {"analyte": "G6PD", "calid": "1/0/0/0", "caldate": "01/2023","expdate": "01/2023", "unit": "", "batchid": "LFA001", "measl":"0", "measu":"6"}}

# data_array format
# ["sampleid","analyte","cal_id","value","date","name","age","gender","refer", "unit", "measl", "measu", "batchid"]

# gencal_array format
# ["analyte","cal_id","date", "expdate", "unit", "type","batchid","measl","measu"]

# qr code string format
# "analyte;calid;caldate;expdate;unit;batchid;measl;measu"
# examples:
# "TSH;-90/45/1598/230;01/2023;03/2024;mg/ml;0123-01;5.0;50.0"
# "17OHP;1/21/56/0;10/2021;12/2023;ng/ml;01/89/98"

# calid format
# fit/const1/const2/const3/const4
# fit= 1: linear; 2: log-linear; 3:power; 4:4pl
# example
# 1/0.07/9.3/0
#---------------------------------------------------screens------------------------------------------------------------------------------------------------------------
def Splash():
    global splash
    splash = Tk()
    screen_config.screen_config(splash)
    logo_path = deviceinfo.path+"splash_logo.png"
    logo = Image.open(logo_path)
    img = ImageTk.PhotoImage(logo)
    try:
        hardwaretest.at_boot(0)
    except:
        results.usesummary('Hardware test not run at boot')
    Label(splash, text="Made For", font = screen_config.labelfont,background = "white", justify = 'left').place(relx=0.1,rely=0.2,anchor=CENTER)
    Label(splash, image=img, background = "white").place(relx=0.52,rely=0.4,anchor=CENTER)
    Button(splash, bd=0, text="Start Testing", font = ("Helvetica", "24",), background = "white",command= lambda:Homepage()).place(relx=0.5,rely=0.67,anchor=CENTER)

    # bottom_img = ImageTk.PhotoImage(Image.open(deviceinfo.path+"bottom_logo.png"))

    # Label(splash, image=bottom_img, background = "white").place(relx=0.5,rely=0.85,anchor=CENTER)

    global prevscreen
    prevscreen = []
    global conc_array
    conc_array = []
    global result_array
    result_array = []
    global tl_array
    tl_array = []
    global cl_array
    cl_array = []
#-------------------------------------------Settings screens---------------------------------------------------
    def drawMenu(parent):
        menubar = Menu(parent, font = screen_config.menufont, relief=FLAT, bd=0)
        homep = Menu(menubar, tearoff = 0)
        menubar.add_cascade(label ='Test', menu = homep, font = screen_config.menufont )
        homep.add_command(label="Start Testing", font = screen_config.buttonfont,command = lambda:Homepage()) #command=imagepro.addparaqr)
        homep.add_command(label="Biomarkers", font = screen_config.buttonfont,command=lambda:AnalyteView())
        homep.add_command(label ='Add Biomarkers', font = screen_config.buttonfont, command = lambda:AddParameter())

        result = Menu(menubar, tearoff = 0)
        menubar.add_cascade(label ='Results', menu = result, font = screen_config.menufont)
        result.add_command(label ='View Results', font = screen_config.buttonfont, command = lambda:ResultView())
        result.add_command(label ='Search Results', font = screen_config.buttonfont, command = lambda:SearchView())

        settings = Menu(menubar, tearoff = 0)
        menubar.add_cascade(label ='Settings', menu = settings, font = screen_config.menufont)
        settings.add_command(label ='Device Overview ', font = screen_config.buttonfont, command = lambda:DeviceInfo())
        settings.add_command(label ='Data Backup & Updates', font = screen_config.buttonfont, command = lambda:DeviceData())
#         settings.add_command(label ='Connect to Wifi', font = screen_config.buttonfont, command = lambda:DeviceSettings())
        settings.add_command(label= 'Connect to Wifi ', font = screen_config.buttonfont, command= lambda:widgets.askquestion("Connect to wifi ?", WifiInfo,''))
#         settings.add_command(label ='Change Admin Password', font = screen_config.buttonfont, command = lambda:AdminPassword())
        settings.add_command(label ='Troubleshoot', font = screen_config.buttonfont, command = lambda:Hardwarescan())
        # settings.add_command(label ='Service Access', font = screen_config.buttonfont, command = lambda:servicerun(utils.connectvpn, "connect remotely"))
#         if deviceinfo.factorystate=="service":
#             service.add_command(label ='Generate Calid', font = screen_config.buttonfont, command = lambda:factoryrun(Gencal, "enter factory mode",[], [], gencal_array, [], []))

        shutdown = Menu(menubar, tearoff = 0)
        menubar.add_cascade(label ='Power', menu = shutdown, font = screen_config.menufont)
        shutdown.add_command(label ='Shutdown', font = screen_config.buttonfont, command = lambda:exitprocess.poweroff())
#         shutdown.add_command(label ='Restart', font = screen_config.buttonfont, command = lambda:exitprocess.restart())
        shutdown.add_command(label ='Exit Application', font = screen_config.buttonfont, command = lambda:exitapp(splash.destroy, "exit application"))
        parent.config(menu = menubar)

    def DeviceInfo():
        # Log the event of viewing device overview
        results.usesummary('Device Overview seen')

        global sysinfo
        sysinfo = Toplevel()
        screen_config.screen_config(sysinfo)
        drawMenu(sysinfo)
        sys_time = datetime.now().replace(microsecond=0)

        # Display system information
        Label(sysinfo, text=" Device Overview  ", font=screen_config.menufont, background="white", justify="center").place(relx=0.3, rely=0.08)
#         Label(sysinfo, text="____________________________________________________________________________________________________________________",font=screen_config.labelfont, background="white", justify="center").place(relx=0.1, rely=0.12)
        Label(sysinfo, text=f"Device ID: {deviceinfo.device_id}", font=("Helvetica", "14", "bold"), background="white", justify="left").place(relx=0.1, rely=0.2)
        Label(sysinfo, text=f"Date/Time: {sys_time}",font=("Helvetica", "14", "bold"),background="white",justify="left").place(relx=0.1, rely=0.3)
        Label(sysinfo, text=f"SW VER:    {deviceinfo.software_version}", font=("Helvetica", "14", "bold"), background="white", justify="left").place(relx=0.1, rely=0.4)
        Label(sysinfo, text=f"Mfg.Date:  {deviceinfo.install_date}", font=("Helvetica", "14", "bold"), background="white", justify="left").place(relx=0.1, rely=0.5)
        Label(sysinfo, text=f"Installed For:  {deviceinfo.lab_name}", font=("Helvetica", "14", "bold"), background="white", justify="left").place(relx=0.1, rely=0.6)
        Label(sysinfo, text=f"Lab Add.:  {deviceinfo.lab_address}", font=("Helvetica", "14", "bold"), background="white", justify="left").place(relx=0.1, rely=0.7)
        Button(sysinfo, text="Update Lab Info",font=screen_config.buttonfont, width=14, background="white",command=Info).place(relx=0.1, rely=0.8)
        Button(sysinfo, text="Sync Time",font=("Helvetica", "14", "bold"), width=12,background="white",command=TimeInfo).place(relx=0.5, rely=0.28 )
        # Load and display the lab logo
        try:
            image_path = deviceinfo.path + "lab_logo.png"
            imagecopy = Image.open(image_path).resize((100, 100))
            logo_img = ImageTk.PhotoImage(imagecopy)
            label = Label(sysinfo, image=logo_img, background="white")
            label.image = logo_img
            label.place(relx=0.9, rely=0.2, anchor=CENTER)
        except Exception as e:
            print(e)
            results.usesummary(f"Error loading lab logo: {e}")   
    
    
    def Info():
        # Log the event of accessing device info page
        results.usesummary('Update Lab info page accessed')

        global info
        info = Toplevel()
        screen_config.screen_config(info)
        drawMenu(info)

        # Define common widget properties
        widget_props = {
            'font': screen_config.smallfont,
            'background': "white",
            'justify': "left"
        }

        # Define uniform label properties
        label_props = widget_props.copy()
        label_props.update({'justify': "center"})

        # Create and place labels and entries
        labels = [
            ("Enter lab name", 0.1, 0.2),
            ("Enter lab address", 0.1, 0.3),
            ("Enter referral doctor", 0.1, 0.4)]
            # ("Admin password", 0.1, 0.5)]

        entries = []
        for text, x, y in labels:
            Label(info, text=text, **label_props).place(relx=x, rely=y)
            entry = Entry(info, **widget_props)
            entry.place(relx=0.5, rely=y)
            entries.append(entry)

        labE, addE, refE, passE = entries

        # Update button
        # Button(
        #     info,
        #     text="Upload logo and signature",
        #     font= screen_config.smallfont,
        #     command=lambda: update(labE, addE, refE, passE)
        # ).place(relx=0.6, rely=0.5)
            

        
        def update(labE, addE, refE, passE):
            # password = passE.get()

            # if password == deviceinfo.admin_pwd:
                # Ask if the user wants to update the signature and lab logo
            widgets.askquestion(info, "Do you want to update signature?", utils.sigupdate, '')
            widgets.askquestion(info, "Do you want to update lab logo?", utils.logoupdate, '')

            # Retrieve and update the lab name and address
            lab_name = labE.get()
            lab_add = addE.get()
            utils.updatedeviceinfo('lab_name', deviceinfo.lab_name, lab_name)
            utils.updatedeviceinfo('lab_address', deviceinfo.lab_address, lab_add)

            # Notify the user and log the update
            widgets.error( "Lab Info Updated")
            results.usesummary("Lab Info updated")

            # else:
            #     widgets.error(info, "Incorrect Admin Password")

        widgets.drawKeyboard(info)
        screen_config.kill_previous(prevscreen)
        prevscreen.append(info)
        info.mainloop()
        
    def TimeInfo():
        global timeinfo
        timeinfo = Toplevel()
        screen_config.screen_config(timeinfo)
        drawMenu(timeinfo)

        # Define common widget properties
        widget_props = {
            'font': screen_config.smallfont,
            'background': "white",
            'justify': "left"
        }

        # Define uniform label properties
        label_props = widget_props.copy()
        label_props.update({'justify': "center"})

        # Create and place labels
        labels = [
            ("Current System Time: " + str(datetime.now().replace(microsecond=0)), 0.3, 0.1),
            ("Date (MM/DD/YYYY)", 0.1, 0.2),
            ("Time (HH:MM:SS (24 hr))", 0.1, 0.3)] 
            # ("Admin password", 0.1, 0.4)]

        for text, x, y in labels:
            Label(timeinfo, text=text, **label_props).place(relx=x, rely=y)

        # Create and place entries
        dateE = Entry(timeinfo, **widget_props)
        dateE.place(relx=0.5, rely=0.2)

        timeE = Entry(timeinfo, **widget_props)
        timeE.place(relx=0.5, rely=0.3)

        passE = Entry(timeinfo, show="*", **widget_props)
        passE.place(relx=0.5, rely=0.4)

        # Update button
        # Button(
        #     timeinfo,
        #     text="Update Date and Time",
        #     font=screen_config.smallfont,
        #     background="white",
        #     command=lambda: onpress(dateE, timeE, passE)
        # ).place(relx=0.5, rely=0.5)

        def onpress(dateE, timeE, passE):
            # password = passE.get()

            # if password == deviceinfo.admin_pwd:
            utils.change_time(dateE, timeE, passE)
            widgets.error( "System time updated")
            TimeInfo()  # Refresh the time info window
            # else:
            #     widgets.error(timeinfo, "Incorrect Admin Password")

        widgets.drawKeyboard(timeinfo)
        screen_config.kill_previous(prevscreen)
        prevscreen.append(timeinfo)
        timeinfo.mainloop()



        # Manage previous screen history and start the main loop
        screen_config.kill_previous(prevscreen)
        prevscreen.append(sysinfo)
        sysinfo.mainloop()


    def DeviceData():
        # Log the event of accessing the Data Backup page
        results.usesummary('Data Backup page accessed')

        global devicedata
        devicedata = Toplevel()
        screen_config.screen_config(devicedata)
        drawMenu(devicedata)

        # Title Label
        Label(
            devicedata,
            text="-------Backup or Restore the data------",
            font=screen_config.smallfont,
            background="white",
            justify="center"
        ).place(relx=0.1, rely=0.1)

        # Attempt to fetch available memory and update device info
        try:
            avail_mem = str(hardwaretest.Diskmemcheck(''))
        except Exception as e:
            avail_mem = "Could not be fetched"
            results.usesummary(f"Error fetching memory info: {e}")

        utils.updatedeviceinfo('avail_mem', deviceinfo.avail_mem, avail_mem)

        # Labels for device data
        Label(
            devicedata,
            text=f"Last Backup: {deviceinfo.backup_time}",
            font=screen_config.labelfont,
            background="white",
            justify="left"
        ).place(relx=0.1, rely=0.2)

        Label(
            devicedata,
            text=f"Available Memory (%): {deviceinfo.avail_mem}",
            font=screen_config.labelfont,
            background="white",
            justify="left"
        ).place(relx=0.1, rely=0.3)

        # Buttons for data operations
        Button(
            devicedata,
            text="Backup Data",
            width=20,
            font=screen_config.labelfont,
            background="white",
            command=utils.results_backup
        ).place(relx=0.05, rely=0.5)

        Button(
            devicedata,
            text="Restore Data from USB",
            width=20,
            font=screen_config.labelfont,
            background="white",
            command=utils.restore
        ).place(relx=0.35, rely=0.5)

        Button(
            devicedata,
            text="Update Device from USB",
            width=20,
            font=screen_config.labelfont,
            background = 'gray',
            bd = 0,
            command=utils.update
        ).place(relx=0.05, rely=0.7)

        # Manage previous screen history and start the main loop
        screen_config.kill_previous(prevscreen)
        prevscreen.append(devicedata)
        devicedata.mainloop()

    def DeviceSettings():
        # Log the event of accessing the device settings page
        results.usesummary('Wifi page accessed')

        global settings
        settings = Toplevel()
        screen_config.screen_config(settings)
        drawMenu(settings)

        # Define global buttons
        global btn1, btn2, btn3

        # Title and system information labels
        Label(
            settings,
            text="Connect to Wifi",
            font=screen_config.menufont,
            background="white",
            justify="center"
        ).place(relx=0.1, rely=0.5)

        # Settings labels
        Label(
            settings,
            text="WiFi: ",
            font=screen_config.labelfont,
            background="white",
            justify="left"
        ).place(relx=0.1, rely=0.2)

        Button(
            settings,
            text="Connect to Wifi",
            font=screen_config.buttonfont,
            width=18,
            background="white",
            command=lambda: WifiInfo
        ).place(relx=0.2, rely=0.2)

        # Manage previous screen history and start the main loop
        screen_config.kill_previous(prevscreen)
        prevscreen.append(settings)
        settings.mainloop()

    def WifiInfo():
        global wifiinfo
        print(422)
        wifiinfo = Toplevel()
        screen_config.screen_config(wifiinfo)
        drawMenu(wifiinfo)
        ssid_list=[]
        try:
            # Get the list of available WiFi networks
            ssid_list = utils.list_wifi()
            print(ssid_list)
        except:
            ssid_list = []
            widgets.error("No networks detected")
            # Set up the GUI elements for selecting WiFi and entering passwords
        var = StringVar()
        Label(wifiinfo, text="Select WiFi network", font=screen_config.labelfont, background="white", justify="center").place(relx=0.1, rely=0.1)
        ssidE = ttk.Combobox(wifiinfo, textvariable=var, state="readonly", values=ssid_list, font=screen_config.buttonfont, width=20)
        ssidE.place(relx=0.5, rely=0.1)
        ssidE.set("SELECT SSID")

        Label(wifiinfo, text="Enter WiFi password", font=screen_config.labelfont, background="white", justify="center").place(relx=0.1, rely=0.2)
        wpassE = Entry(wifiinfo, font=screen_config.smallfont, background="white", justify="left", width=20)
        wpassE.place(relx=0.5, rely=0.2)

        # Label(wifiinfo, text="Admin password", font=screen_config.smallfont, background="white", justify="center").place(relx=0.1, rely=0.3)
        # passE = Entry(wifiinfo, show="*", font=screen_config.smallfont, background="white", justify="left")
        # passE.place(relx=0.5, rely=0.3)

        # Button to connect to the selected WiFi
        Button(wifiinfo, text="Connect", font=screen_config.labelfont, background="white", command=lambda: utils.update_wifi(ssidE, wpassE, '')).place(relx=0.45, rely=0.5)

        # Draw the on-screen keyboard and manage the previous screen
        widgets.drawKeyboard(wifiinfo)
        screen_config.kill_previous(prevscreen)
        prevscreen.append(wifiinfo)
        wifiinfo.mainloop()
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def AddParameter():
        global addpara, batchE, caldateE, calidE, testdrop
        results.usesummary('Add Parameter page accessed')
        addpara = Toplevel()
        screen_config.screen_config(addpara)
        drawMenu(addpara)

        def create_label(text, relx, rely):
            return Label(addpara, text=text, font=screen_config.labelfont, background="white", justify="center").place(relx=relx, rely=rely)

        def create_entry(default_text, relx, rely):
            entry = Entry(addpara, font=screen_config.labelfont)
            entry.insert(0, default_text)
            entry.place(relx=relx, rely=rely)
            return entry

        def create_combobox(values, default_text, relx, rely):
            var = StringVar()
            combobox = ttk.Combobox(addpara, textvariable=var, values=values, font=screen_config.labelfont, width=15)
            combobox.place(relx=relx, rely=rely)
            combobox.set(default_text)
            return combobox

        def gen_qr():
            analyte = testdrop.get()
            unit = unitdrop.get()
            batchid = batchE.get()
            caldate = caldateE.get()
            expdate = expdateE.get()
            calid = calidE.get()
            measl = measlE.get()
            measu = measuE.get()

            qrstring = f"{analyte};{calid};{caldate};{expdate};{unit};{batchid};{measl};{measu}"
            widgets.error( qrstring)
            img = qrcode.make(qrstring)
            img.save(deviceinfo.path + f'qr/{batchid}.png')
            img = img.resize((100, 100))
            img.save(deviceinfo.path + f'qr/{batchid}_resized.png')
            widgets.error( f"QR code generated for batchid: {batchid}")

        def on_press():
            analyte = testdrop.get()
            unit = unitdrop.get()
            batchid = batchE.get()
            caldate = caldateE.get()
            expdate = expdateE.get()
            calid = calidE.get()
            measl = measlE.get()
            measu = measuE.get()

            if any(field == '' for field in [analyte, batchid, expdate]) or measl in ['Lower Limit', ''] or measu in ['Upper Limit', '']:
                widgets.error( "Parameter information is missing")
                return

            if utils.checkcaldate(caldate) and utils.checkcalid(calid):
                utils.updatepara(analyte, calid, caldate, expdate, batchid, measl, measu, unit)
            else:
                widgets.error( "Incorrect information format")

        # Populate analyte and unit lists
        analytelist = [test['analyte'] for test in TinyDB(deviceinfo.path + 'analytes.json').all()]
        unitlist = [' ', 'mg/L', 'mg/dl', 'ng/ml', 'pg/ml', 'IU/ml', 'uIU/ml']

        # Create UI elements
        create_label("Enter batchid", 0.1, 0.15)
        batchE = create_entry("", 0.5, 0.15)

        create_label("Enter Calid", 0.1, 0.35)
        calidE = create_entry("", 0.5, 0.35)
        if deviceinfo.factorystate == "service":
            Button(addpara, text="Gen CalID", font=screen_config.labelfont, width=10, bd=0, command=gen_qr).place(relx=0.8, rely=0.33)

        create_label("Enter Cal date (MM/YY)", 0.1, 0.45)
        caldateE = create_entry("", 0.5, 0.45)

        create_label("Enter Exp date (MM/YY)", 0.1, 0.25)
        expdateE = create_entry("", 0.5, 0.25)

        testdrop = create_combobox(analytelist, "Enter Biomarker ", 0.05, 0.05)
        testdrop.set("Enter Analyte")
        unitdrop = create_combobox(unitlist, "Enter Units", 0.3, 0.05)
        unitdrop.set("Enter Units")

        measlE = create_entry("Lower Limit", 0.55, 0.05)
        measuE = create_entry("Upper Limit", 0.75, 0.05)

        Button(addpara, text="Proceed", font=screen_config.labelfont, width=10, bd=0, command=on_press).place(relx=0.5, rely=0.55)
        Button(addpara, text="Scan QR", font=screen_config.labelfont, width=10, bd=0, command=imagepro.addparaqr).place(relx=0.7, rely=0.55)

        if deviceinfo.factorystate == "service":
            Button(addpara, text="Proceed", font=screen_config.labelfont, width=10, bd=0, command=on_press).place(relx=0.1, rely=0.55)
            Button(addpara, text="Scan QR", font=screen_config.labelfont, width=10, bd=0, command=imagepro.addparaqr).place(relx=0.3, rely=0.55)
            Button(addpara, text="Gen QR", font=screen_config.labelfont, width=10, bd=0, command=gen_qr).place(relx=0.5, rely=0.55)
            Button(addpara, text="Add csv", font=screen_config.labelfont, width=10, bd=0, command=utils.addcsv).place(relx=0.7, rely=0.55)

        widgets.drawKeyboard(addpara)
        screen_config.kill_previous(prevscreen)
        prevscreen.append(addpara)
        addpara.mainloop()

#-------------------------------------------------------------------------------------------------------------------
    def Hardwarescan():
        global hscan
        hscan = Toplevel()
        screen_config.screen_config(hscan)
        drawMenu(hscan)
        btn1 = Button(hscan, activebackground='#ff0000', text = "Check available memory", font=screen_config.smallfont, width = 30, bd = 0, command = lambda: hardwaretest.Diskmemcheck(btn1))
        btn1.place(relx=0.1,rely=0.1)
        btn2 = Button(hscan, activebackground='#ff0000',text = "Check SD card speed", font=screen_config.smallfont, width = 30, bd = 0, command = lambda: hardwaretest.speedcheck(btn2))
        btn2.place(relx=0.5,rely=0.1)
        btn3 = Button(hscan, activebackground='#ff0000',text = "Check CPU utilization", font=screen_config.smallfont, width = 30, bd = 0, command = lambda: hardwaretest.Rammemcheck(btn3))
        btn3.place(relx=0.1,rely=0.3)
        btn4 = Button(hscan, activebackground='#ff0000',text = "Check undervoltages", font=screen_config.smallfont, width = 30, bd = 0, command = lambda: hardwaretest.undervolt(btn4))
        btn4.place(relx=0.5,rely=0.3)
        btn5 = Button(hscan, activebackground='#ff0000',text = "Check system clock", font=screen_config.smallfont, width = 30, bd = 0, command = lambda: hardwaretest.RTCactive(btn5))
        btn5.place(relx=0.1,rely=0.5)
        
        Button(hscan, text = "Complete scan", activebackground='#ff0000',font=screen_config.smallfont, width = 30, bd = 0, command = lambda: hardwaretest.at_boot(1)).place(relx=0.5,rely=0.5)        
        
        Button(hscan, text = "View reports", font=screen_config.smallfont, width = 15, bd = 0, command = lambda: utils.browseFiles(deviceinfo.path+"hardwaretest", '*.pdf')).place(relx=0.1,rely=0.7)
        Button(hscan, text = "Access images", font=screen_config.smallfont, width = 15, bd = 0, command = lambda: utils.browseFiles(deviceinfo.path+"captured", '*.jpg')).place(relx=0.4,rely=0.7)
        Button(hscan, text = "Access summary", font=screen_config.smallfont, width = 15, bd = 0, command = lambda: utils.browseFiles(deviceinfo.path+"usesummary", '*.csv')).place(relx=0.7,rely=0.7)
        
        screen_config.kill_previous(prevscreen)
        prevscreen.append(hscan)
        hscan.mainloop() 

    def exitapp(function, name):
        screen_config.kill_previous(prevscreen)
        global exitpage
        exitpage = Toplevel()
        screen_config.screen_config(exitpage)
        drawMenu(exitpage)
        prevscreen.append(exitpage)
        
        Label(exitpage, text="Enter service password to "+name, font = screen_config.smallfont, background = "white", justify="center").place(relx=0.5,rely=0.15,anchor=CENTER)
        
        passE = Entry(exitpage,show="*",font = screen_config.titlefont)
        passE.place(relx=0.5,rely=0.3,anchor=CENTER)
        
        def exit_app():
            password = passE.get()
            if (password==deviceinfo.service_pwd): function()
            else: widgets.error("Service password is incorrect")
        
        Button(exitpage, text='Proceed', font = screen_config.buttonfont, width = 15,background = "white", command=lambda: exit_app()).place(relx=0.3,rely=0.5,anchor=CENTER)
        Button(exitpage, text='Cancel', font = screen_config.buttonfont, width = 15, background = "white", command=lambda: Homepage()).place(relx=0.6,rely=0.5,anchor=CENTER)
        widgets.drawKeyboard(exitpage)
        exitpage.mainloop()
#-----------------------------------------------------------------------------------------------------------------------
    def create_service_page(page_class, function, *args):
        screen_config.kill_previous(prevscreen)
        page = page_class()
        screen_config.screen_config(page)
        drawMenu(page)
        prevscreen.append(page)

        # Label(page, text=f"Enter service password to {function.__name__}", font=screen_config.smallfont, background="white", justify="center").place(relx=0.5, rely=0.15, anchor=CENTER)

        # passE = Entry(page, show="*", font=screen_config.titlefont)
        # passE.place(relx=0.5, rely=0.3, anchor=CENTER)

        def handle_proceed():
            # password = passE.get()
            # if password == deviceinfo.service_pwd:
            function(*args)
            # else:
            #     widgets.error(page, "Service password is incorrect")

        Button(page, text='Proceed', font=screen_config.buttonfont, width=15, background="white", command=handle_proceed).place(relx=0.3, rely=0.5, anchor=CENTER)
        Button(page, text='Cancel', font=screen_config.buttonfont, width=15, background="white", command=Homepage).place(relx=0.6, rely=0.5, anchor=CENTER)

        widgets.drawKeyboard(page)
        page.mainloop()
    def servicerun(function, name):
        create_service_page(Toplevel, function)
#----------------------------------------------------------------
    # def AdminPassword():
    #     def change_pass():
    #         old_password = oldpassE.get()
    #         new_password = newpassE.get()
    #         devpass = devpassE.get()

    #         if old_password == deviceinfo.admin_pwd and devpass == deviceinfo.service_pwd:
    #             utils.updatedeviceinfo('admin_pwd', old_password, new_password)
    #             widgets.error(adminpass, "Admin Password was changed")
    #             results.usesummary("Admin password was changed")
    #         else:
    #             widgets.error(adminpass, "Incorrect Credentials")
    #         Homepage()

    #     # Create new Toplevel window
    #     adminpass = Toplevel()
    #     screen_config.screen_config(adminpass)
    #     drawMenu(adminpass)
    #     screen_config.kill_previous(prevscreen)
    #     prevscreen.append(adminpass)

    #     # Set up the layout for the password change form
    #     Label(adminpass, text="Enter old admin password", font=screen_config.labelfont, background="white", justify="center").place(relx=0.3, rely=0.1, anchor=CENTER)
    #     oldpassE = Entry(adminpass, show="*", font=screen_config.labelfont)
    #     oldpassE.place(relx=0.7, rely=0.1, anchor=CENTER)

    #     Label(adminpass, text="Enter new admin password", font=screen_config.labelfont, background="white", justify="center").place(relx=0.3, rely=0.2, anchor=CENTER)
    #     newpassE = Entry(adminpass, show="*", font=screen_config.labelfont)
    #     newpassE.place(relx=0.7, rely=0.2, anchor=CENTER)

    #     Label(adminpass, text="Enter service password", font=screen_config.labelfont, background="white", justify="center").place(relx=0.3, rely=0.3, anchor=CENTER)
    #     devpassE = Entry(adminpass, show="*", font=screen_config.labelfont)
    #     devpassE.place(relx=0.7, rely=0.3, anchor=CENTER)

    #     Button(adminpass, text='Change Password', font=screen_config.buttonfont, width=15, background="white", command=change_pass).place(relx=0.3, rely=0.5, anchor=CENTER)
    #     Button(adminpass, text='Cancel', font=screen_config.buttonfont, width=15, background="white", command=Homepage).place(relx=0.6, rely=0.5, anchor=CENTER)

    #     widgets.drawKeyboard(adminpass)
    #     adminpass.mainloop()

#---------------------------------------------------------------------------------------------------------------------- 
    
    def Homepage():
        global homepage
        homepage = Toplevel()
        db = TinyDB(deviceinfo.path+'results/results.json')
        analytedb = TinyDB(deviceinfo.path+'analytes.json')
        Sample = Query()
        global sampleidE
        global sampleE
        
        data_array = ["","","","","","","","","","",""]
        screen_config.screen_config(homepage)
        drawMenu(homepage)
        
        Label(homepage, text = "Enter Sample ID",font = screen_config.menufont, background = "white").place(relx=0.2,rely=0.25,anchor=CENTER)
        sampleidE = Entry(homepage, font = screen_config.buttonfont)
        
        sampleidE.place(relx=0.35,rely=0.2)
        analytelist = ['Add New']
        analytedb = TinyDB(deviceinfo.path+'analytes.json')
        testlist = analytedb.all()
        testlist = sorted(testlist, key = lambda x: x['analyte'])
        for test in testlist:
            if test['analyte'] not in analytelist:
                analytelist.append(test['analyte'])
        var = StringVar()
        testdrop= ttk.Combobox(homepage,textvariable=var, state="readonly", values=analytelist, font = screen_config.menufont, width=12)
        testdrop.place(relx=0.7, rely=0.2)
        testdrop.set("Select Test ")
        Button(homepage, bd=0, text = "Proceed", font = screen_config.menufont, justify="left", width =12, command = lambda: onpress(data_array)).place(relx=0.35,rely=0.35)    
        
    
        def onpress(data_array):
            try:
                analyte=testdrop.get()
                sampleid=str(sampleidE.get())
            except: widgets.error("Could not get analyte")
            try:
                if 'Select Test' in analyte:
                    widgets.error("Please select test")
                elif 'Add New' in analyte: AddParameter()
                elif (sampleid[0]=="0"):widgets.error("Sampleid shouldn't start with 0")
                else:
                    data_array[0]=str(sampleid)
                    data_array[1]=analyte
                    if db.search(Sample.sampleid == sampleid):
                        e = "Sampleid already exists. Proceed?"
                        widgets.askquestion(e,InstructionPage,data_array)
                    else:
                        results.usesummary("Test for "+str(sampleid)+" was initiated")
                        InstructionPage(data_array)                          
            except Exception as e:
                print(e)
                results.usesummary("Error occurred in test flow")
                widgets.error("Error occurred in test flow")                
        widgets.drawKeyboard(homepage)
        screen_config.kill_previous(prevscreen)
        prevscreen.append(homepage)
        homepage.mainloop()
        
    def InstructionPage(data_array):
        global instructionpage
        global caldrop
        
        instructionpage = Toplevel()
        screen_config.screen_config(instructionpage)
        drawMenu(instructionpage)
        
        # img = ImageTk.PhotoImage(Image.open(deviceinfo.path+"instructions.jpg"))
        
        Label(instructionpage, text = "Sample id: "+str(data_array[0])+":"+str(data_array[1]), font=screen_config.menufont, background = "white").place(relx=0.5,rely=0.1,anchor=CENTER)
        # Label(instructionpage, image = img, background = "white").place(relx=0.33,rely=0.4,anchor=CENTER)
        
        btn_img = ImageTk.PhotoImage(Image.open(deviceinfo.path+"scan_qr.png"))
        Button(instructionpage, background="white", image = btn_img, justify="center", command=lambda: imagepro.addparaqr()).place(relx=0.5,rely=0.4,anchor=CENTER)        

        analytedb = TinyDB(deviceinfo.path+'analytes.json')
        Sample = Query()
        testlist = analytedb.search(Sample.analyte==data_array[1])
        clist=[]       
        for test in testlist:
            if test['batchid'] not in clist:
                clist.append(test['batchid'])
        var = StringVar()
        caldrop= ttk.Combobox(instructionpage, textvariable=var, state="readonly", values=clist, font = screen_config.buttonfont, width=16)
        caldrop.place(relx=0.5,rely=0.65,anchor=CENTER)
        caldrop.set("Select BatchId")

        Button(instructionpage, background="white", text = "Run Test", font = screen_config.menufont, justify="left", command=lambda: onpress(data_array)).place(relx=0.5,rely=0.8,anchor=CENTER)
            
        def onpress(data_array):
            batchid=caldrop.get()
            if 'Select' in batchid:
                widgets.error("Please select BatchID")
                InstructionPage(data_array)
            analytedb = TinyDB(deviceinfo.path+'analytes.json')
            Sample = Query()
            callist=analytedb.search(Sample.batchid==batchid)
            
            for c in callist:
                calid=c['calid']
                unit = c['unit']
                data_array[2]=calid
                data_array[9]=unit
                data_array[10]=batchid
            
            print('calid '+str(data_array[2])+' unit'+str(data_array[9]))
            now = datetime.now()
            date = now.strftime("%d_%m_%Y_%H_%M")
            data_array[4]=date
            
            db = TinyDB(deviceinfo.path+'results/results.json')
            Sample = Query()
            searchlist = db.search(Sample.sampleid==str(data_array[0]))
            for s in searchlist:
                if s['name']=="": results.usesummary("No patient data for sampleid "+str(data_array[0]))
                else:
                    data_array[5]=s['name']
                    data_array[6]=s['age']
                    data_array[7]=s['gender']
                    data_array[8]=s['refer']
                    break
            print("data_array", data_array)
            ResultPage(data_array,0)
                
        screen_config.kill_previous(prevscreen)
        prevscreen.append(instructionpage)
        instructionpage.mainloop()
    
    def ResultPage(data_array,overwrite):        
        global resultpage
        resultpage = Toplevel()
        screen_config.screen_config(resultpage)
        drawMenu(resultpage)
        global bstate
        bstate = 'disabled'
        
        imagepro.read_test(data_array,overwrite)
               
        
        Label(resultpage, text = "Sample ID: " +data_array[0], font = screen_config.labelfont, background = "white", justify="left").place(relx=0.1,rely=0.1)
        Label(resultpage, text = "Date: " + data_array[4], font = screen_config.labelfont, background = "white", justify="left").place(relx=0.1,rely=0.2)

        Label(resultpage, text = "Analyte: " + data_array[1], font = screen_config.labelfont, background = "white", justify="left").place(relx=0.1,rely=0.3)
        Label(resultpage, text = "Cal_id: " + data_array[2], font = screen_config.labelfont, background = "white", justify="left").place(relx=0.1,rely=0.4)  
        print("Result: " + str(data_array[3])+ " " + data_array[9])
        if data_array[3].isnumeric == True:
            Label(resultpage, text = "Result: " + str(data_array[3])+ " " + data_array[9], font = screen_config.labelfont, background = "white", justify="left").place(relx=0.1,rely=0.5)
        elif data_array[3] == "Pos":
            Label(resultpage, text = "Result: " + str(data_array[3])+ " " + data_array[9], foreground='#ff0000', font = "Helvetica 14 bold", background = "white", justify="left").place(relx=0.1,rely=0.5)
        elif "Err" in data_array[3]:
            Label(resultpage, text = "Result: " + str(data_array[3]),foreground='#ff0000', font = "Helvetica 14 bold", background = "white", justify="left").place(relx=0.1,rely=0.5)
        else:
            Label(resultpage, text = "Result: " + str(data_array[3])+ " " + data_array[9], font = screen_config.labelfont, background = "white", justify="left").place(relx=0.1,rely=0.5)
        
        if data_array[5] and data_array[6] and data_array[7] != '':
            Label(resultpage, text = "Name: " + data_array[5], font = screen_config.labelfont, background = "white", justify="left").place(relx=0.1,rely=0.6)
            Label(resultpage, text = "Age: " + data_array[6]+"  Gender: " + data_array[7], font = screen_config.labelfont, background = "white", justify="left").place(relx=0.3,rely=0.6)
        
        sampleid = data_array[0]
        
        try: 
            image = Image.open(deviceinfo.path+'captured/roi_'+str(sampleid)+'_'+str(data_array[4])+'.jpg')
            imagecopy = image.resize((120, 120))
            cap_img = ImageTk.PhotoImage(imagecopy)
            Label(resultpage, image = cap_img, background = "white").place(relx=0.7,rely=0.2,anchor=CENTER)
        
            path = deviceinfo.path+'captured/peaks_'+str(sampleid)+'_1'+'_'+str(data_array[4])+'.png'
            image = Image.open(deviceinfo.path+'captured/peaks_'+str(sampleid)+'_1'+'_'+str(data_array[4])+'.png')
            imagecopy = image.resize((120, 120))
            imagecopy2 = image.resize((300, 300))
            imagecopy2 = ImageTk.PhotoImage(imagecopy2)
            plot_img = ImageTk.PhotoImage(imagecopy)
            Button(resultpage, image = plot_img, background = "white", command=lambda: utils.show_image(imagecopy2)).place(relx=0.7,rely=0.6,anchor=CENTER)
        except Exception as e:
            print(e)
            image = Image.open(deviceinfo.path+'captured/capturedimage_'+str(sampleid)+'_'+str(data_array[4])+'.jpg')
            imagecopy = image.resize((120, 120))
            cap_img = ImageTk.PhotoImage(imagecopy)
            Label(resultpage, image = cap_img, background = "white").place(relx=0.7,rely=0.2,anchor=CENTER)      

        if data_array[5]=="":
            bstate='disabled'
            results.usesummary("Patient data report was not generated because no patientid")
        else:
            bstate = 'normal'
            results.genpdf(data_array)    
        def showpdf():
            output = deviceinfo.path+'results/'+data_array[0]+'_'+data_array[1]+'_'+str(data_array[4])+'.pdf'
            webbrowser.open_new(output)
            
        # Button(resultpage, text = "View Report", state=bstate, bd=0, font = screen_config.labelfont, justify="left", width =15, command=lambda: showpdf()).place(relx=0.1,rely=0.8)
        Button(resultpage, text = "Re-test", bd=0, font = screen_config.labelfont, justify="left", width =15, command=lambda: ResultPage(data_array,1)).place(relx=0.4,rely=0.8)
        Button(resultpage, text = "Continue Test", bd=0, font = screen_config.labelfont, justify="left", width =15, command=lambda: Samplewid(data_array[0],data_array[1],data_array[2], data_array[9],data_array[10])).place(relx=0.7,rely=0.8)
        Button(resultpage, text= "Print Results", bd=0, font=screen_config.labelfont, justify="left", width=15,command=lambda: printer.thermalprint(data_array)).place(relx=0.1, rely=0.8)
        screen_config.kill_previous(prevscreen)
        prevscreen.append(resultpage)
        resultpage.mainloop()
        
    def Samplewid(sampleid, analyte, calid, unit,batchid):
        data_array = [str(sampleid),analyte,calid,"","","","","","",unit,batchid]
        global swidget
        swidget = Toplevel()
        global tempidE
        drawMenu(swidget)
        screen_config.screen_config(swidget)
        Label(swidget, text = "Testing for "+analyte+" with calid"+calid, background = 'white',font = screen_config.buttonfont, justify="left").place(relx=0.1,rely=0.1)    
        
        tempidE = Entry(swidget, font = screen_config.buttonfont)
        tempidE.place(relx=0.1,rely=0.3)
        tempidE.insert(0,str(sampleid))
        
        Button(swidget, bd=0, text = "Run Test", font = screen_config.buttonfont, justify="left", width =10, command = lambda: onpress(analyte, calid)).place(relx=0.5,rely=0.3)    
        
        def onpress(analyte, calid):
            sampleid = tempidE.get()
            searchearlier(sampleid)
            data_array[0]=sampleid
            results.usesummary("Test done for sampleid "+sampleid)
        
            now = datetime.now()
            date = now.strftime("%d_%m_%Y_%H_%M")
            data_array[4]=str(date)
            ResultPage(data_array,0)
    
        def searchearlier(sampleid):
            db = TinyDB(deviceinfo.path+'results/results.json')
            Sample = Query()
            searchlist = db.search(Sample.sampleid==sampleid)
            for s in searchlist:
                if s['name']=="":print('none')
                else:
                    data_array[5]=s['name']
                    data_array[6]=s['age']
                    data_array[7]=s['gender']
                    data_array[8]=s['refer']
                    break
            
        widgets.drawKeyboard(swidget)
        screen_config.kill_previous(prevscreen)
        prevscreen.append(swidget)
        swidget.mainloop()
    
    def PatientData(data_array):
        global IdE
        global nameE
        global ageE
        global var
        global referE
        
        global patientdata
        patientdata = Toplevel()
        screen_config.screen_config(patientdata)
        drawMenu(patientdata)

        Label(patientdata, text = "Sample Id:  "+ str(data_array[0]) ,font = screen_config.labelfont, background = "white", justify="left").place(relx=0.1,rely=0.01)
        Label(patientdata, text = "Patient Name",font = screen_config.smallfont, background = "white", justify="left").place(relx=0.1,rely=0.1)
        nameE = Entry(patientdata,font = screen_config.smallfont, background = "white")
        nameE.place(relx=0.5,rely=0.1)
            
        Label(patientdata, text = "Gender",font = screen_config.smallfont, background = "white", justify="left").place(relx=0.1,rely=0.2)
        genlist = ["Female", "Male", "Other"]
        var = StringVar()
        gendrop = ttk.Combobox(patientdata, textvariable = var, state = 'readonly', values = genlist, font =screen_config.smallfont, width = 20)
        gendrop.place(relx =0.5, rely = 0.2)
        gendrop.set("Gender")
        
        Label(patientdata, text = "Age ",font = screen_config.smallfont, background = "white", justify="left").place(relx=0.1,rely=0.3)
        ageE = Entry(patientdata, font = screen_config.smallfont, background = "white")
        ageE.place(relx=0.5,rely=0.3)
        
        Label(patientdata, text = "Referred by",font = screen_config.smallfont, background = "white", justify="left").place(relx=0.1,rely=0.4)
        referE = Entry(patientdata, font = screen_config.smallfont, background = "white")
        referE.place(relx=0.5,rely=0.4)
        
        Button(patientdata, text='Submit Details', bd=0, font = screen_config.buttonfont, width=10, command=lambda: widgets.askquestion("Proceed with patient details?", add_patientdetails, data_array)).place(relx=0.1,rely=0.5)
         
        def add_patientdetails(data_array):
            results.usesummary("Patient details were to be added")
        
            db = TinyDB(deviceinfo.path+'/results/results.json')
            Sample = Query()
            name = nameE.get()
            age = ageE.get()
            gender = var.get()
            refer = referE.get()
            if(name=='')or(gender=='')or(refer==''): widgets.error("Please enter all details")
            elif(age.isnumeric==False)or(int(age)<0)or(int(age)>120): widgets.error("Please enter valid age")
            else:
                data_array[5]=name
                data_array[6]=age
                data_array[7]=gender
                data_array[8]=refer
                try:
                    db = TinyDB(deviceinfo.path+'results/results.json')
                    db.update({'name': name, 'age': age, 'gender': gender, 'refer':refer}, Sample.sampleid == str(data_array[0]))
                    widgets.error( "Sample ID: "+str(data_array[0])+" is updated")
                    results.usesummary("Patient details for Sample ID: "+str(data_array[0])+" is updated")
                except Exception as e:
                    print(e)
                    widgets.error( "Could not update patient details")
                    results.usesummary("Could not update patient details.")
                ResultView()
        widgets.drawKeyboard(patientdata)
        prevscreen.append(patientdata)
        patientdata.mainloop()
    
    def treeview_sort_column(tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l): tv.move(k, '', index)
        tv.heading(col, text=col, command=lambda _col=col: treeview_sort_column(tv, _col, not reverse))

    def ResultView():
        results.usesummary("ResultView accessed")
        screen_config.kill_previous(prevscreen)
        global resultview
        resultview = Toplevel()
        screen_config.screen_config(resultview)
        prevscreen.append(resultview)
        drawMenu(resultview)
        global result_list
        columns = ('Sample_id','Name','Analyte','Result','Test Date')
        grid_frame = LabelFrame(resultview, text = 'All results', font = screen_config.smallfont, background="white")
        grid_frame.pack(side=TOP, fill = 'both')
        tree = ttk.Treeview(grid_frame, columns=columns, height=15, show='headings')
        tree.pack(side=TOP, fill = 'both')
            
        tree.heading('Sample_id', text='Sample Id', command=lambda: treeview_sort_column(tree, 'Sample_id', False))
        tree.column("Sample_id", width=150, stretch=NO)
        
        tree.heading('Name', text='Name', command=lambda: treeview_sort_column(tree, 'Name', False))
        tree.column("Name", width=150, stretch=NO)
        
        tree.heading('Analyte', text='Analyte', command=lambda: treeview_sort_column(tree, 'Analyte', False))
        tree.column("Analyte", width=150, stretch=NO)
        
        tree.heading('Result', text='Result', command=lambda: treeview_sort_column(tree, 'Result', False))
        tree.column("Result", width=150, stretch=NO)
        
#         tree.heading('Test Date', text='Test Date', command=lambda: treeview_sort_column(tree, 'Test Date', False))
#         tree.column("Test Date", width=150, stretch=NO)
        
        global pagenumber
        pagenumber = 0
        per_page = 15
       
        try: 
            db = TinyDB(deviceinfo.path+'results/results.json')
            arr = db.all()
            result_list = arr[::-1]
        except:
            widgets.error("No data fetched")
        
        n_pages = int(len(result_list)/per_page)
        
        def prev_btn(pagenumber):
            pagenumber = pagenumber-1
            if (pagenumber<0): pagenumber=0
            update_list(pagenumber)
        
        def next_btn(pagenumber):
            pagenumber = pagenumber+1
            update_list(pagenumber)
            
        def clear_all():
            for item in tree.get_children(): tree.delete(item)
                           
        def update_list(pagenumber):
            clear_all()
            readings = []
            start_index = pagenumber*per_page
            end_index = (pagenumber + 1)*per_page

            list_page = result_list[start_index:end_index]
            for l in list_page:
                readings.append((l['sampleid'],l['name'],l['analyte'], ((l['result'])+' '+l['unit']), (str(l['date'])+'.')))
            for reading in readings:
                tree.insert('', tk.END, values=reading)
        
        def singlereport(event):
            for selected_item in tree.selection():
                item = tree.item(selected_item)
                sampleid = item['values'][0]
                analyte = item['values'][2]
                date = item['values'][4]
                date = str(date).rstrip('.')
                data_array = ["","","","","","","","","","",""]
                data_array[0] = str(item['values'][0])
                data_array[1] = str(item['values'][2])
                data_array[3] = str(item['values'][3])
                data_array[4] = str(item['values'][4])
                try:
                    data_array[5] = str(item['values'][1])
                    slist = db.search(Sample.name==data_array[5])
                    s = slist[0]
                    data_array[6]=s['age']
                    data_array[7]=s['gender']
                    data_array[8]=s['refer']
                    results.genpdf(data_array)
                    x = deviceinfo.path+'results/'+str(sampleid)+'_'+str(analyte)+'_'+date+'.pdf'
                    webbrowser.open_new(x)
                    results.usesummary("Report for sampleid was accessed: "+str(sampleid))
                except Exception as e:
                    print(e)
                    widgets.error("Could not access report as there is no patient data")
                    results.usesummary("Could not access report as there is no patient data")
               
        tree.bind("<Double-1>",singlereport)
        
        def show_pdf():
            for selected_item in tree.selection():
                item = tree.item(selected_item)
                sampleid = str(item['values'][0])
                analyte=item['values'][2]
                try:
                    results.patientpdf(sampleid)
                    webbrowser.open_new(deviceinfo.path+'results/'+str(sampleid)+'.pdf')
                    results.usesummary("Full report for sampleid was generated: "+str(sampleid))
                except Exception as e:                     
                    results.usesummary("Full report for sampleid" +str(sampleid)+ " could not be generated.")
        
        def delr(sampleid):
            for selected_item in tree.selection():
                item = tree.item(selected_item)
                sampleid = item['values'][0]
                analyte=item['values'][2]
                date = item['values'][4]
                date = str(date).rstrip('.')
                x = deviceinfo.path+'results/'+str(sampleid)+'_'+str(analyte)+'_'+date+'.pdf'
                if os.path.isfile(x):
                   os.remove(x)
                   widgets.error(str(sampleid)+"deleted from records")
                   results.usesummary(str(sampleid)+"_"+str(analyte)+" deleted from records")
                else: widgets.error( "Could not delete record")
                
            tree.delete(*tree.selection())
        def search_results(search_list):
           clear_all()
           readings = []
           for l in search_list:
               readings.append((l['sampleid'], l['name'],l['analyte'], ((l['result'])+l['unit']),l['date']))
           for reading in readings:
               tree.insert('', tk.END, values=reading)
           string = 'Number of results fetched: '+str(len(search_list) )
           widgets.error(string)
           update_list(search_list,0)
        def Search(searchE):
           s = str(searchE.get())
           exp = s
           arr = TinyDB(deviceinfo.path+'results/results.json')
           Sample=Query()
           Querymod = ((Sample.sampleid.matches(exp))|(Sample.name.matches(exp))|(Sample.analyte.matches(exp))|(Sample.date.matches(exp))|(Sample.result.matches(exp)))
           results.usesummary("Results searched for: "+exp)

           search_list = arr.search(Querymod)
           result_list = search_list[::-1]
           if len(search_list)==0: widgets.error("No reports found")
           search_results(search_list)

        def del_record():
            arr = TinyDB(deviceinfo.path+'results/results.json')
            for selected_item in tree.selection():
                item = tree.item(selected_item)
                sampleid = item['values'][0] 
                result = item['values'][3]
                time = item['values'][4]
                try:
                    print(result, sampleid)
                    arr.remove((Sample.date == time)and(Sample.sampleid==sampleid))
                    widgets.error("Selected result was deleted")
                    Search(searchE)
                except Exception as e:
                    print(e)
                results.usesummary("User deleted from records"+str(sampleid)+"_"+str(time))

                q = "Delete pdf report for "+str(sampleid)+" ?"
                widgets.askquestion(q, delr, str(sampleid))
                ResultView()

        def adddetail():    
            data_array = ["","","","","","","","","","",""]
            for selected_item in tree.selection():
                item = tree.item(selected_item)
            data_array[0] = str(item['values'][0])
            data_array[1] = str(item['values'][2])
            data_array[3] = str(item['values'][3])
            data_array[4] = str(item['values'][4])
            #data_array[10] missing
            PatientData(data_array)
        #---------------------------------------------------------------------
            
        button_frame = LabelFrame(resultview, text = '',background="white")
        button_frame.pack(side = BOTTOM)
        Button(button_frame, text = "Prev", font = screen_config.labelfont, background="white", width=15, bd=0, command = lambda: prev_btn(pagenumber)).pack(side = LEFT)
        Button(button_frame, text = "Next", font = screen_config.labelfont, background="white", width=15, bd=0, command = lambda: next_btn(pagenumber)).pack(side = LEFT)
        Button(button_frame, text = "View Report", font = screen_config.labelfont, background="white",width=15, bd=0, command = lambda: show_pdf()).pack(side = LEFT)
        Button(button_frame, text = "Add Details", font = screen_config.labelfont, background="white", width=15, bd=0, command = lambda: adddetail()).pack(side = LEFT)
        # Button(button_frame, text = "Delete", font = screen_config.labelfont, background="white", width=15, bd=0, command = lambda: del_record()).pack(side = LEFT)
        
        update_list(0)
        resultview.mainloop()

    def SearchView():
        screen_config.kill_previous(prevscreen)
        global searchview
        searchview = Toplevel()
        screen_config.screen_config(searchview)
        prevscreen.append(searchview)
        drawMenu(searchview)
        
        global search_list
        global searchE
        search_list = []
        
        columns = ('Sample_id','Name','Analyte','Result','Test Date')

        search_frame = LabelFrame(searchview, text = '',background="white")
        search_frame.pack(side = TOP, fill = 'x')
        searchE = Entry(search_frame,  width = 25, font= screen_config.smallfont)
        searchE.pack(side = LEFT)

        def Search(searchE):
           s = str(searchE.get())
           exp = s
           arr = TinyDB(deviceinfo.path+'results/results.json')
           Sample=Query()
           Querymod = ((Sample.sampleid.matches(exp))|(Sample.name.matches(exp))|(Sample.analyte.matches(exp))|(Sample.date.matches(exp))|(Sample.result.matches(exp)))
           results.usesummary("Results searched for: "+exp)

           search_list = arr.search(Querymod)
           result_list = search_list[::-1]
           if len(search_list)==0: widgets.error("No reports found")
           search_results(search_list)

        def search_results(search_list):
           clear_all()
           readings = []
           for l in search_list:
               readings.append((l['sampleid'], l['name'],l['analyte'], ((l['result'])+l['unit']),l['date']))
           for reading in readings:
               tree.insert('', tk.END, values=reading)
           string = 'Number of results fetched: '+str(len(search_list) )
           widgets.error(string)
           update_list(search_list,0)

        
        tree = ttk.Treeview(searchview, columns=columns, show='headings')
        tree.pack(side=TOP, fill = 'x')
            
        tree.heading('Sample_id', text='Sample Id', command=lambda: treeview_sort_column(tree, 'Sample_id', False))
        tree.column("Sample_id", width=100, stretch=NO)
        
        tree.heading('Name', text='Name', command=lambda: treeview_sort_column(tree, 'Name', False))
        tree.column("Name", width=200, stretch=NO)
        
        tree.heading('Analyte', text='Analyte', command=lambda: treeview_sort_column(tree, 'Analyte', False))
        tree.column("Analyte", width=100, stretch=NO)
        
        tree.heading('Result', text='Result', command=lambda: treeview_sort_column(tree, 'Result', False))
        tree.column("Result", width=200, stretch=NO)
        
#         tree.heading('Test Date', text='Test Date', command=lambda: treeview_sort_column(tree, 'Test Date', False))
#         tree.column("Test Date", width=200, stretch=NO)
        
        readings = []
        global pagenumber
        pagenumber = 0
        per_page = 7
        n_pages = int(len(search_list)/per_page)
            
        def prev_btn(search_list, pagenumber):
            pagenumber = pagenumber-1
            if (pagenumber<0): pagenumber=0
            update_list(search_list,pagenumber)
           
        def next_btn(search_list,pagenumber):
            pagenumber = pagenumber+1
            update_list(search_list,pagenumber)
           
        def clear_all():
            for item in tree.get_children(): tree.delete(item)
            
        def delr(sampleid):
            for selected_item in tree.selection():
                item = tree.item(selected_item)
                sampleid = item['values'][0]
                analyte=item['values'][2]
                date = item['values'][4]
                date = str(date).rstrip('.')
                x = deviceinfo.path+'results/'+str(sampleid)+'_'+str(analyte)+'_'+date+'.pdf'
                if os.path.isfile(x):
                   os.remove(x)
                   widgets.error(str(sampleid)+"deleted from records")
                   results.usesummary(str(sampleid)+"_"+str(analyte)+" deleted from records")
                else: widgets.error("Could not delete record")
                
            tree.delete(*tree.selection())

            
        def del_record():
            arr = TinyDB(deviceinfo.path+'results/results.json')
            for selected_item in tree.selection():
                item = tree.item(selected_item)
                sampleid = item['values'][0] 
                result = item['values'][3]
                time = item['values'][4]
                try:
                    print(result, sampleid)
                    arr.remove((Sample.date == time)and(Sample.sampleid==sampleid))
                    widgets.error("Selected result was deleted")
                    Search(searchE)
                except Exception as e:
                    print(e)
                results.usesummary("User deleted from records"+str(sampleid)+"_"+str(time))

                q = "Delete pdf report for "+str(sampleid)+" ?"
                widgets.askquestion(q, delr, str(sampleid))
                SearchView()
            
        def update_list(search_list,pagenumber):
            clear_all()
            readings = []
            start_index = pagenumber*per_page
            end_index = (pagenumber + 1)*per_page
            list_page = search_list[start_index:end_index]
            print('list_page',list_page)
            for l in list_page:
                readings.append((l['sampleid'], l["name"], l['analyte'], (str(l['result'])+l['unit']),str(l['date'])+'.'))
            for reading in readings:
                tree.insert('', tk.END, values=reading)
            
        def show_pdf():
            for selected_item in tree.selection():
                item = tree.item(selected_item)
                sampleid = str(item['values'][0])
                results.patientpdf(sampleid)
                results.usesummary("Full report generated and viewed for "+str(sampleid))
                webbrowser.open_new(deviceinfo.path+'results/'+str(sampleid)+'.pdf')
        
        def adddetail():    
            data_array = ["","","","","","","","","",""]
            for selected_item in tree.selection():
                item = tree.item(selected_item)
                data_array[0] = str(item['values'][0])
                data_array[1] = str(item['values'][2])
                data_array[3] = str(item['values'][3])
                data_array[4] = str(item['values'][4])
            PatientData(data_array)
 
    
        Button(search_frame, text = "Search", font = screen_config.smallfont, background="white", width=10, command = lambda: Search(searchE)).pack(side = LEFT)
        Button(search_frame, text = "Prev", font = screen_config.smallfont, background="white", width=10, command = lambda: prev_btn(search_list,pagenumber)).pack(side = LEFT)
        Button(search_frame, text = "Next", font = screen_config.smallfont, background="white", width=10, command = lambda: next_btn(search_list,pagenumber)).pack(side = LEFT)
        Button(search_frame, text = "Delete", font = screen_config.smallfont, background="white",width=10, command = lambda: del_record()).pack(side = LEFT)
        Button(search_frame, text = "Report", font = screen_config.smallfont, background="white",width=10, command = lambda: show_pdf()).pack(side = LEFT)
        Button(search_frame, text = "Add Details", font = screen_config.smallfont, background="white",width=10, command = lambda: add_detail()).pack(side = LEFT)
        
        keyboard_frame = LabelFrame(searchview, text = '',background="white")
        keyboard_frame.pack(side = TOP, fill = 'x')

        widgets.drawKeyboard(keyboard_frame)
        searchview.mainloop()

    def AnalyteView():
        screen_config.kill_previous(prevscreen)
        global anaview
        anaview = Toplevel()
        screen_config.screen_config(anaview)
        prevscreen.append(anaview)
        drawMenu(anaview)
        global analyte_list
        columns = ('Analyte','BatchID','CalID','CalDate','ExpDate')
        grid_frame = LabelFrame(anaview, text = 'All biomarkers', font = screen_config.smallfont, background="white")
        grid_frame.pack(side=TOP, fill = 'both')
        tree = ttk.Treeview(grid_frame, columns=columns, height=15, show='headings')
        tree.pack(side=TOP, fill = 'both')
            
        tree.heading('Analyte', text='Biomarkers', command=lambda: treeview_sort_column(tree, 'Analyte', False))
        tree.column("Analyte", width=120, stretch=NO)
        
        tree.heading('BatchID', text='BatchID', command=lambda: treeview_sort_column(tree, 'BatchID', False))
        tree.column("BatchID", width=120, stretch=NO)
        
        tree.heading('CalID', text='CalID', command=lambda: treeview_sort_column(tree, 'CalID', False))
        tree.column("CalID", width=150, stretch=NO)
        
        tree.heading('CalDate', text='CalDate', command=lambda: treeview_sort_column(tree, 'CalDate', False))
        tree.column("CalDate", width=100, stretch=NO)
        
        tree.heading('ExpDate', text='ExpDate', command=lambda: treeview_sort_column(tree, 'ExpDate', False))
        tree.column("ExpDate", width=100, stretch=NO)
        
#         tree.heading('Lower Limit', text='Lower Limit', command=lambda: treeview_sort_column(tree, 'Lower Limit', False))
#         tree.column("Lower Limit", width=100, stretch=NO)
#         
#         tree.heading('Upper Limit', text='Upper Limit', command=lambda: treeview_sort_column(tree, 'Upper Limit', False))
#         tree.column("Upper Limit", width=100, stretch=NO)
                
        global pagenumber
        pagenumber = 0
        per_page = 15
       
        try: 
            db = TinyDB(deviceinfo.path+'analytes.json')
            arr = db.all()
            sorted_arr = sorted(arr, key = lambda x:x['analyte'], reverse = True)
            result_list = sorted_arr[::-1]
        except:
            widgets.error("No data fetched")
        
        n_pages = int(len(result_list)/per_page)
        
        def prev_btn(pagenumber):
            pagenumber = pagenumber-1
            if (pagenumber<0): pagenumber=0
            update_list(pagenumber)
        
        def next_btn(pagenumber):
            pagenumber = pagenumber+1
            update_list(pagenumber)
        
        def clear_all():
            for item in tree.get_children(): tree.delete(item)
                           
        def update_list(pagenumber):
            clear_all()
            readings = []
            start_index = pagenumber*per_page
            end_index = (pagenumber + 1)*per_page

            list_page = result_list[start_index:end_index]
            for l in list_page:
                readings.append((l['analyte'],l['batchid'],l['calid'],l['caldate'],l['expdate']))
            for reading in readings:
                tree.insert('', tk.END, values=reading)       

        def del_record():
            for selected_item in tree.selection():
                item = tree.item(selected_item)
                print('item',item['values'])
                batchid = item['values'][1]
            tree.delete(*tree.selection())
            analytedb = TinyDB(deviceinfo.path+'analytes.json')
            Sample = Query()
            analytedb.remove(Sample.batchid == str(batchid))
            results.usesummary("User deleted from analyte records calibration"+str(batchid))          
            widgets.error(str(batchid)+' deleted from the records')
            AnalyteView()
        
        def del_all(var):
            try:
                analytedb = TinyDB(deviceinfo.path+'analytes.json')
                analytedb.truncate()
                e = "All analyte records deleted from Database"
                results.usesummary(e)          
                widgets.error(e)
                AnalyteView()
            except Exception as e:
                widgets.error(str(e))
                results.usesummary(str(e))
        
        button_frame = LabelFrame(anaview, text = '',background="white")
        button_frame.pack(side = BOTTOM, fill = 'x')
        Button(button_frame, text = "Prev", font = screen_config.labelfont, background="white", width=10, bd=0, command = lambda: prev_btn(pagenumber)).pack(side = LEFT)
        Button(button_frame, text = "Next", font = screen_config.labelfont, background="white", width=10, bd=0, command = lambda: next_btn(pagenumber)).pack(side = LEFT)
        Button(button_frame, text = "Delete", font = screen_config.labelfont, background="white", width=10, bd=0, command = lambda: del_record()).pack(side = LEFT)
        Button(button_frame, text = "Remove All", font = screen_config.labelfont, background="white", width=10, bd=0, command = lambda: widgets.askquestion("This will delete all analyte data. Do you want to proceed?",del_all, 1)).pack(side = LEFT)
        update_list(0)

    
    def Gencal(tl_array, cl_array, gencal_array, conc_array, result_array):
        # gencal_array format
        # ["analyte","unit", "type", "batchid", "expdate", "measl","measu"]
        
        global gencal
        gencal = Toplevel()
        screen_config.screen_config(gencal)
        analytelist = []
        callist = ["Linear","Log-Linear","Power","4PL"]
        
        global analyte
        global calid
        global testdrop
        global caldrop
        global unitdrop
        global batchE
        global calE
        global expE
        global measlE
        global measuE
        global unit
        
        print(tl_array)
        print(cl_array)
        print(result_array)
        print(conc_array)
        
        analytedb = TinyDB(deviceinfo.path+'analytes.json')
        testlist = analytedb.all()
        
        for testl in testlist:
            if testl['analyte'] not in analytelist:
                analytelist.append(testl['analyte'])
        
        var = StringVar()
        testdrop= ttk.Combobox(gencal,textvariable=var, state="readonly", values=analytelist, font = screen_config.buttonfont, width=15)
        testdrop.place(relx=0.1, rely=0.05)
        testdrop.set(gencal_array[0])
        
        unitlist = [' ', 'mg/L', 'mg/dl', 'ng/ml', 'pg/ml', 'IU/ml','uIU/ml']
        var1 = StringVar()
        unitdrop= ttk.Combobox(gencal,state="readonly", textvariable=var1, values=unitlist, font = screen_config.labelfont, width=15)
        unitdrop.place(relx=0.4, rely=0.05)
        unitdrop.set(gencal_array[1])
        
        var2 = StringVar()
        caldrop= ttk.Combobox(gencal,textvariable=var2, state="readonly", values=callist, font = screen_config.buttonfont, width=15)
        caldrop.place(relx=0.7, rely=0.05)
        caldrop.set(gencal_array[2]) 
            
        Label(gencal, text="Batch number", font = screen_config.labelfont, background = "white", justify="center").place(relx=0.1,rely=0.15)
        batchE = Entry(gencal,font = screen_config.labelfont)
        batchE.insert(0,gencal_array[3])
        batchE.place(relx=0.4,rely=0.15)
                        
        Label(gencal, text="Exp Date (MM/YY)", font = screen_config.labelfont, background = "white", justify="center").place(relx=0.1,rely=0.25)
        expE = Entry(gencal,font = screen_config.labelfont)
        expE.insert(0,gencal_array[4])
        expE.place(relx=0.4,rely=0.25)
        
        Label(gencal, text="Lower Limit", font = screen_config.labelfont, background = "white", justify="center").place(relx=0.1,rely=0.35)
        measlE = Entry(gencal,font = screen_config.labelfont)
        measlE.insert(0,gencal_array[5])
        measlE.place(relx=0.4,rely=0.35)

#         Label(gencal, text="Upper Limit", font = screen_config.labelfont, background = "white", justify="center").place(relx=0.1,rely=0.45)
#         measuE = Entry(gencal,font = screen_config.labelfont)
#         measuE.insert(0,gencal_array[6])
#         measuE.place(relx=0.4,rely=0.45)
        
        try:
            plt.scatter(conc_array, result_array)
            plt.savefig(deviceinfo.path+'qr/plt_'+gencal_array[3]+'.jpg')
            plt.close()
            img = Image.open(deviceinfo.path+'qr/plt_'+gencal_array[3]+'.jpg')
            imgcopy = img.resize((150, 150))
            plt_img = ImageTk.PhotoImage(imgcopy)
            imgs = ImageTk.PhotoImage(img)
            Button(gencal, image = plt_img, background = "white", command=lambda: utils.show_image(imgs)).place(relx=0.8,rely=0.35,anchor=CENTER)
        except Exception as e: print(e)
            
        btn1 = Button(gencal, text = "Add data point", font=screen_config.buttonfont, bd = 0, command = lambda: adddata(tl_array, cl_array, conc_array, result_array, gencal_array)) 
        btn1.place(relx=0.1,rely=0.55)
        
        btn2 = Button(gencal, text = "Get calibration fit", activebackground='#ff0000', font=screen_config.buttonfont, bd = 0, command = lambda: calgen(tl_array, cl_array, conc_array, result_array, gencal_array[3], gencal_array)) 
        btn2.place(relx=0.4,rely=0.55)
        
        btn3 = Button(gencal, text = "Home", font=screen_config.buttonfont, bd = 0, command = lambda: Homepage()) 
        btn3.place(relx=0.7,rely=0.55)
        
        def adddata(tl_array, cl_array, conc_array, result_array, gencal_array):
            global swidget
            swidget = Toplevel()
            
            global tempidE
            global tvalE
            global cvalE
            global valE
            screen_config.widget_config(swidget)
            
            test = testdrop.get()
            fit = caldrop.get()
            unit = unitdrop.get()
            batch = batchE.get()
            date = datetime.now().strftime('%m/%y')
            exp = expE.get()
            measu = measuE.get()
            measl = measlE.get()
            gencal_array=[test,unit,fit,batch,exp,measl,measu]
            print('gencal_array', gencal_array) 
            
            Label(swidget, text = "Enter concentration", background = 'white',font = screen_config.buttonfont, justify="left").place(relx=0.1,rely=0.1)    
            tempidE = Entry(swidget, font = screen_config.buttonfont)
            tempidE.place(relx=0.5,rely=0.1)
            
            Label(swidget, text = "Enter Control line AU", background = 'white',font = screen_config.buttonfont, justify="left").place(relx=0.1,rely=0.2)    
            cvalE = Entry(swidget, font = screen_config.buttonfont)
            cvalE.place(relx=0.5,rely=0.2)
            
            Label(swidget, text = "Enter Test line AU", background = 'white',font = screen_config.buttonfont, justify="left").place(relx=0.1,rely=0.3)    
            tvalE = Entry(swidget, font = screen_config.buttonfont)
            tvalE.place(relx=0.5,rely=0.3)
            
            Label(swidget, text = "Or enter raw value", background = 'white',font = screen_config.buttonfont, justify="left").place(relx=0.1,rely=0.4)    
            valE = Entry(swidget, font = screen_config.buttonfont)
            valE.place(relx=0.5,rely=0.4)  
            
            Button(swidget, bd=0, text = "Proceed", font = screen_config.buttonfont, justify="left", width =10, command = lambda: onpress(tl_array, cl_array, conc_array, result_array, batch, test)).place(relx=0.1,rely=0.5)    
            Button(swidget, bd=0, text = "Add from CSV", font = screen_config.buttonfont, justify="left", width =10, command = lambda: fromcsv(conc_array, result_array, gencal_array)).place(relx=0.5,rely=0.5)    
            
            def fromcsv(conc_array, result_array, gencal_array):
#                 try:
                conc_array, result_array = utils.csv_gencal(conc_array, result_array)
                Gencal(tl_array, cl_array, gencal_array, conc_array, result_array)
#                 except Exception as e:
#                     print(e)
#                     widgets.error("Could not add data from file")
                    
            def onpress(tl_array, cl_array, conc_array, result_array, batch, test):
                conc = tempidE.get()
                tl = tvalE.get()
                cl = cvalE.get()
                rv = valE.get()
                
                def addpoint(tl_array, cl_array, conc_array, result_array, tl, cl, temp, conc):
                    try:
                        conc_array = np.append(conc_array, float(conc))
                        try: tl_array = np.append(tl_array, float(tl))
                        except: tl_array = np.append(tl_array, 'NA')
                        try: cl_array = np.append(cl_array, float(cl))
                        except: cl_array = np.append(cl_array, 'NA')
                        result_array = np.append(result_array, float(temp))
                        Gencal(tl_array, cl_array, gencal_array, conc_array, result_array)
                    except Exception as e:
                        print(e)
                        widgets.error("Could not add datapoint")
                
                if conc == '':
                    widgets.error("Please enter concentration")  
                elif tl == cl == rv == '': 
                    try: 
                        captured_image = imagepro.camcapture(batch,'')  
                        roi_image = imagepro.roi_singlecard(captured_image, batch, '')
                    except Exception as e: print(e)
                    if "Bilirubin" in test: 
                        tl==cl==0
                        temp = imagepro.val_bilirubin(captured_image,batch,'')
                        temp = round(temp,3)
                    elif test in deviceinfo.threelineDict:
                        array = imagepro.scan_card(roi_image)
                        tl, cl, temp = imagepro.val_card(array, 1, 1, batch, '')
                    else:
                        array = imagepro.scan_card(roi_image)
                        tl, cl, temp = imagepro.val_card(array, 0, 1, batch, '')    
                elif rv=='':
                    if deviceinfo.raw_value=="ratio":
                        try: temp = float(tl)/float(cl)
                        except: widgets.error("Please enter numeric values for Test and Control Value")
                    else:
                        try: temp = float(tl)
                        except: widgets.error("Please enter numeric values for Test and Control Value")
   
                else:
                    if deviceinfo.raw_value=="ratio":
                        try:temp = float(rv)
                        except: widgets.error("Please enter numeric Raw Value")
                    else: widgets.error("Please enter numeric values for Test and Control Value")
   
                    
                string = "Test Value: "+str(tl)+" Control Value: "+str(cl)+" Raw Value: "+str(temp)+ "  Proceed?"
                response = messagebox.askquestion(title=None, message=string)
                if response == "no": x = 1
                else: addpoint(tl_array, cl_array, conc_array, result_array, tl, cl, temp, conc)
            
            screen_config.kill_previous(prevscreen)
            prevscreen.append(swidget)
            widgets.drawKeyboard(swidget)
            swidget.mainloop()  
                
        def calgen(tl_array, cl_array, conc_array, result_array, batch, gencal_array):    
            #cal_id = fit/const1/const2/const3/const4
            # gencal_array format
            # ["analyte","unit", "type", "batchid", "expdate", "measl","measu"]
            datenow = datetime.now().strftime('%d_%m_%y_%H_%M')
            try:
                f = open(deviceinfo.path+'qr/gencal_'+batch+'_'+datenow+'.csv', 'a')
                writer = csv.writer(f)
                row = "Test_Line"+','+"Control_Line"+','+"Conc"+','+"Result"+"\n"
                f.write(row) 
                i = 0
                while(i<len(conc_array)-1):
                    try: row = str(tl_array[i])+','+str(cl_array[i])+','+str(conc_array[i])+','+str(result_array[i])+"\n"
                    except: row = 'NA'+','+'NA'+','+str(conc_array[i])+','+str(result_array[i])+"\n"
                    f.write(row)
                    i = i+1
                f.close()
            except Exception as e:
                print(e)
                widgets.error("Could not write csv")
            
            try:
                date = datetime.now().strftime('%m/%y')
                p_factor = caldrop.get()
                if p_factor =='':widgets.error("No fit parameter selected")
                elif (p_factor=="Linear"):
                    def func(x,a,b): return a*x+b
                    pars, cov = curve_fit(func,conc_array,result_array)
                    print(cov)
                    plt.plot(conc_array, result_array, '*')
                    plt.plot(conc_array, func(conc_array, *pars))
                    plt.savefig(deviceinfo.path+'qr/plt'+batch+'.jpg')
                    plt.close()
                    calid = "1/"+str(round(pars[0]*100,2))+"/"+str(round(pars[1]*100,2))+"/0/0"
                elif (p_factor=="Log-Linear"):
                    def func(x, a, b, c): return a*np.log(t*b)+c
                    pars, cov = curve_fit(func,conc_array,result_array,p0=[0, 0],bounds=(-np.inf, np.inf))
                    print(cov)
                    plt.plot(conc_array, result_array)
                    plt.plot(conc_array, func(conc_array, *pars))
                    plt.savefig(deviceinfo.path+'qr/plt'+batch+'.jpg')
                    plt.close()
                    calid = "2/"+str(round(pars[0]*100,2))+"/"+str(round(pars[1]*100,2))+"/0/0"
                elif (p_factor=="Power"):
                    def power(x, a, b, c): return a*pow(x,b)+c
                    pars, cov = curve_fit(power,conc_array,result_array,p0=[0, 0],bounds=(-np.inf, np.inf))
                    print(cov)
                    plt.plot(conc_array, result_array)
                    plt.plot(conc_array, power(conc_array, *pars))
                    plt.savefig(deviceinfo.path+'qr/plt'+batch+'.jpg')
                    plt.close()
                    calid = "3/"+str(round(pars[0]*100,2))+"/"+str(round(pars[1]*100,2))+"/"+str(round(pars[2]*100,2))+"/0"          
                elif (p_factor=="4PL"):
                    def fourpl(x, a, b, c, d):return d+((a-d)/(1+pow(x/c,b)))
                    pars, cov = curve_fit(fourpl,conc_array,result_array)
                    print(cov)
                    plt.plot(conc_array, result_array)
                    plt.plot(conc_array, fourpl(conc_array, *pars))
                    plt.savefig(deviceinfo.path+'qr/plt'+batch+'.jpg')
                    plt.close()
                    calid = "4/"+str(round(pars[0]*100,2))+"/"+str(round(pars[1]*100,2))+"/"+str(round(pars[2]*100,2))+"/"+str(round(pars[3]*100,2))          
                else: print("None")
            except Exception as e:
                print(e)
                widgets.error("Could not fit plot")     
            # qr code string format
            # "analyte;calid;caldate;expdate;unit;batchid;measl;measu"
            
            qrstring = gencal_array[0]+';'+calid+';'+date+';'+gencal_array[4]+';'+gencal_array[1]+';'+gencal_array[3]+';'+gencal_array[5]+';'+gencal_array[6]
            widgets.error(qrstring)
            img = qrcode.make(qrstring)
            img.save(deviceinfo.path+'qr/'+gencal_array[3]+'.png')
            img = img.resize((100, 100))
            img.save(deviceinfo.path+'qr/'+gencal_array[3]+'_resized.png')
            widgets.error("QR code generated for batchid:"+gencal_array[3])
            
            analytedb = TinyDB(deviceinfo.path+'analytes.json')
            Sample = Query()
            try:
                analyte_str = {"analyte": gencal_array[0], "calid": calid, "caldate": date, "expdate": gencal_array[4], "batchid": gencal_array[3], "measl": str(gencal_array[5]), "measu": str(gencal_array[6]), "unit": gencal_array[1]}
                analytedb.insert(analyte_str)
                widgets.error(gencal,"Parameter for "+gencal_array[3]+" has been updated")
                results.usesummary("Parameter for "+gencal_array[3]+" has been updated from generate function")
            except Exception as e:
                print(e)
                widgets.error("Calibration data could not be updated")
                results.usesummary("Calibration data could not be updated")                    

        screen_config.kill_previous(prevscreen)
        prevscreen.append(gencal)
        widgets.drawKeyboard(gencal)
        gencal.mainloop()   
    
    splash.mainloop()  
Splash()
