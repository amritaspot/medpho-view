from picamera import PiCamera
from time import sleep
import time
from datetime import datetime, date
from tinydb import TinyDB, Query, where
import RPi.GPIO as GPIO
import matplotlib.pyplot as plt
import numpy as np
import cv2
from scipy.signal import find_peaks, peak_widths, peak_prominences, savgol_filter
from scipy import sparse
from scipy.sparse.linalg import spsolve
import widgets
import deviceinfo
import csv
import results
import utils
import traceback


def camcapture(sampleid, date):
    camera = PiCamera()
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(40, GPIO.OUT)
    GPIO.output(40, True)
    GPIO.cleanup
    camera.start_preview()
    time.sleep(3)
    
    x = deviceinfo.path+'captured/capturedimage_'+str(sampleid)+'_'+str(date)+'.jpg'
    camera.capture(x)
    camera.stop_preview()
    GPIO.output(40,False)
    input_image = cv2.imread(x)
    camera.close()
    return input_image

def addparaqr():
    try:
        image = camcapture('qr', '')
        detect = cv2.QRCodeDetector()
        string, points, straight_qrcode = detect.detectAndDecode(image)
        print(string)
        results.usesummary("QR code scanned and decoded for "+ string)
        widgets.error(string)
        analyte, calid, caldate, expdate, unit, batchid, measl, measu = string.split(';')
        analytedb = TinyDB(deviceinfo.path+'analytes.json')
        Sample = Query()
        if analytedb.search(Sample.batchid == batchid): widgets.error("Calibration "+calid+" already exists")
        else:utils.updatepara(analyte,calid,caldate,expdate,batchid,measl,measu,unit)
        results.usesummary("Calibration for "+calid+" read from QR scan")
    except Exception as e:
        print(e)
        widgets.error("Could not add analyte")  


def baseline_correction(y, lam, p):
    L = len(y)
    D = sparse.diags([1,-2,1],[0,-1,-2],shape=(L,L-2))
    D = lam*D.dot(D.transpose())
    w = np.ones(L)
    W = sparse.spdiags(w,0,L,L)
    for i in range(1,10):
        W.setdiag(w)
        Z = W+D
        z = spsolve(Z, w*y)
        w = p*(y>z)+(1-p)*(y<z)
    return z

def takefourth(array):
    return array[4]

def rgb2cmk(img):
    bgrdash = img.astype(np.float64)/255
    K = 1 - np.max(bgrdash,axis=2)
    C = (1-bgrdash[...,2] -K)/(1-K)
    M = (1-bgrdash[...,1] -K)/(1-K)
    Y = (1-bgrdash[...,0] -K)/(1-K)
    CMY = (np.dstack((C,M,Y))*255).astype(np.uint8)
    return CMY


def roi_segment(img, sampleid, date):
    image = img.copy()
    
    img = cv2.GaussianBlur(img, (15,15),0)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    sobelx = cv2.Sobel(img,cv2.CV_64F,1,0,ksize=5)
    sobely = cv2.Sobel(img,cv2.CV_64F,0,1,ksize=5)
    
    abs_grad_x = cv2.convertScaleAbs(sobelx)
    abs_grad_y = cv2.convertScaleAbs(sobely)
    grad = cv2.addWeighted(abs_grad_x, 0.05, abs_grad_y, 0.05, 0)  
   
    ret, thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    thresh = thresh.astype(np.uint8)
    cnts,_ = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2:]
    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)
    cv2.drawContours(img, cnts, -1, (0,255,0), 3)
       
    rect = []
    [img_width, img_height] = img.shape[:2]
    for c in cnts:
        epsilon = 0.01*cv2.arcLength(c,True)
        approx = cv2.approxPolyDP(c,epsilon,True)
        if (len(approx)>=4):
            (x, y, w, h) = cv2.boundingRect(approx)
            cv2.rectangle(img, (x, y), (x+w, y+h), (255,0,0), 2)
            rect.append((x,y,w,h,(h*w)))
    rect.sort(key=takefourth, reverse=True)
    arr=rect[0]
    x1 = arr[0]
    y1 = arr[1]
    w1 = arr[2]
    h1 = arr[3]
    roi_image=image[y1:y1+h1, x1:x1+w1]   
    cv2.imwrite(deviceinfo.path+'captured/roi_'+str(sampleid)+'_'+str(date)+'.jpg',roi_image) 
    return roi_image

def roi_dengue_combo(img):
    ## Roi for dengue combo ab IgG/IgM and NS1
    image = img.copy()
    cnts = get_cnts(img)
    rect = []
    [img_width, img_height] = img.shape[:2]
    for c in cnts:
        print('ca',cv2.contourArea(c))
        if cv2.contourArea(c)>5000:
            epsilon = 0.01*cv2.arcLength(c,True)
            approx = cv2.approxPolyDP(c,epsilon,True)
            if (len(approx)>=4):
                (x, y, w, h) = cv2.boundingRect(approx)
                if y > 20:
                    cv2.rectangle(img, (x, y), (x+w, y+h), (255,0,0), 2)
                    rect.append((x,y,w,h,(h*w)))
    rect = sorted(rect, key=takefirst, reverse=False)
    AgAb = get_coordinate(rect[0],image)
    cv2.imwrite(get_path('captured/AgAb.jpg'),AgAb)
    NS1 = get_coordinate(rect[1],img)
    cv2.imwrite(get_path('captured/NS1.jpg'),NS1)
    return AgAb, NS1

def HIV(image, sampleid, date):
    segment = roi_singlecard(image,sampleid, date)
    result_array = scan_card(segment)
    dataNew=result_array[1:-1]
    n = len(dataNew)
    base = dataNew[n-1]   
    index1 = 0
    diff = 0
    neg_array = []  
    res_array = 0-dataNew
    base_array = baseline_correction(res_array, 1000, 0.005)
    i = 0
    while(i<n):
        neg_array = np.append(neg_array, res_array[i]-base_array[i])
        i = i+1
    check_noise, properties = find_peaks(neg_array)
    noise = peak_prominences(neg_array, check_noise)[0]
    try:
        if len(noise)<50:
            if (max(noise)-min(noise)) < 20:
                len_noise = 51
            else: len_noise = len(noise)
        print('noise value', len(noise), min(noise),max(noise))
    except Exception as e:
        results.usesummary(str(e))
        widgets.error(str(e))
    try: pr = int(deviceinfo.peak_threshold)
    except: pr = 5
    peaks, properties = find_peaks(neg_array, prominence=pr, width=(5,40), distance = 10)
    prominences = peak_prominences(neg_array, peaks)[0]
    widths = peak_widths(neg_array, peaks)[0]
    results.usesummary(str(prominences))    
    x_arr =neg_array
    plt.plot(neg_array)
    plt.plot(peaks, neg_array[peaks], 'x')
    plt.savefig(deviceinfo.path+'captured/peaks_'+str(sampleid)+'_'+str(1)+'_'+str(date)+'.png')
    plt.close()
    value = '0'
    try:
        if (len(prominences)==0): value = "Err 03: no control line"
        elif (len(prominences)>4): value = "Err 04: high background"
        elif (len(prominences)==3): value = "Positive for HIV-1 and HIV-2"  
        else:
            if (peaks[1]-peaks[0])<100:
                value = "Positive for HIV-2"
            else:
                value = "Positive for HIV-1"
    except Exception as e:
#         print(e)
        value = "Negative"
    return value
def styphi(image, sampleid, date):
    segment = roi_singlecard(image,sampleid, date)
    result_array = scan_card(segment)
    dataNew=result_array[1:-1]
    n = len(dataNew)
    base = dataNew[n-1]   
    index1 = 0
    diff = 0
    neg_array = []  
    res_array = 0-dataNew
    base_array = baseline_correction(res_array, 1000, 0.005)
    i = 0
    while(i<n):
        neg_array = np.append(neg_array, res_array[i]-base_array[i])
        i = i+1
    check_noise, properties = find_peaks(neg_array)
    noise = peak_prominences(neg_array, check_noise)[0]
    try:
        if len(noise)<50:
            if (max(noise)-min(noise)) < 20:
                len_noise = 51
            else: len_noise = len(noise)
        print('noise value', len(noise), min(noise),max(noise))
    except Exception as e:
        results.usesummary(str(e))
        widgets.error(str(e))
    try: pr = int(deviceinfo.peak_threshold)
    except: pr = 5
    peaks, properties = find_peaks(neg_array, prominence=pr, width=(5,40), distance = 10)
    prominences = peak_prominences(neg_array, peaks)[0]
    widths = peak_widths(neg_array, peaks)[0]
    results.usesummary(str(prominences))    
    x_arr =neg_array
    plt.plot(neg_array)
    plt.plot(peaks, neg_array[peaks], 'x')
    plt.savefig(deviceinfo.path+'captured/peaks_'+str(sampleid)+'_'+str(1)+'_'+str(date)+'.png')
    plt.close()
    value = '0'
    try:
        if (len(prominences)==0): value = "Err 03: no control line"
        elif (len(prominences)>4): value = "Err 04: high background"
        elif (len(prominences)==3): value = "Positive for IgG and IgM"  
        else:
            if (peaks[1]-peaks[0])<100:
                value = "Positive for IgM"
            else:
                value = "Positive for IgG"
    except Exception as e:
#         print(e)
        value = "Negative"
    return value

def dengue_iggm(image, sampleid, date):
    result_array = scan_card(image)
    dataNew=result_array[1:-1]
    n = len(dataNew)
    neg_array = []  
    res_array = 0-dataNew
    base_array = baseline_correction(res_array, 1000, 0.005)
    i = 0
    while(i<n):
        neg_array = np.append(neg_array, res_array[i]-base_array[i])
        i = i+1
    check_noise, properties = find_peaks(neg_array)
    noise = peak_prominences(neg_array, check_noise)[0]
    try:
        if len(noise)<50:
            if (max(noise)-min(noise)) < 20:
                len_noise = 51
    except Exception as e:
        results.usesummary(str(e))
        widgets.error(str(e))
    try: pr = int(deviceinfo.peak_threshold)
    except: pr = 5
    peaks, properties = find_peaks(neg_array, prominence=pr, width=(5,40), distance = 10)
    prominences = peak_prominences(neg_array, peaks)[0]
    widths = peak_widths(neg_array, peaks)[0]
    results.usesummary(str(prominences))    
    x_arr =neg_array
    plt.plot(neg_array)
    plt.plot(peaks, neg_array[peaks], 'x')
    plt.savefig(deviceinfo.path+'captured/peaks_'+str(sampleid)+'_'+str(1)+'_'+str(date)+'.png')
    plt.close()
    value = '0'
    try:
        if (len(prominences)==0): value = "Err 03: no control line"
        elif (len(prominences)>4): value = "Err 04: high background"
        elif (len(prominences)==3): value = "Positive for IgG and IgM"  
        else:
            if (peaks[1]-peaks[0])<100:
                value = "Positive for IgM"
            else:
                value = "Positive for IgG"
    except Exception as e:
        print(e)
        value = "Negative for IgG/IgM"
    return value

def dengue_ns1(image, sampleid, date):
    result_array = scan_card(image)
    dataNew=result_array[1:-1]
    n = len(dataNew)
    neg_array = []  
    res_array = 0-dataNew
    base_array = baseline_correction(res_array, 1000, 0.005)
    i = 0
    while(i<n):
        neg_array = np.append(neg_array, res_array[i]-base_array[i])
        i = i+1
    check_noise, properties = find_peaks(neg_array)
    noise = peak_prominences(neg_array, check_noise)[0]
    try:
        if len(noise)<50:
            if (max(noise)-min(noise)) < 20:
                len_noise = 51
    except Exception as e:
        results.usesummary(str(e))
        widgets.error(str(e))
    try: pr = int(deviceinfo.peak_threshold)
    except: pr = 5
    peaks, properties = find_peaks(neg_array, prominence=pr, width=(5,40), distance = 10)
    prominences = peak_prominences(neg_array, peaks)[0]
    widths = peak_widths(neg_array, peaks)[0]
    results.usesummary(str(prominences))    
    x_arr =neg_array
    plt.plot(neg_array)
    plt.plot(peaks, neg_array[peaks], 'x')
    plt.savefig(deviceinfo.path+'captured/peaks_'+str(sampleid)+'_'+str(1)+'_'+str(date)+'.png')
    plt.close()
    value = '0'
    try:
        if (len(prominences)==0): value = "Err 03: no control line"
        elif (len(prominences)>4): value = "Err 04: high background"
        elif (len(prominences)==2): value = "Positive for NS1"  
        else:
            value = "Negative for NS1"
    except Exception as e:
        print(e)
    return value


def val_bloodgroup(image, sampleid, date):
    segment = roi_singlecard(image,sampleid, date)
    result_array = scan_card(segment)
    dataNew=result_array[1:-1]
    n = len(dataNew)
    base = dataNew[n-1]   
    index1 = 0
    diff = 0
    neg_array = []  
    res_array = 0-dataNew
    base_array = baseline_correction(res_array, 1000, 0.005)
    i = 0
    while(i<n):
        neg_array = np.append(neg_array, res_array[i]-base_array[i])
        i = i+1
    check_noise, properties = find_peaks(neg_array)
    noise = peak_prominences(neg_array, check_noise)[0]
    try:
        if len(noise)<50:
            if (max(noise)-min(noise)) < 20:
                len_noise = 51
            else: len_noise = len(noise)
        print('noise value', len(noise), min(noise),max(noise))
    except Exception as e:
        results.usesummary(str(e))
        widgets.error(str(e))
    try: pr = int(deviceinfo.peak_threshold)
    except: pr = 5
    peaks, properties = find_peaks(neg_array, prominence=pr, width=(5,40), distance = 10)
    prominences = peak_prominences(neg_array, peaks)[0]
    widths = peak_widths(neg_array, peaks)[0]
    results.usesummary(str(prominences))    
    x_arr =neg_array
    plt.plot(neg_array)
    plt.plot(peaks, neg_array[peaks], 'x')
    plt.savefig(deviceinfo.path+'captured/peaks_'+str(sampleid)+'_'+str(1)+'_'+str(date)+'.png')
    plt.close()
    value = '0'
    
    try:
        if (len(prominences)==0): value = "Err 03: no control line"
        elif (len(prominences)>4): value = "Err 04: high background"
        elif len(prominences)==0: value = "O -ve"
        elif (len(prominences)==3): value = "AB +ve" 
        else:
            res_dict = []
            for peak in peaks:
                if 0<peak<100: res_dict.append("A")
                elif 100<peak<200: res_dict.append("B")
                elif 200<peak<300: res_dict.append("D")
            print(res_dict)
            if "A" and "D" in res_dict: value = "A +ve"         
            elif "B" and "D" in res_dict: value = "B +ve"
            elif "A" and "B" and "D" in res_dict: value = "AB +ve"
            if "D" not in res_dict:
                if "A" in res_dict: value = "A -ve"
                elif "B" in res_dict: value = "B -ve"
                elif "A" and "B" in res_dict: value = "AB -ve"
                
    except Exception as e:
        print(e)

    return value




# def val_bloodgroup(input,sampleid,date):    
#     img = input[50:180, 0:780]
#     img1 = img[0:150, 0:190]
#     img2 = img[0:150, 190:380]
#     img3 = img[0:150, 380:570]
#     img4 = img[0:150, 570:750]
#     img_rot = cv2.rotate(input, cv2.ROTATE_180)
    
#     cv2.imwrite(deviceinfo.path+'captured/capturedimage_'+str(sampleid)+'_'+str(date)+'.jpg', img_rot)
#     cv2.imwrite(deviceinfo.path+'captured/bloodgroup_crop_'+str(sampleid)+'_'+str(date)+'.jpg', img)
#     cv2.imwrite(deviceinfo.path+'captured/bloodgroup_crop_'+str(sampleid)+'_C'+str(date)+'.jpg', img1)
#     cv2.imwrite(deviceinfo.path+'captured/bloodgroup_crop_'+str(sampleid)+'_D'+str(date)+'.jpg', img2)
#     cv2.imwrite(deviceinfo.path+'captured/bloodgroup_crop_'+str(sampleid)+'_B'+str(date)+'.jpg', img3)
#     cv2.imwrite(deviceinfo.path+'captured/bloodgroup_crop_'+str(sampleid)+'_A'+str(date)+'.jpg', img4)
#     result_c = scan_bg(img1,sampleid,date)
#     result_d = scan_bg(img2,sampleid,date)
#     result_b = scan_bg(img3,sampleid,date)
#     result_a = scan_bg(img4,sampleid,date)
#     print(result_c+':'+result_d+':'+result_b+':'+result_a)
#     return result_c, result_d, result_b, result_a

def scan_bg(img,sampleid,date):
    img = rgb2cmk(img)
    c,m,k = cv2.split(img)
    hist_l_o = cv2.calcHist([m],[0],None,[256],[0,256])
    hist_l = savgol_filter(hist_l_o[:,0],21,2)
    plt.plot(hist_l)
    peaks, properties = find_peaks(hist_l, distance = 20, prominence = 10) 
    prominences = peak_prominences(hist_l, peaks)[0]
    print(prominences)
    plt.plot(peaks, hist_l[peaks],"*")  
    plt.savefig(deviceinfo.path+'captured/peaks_'+str(sampleid)+'_1_'+str(date)+'.png')
    plt.close()
    print(prominences)
    try:
        if (len(prominences)>1):
            result = 'Pos'
        else:result = 'Neg'
    except Exception as e:
        print(e)
        result = "Unknown error occurred"
        widgets.error('Please read test again')
    return result


def val_g6pd(input, sampleid,date):    
    img1 = input[300:450, 320:500]
    cv2.imwrite(deviceinfo.path+'captured/g6pd_crop_'+str(sampleid)+'_'+str(date)+'.jpg', img1)
    img = roi_segment(img1, sampleid, str(date))
    img = rgb2cmk(img)
    c,m,k = cv2.split(img)
    hist_l_o = cv2.calcHist([m],[0],None,[256],[0,256])
    hist_l = savgol_filter(hist_l_o[:,0],21,2)
    plt.plot(hist_l)
    peaks, properties = find_peaks(hist_l, distance = 20, prominence = 10) 
    prominences = peak_prominences(hist_l, peaks)[0]
    print(prominences)
    plt.plot(peaks, hist_l[peaks],"*")  
    plt.savefig(deviceinfo.path+'captured/peaks_'+str(sampleid)+'_1_'+str(date)+'.png')
    plt.close()
    print(prominences)
    try:
        diff = prominences[0]-prominences[1]
    except: diff = 0
    print(diff)
    try:
        if (len(prominences)==2):
            result = 'Normal'
            if prominences[1]<100:
                result = 'Could not determine result'
                widgets.error("Run test with different card")
        elif (len(prominences)<2):result = 'Deficient'
        else:
            result = 'Could not determine result'
            widgets.error("Run test with different card")
    except Exception as e:
        print(e)
        result = "Unknown error occurred"
        widgets.error('Please read test again')
    return result

def val_bilirubin(input, sampleid,date):
    img1 = input[100:600, 320:500]
    cv2.imwrite(deviceinfo.path+'captured/bili_crop_'+str(sampleid)+'_'+str(date)+'.jpg', img1)
    img = roi_segment(img1, sampleid, str(date))
    b,g,r = cv2.split(img)
    hist_l_o = cv2.calcHist([b],[0],None,[256],[0,256])
    hist_l = savgol_filter(hist_l_o[:,0],21,2)
    plt.plot(hist_l)
    peaks, properties = find_peaks(hist_l, prominence = 20)
    print(peaks)
    prominences = peak_prominences(hist_l, peaks)[0]
    plt.plot(peaks, hist_l[peaks],"*")  
    plt.savefig(deviceinfo.path+'captured/peaks_'+str(sampleid)+'_1_'+str(date)+'.png')
    plt.close()
    return prominences[0]

def val_qual(value):
    try:
        value = float(value)
        if value>0: value = "Pos"
        else: value = "Neg"
    except:
        if "Below" in value: value = "Neg"
    return str(value)

def roi_twocard(image, sampleid, date):
    img1 = image[0:480, 0:400]
    img2 = image[0:480, 400:800]
    try:
        cropped1 = roi_segment(img1, sampleid+'_1', str(date))
        cropped2 = roi_segment(img2, sampleid+'_2', str(date))
    except Exception as e:
        results.usesummary(str(e))
        widgets.error('Could not identify test')
    return cropped1, cropped2

def roi_fourcard(image, sampleid, date):
    img1 = image[0:480, 0:200]
    img2 = image[0:480, 200:400]
    img3 = image[0:480, 400:600]
    img4 = image[0:480, 600:800]
    try:
        cropped1 = roi_segment(img1, sampleid+'_1', str(date))
        cropped2 = roi_segment(img2, sampleid+'_2', str(date))
        cropped3 = roi_segment(img3, sampleid+'_3', str(date))
        cropped4 = roi_segment(img4, sampleid+'_4', str(date))
    except Exception as e:
        results.usesummary(str(e))
        widgets.error('Could not identify test')
    return cropped1, cropped2, cropped3, cropped4

def roi_singlecard(image, sampleid, date):
    img = image[100:480, 350:450]
    cv2.imwrite(deviceinfo.path+'captured/firstroi_'+str(sampleid)+'_'+str(date)+'.jpg',img)
    try: cropped = roi_segment(img, sampleid, str(date))
    except Exception as e:
         results.usesummary(str(e))
         widgets.error(str(e))
    return cropped

def scan_card(segment):
    input = segment
    [a, b] = input.shape[:2]
    result_array = []
    x = 1
    y = 20
    sum = 0
    while (y<a-20): 
        line = input[y:y+3, x:x+b]
        avg_color_per_row = np.average(line, axis=0)
        avg_color = np.average(avg_color_per_row, axis=0)
        sum = avg_color[0]+avg_color[1]+avg_color[2]
        result_array = np.append(result_array, sum)
        y = y+1
    return result_array

def val_card(result_array, lines, segid, sampleid, date):
    dataNew=result_array[10:-1]
    n = len(dataNew)
    base = dataNew[n-1]   
    index1 = 0
    diff = 0
    neg_array = []  
    res_array = 0-dataNew
    base_array = baseline_correction(res_array, 1000, 0.005)
    i = 0
    while(i<n):
        neg_array = np.append(neg_array, res_array[i]-base_array[i])
        i = i+1
    check_noise, properties = find_peaks(neg_array)
    noise = peak_prominences(neg_array, check_noise)[0]
    try:
        if len(noise)<100:
            if (max(noise)-min(noise)) < 20:
                len_noise = 51
            else: len_noise = len(noise)
        print('noise value', len(noise), min(noise),max(noise))
    except Exception as e:
        results.usesummary(str(e))
        widgets.error(str(e))
    try: pr = int(deviceinfo.peak_threshold)
    except: pr = 8
    peaks, properties = find_peaks(neg_array, prominence=pr, width=(5,60), distance = 10)
    prominences = peak_prominences(neg_array, peaks)[0]
    widths = peak_widths(neg_array, peaks)[0]
    results.usesummary(str(prominences))    
    x_arr =neg_array
    plt.plot(neg_array)
    plt.plot(peaks, neg_array[peaks], 'x')
    plt.savefig(deviceinfo.path+'captured/peaks_'+str(sampleid)+'_'+str(segid)+'_'+str(date)+'.png')
    plt.close()
    test_value = control_value = value = "NA"
    try:
        if len_noise>50:
            value = "Err 01: could not detect sample"
        else:
            print('lines', lines)
            if len(prominences)==0: value = "Err 02: no control line"
            elif 10>len(prominences)>5: value = "Err 03: high background"
            elif (len(prominences)==1):
                control_value = (round(prominences[0],2))
                value = "Neg"  
            else:
                n = len(prominences)
                if lines==0:
                    test_value = (round(prominences[1],2))
                elif lines==1:
                    test_value_1 = (round(prominences[1],2))
                    test_value_2 = (round(prominences[2],2))
                    test_value = [test_value_1, test_value_2]
                else: widgets.error("Could not identify analyte")
                control_value = (round(prominences[0],2))
                try:
                    if deviceinfo.raw_value == 'test':
                        value = str(round(test_value,2))
                    elif deviceinfo.raw_value == 'ratio':
                        value = str(round(test_value/control_value,2))
                    else: results.usesummary("Device info raw value not defined correctly")
                except Exception as e:
                    results.usesummary(str(e))
    except Exception as e:
        print(e)
        results.usesummary(str(e))
        value = "Err 04: Test not detected"
    if 'Err' in value:print(value)
    string = "Test Value: "+str(test_value)+" Control Value: "+str(control_value)+" Raw Value: "+str(value)
    results.usesummary(string)
    print(test_value, control_value, value)
    return test_value, control_value, value   

def cal_conc(temp,cal_id):
    if cal_id=='1/1/1/1':
        result = temp
        return result
    elif 'Err' in str(temp):
        result = temp
        return result
    elif 'Below' in str(temp):
        result = temp
        return result
    else: 
        try:y = float(temp)
        except: y = 0
        #the calibration text needs to be a/b/c/d:mm/yy:l
        print(cal_id, 'calid')
        
        details_cal = cal_id.split("/")
        a = float(details_cal[0])
        b = float(details_cal[1])/100
        c = float(details_cal[2])/100
        #for p_factor = 1 (linear curve); y = const1*x+const2
        #for p_factor = 2 (log-linear curve); y = const1*ln(x)+const2
        #for p_factor = 3 (polynomial curve); y = const1*x^3+const2*x^2+const3*x+const4
        #for p_factor neither 1,2,3 machine assumes 4pl calibration
        
        ##// 4pl log reg
        #a = the minimum value that can be obtained 
        #d = the maximum value that can be obtained 
        #c = the point of inflection (i.e. the point on the S shaped curve halfway between a and d)
        #b = Hill’s slope of the curve (i.e. this is related to the steepness of the curve at point c).
        #for (4pl logreg); x = c*((a-d)/(y-d) -1)^(1/b)

        if (a==1):
            res = (y - c)/b
        elif (a==2):
            temp = ((y - c)/b)
            res = np.exp(temp)
        elif (a==3):
            temp = np.log(y/b)/c
            res = pow(10,temp)
        else:
            a = float(details_cal[1])/100 
            b = float(details_cal[2])/100 
            c = float(details_cal[3])/100
            d = float(details_cal[4])/100
            print(a,b,c,d,y)
            h = round((((a-d)/(y-d)) -1),2)
            res = c*(pow(h,(1/b)))
            results.usesummary(str(res))
        if isinstance(res, complex):
            result = "Err 06: Outside measuring range"
        elif res<0 or res==0:
            result = "Below detectable limits"
        elif res>0 :result = str(round(res, 2))
        else: result = "Unknown error occurred"
    return result        

#----------------------------------QC test functions--------------------------------------------
def multirun(number, analyte):
    results.usesummary("Multirun started")
    today = str(date.today())
    devread = []
    cl = []
    tl = []
    rv = []
    g6pd = []
    j = 0
    try:
        for j in range(int(number)):
            image = camcapture(analyte, today)
            try:
                roi = roi_singlecard(image,analyte, today)
                result_array = scan_card(roi)
                tl, cl, rv = val_card(result_array, 1, 1, analyte, today)
                devread = np.array([tl, cl, rv])
            except Exception as e:
                widgets.error(str(e))
                results.usesummary(str(e))
            j = j+1
    except Exception as e:
        results.usesummary(str(e))
        devread = np.array(['err','err','err'])
        widgets.error(str(e))
    return devread

def calfit(conc_array, result_array, calid):
    details_cal = calid.split("/")
    p_factor = int(details_cal[0])
    const1 = float(details_cal[1])/100
    const2 = float(details_cal[2])/100
    #for p_factor = 1 (linear curve); y = const1*x+const2
    #for p_factor = 2 (log-linear curve); y = const1*ln(x)+const2
    #for p_factor = 3 (power curve); y = const1*x^const2
    #add 4pl curve to this
    cal_res = []
    if (p_factor==1):
        for conc in conc_array:
            y = const1*float(conc)+const2
            cal_res.append(y)
    elif (p_factor==2):
        for conc in conc_array:
            y = const1*np.log(float(conc))+const2
            cal_res.append(y)
    elif (p_factor==3):
        for conc in conc_array:
            y = pow(const1*float(conc),const2)
            cal_res.append(y)
    else:
        a = float(details_cal[0])/100 
        b = float(details_cal[1])/100 
        c = float(details_cal[2])/100
        d = float(details_cal[3])/100
        for conc in conc_array:
            k = pow(float(conc)/c,b)
            h = (a-d)/(1+k)
            y = d+h
            cal_res.append(y)
    try:
        plt.plot(conc_array,cal_res)
        plt.plot(conc_array, result_array)
        plt.savefig(deviceinfo.path+'qctests/calfit_'+calid+'.png')
        plt.close()
    except Exception as e:
        print(e)
        widgets.error("Could not generate plot")
    try:
        corr_matrix = np.corrcoef(cal_res, result_array)
        corr = corr_matrix[0,1]
        R_sq = str(corr**2)
    except Exception as e:
        R_sq = 'Err'
        print(e)
        widgets.error("Could not calculate R")
    return R_sq

#---------------------------------------------------------------------
def malaria(image, sampleid, date):
    segment = roi_singlecard(image,sampleid, date)
    result_array = scan_card(segment)
    dataNew=result_array[1:-1]
    n = len(dataNew)
    base = dataNew[n-1]   
    index1 = 0
    diff = 0
    neg_array = []  
    res_array = 0-dataNew
    base_array = baseline_correction(res_array, 1000, 0.005)
    i = 0
    while(i<n):
        neg_array = np.append(neg_array, res_array[i]-base_array[i])
        i = i+1
    check_noise, properties = find_peaks(neg_array)
    noise = peak_prominences(neg_array, check_noise)[0]
    try:
        if len(noise)<50:
            if (max(noise)-min(noise)) < 20:
                len_noise = 51
            else: len_noise = len(noise)
        print('noise value', len(noise), min(noise),max(noise))
    except Exception as e:
        results.usesummary(str(e))
        widgets.error(str(e))
    try: pr = int(deviceinfo.peak_threshold)
    except: pr = 5
    peaks, properties = find_peaks(neg_array, prominence=pr, width=(5,40), distance = 10)
    prominences = peak_prominences(neg_array, peaks)[0]
    widths = peak_widths(neg_array, peaks)[0]
    results.usesummary(str(prominences))    
    x_arr =neg_array
    plt.plot(neg_array)
    plt.plot(peaks, neg_array[peaks], 'x')
    plt.savefig(deviceinfo.path+'captured/peaks_'+str(sampleid)+'_'+str(1)+'_'+str(date)+'.png')
    plt.close()
    value = '0'
    try:
        if (len(prominences)==0): value = "Err 03: no control line"
        elif (len(prominences)>4): value = "Err 04: high background"
        elif (len(prominences)==3): value = "Positive for P.F and P.V"  
        else:
            if (peaks[1]-peaks[0])<100:
                value = "Positive for P.V"
            else:
                value = "Positive for P.f"
    except Exception as e:
#         print(e)
        value = "Negative"
    return value



#------------------------------------------final read function--------------
def read_test(data_array,overwrite):
    date = data_array[4]
    if (overwrite==1):
        try:
            db = TinyDB(deviceinfo.path+"results/results.json")
            last = db.all()[-1]
            db.remove(doc_ids=[last.doc_id])
            results.usesummary("Test result was overwritten")
        except:results.usesummary("No results overwritten")
    captured_image = camcapture(data_array[0], data_array[4])
    results.usesummary("Image captured")
    try:
        if (data_array[1]=='G6PD'): 
            val = val_g6pd(captured_image,data_array[0], data_array[4])
            results.usesummary("G6PD assay analysed")
            data_array[3]=val        
        elif (data_array[1]=='Bilirubin'):
            temp = val_bilirubin(captured_image,data_array[0], data_array[4])
            results.usesummary("Bilirubin assay analysed")
            val = cal_conc(temp, data_array[2])
            data_array[3] = str(round(val,2))
            
        elif ('Entero' in data_array[1]) :
            seg1, seg2 =  roi_twocard(captured_image, data_array[0], date)
            array1 =  scan_card(seg1)
            array2 =  scan_card(seg2)
            try:
                tl1, cl1, value1 =  val_card(array1, 0, 1, data_array[0], date)
                tl2, cl2, value2 =  val_card(array2, 0, 2, data_array[0], date)
            except:
                widgets.error("Could not read test")
                val = "Could not read test"
            results.usesummary(data_array[1]+" analysed")
            results.usesummary(str(value1)+';'+str(value2))
            if 'Entero' in data_array[1]:
                val = "IgG: " + val_qual(value1)+"; IgM: "+val_qual(value2)
            else:
                val = val_qual(value1)+"; "+val_qual(value2)
        elif ('HIV' in data_array[1]):
            results.usesummary(data_array[1]+" analysed")
    #         try:
            val =  HIV(captured_image, data_array[0], date)
    #         except:
    #             widgets.error("Could not read test")
    #             val = "Could not read test"
            results.usesummary(data_array[1]+" analysed")
            results.usesummary(str(val))
            val = val
        elif ('Malaria' in data_array[1]):
            results.usesummary(data_array[1]+ "analysed")
            val = malaria(captured_image, data_array[0],date)
            results.usesummary(data_array[1]+" analysed")
            results.usesummary(str(val))
            val = val
        elif ('S. typhi' in data_array[1]):
            results.usesummary(data_array[1]+" analysed")
    #         try:
            val =  styphi(captured_image, data_array[0], date)
    #         except:
    #             widgets.error("Could not read test")
    #             val = "Could not read test"
            results.usesummary(data_array[1]+" analysed")
            results.usesummary(str(val))
            val = val
                
        elif ('Dengue' in data_array[1]) :
            seg1, seg2 =  roi_twocard(captured_image,data_array[0], data_array[4])
            try:
                 val1 = dengue_iggm(seg1,data_array[0],date)
                 val2 = dengue_ns1(seg2,data_array[0],date)
                 val = val1+val2
            except:
                widgets.error("Could not read test")
                val = "Could not read test"
            results.usesummary(data_array[1]+" analysed")
            results.usesummary(str(value1)+';'+str(value2))
            val = "IgG: " +val_qual(tl1[0])+ "; IgM: " +val_qual(tl1[1])+"; NS1-Ag: "+val_qual(value2)
            
        elif ('Virdict' in data_array[1]):  
            try:
                seg1, seg2, seg3, seg4 =  roi_fourcard(captured_image, data_array[0], date)
                array1 =  scan_card(seg1)
                array2 =  scan_card(seg2)
                array3 =  scan_card(seg3)
                array4 =  scan_card(seg4)
                tl1, cl1, value1 =  val_card(array1, 0, 1, data_array[0], date)
                tl2, cl2, value2 =  val_card(array2, 0, 2, data_array[0], date)
                tl3, cl3, value3 =  val_card(array3, 0, 3, data_array[0], date)
                tl4, cl4, value4 =  val_card(array4, 0, 4, data_array[0], date)
                results.usesummary(data_array[1]+" analysed")
                results.usesummary(str(value1)+';'+str(value2)+';'+str(value3)+';'+str(value4))
                val = "Syp: "+val_qual(value1)+" HCV; "+val_qual(value2)+" ;HIV "+val_qual(value3)+" ;HbsAg "+val_qual(value4)
            except:
                widgets.error("Could not read test")
                val = "Could not read test"
        
        elif ('Blood Group' in data_array[1]):
            val = val_bloodgroup(captured_image,data_array[0], date)
            print("BG", val)

            
                        # if ctrl =="Pos": val = "Err 01: Test is invalid"
            # else:
            #     if (d=="Pos") and (a=="Pos")and (b=="Pos"): val = "AB+"
            #     elif (d=="Neg") and (a=="Pos")and (b=="Pos"): val = "AB-"
            #     elif (d=="Pos") and (a=="Neg")and (b=="Neg"): val = "O+"
            #     elif (d=="Neg") and (a=="Neg")and (b=="Neg"): val = "O-"
            #     elif (d=="Pos") and (a=="Pos"): val = "A+"
            #     elif (d=="Pos") and (b=="Pos"): val = "B+"
            #     elif (d=="Neg") and (a=="Pos"): val = "A-"
            #     elif (d=="Neg") and (b=="Pos"): val = "B-"
            #     else: val = "Err 02: Could not read test"

        else:
            results.usesummary(data_array[1]+" analysed")
            roi_image =  roi_singlecard(captured_image, data_array[0], date)
            array =  scan_card(roi_image)
            if data_array[0] in deviceinfo.threelineDict:
                print('three line test')
                tv, cv, temp =  val_card(array, 0, 1, data_array[0], date)
            elif data_array[1]=='FSH-demo':
                print('in fsh demo')
                tv, cv, temp =  val_card(array[30:-10], 0, 1, data_array[0], date)
            else:
                tv, cv, temp =  val_card(array, 0, 1, data_array[0], date)
            results.usesummary("assay scanned. TL: "+str(tv)+" CL: "+str(cv)+" RV: "+str(temp))
            val =  cal_conc(temp, data_array[2])
            try:
                analytedb = TinyDB(deviceinfo.path+'analytes.json')
                Sample = Query()
                alist = analytedb.search(Sample.analyte == data_array[1])
                a = alist[0]
                try:
                    if float(val)<float(a['measl']): val = str(val)+'(L)'
                    elif float(val)>float(a['measu']): val = str(val)+'(H)'
                    else: val = val
                except:
                    if 'Below' in val: val = "Result below "+str(a['measl'])
                    elif "Err" in val: widgets.error(val)
                    else: val = val
            except: ''
    except Exception as e:
        traceback.print_exc()
        widgets.error("Error occured while reading the test.")
    
    try:
        data_array[3]=val
        if "Err" in val:results.usesummary("Not added because it had error")
        else:
            db = TinyDB(deviceinfo.path+'results/results.json')
            result={"sampleid": data_array[0], "analyte": data_array[1], "cal_id": data_array[2], "result": data_array[3], "unit": data_array[9],"date": data_array[4], "name": data_array[5], "age": data_array[6], "gender": data_array[7]}
            db.insert(result)
            results.usesummary("Result added in database")        
    except: widgets.error("Could not add results to database")
    pass        
