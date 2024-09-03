from tinydb import TinyDB, Query, where
import tkinter as tk
from tkinter import filedialog
import subprocess
from datetime import datetime, date
from subprocess import Popen, PIPE
import numpy as np
from pyzbar.pyzbar import decode

import webbrowser
import widgets
import deviceinfo
import os
import json
import csv
import results
import subprocesses
import imagepro

def get_pendrive():
    result = subprocess.run(["sudo","lsblk", "-o", "NAME,MOUNTPOINT"],stdout = subprocess.PIPE, universal_newlines = True)
    output = result.stdout
    lines = output.split("\n")
    for line in lines[1:]:
        parts = line.split()
        if len(parts)<2:
            continue
        if parts[1].startswith("/") and "media" in parts[1]:
            old_name = parts[1]
            subprocess.run(["sudo", "fatlabel", "/dev/sda1", "IMACAP"])
            return old_name


def addcsv():
    pendrive = get_pendrive()
    if not pendrive: widgets.error("Please insert pendrive")
    filename = filedialog.askopenfilename(initialdir = ('/media/pi/BABYSAFE'), title = "Select a File", filetypes = (("data files","*.csv"),))
    analytedb = TinyDB(deviceinfo.path+'analytes.json')
    Sample = Query()
    with open(filename, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            print(row)
            data = row    
            try:
                string = {"analyte": data['analyte'], "calid": data['calid'], "caldate": data['caldate'], "expdate": data['expdate'], "batchid": data['batchid'], "measl": data['measl'], "measu": data['measu'], "unit": data['unit'] }
                print(string)
                analytedb.insert(string)
                widgets.error("Analytes from file were added" + "/n" + "See analytes table to avoid duplication")
            except Exception as e: 
                widgets.error(str(e))
                results.usesummary(str(e))
                widgets.error("Could not upload data for from csv")

def csv_gencal(conc_array, result_array):
    pendrive = get_pendrive()
    if not pendrive: widgets.error("Please insert pendrive")
    filename = filedialog.askopenfilename(initialdir = ('/media/pi/IMACAP'), title = "Select a File", filetypes = (("data files","*.csv"),))
    with open(filename, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            print(row)
            conc_array=np.append(conc_array, float(row['Conc']))
            result_array=np.append(result_array, float(row['Result']))

    results.usesummary("Data added from CSV file for generation of Calid")
    return conc_array, result_array

def results_backup():
    sys_time = str(datetime.now().replace(microsecond=0))
    date = datetime.now().strftime('%y-%m-%d')
    src_folder = deviceinfo.path + 'results'
    try:
        pendrive = get_pendrive()
    except Exception as e: 
        widgets.error(str(e))
        results.usesummary(str(e))
    if not pendrive:
        widgets.error("Please insert pendrive")
    else:
        dst_folder = pendrive+"/backup_"+date
        try:
            subprocess.run(["sudo", "mkdir", "-p", dst_folder])
            subprocess.run(["sudo", "cp", "-r", src_folder, dst_folder])
        except Exception as e: 
            widgets.error(str(e))
            results.usesummary(str(e))
        updatedeviceinfo("backup_time", deviceinfo.backup_time, sys_time)
        widgets.error("Backup is complete")


def browseFiles(path, filetype):
    filename = filedialog.askopenfilename(initialdir = path, title = "Select a File", filetypes = (("Files", filetype),))
    try: webbrowser.open_new(filename)
    except Exception as e: 
        widgets.error(str(e))
        results.usesummary(str(e))   

def exportFiles(path):
    filename = filedialog.askopenfilename(initialdir = path, title = "Select a File", filetypes = (("Files", "*.pdf"),))
    try:
        pendrive = get_pendrive()
        subprocess.run(["sudo", "cp", "-r", filename, pendrive])
        widgets.error("File copied to "+pendrive)
    except Exception as e: 
        widgets.error(str(e))
        results.usesummary(str(e)) 

def restore():
    global msg
    path = deviceinfo.path + 'results/'
    pendrive = get_pendrive() 
    if not pendrive:
        widgets.error("Please insert pendrive and try again")
    else:
        src_folder = filedialog.askdirectory(title = "Select the folder", initialdir = pendrive)
        dst_folder = path
        counter = 0
        merge_result_json(src_folder,dst_folder)
        while True:
            if not os.listdir(src_folder):
                widgets.error("Selected folder is empty")
            break
        for filename in os.listdir(src_folder):
            src_item = os.path.join(src_folder, filename)
            dst_item = os.path.join(dst_folder, filename)
            if os.path.basename(src_item) not in os.listdir(dst_folder):
                subprocess.run(["sudo", "cp", "-r", src_item, dst_folder])
            else:
                counter += 1
        if counter != 0:
            msg = str(counter)  + 'reports already exist, all other files are copied '
        else:
            msg = "Results are restored"
        widgets.error(msg)
                
def merge_result_json(src_folder,dst_folder):
    result_file ="results.json"
    src_path = os.path.join(src_folder,result_file)
    dst_path = os.path.join(dst_folder, result_file)

    if not os.path.exists(src_path) or not os.path.exists(dst_path):
        msg = "results.json is missing in pendrive"
        widgets.error(msg)
    else:
        with open(src_path, 'r')as src_f, open(dst_path, 'r') as dst_f:
            src_data = json.load(src_f)
            dst_data = json.load(dst_f)
        for key, value in src_data.items():
            if key not in dst_data:
                dst_data[key] = value
        with open(dst_path, 'w') as merg_f:
            json.dump(dst_data, merg_f, indent = 4)

def sigupdate(string):
    dst_file = deviceinfo.path+'signature.png'
    src_folder = get_pendrive()
    if not src_folder:
        widgets.error("Please insert pendrive")
    else:
        filename = filedialog.askopenfilename(initialdir = src_folder, title = "Select a File", filetypes = (("Signature", "*.png"),))
        try:
            subprocess.run(["sudo", "cp", "-r", filename, dst_file])
            widgets.error("New Signature Added")
        except Exception as e: 
            widgets.error(str(e))
            results.usesummary(str(e))
            widgets.error("Could not add signature")
            
def logoupdate(string):
    dst_file = deviceinfo.path+'lab_logo.png'
    src_folder = get_pendrive()
    if not src_folder:
        widgets.error("Please insert pendrive")
    else:
        filename = filedialog.askopenfilename(initialdir = src_folder, title = "Select a File", filetypes = (("Logo", "*.png"),))
        try:
            subprocess.run(["sudo", "cp", "-r", filename, dst_file])
            widgets.error("New Logo Added")
        except Exception as e: 
            widgets.error(str(e))
            results.usesummary(str(e))
            widgets.error("Could not add signature")

def update():
    path = deviceinfo.path
    cmd = "ls " + path + "| wc -l "
    try:
        i=1
        process = subprocess.run([cmd] , shell = True, stdout=subprocess.PIPE).stdout.decode("utf-8")
        num_folder = int(process)
    
        folder_sum= str(num_folder + i)
        folder = deviceinfo.path
        rename_folder = folder+folder_sum
        command= "mv" + " " + folder + " " + rename_folder
        move_command = "mv" + " " + rename_folder + " " + "/home/pi/prev_imacap"
        remove_command = " rm -rf rename_folder"
        process = subprocess.run([command], shell = True, stdout=subprocess.PIPE).stdout.decode("utf-8")
        process = subprocess.run([move_command], shell = True, stdout=subprocess.PIPE).stdout.decode("utf-8")
        process = subprocess.run([remove_command], shell = True, stdout=subprocess.PIPE).stdout.decode("utf-8")
    except Exception as e: 
        widgets.error(str(e))
        results.usesummary(str(e)) 
        widgets.error("Could not move previous version")    
    try:    
        def new_version(path):
            pendrive = get_pendrive()
            subprocess.run(["cp", "-r", f"{pendrive}/viewdx.py", path])
        widgets.askquestion("Update Software?", new_version, path)
    except Exception as e: 
        widgets.error(str(e))
        results.usesummary(str(e)) 
        widgets.error("Could not update software")
    pass

def check_format(date, time):
    flage = 1
    if (date=="")|(time==""):
        flage = 0
        e = "Please add the date and time"
    elif (len(time)!=10) and (len(date)!=10):
        flage = 0
        e = "Date-time format is not correct"
    elif (date[2] != '/' and date[5] != '/') and (time[2]!= ':' and time[5] != ':'):
        e = "Date-time format is not correct"
        flage = 0
    else: e=""
    return flage 
    
def change_time(dateE, timeE, passE):
        date = dateE.get()
        time = timeE.get()
        flage = check_format(date, time)
        if flage == 1:
            time = time.split(":")
            hours = time[0]
            minutes = time[1]
        
            date = date.split('/')
            month = date[0]
            day = date[1]
            year = date[2]
            try:
                monthDict={1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
                if hours is not None:
                    if not 0 <= int(hours) < 24:
                        e = "Hours is out of range [0,23]."
                    rtc = str(hours)
                if minutes is not None:
                    if not 0 <= int(minutes) < 60:
                        e = 'Minutes is out of range [0,59].'
                    rtc = rtc + ':' + str(minutes)
            
                if month is not None:
                    if not 1 <= int(month) <=  12:
                        e = 'Month is out of range [1,12].'
                    rtc_d = str(monthDict[int(month)])
                
                if day is not None:
                    if not 1 <= int(day) <= 31:
                        e = ('Date is out of range [1,31].')
                    rtc_d = rtc_d + '-' + str(day)
            
                if year is not None:
                    if not 2023 <= int(year) < 2123:
                        e = 'Year is out of range [2023,2123].'
                    rtc_d = rtc_d + '-' + str(year)
                #widgets.error(e)

                rtc_cmd = '"' + rtc_d + " " + rtc +'"'
                command = "sudo hwclock --set --date " + rtc_cmd
                process = subprocess.run([command], shell = True, stdout = subprocess.PIPE).stdout.decode("utf-8")
                time_string = str(dateE.get())+' ' +str(timeE.get())
                subprocess.run(['sudo','date','-s', time_string])
                sysdate = subprocess.run(['date'])
                print(sysdate)
                widgets.error("System Time was updated to "+rtc_cmd)
            except Exception as e:
                print(e)
                #widgets.error(str(e))
                #results.usesummary(str(e))

def connectvpn():
    if deviceinfo.remoteconnect=="Enabled":
        try:
            Enable_vnc = subprocess.Popen(['sudo systemctl start vncserver-x11-serviced'],shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            print("connected")
            widgets.error("VNC Connected")
            exitprocess.restart()
        except Exception as e: 
            widgets.error(str(e))
            results.usesummary(str(e)) 
    else:
        try:
            Disable_vnc = subprocess.Popen(['sudo systemctl stop vncserver-x11-serviced'],shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            print("disconnected")
            widgets.error("VNC could not be connected")
            exitprocess.restart()
        except Exception as e: 
            widgets.error(str(e))
            results.usesummary(str(e))

def updatedeviceinfo(variable, old_string, new_string):
    try:
        f = open(deviceinfo.path+'deviceinfo.py','r')
        data = f.readlines()
        f.close()
        
        for line in data:
            if variable in line:
                print(line)
                oldline = line
                newline = line.replace(old_string, str(new_string))
                print(newline)
        with open(deviceinfo.path+'deviceinfo.py','r') as f:
            filedata = f.read()
            filedata = filedata.replace(str(oldline), str(newline))
        with open(deviceinfo.path+'deviceinfo.py','w') as f:
            f.write(filedata)
        f.close()
    except Exception as e: 
        widgets.error(str(e))
        results.usesummary(str(e))
        widgets.error('Unexpected error during writing deviceinfo')


# def togglewifi(state):
#     if state == "Enabled":
#             subprocess.run(["sudo", "systemctl", "enable", "wpa_supplicant@wlan0.service"])
#             exitprocess.restart()
#     elif state == "Disabled":
#             subprocess.run(["sudo", "systemctl", "disable", "wpa_supplicant"])
#             exitprocess.restart()
#     else: widgets.error("Some error occurred")
        
def list_wifi():
    wifi_list =[]
    
    try:
#         s = subprocess.run(["rfkill", "list", "wifi"],capture_output=True,text=True,check=True).stdout
#         if "Soft blocked: yes" in s:
#             print(343)
        subprocess.run(["rfkill", "unblock","wifi"],check = True)
        s = subprocess.run(["rfkill", "list", "wifi"],capture_output=True,text=True,check=True).stdout
        print(s)
        command = "sudo iwlist wlan0 scan | grep ESSID"
        process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        output = process.stdout
        for l in output.splitlines():
            wifi_list.append(l)
    except subprocess.CalledProcessError as e:
        widgets.error(None,f"Error listing WiFi networks")
        results.usesummary(str(e))
    return wifi_list[1:]

def connect_wifi(ssid,password):
    config_lines = [
        'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev',
        'update_config=1',
        'country=INDIA',
        '',
        'network={',
        '\tssid="{}"'.format(ssid),
        '\tpsk="{}"'.format(password),
        '}'
    ]
    config = '\n'.join(config_lines)
    os.popen("sudo chmod a+w /etc/wpa_supplicant/wpa_supplicant.conf")
    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as wifi:
        wifi.write(config)
#     widgets.error("Wifi config added")
    wlan_interface = os.popen("iw dev | awk '$1==\"Interface\"{print $2}'").read().strip()
    
    if wlan_interface:
        os.popen(f"sudo wpa_cli -i {wlan_interface} reconfigure")
#         widgets.error("Wi-Fi configured successfully!")
    else:
        widgets.error("No wireless interface found on the system.")
        
def update_wifi(ssidE, wpassE, passE):
#     if (passE.get()==deviceinfo.admin_pwd):
    try:
        ssid = ssidE.get()
        ssid_ = ssid[26:]
        ssid_replace = ssid_.replace('"','')
        key = wpassE.get()
        if (ssid_=="")|(key==""):
            e = "Please add the details"
            widgets.error(e)
        else:
            connect_wifi(ssid_replace,key)
            widgets.error('Wifi Connected')
    except Exception as e: 
        print(e)
        results.usesummary(str(e))
        widgets.error('Could not connect wifi')
#     else: widgets.error("Incorrect Admin Password")

def get_ip_add():
    output = subprocess.run(['ifconfig','wlan0'],stdout=subprocess.PIPE).stdout.decode('utf-8')
    for line in output.split('\n'):
        if 'inet' in line and 'inet6' not in line:
            ip_address = line.split()[1]
            if ip_add != '127.0.0.1':
                address = ip_add
                widgets.error(address)
    return address
    
def show_image(image):
    popup = tk.Toplevel()
    popup.title("Plot")
    image_label = tk.Label(popup, image = image)
    image_label.pack()
              
            
def checkcaldate(string):
    now = datetime.now()
    date = now.strftime("%m_%y")
    nowstring = date.split('_')
    month = int(nowstring[0])+1
    year = int(nowstring[1])
    t_now = year+month/12
    dstring = str(string)
    print(dstring)
    check = 0
    data = dstring.split('/')
    print(data)
    t_date = int(data[1])+int(data[0])/12
    elapsed = t_now-t_date
    print(elapsed)
    if (13>int(data[0])>0)and(2>elapsed>0): 
        check = 1
    else: widgets.error("Calibration date is invalid")
    return check

def checkcalid(string):
    check = 0
    data = string.split('/')
    numd=[]
    try:
        for d in data: 
            numd.append(float(d))
            if (7>len(numd)>3): check=1
        if numd[0]==1 or numd[0]==2 or numd[0]==3 or numd[0]==4:
            check = 1
        else: check=0
    except Exception as e: 
        results.usesummary(str(e))
        widgets.error("Calid string format is incorrect")
    return check

def analytecheck():
    analytedb = TinyDB(deviceinfo.path+'analytes.json')
    Sample = Query()
    ana_list = analytedb.all()
    purged=[]
    for ana in ana_list:
        check = checkcaldate(ana['caldate'])
        if check==0: 
            purged.append(ana['calid'])
            analytedb.remove(Sample.calid==ana['calid'])
            widgets.error("Entries for calid "+ana['calid']+" have been removed")
    if len(purged)==0:widgets.error("No calibration ids need to be removed")    

def updatepara(analyte, calid, caldate, expdate, batchid, measl, measu, unit):
    analytedb = TinyDB(deviceinfo.path+'analytes.json')
    analyte_str = {"analyte": analyte, "calid": calid, "caldate": caldate, "expdate": expdate, "batchid": batchid}
    analytedb.insert(analyte_str)
    widgets.error("Parameter for "+calid+" has been updated")                
    results.usesummary("Parameter for "+calid+" has been updated")
