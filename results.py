from fpdf import FPDF
import csv
from tinydb import TinyDB, Query, where
from tinydb.table import Document
from datetime import datetime
import widgets
import deviceinfo


# data_array format
# ["sampleid","analyte","cal_id","value","date","name","age","gender","refer","unit"]

def usesummary(line):
    now = datetime.now()
    date = now.strftime("%d_%m_%Y")
    time = now.strftime("%H:%M:%S")
    f = open(deviceinfo.path+'usesummary/'+str(deviceinfo.device_id)+'_usesummary_'+str(date)+'.csv', 'a')
    writer = csv.writer(f)
    row = str(time)+':'+line+"\n"
    print(row)
    f.write(row)
    f.close()

def report(lines):
    try:
        if (lines==""):widgets.error("Hardware scan data not available")
        else:
            now = datetime.now()
            date = now.strftime("%d_%m_%Y")
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", size = 14)
            try:
                pdf.image(deviceinfo.path +'lab_logo.png',5,5,20)
                pdf.cell(200, 10, txt = deviceinfo.lab_name, ln=1,align='C')
                pdf.cell(200, 10, txt = deviceinfo.lab_address, ln=1,align='C')
                pdf.cell(200, 10, txt = "---------------------------------------------------REPORT-----------------------------------------------------", ln=3,align='C')
            except Exception as e: 
                widgets.error(str(e))
                usesummary(str(e))
            pdf.cell(200, 10, txt = "Report Date: "+str(date), ln=4,align='L')
            pdf.cell(200, 10, txt = "Report Generated for Device id: "+deviceinfo.device_id,ln=31,align='L')   
            i = 1                 
            for l in lines:
                pdf.cell(200, 10, txt = l, ln=5+i,align='L')
                i = i+1
            pdf.output(deviceinfo.path+'hardwaretest/'+str(date)+'.pdf')
            widgets.error("Hardware scan report generated")
    except Exception as e: 
        usesummary(str(e))
    pass

def qcreport(lines, analyte):
    try:
        if (lines==""):widgets.error("QC Test data not available")
        else:
            now = datetime.now()
            date = now.strftime("%d_%m_%Y")
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", size = 14)
            try:
                pdf.image(deviceinfo.path +'lab_logo.png',5,5,20)
                pdf.cell(200, 10, txt = deviceinfo.lab_name, ln=1,align='C')
                pdf.cell(200, 10, txt = deviceinfo.lab_address, ln=1,align='C')
                pdf.cell(200, 10, txt = "---------------------------------------------------REPORT-----------------------------------------------------", ln=3,align='C')
            except Exception as e: 
                widgets.error(str(e))
                usesummary(str(e))

            pdf.cell(200, 10, txt = "Report Date: "+str(date), ln=1,align='L')
            pdf.cell(200, 10, txt = "Report Generated for Device id: "+deviceinfo.device_id,ln=2,align='L')   
            i = 1                 
            for l in lines:
                pdf.cell(200, 10, txt = l, ln=3+i,align='L')
                i = i+1
            try:
                pdf.image(deviceinfo.path +'signature.png',50,5,10)
                pdf.cell(200, 10, txt = 'Signature', ln=30,align='C')
            except Exception as e: 
                widgets.error(str(e))
                usesummary(str(e))

            pdf.output(deviceinfo.path+'qctest/'+analyte+'_'+str(date)+'.pdf')
            widgets.error("QC test report has been generated")
    except Exception as e: 
        widgets.error(str(e))
        usesummary(str(e))
    pass

def genpdf(data_array):
    db = TinyDB(deviceinfo.path+'/results/results.json')
    Sample = Query()
    sampleid = data_array[0]
    analyte = data_array[1]
    calid = data_array[3]
    if (sampleid==""): widgets.error("SampleID doesn't exist")
    else:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size = 14)
        try:
            pdf.image(deviceinfo.path +'lab_logo.png',5,5,20)
        except Exception as e: 
            widgets.error(str(e))
            usesummary(str(e))
        try:
            pdf.cell(200, 10, txt = deviceinfo.lab_name, ln=1,align='C')
            pdf.cell(200, 10, txt = deviceinfo.lab_address, ln=1,align='C')
            pdf.cell(200, 10, txt = "---------------------------------------------------REPORT-----------------------------------------------------", ln=3,align='C')
            pdf.cell(200, 10, txt = "SampleID: "+data_array[0], ln=5,align='L')
            pdf.cell(200, 10, txt = "Patient Name: "+data_array[5], ln=6,align='L')
            pdf.cell(200, 10, txt = "Age: "+data_array[6], ln=7,align='L')
            pdf.cell(200, 10, txt = "Gender: "+data_array[7], ln=8,align='L')
            pdf.cell(200, 10, txt = "Referred by: "+data_array[8], ln=9,align='L')
            pdf.cell(200, 10, txt = "--------------------------------------------------------------------------------------------------", ln=10,align='C')
            
        except Exception as e: 
            widgets.error(str(e))
            usesummary(str(e))
        
        try:
            roi_img = deviceinfo.path+'captured/roi_'+str(data_array[0])+'_'+str(data_array[4])+'jpg'
            plot_img = deviceinfo.path+'captured/peaks_'+str(sampleid)+'_1_'+str(data_array[4])+'png'
            pdf.image(roi_img,140,40,10)
            pdf.image(plot_img,100,40,40)
        except:
            roi_img = deviceinfo.path+'captured/capturedimage_'+str(data_array[0])+'_'+str(data_array[4])+'jpg'
            pdf.image(roi_img,140,40,40)
        try: 
            pdf.cell(200, 10, txt = "Analyte:  ", ln=12,align='L')
            pdf.cell(200, 10, txt = "Result: "+data_array[3]+' '+data_array[9], border=1, ln=13,align='L')
            pdf.cell(200, 10, txt = "Test Date: "+str(data_array[4]), ln=14,align='L')
        except Exception as e: print(e)
        try:
            pdf.image(deviceinfo.path +'signature.png',20,150,40)
        except Exception as e: 
            widgets.error(str(e))
            usesummary(str(e))
            widgets.error("Could not add signature")
        try:
            pdf.cell(200, 10, txt = "--------------------------------------------------------------------------------------------------", ln=16,align='C')
            pdf.cell(200, 10, txt = "", ln=18,align='L')
            pdf.cell(200, 10, txt = "", ln=19,align='L')
            pdf.cell(200, 10, txt = "", ln=20,align='L')
            pdf.cell(200, 10, txt = "Signature: ", ln=90,align='L')
            pdf.set_font("helvetica", size = 8)
            pdf.cell(200, 10, txt = "----------------------------------------------------------------------------------------------------------------------------------------", ln=92,align='C')
            
            pdf.cell(200, 10, txt = "Report Generated on Device id: "+deviceinfo.device_id+ "Software Version: "+deviceinfo.software_version,ln=95,align='C')                
        except Exception as e: 
            widgets.error(str(e))
            usesummary(str(e))
        pdf.output(deviceinfo.path+'results/'+str(sampleid)+'_'+str(analyte)+'_'+str(data_array[4])+'pdf')


def patientpdf(sampleid):
    db = TinyDB(deviceinfo.path+'results/results.json')
    Sample = Query()
    plist = db.search(Sample.sampleid == sampleid)
    if (plist==""): widgets.error("SampleID could not be fetched")
    else:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size = 14)
        try:
            pdf.image(deviceinfo.path +'lab_logo.png',5,5,20)
            pdf.cell(200, 10, txt = deviceinfo.lab_name, ln=1,align='C')
            pdf.cell(200, 10, txt = deviceinfo.lab_address, ln=1,align='C')
            pdf.cell(200, 10, txt = "---------------------------------------------------REPORT-----------------------------------------------------", ln=3,align='C')
        except Exception as e: 
            widgets.error(str(e))
            usesummary(str(e))

        try:
            index=plist[0]
            pdf.cell(200, 10, txt = "Sample Id: "+index['sampleid'], ln=5,align='L')
            pdf.cell(200, 10, txt = "Patient Name: "+index['name'], ln=6,align='L')
            pdf.cell(200, 10, txt = "Age: "+index['age'], ln=7,align='L')
            pdf.cell(200, 10, txt = "Gender: "+index['gender'], ln=8,align='L')
            pdf.cell(200, 10, txt = "--------------------------------------------------------------------------------------------------", ln=13,align='L')
            i = 0
            for l in plist:
                pdf.cell(200, 10, txt = " Analyte: "+l['analyte']+ " Result: "+l['result']+" Test Date: "+l['date'], ln=10+i,align='L')
                i=i+1

            pdf.cell(200, 10, txt = "Signature: ", ln=30,align='L')
            pdf.cell(200, 10, txt = "--------------------------------------------------------------------------------------------------", ln=35,align='L')
            
            pdf.set_font("helvetica", size = 8)
            pdf.cell(200, 10, txt = "Report Generated on Device id: "+deviceinfo.device_id+ "Software Version: "+deviceinfo.software_version,ln=40,align='L')                
            pdf.output(deviceinfo.path+'results/'+str(sampleid)+'.pdf')
        except Exception as e: 
            widgets.error(str(e))
            usesummary(str(e))
            widgets.error("Could not generate pdf")

