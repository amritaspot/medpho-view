import subprocess
import RPi.GPIO as GPIO
from datetime import datetime
import time
from PIL import Image, ImageTk
import imagepro
import deviceinfo
import results
import utils
import widgets

def at_boot(overwrite):
    lines = []
    markup = ""
    
    now = datetime.now()
    date = now.strftime("%d_%m_%Y")
    string = date.split('_')
    day = int(string[0])
    
    if ((deviceinfo.hstate=="Enabled")and(day=='10'))or(overwrite==1):
        try: 
            lines.append("Running camera check")
            c = cameracheck(markup)
            lines.append(c)
        except Exception as e:
            widgets.error(str(e))
            results.usesummary(str(e))
            lines.append("Could not check camera")
        try: 
            lines.append("Running voltage check")
            v = undervolt(markup)
            lines.append(v)
        except Exception as e:
            widgets.error(str(e))
            results.usesummary(str(e))
            lines.append("Could not check undervoltage")
        try:
            lines.append("Running RTC check")
            r = RTCactive(markup)
            lines.append(r)
        except Exception as e:
            widgets.error(str(e))
            results.usesummary(str(e))
            lines.append("Could not check RTC")
        try:
            lines.append("Running SDCard check")
            sd = speedcheck(markup)
            lines.append(sd)
        except Exception as e:
            widgets.error(str(e))
            results.usesummary(str(e))
            lines.append("Could not check SD card")
        try:
            lines.append("Running memory check")
            dk = str(Diskmemcheck(markup))+"%" 
            lines.append(dk)
        except Exception as e:
            widgets.error(str(e))
            results.usesummary(str(e))
            lines.append("Could not check memory")
        try:
            lines.append("Running RAM check")
            ram = str(Rammemcheck(markup))
            lines.append(ram)
        except Exception as e:
            widgets.error(str(e))
            results.usesummary(str(e))
            lines.append("Could not check RAM")
        try:
            results.report(lines)
            widgets.error("Hardware scan completed")
        except Exception as e:
            results.usesummary(str(e))
            widgets.error("Scan completed but could not generate report")
    print(lines)
def cameracheck(markup):
    outcamera = ""
    try:
        proc = subprocess.Popen('raspistill test.jpg'';''vcgencmd get_camera',  shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        output=str(proc.communicate())
        outcamera = output[2:48]
        detect = str('supported=1 detected=1, libcamera interfaces=0')
        if outcamera == detect:
            outstr = "Camera detected"
        else:
            outstr = "Camera not detected"
        try: markup.configure(text=outstr)
        except: ''
    except Exception as e:
        widgets.error(str(e))
        results.usesummary(str(e)) 
        widgets.error("Could not check camera status")
    return outcamera


def undervolt(markup):
    a = ""
    try:
        global undervoltage
        data = subprocess.Popen(['vcgencmd get_throttled'],shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        output = str(data.communicate())# https://www.raspberrypi.com/documentation/computers/os.html#vcgencmd documentation site
        a = ''.join(output)
        outvolt = output[14:19]
        undervolt = str(5000)
        if undervolt in a:
            outstr = "Undervoltage detected"
        else:
            outstr = "No Undervoltage detected"
        try: markup.configure(text=outstr)
        except:''
    except Exception as e:
        widgets.error(str(e))
        results.usesummary(str(e)) 
        widgets.error("Could not check voltage")
    return a

def GPIOcheck(markup):
    outstr=""
    try: 
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(21, GPIO.OUT)
        GPIO.output(21, GPIO.HIGH)
        GPIO.setwarnings(False)
        state = GPIO.input(21)
        GPIO.output(21, GPIO.LOW)
        if state:
            outstr = "GPIO pins are functioning"
        else:
            outstr = "GPIO pins may not be functioning"
    except Exception as e:
        widgets.error(str(e))
        results.usesummary(str(e))
        outstr = "Unexpected error occurred"
    try: markup.configure(text = outstr)
    except: ''
    return outstr
        

def RTCactive(markup):
    outstr=""
    try:
        timenow1= datetime.now()
        timestamp1 = datetime.timestamp(timenow1)
        time.sleep(10)
        timenow2= datetime.now()
        timestamp2 = datetime.timestamp(timenow2)
        if timestamp2 > timestamp1:
            outstr = "RTC is functioning accurately"
        else:
            outstr = "RTC is not functioning accurately"
        try: markup.configure(text = outstr)
        except: ''
    except Exception as e:
        widgets.error(str(e))
        results.usesummary(str(e))
        widgets.error("Could not test RTC") 
    return outstr

def speedcheck(markup):
    comstr=""
    try:
        proc = subprocess.Popen('dd if=/dev/zero of=./speedTestFile bs=20M count=5 oflag=direct' ';' 'dd if=./speedTestFile of=/dev/zero bs=20M count=5 oflag=dsync ', shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)# coverting byte array to string
        output = str(proc.communicate())
        outwrite = output[80:90] 
        outread = output[177:187]
        w = float(outwrite.split(' ')[1])
        r = float(outread.split(' ')[1])
        comstr = "outwrite: "+str(outwrite)+": outread: "+str(outread)
        if w>r:
            outstr = "Adequate Performance"
        else:
            outstr = "Inadequate Performance"
        try: markup.configure(text = outstr)
        except: ''
    except Exception as e:
        widgets.error(str(e))
        results.usesummary(str(e))
        widgets.error("Exception occurred")
    return comstr

def Diskmemcheck(markup):
    outstr=""
    try:
        proc = subprocess.Popen('df -h', shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)# coverting byte array to string
        output = str(proc.communicate())
        outmem = output[85:88]
        print(outmem)
        outmem_int = int(outmem)
        Availmem = int(100)
        AvailDiskmem = (Availmem - (outmem_int))
        mem_threshold = int(10) 
        if mem_threshold < AvailDiskmem : 
            outstr = "Available :" + str(AvailDiskmem)+"%"
        else:
            outstr = "Critically low" + str(AvailDiskmem)
        try: markup.configure(text = outstr)
        except: ''
        utils.updatedeviceinfo('avail_mem',deviceinfo.avail_mem, str(AvailDiskmem))
    except Exception as e:
        widgets.error(str(e))
        results.usesummary(str(e))
        widgets.error("Could not test memory")
    return AvailDiskmem

def Rammemcheck(markup):
    memstring=""
    try:
        proc = subprocess.Popen('cat /proc/meminfo', shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)# coverting byte array to string
        output = str(proc.communicate())
        outmem = output[74:85]
        print(outmem)
        outmemmb = int(int(outmem)/1024)
        
        memstring = "Available RAM (Mb) = " + str(outmemmb)
        print(memstring)
        try: markup.configure(text = memstring)
        except: ''
    except Exception as e:
        widgets.error(str(e))
        results.usesummary(str(e))
        widgets.error("Could not check RAM")
    return memstring

def callimage(image_path, markup):
    image = Image.open(image_path)
    img = image.resize((200, 200))
    shwimg = ImageTk.PhotoImage(img)
    markup.configure(image=shwimg)
    markup.image=shwimg


#------------------------------------------------------------
def checkfocus(markup):
    image = imagepro.camcapture('focus', '')
    image_path = deviceinfo.path+'/captured/capturedimage_focus_.jpg'
    callimage(image_path, markup)
    pass

def checkcolor(markup):
    image = imagepro.camcapture('color', '')
    image_path = deviceinfo.path+'/captured/capturedimage_color_.jpg'
    callimage(image_path, markup)
    pass

def checklux(markup):
    image = imagepro.camcapture('lux', '')
    image_path = deviceinfo.path+'/captured/capturedimage_lux_.jpg'
    callimage(image_path, markup)
    pass

def checkroi(markup):
    image = imagepro.camcapture('roi', '')
    roi=imagepro.roi_segment(image, 'roi', '')
    image_path = deviceinfo.path+'/captured/roi_roi_.jpg'
    callimage(image_path, markup)
    pass
