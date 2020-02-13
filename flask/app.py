from flask import Flask, render_template, request, redirect, url_for, session
import OpenOPC
import json
import xml.etree.ElementTree as ET
import datetime
from werkzeug import secure_filename

#global opcreadlist
#global readgroup
#global proc_step

app = Flask(__name__)

class g:
    opc = None
    times = ["50ms", "100ms", "250ms", "500ms", "1s", "5s", "10s", "1m", "10min", "60min"]
    tag_info = ["Selected item: ", "", "", ""]
    table_data = [[],[],[]]
    
    hold_table_data_periodic = []
    hold_table_data_tag_trigger = []
    hold_table_data_file_trigger = []
    table_row_count = len(table_data[0])
    selectedRow = None
    listbox = []
    opc_list = []   #simulation items
    opc_list_2 = [] #random.int4
    periodic_display = 'none'
    tag_trigger_display = 'none'
    file_trigger_display = 'none'
    tag_trigger_info = [["Selected item: ", "", "", ""],["Selected item: ", "", "", ""],["Selected item: ", "", "", ""]]
    tag_trigger_temp = [[],[],[]]
    scaleMinMax = (0,0)
    rangeMinMax = (0,0)
    tag_trigger_scaleMinMax = [(0,0),(0,0),(0,0)]
    tag_trigger_rangeMinMax = [(0,0),(0,0),(0,0)]
    loadAll = ''
    loadedFile = None
    rememberLoadFile = None
    newFile = None
    newFileString = '<xml_file_start><OPC_Servers></OPC_Servers><timed_trig><st_times><group_50ms /><group_100ms /><group_250ms /><group_500ms /><group_1s/><group_5s /><group_10s /><group_1min /><group_10min /><group_60min /></st_times><sp_times /></timed_trig><tag_trig /><file_trig /></xml_file_start>'


@app.route('/', methods=['GET', 'POST'])
def index_page():
    if request.method == "POST":
        if "buttonNew" in request.form:
            g.newFile = open("newXML.xml", "w+")
            g.newFile.write(g.newFileString)
            g.newFile.close()
            return redirect(url_for('newButton_page'))

        elif "buttonLoad" in request.form:
            return redirect(url_for('loadButton_page'))

    return render_template('index.html')

@app.route('/newButton', methods=['GET', 'POST'])
def newButton_page():
    g.listbox = []
    g.tag_info = ["Selected item: ", "", "", ""]
    g.table_data = [[],[],[]]
    g.opc_list = []   #simulation items
    g.opc_list_2 = [] #random.int4
    g.periodic_display = 'none'
    g.tag_trigger_display = 'none'
    g.file_trigger_display = 'none'
    g.tag_trigger_info = [["Selected item: ", "", "", ""],["Selected item: ", "", "", ""],["Selected item: ", "", "", ""]]
    g.tag_trigger_temp = [[],[],[]]
    g.scaleMinMax = (0,0)
    g.rangeMinMax = (0,0)
    g.tag_trigger_scaleMinMax = [(0,0),(0,0),(0,0)]
    g.tag_trigger_rangeMinMax = [(0,0),(0,0),(0,0)]
    g.loadAll = ''
    g.loadedFile = None
    g.rememberLoadFile = None
    dFlag=True
    if request.method == "POST":
        if "remove" in request.form:
            arr = request.form['remove'].split(',')
            if arr[1] == 'pr':
                if len(g.table_data[0]) > 0:
                    del g.table_data[0][int(arr[0])]
                    for i in range(len(g.table_data[0])):
                        g.table_data[0][i][0] = str(i)
            elif arr[1] == 'tt':
                if len(g.table_data[1]) > 0:
                    del g.table_data[1][int(arr[0])]
                    for i in range(len(g.table_data[1])):
                        g.table_data[1][i][0] = str(i)
            elif arr[1] == 'ft':
                if len(g.table_data[2]) > 0:
                    del g.table_data[2][int(arr[0])]
                    for i in range(len(g.table_data[2])):
                        g.table_data[2][i][0] = str(i)
                
                return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow, 
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "server_remove" in request.form:
            tree = ET.parse(g.newFile.name)
            abraham = tree.getroot().find('OPC_Servers')
            ishmael = abraham.findall('OPC_Server')
            if len(g.listbox) > 0:
                del g.listbox[int(request.form.get('server_remove'))]
                for opcs in ishmael:
                    if opcs.find('id').text == request.form['server_remove']:
                        abraham.remove(opcs)
                        break
                ishmael = abraham.findall('OPC_Server')
                for svs in range(len(g.listbox)):
                    g.listbox[svs][0] = str(svs)
                for o in range(len(ishmael)):
                    ishmael[o].find('id').text = str(o) 

                tree.write(open(g.newFile.name, 'wb'))
                
                return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow, 
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "defineServer" in request.form:
            tree = ET.parse(g.newFile.name)
            root = tree.getroot()
            servers = root.find('OPC_Servers')
            sList = servers.findall('OPC_Server')
            new = ET.SubElement(servers, 'OPC_Server')
            newid = ET.SubElement(new, 'id')
            newid.text = str(len(sList))
            newtype = ET.SubElement(new, 'type')
            newtype.text = request.form['da_ua']
            newaddress = ET.SubElement(new, 'address')
            newaddress.text = request.form['ogSaddress']
            newserver = ET.SubElement(new, 'server')
            newserver.text = request.form['ogSname']
            newredundancy = ET.SubElement(new, 'redundancy')
            newredaddress = ET.SubElement(new, 'red_address')
            newredserver = ET.SubElement(new, 'red_server')
            newactiveserver = ET.SubElement(new, 'active_server')
            newactiveserver.text = '0'
            if 'redundantCheckbox' in request.form:
                newredundancy.text = request.form['redundantCheckbox']
                newredaddress.text = request.form['redSaddress']
                newredserver.text = request.form['redSname']
            else:
                newredundancy.text = '0'
                newredaddress.text = request.form['ogSaddress']
                newredserver.text = request.form['ogSname']

            tree.write(open(g.newFile.name, 'wb'))
            g.listbox.append([newid.text,
                    newtype.text,
                    newaddress.text,
                    newserver.text,
                    newredundancy.text,
                    newredaddress.text,
                    newredserver.text,
                    newactiveserver.text])
  

        elif "ipaddrEnter" in request.form:
            g.opc = OpenOPC.open_client(request.form["ipaddr"])
            for opcS in g.opc.servers():
                g.listbox.append(opcS)

            return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow, 
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)
        

        elif "serverEnter" in request.form:
            g.opc = OpenOPC.open_client('127.0.0.1')
            g.opc.connect(request.form["serverSelect"].split(',')[3][2:-1])
            g.opc_list = g.opc.list()
            return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "periodicB" in request.form:
            if g.periodic_display == 'block':
                g.periodic_display = 'none'
            else:
                g.periodic_display = 'block'
            g.tag_trigger_display = 'none'
            g.file_trigger_display = 'none'
            g.tag_info[1], g.tag_info[2], g.tag_info[3] = ("", "", "")
            
            return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "tag_triggerB" in request.form:
            g.periodic_display = 'none'
            if g.tag_trigger_display == 'block':
                g.tag_trigger_display = 'none'
            else:
                g.tag_trigger_display = 'block'
            g.file_trigger_display = 'none'
            g.tag_info[1], g.tag_info[2], g.tag_info[3] = ("", "", "")
            return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "file_triggerB" in request.form:
            g.periodic_display = 'none'
            g.tag_trigger_display = 'none'
            if g.file_trigger_display == 'block':
                g.file_trigger_display = 'none'
            else:
                g.file_trigger_display = 'block'
            g.tag_info[1], g.tag_info[2], g.tag_info[3] = ("", "", "")
            return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitForm" in request.form:
            g.tag_info[1] = request.form['submitForm']
            list_buffer = request.form['submitForm'] + '*.*'
            g.opc_list_2 = g.opc.list(list_buffer, recursive=True)
            return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitForm2" in request.form:
            g.tag_info[2] = "." + request.form['submitForm2']
            return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)
                                            
        elif "submitForm_tagT11" in request.form:
            g.tag_trigger_info[0][1] = request.form['submitForm_tagT11']
            list_buffer = request.form['submitForm_tagT11'] + '*.*'
            g.opc_list_2 = g.opc.list(list_buffer, recursive=True)
            return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitForm2_tagT12" in request.form:
            g.tag_trigger_info[0][2] = "." + request.form['submitForm2_tagT12']
            return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitForm_tagT21" in request.form:
            g.tag_trigger_info[1][1] = request.form['submitForm_tagT21']
            list_buffer = request.form['submitForm_tagT21'] + '*.*'
            g.opc_list_2 = g.opc.list(list_buffer, recursive=True)
            return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitForm2_tagT22" in request.form:
            g.tag_trigger_info[1][2] = "." + request.form['submitForm2_tagT22']
            return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitForm_tagT31" in request.form:
            g.tag_trigger_info[2][1] = request.form['submitForm_tagT31']
            list_buffer = request.form['submitForm_tagT31'] + '*.*'
            g.opc_list_2 = g.opc.list(list_buffer, recursive=True)
            return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitForm2_tagT32" in request.form:
            g.tag_trigger_info[2][2] = "." + request.form['submitForm2_tagT32']
            return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitbutt" in request.form and request.form["submitbutt"] == "Add Tag":
            nameHere = request.form['unique_name_input']
            addrHere = g.tag_info[1]+g.tag_info[2]
            g.scaleMinMax = (request.form["scaleMin"], request.form["scaleMax"])
            g.rangeMinMax = (request.form["rangeMin"], request.form["rangeMax"])
            unit = request.form["unit"]
            sampstart = str(datetime.datetime.now())
            opc_id = request.form['serverSelect'].split(',')[0][2:-1]
            g.hold_table_data_periodic.append([str(len(g.table_data[0])), nameHere, addrHere, g.tag_info[3], 
                                               g.scaleMinMax[0], g.scaleMinMax[1], g.rangeMinMax[0], g.rangeMinMax[1], unit, sampstart, opc_id])

            return render_template('newButton.html', listbox=g.listbox,
                                                      opc_list=g.opc_list,
                                                      opc_list_2=g.opc_list_2, 
                                                      times=g.times,
                                                      tag_info=g.tag_info, 
                                                      table_data=g.table_data,
                                                      selectedRow=g.selectedRow,
                                                      periodic_display=g.periodic_display,
                                                      tag_trigger_display=g.tag_trigger_display,
                                                      file_trigger_display=g.file_trigger_display,
                                                      tag_trigger_info=g.tag_trigger_info)

        elif "submitbutt_file" in request.form and request.form["submitbutt_file"] == "Add Tag":
            nameHere = request.form['unique_name_inputF']
            xx = request.form['x_input']
            yy = request.form['y_input']
            addrHere = g.tag_info[1]+g.tag_info[2]
            g.scaleMinMax = (request.form["scaleMinF"], request.form["scaleMaxF"])
            g.rangeMinMax = (request.form["rangeMinF"], request.form["rangeMaxF"])
            unit = request.form["unitF"]
            sampstart = str(datetime.datetime.now())
            opc_id = request.form['serverSelect'].split(',')[0][2:-1]
            g.hold_table_data_file_trigger.append([str(len(g.table_data[2])), nameHere, addrHere, g.scaleMinMax[0], g.scaleMinMax[1], 
                                                   g.rangeMinMax[0], g.rangeMinMax[1], unit, sampstart, 'test_file_path', opc_id, xx, yy])

            return render_template('newButton.html', listbox=g.listbox,
                                                      opc_list=g.opc_list,
                                                      opc_list_2=g.opc_list_2, 
                                                      times=g.times,
                                                      tag_info=g.tag_info, 
                                                      table_data=g.table_data,
                                                      selectedRow=g.selectedRow,
                                                      periodic_display=g.periodic_display,
                                                      tag_trigger_display=g.tag_trigger_display,
                                                      file_trigger_display=g.file_trigger_display,
                                                      tag_trigger_info=g.tag_trigger_info)

        elif "submitbutt_tagT18" in request.form and request.form["submitbutt_tagT18"] == "Save Tag":
            g.tag_trigger_scaleMinMax[0] = (request.form["scaleMin_tagT19"], request.form["scaleMax_tagT19"])
            g.tag_trigger_rangeMinMax[0] = (request.form["rangeMin_tagT19"], request.form["rangeMax_tagT19"])
            unit = request.form["unit_tagT19"]
            g.tag_trigger_temp[0] = [str(len(g.table_data[1])) , request.form['unique_name_input_tagTI'], g.tag_trigger_info[0][1]+g.tag_trigger_info[0][2],
                                    g.tag_trigger_scaleMinMax[0][0], g.tag_trigger_scaleMinMax[0][1], g.tag_trigger_rangeMinMax[0][0], g.tag_trigger_rangeMinMax[0][1], 
                                    unit, str(datetime.datetime.now()), request.form['serverSelect'].split(',')[0][2:-1]]
            return render_template('newButton.html', listbox=g.listbox,
                                                      opc_list=g.opc_list,
                                                      opc_list_2=g.opc_list_2, 
                                                      times=g.times,
                                                      tag_info=g.tag_info, 
                                                      table_data=g.table_data,
                                                      selectedRow=g.selectedRow,
                                                      periodic_display=g.periodic_display,
                                                      tag_trigger_display=g.tag_trigger_display,
                                                      file_trigger_display=g.file_trigger_display,
                                                      tag_trigger_info=g.tag_trigger_info)

        elif "submitbutt_tagT28" in request.form and request.form["submitbutt_tagT28"] == "Save Tag":
            g.tag_trigger_scaleMinMax[1] = (request.form["scaleMin_tagT29"], request.form["scaleMax_tagT29"])
            g.tag_trigger_rangeMinMax[1] = (request.form["rangeMin_tagT29"], request.form["rangeMax_tagT29"])
            unit = request.form["unit_tagT29"]
            g.tag_trigger_temp[1] = [str(len(g.table_data)+1), request.form['unique_name_input_tagTII'], g.tag_trigger_info[1][1]+g.tag_trigger_info[1][2],
                                    g.tag_trigger_scaleMinMax[1][0], g.tag_trigger_scaleMinMax[1][1], g.tag_trigger_rangeMinMax[1][0], g.tag_trigger_rangeMinMax[1][1], 
                                    unit, str(datetime.datetime.now()), request.form['serverSelect'].split(',')[0][2:-1]]
            return render_template('newButton.html', listbox=g.listbox,
                                                      opc_list=g.opc_list,
                                                      opc_list_2=g.opc_list_2, 
                                                      times=g.times,
                                                      tag_info=g.tag_info, 
                                                      table_data=g.table_data,
                                                      selectedRow=g.selectedRow,
                                                      periodic_display=g.periodic_display,
                                                      tag_trigger_display=g.tag_trigger_display,
                                                      file_trigger_display=g.file_trigger_display,
                                                      tag_trigger_info=g.tag_trigger_info)

        elif "submitbutt_tagT38" in request.form and request.form["submitbutt_tagT38"] == "Save Tag":
            g.tag_trigger_scaleMinMax[2] = (request.form["scaleMin_tagT39"], request.form["scaleMax_tagT39"])
            g.tag_trigger_rangeMinMax[2] = (request.form["rangeMin_tagT39"], request.form["rangeMax_tagT39"])
            unit = request.form["unit_tagT39"]
            g.tag_trigger_temp[2] = [str(len(g.table_data)+2), request.form['unique_name_input_tagTIII'], g.tag_trigger_info[2][1]+g.tag_trigger_info[2][2],
                                    g.tag_trigger_scaleMinMax[2][0], g.tag_trigger_scaleMinMax[2][1], g.tag_trigger_rangeMinMax[2][0], g.tag_trigger_rangeMinMax[2][1], 
                                    unit, str(datetime.datetime.now()), request.form['serverSelect'].split(',')[0][2:-1]]
            return render_template('newButton.html', listbox=g.listbox,
                                                      opc_list=g.opc_list,
                                                      opc_list_2=g.opc_list_2, 
                                                      times=g.times,
                                                      tag_info=g.tag_info, 
                                                      table_data=g.table_data,
                                                      selectedRow=g.selectedRow,
                                                      periodic_display=g.periodic_display,
                                                      tag_trigger_display=g.tag_trigger_display,
                                                      file_trigger_display=g.file_trigger_display,
                                                      tag_trigger_info=g.tag_trigger_info)

        elif "submitbutt_tagTsend" in request.form and request.form["submitbutt_tagTsend"] == "Add Tags":
            for held in g.tag_trigger_temp:
                g.hold_table_data_tag_trigger.append(held)
            g.tag_trigger_temp = [[],[],[]]
            g.tag_trigger_scaleMinMax = [(0,0),(0,0),(0,0)]
            g.tag_trigger_rangeMinMax = [(0,0),(0,0),(0,0)]
            return render_template('newButton.html', listbox=g.listbox,
                                                      opc_list=g.opc_list,
                                                      opc_list_2=g.opc_list_2, 
                                                      times=g.times,
                                                      tag_info=g.tag_info, 
                                                      table_data=g.table_data,
                                                      selectedRow=g.selectedRow,
                                                      periodic_display=g.periodic_display,
                                                      tag_trigger_display=g.tag_trigger_display,
                                                      file_trigger_display=g.file_trigger_display,
                                                      tag_trigger_info=g.tag_trigger_info)
        
        elif "times_submit" in request.form  and request.form["times"] == "std_times":
            g.tag_info[3] = request.form['standartTimes']
            return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "times_submit" in request.form and request.form["times"] == "sp_times":
            g.tag_info[3] = request.form['specialTimesInput'] + "s"
            return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info) 

        elif "saveAll" in request.form:
            tree = ET.parse(g.newFile.name)
            new_periodic = g.hold_table_data_periodic
            new_tag_trigger = g.hold_table_data_tag_trigger
            new_file_trigger = g.hold_table_data_file_trigger
            hold_time = ""
            addHere_periodic = tree.getroot().find('timed_trig')
            periodic_addtoindex = 0
            addHere_tag_trigger = tree.getroot().find('tag_trig')
            tag_trigger_addtoindex = 0
            addHere_file_trigger = tree.getroot().find('file_trig')
            file_trigger_addtoindex = 0

            for i in new_periodic:
                g.table_data[0].append(i)
            for i in new_tag_trigger:
                g.table_data[1].append(i)
            for i in new_file_trigger:
                g.table_data[2].append(i)
            for sometag in new_periodic:
                if sometag[3] in g.times:
                    hold_time = addHere_periodic.find('st_times')
                    find_group = hold_time.find('group_'+sometag[3])
                    new_tag = ET.SubElement(find_group, 'tag_'+str(int(g.table_row_count)+periodic_addtoindex))
                    new_t_name = ET.SubElement(new_tag, 't_name')
                    new_t_name.text = sometag[1]
                    new_t_addr = ET.SubElement(new_tag, 't_addr')
                    new_t_addr.text = sometag[2]
                    new_scale_max = ET.SubElement(new_tag, 'scale_max')
                    new_scale_max.text = sometag[4]
                    new_scale_min = ET.SubElement(new_tag, 'scale_min')
                    new_scale_min.text = sometag[5]
                    new_range_max = ET.SubElement(new_tag, 'range_max')
                    new_range_max.text = sometag[6]
                    new_range_min = ET.SubElement(new_tag, 'range_min')
                    new_range_min.text = sometag[7]
                    new_unit = ET.SubElement(new_tag, 'unit')
                    new_unit.text = sometag[8]
                    new_samp_start = ET.SubElement(new_tag, 'samp_start')
                    new_samp_start.text = sometag[9]
                    new_opc_id = ET.SubElement(new_tag, 'OPC_ID')
                    new_opc_id.text = sometag[10]
                else:
                    hold_time = addHere_periodic.find('sp_times')
                    find_group = hold_time.find(sometag[3])
                    new_tag = ET.SubElement(find_group, 'tag_'+str(int(g.table_row_count)+periodic_addtoindex))
                    new_t_name = ET.SubElement(new_tag, 't_name')
                    new_t_name.text = sometag[1]
                    new_t_addr = ET.SubElement(new_tag, 't_addr')
                    new_t_addr.text = sometag[2]
                    new_scale_max = ET.SubElement(new_tag, 'scale_max')
                    new_scale_max.text = sometag[4]
                    new_scale_min = ET.SubElement(new_tag, 'scale_min')
                    new_scale_min.text = sometag[5]
                    new_range_max = ET.SubElement(new_tag, 'range_max')
                    new_range_max.text = sometag[6]
                    new_range_min = ET.SubElement(new_tag, 'range_min')
                    new_range_min.text = sometag[7]
                    new_unit = ET.SubElement(new_tag, 'unit')
                    new_unit.text = sometag[8]
                    new_samp_start = ET.SubElement(new_tag, 'samp_start')
                    new_samp_start.text = sometag[9]
                    new_opc_id = ET.SubElement(new_tag, 'OPC_ID')
                    new_opc_id.text = sometag[10]
                    new_period = ET.SubElement(new_tag, 'period')
                    new_period.text = sometag[3]
                periodic_addtoindex += 1
            
            for sometagtrigger in new_tag_trigger:
                new_tag = ET.SubElement(addHere_tag_trigger, 'tag_trig_'+str(len(g.table_data[1])+tag_trigger_addtoindex))
                new_t_name = ET.SubElement(new_tag, 'tag_trigger_name')
                new_t_name.text = sometagtrigger[1]
                new_t_addr = ET.SubElement(new_tag, 'tag_trigger_addr')
                new_t_addr.text = sometagtrigger[2]
                new_scale_max = ET.SubElement(new_tag, 'tag_trigger_scale_max')
                new_scale_max.text = sometagtrigger[3]
                new_scale_min = ET.SubElement(new_tag, 'tag_trigger_scale_min')
                new_scale_min.text = sometagtrigger[4]
                new_range_max = ET.SubElement(new_tag, 'tag_trigger_range_max')
                new_range_max.text = sometagtrigger[5]
                new_range_min = ET.SubElement(new_tag, 'tag_trigger_range_min')
                new_range_min.text = sometagtrigger[6]
                new_unit = ET.SubElement(new_tag, 'tag_trigger_unit')
                new_unit.text = sometagtrigger[7]
                new_samp_start = ET.SubElement(new_tag, 'tag_trigger_samp_start')
                new_samp_start.text = sometagtrigger[8]
                new_opc_id = ET.SubElement(new_tag, 'tag_trigger_OPC_ID')
                new_opc_id.text = sometagtrigger[9]
                new_value = ET.SubElement(new_tag, 'tag_trigger_value')
                new_value.text = 'ns=5;s=Counter1'
                new_ts = ET.SubElement(new_tag, 'tag_trigger_ts')
                new_ts.text = 'ns=5;s=Sinusoid1'
                tag_trigger_addtoindex += 1

            for somefiletrigger in new_file_trigger:
                new_tag = ET.SubElement(addHere_file_trigger, 'file_trig_'+str(len(g.table_data[2])+file_trigger_addtoindex))
                new_t_name = ET.SubElement(new_tag, 'file_trigger_name')
                new_t_name.text = somefiletrigger[1]
                new_t_addr = ET.SubElement(new_tag, 'file_trigger_addr')
                new_t_addr.text = somefiletrigger[2]
                new_scale_max = ET.SubElement(new_tag, 'file_trigger_scale_max')
                new_scale_max.text = somefiletrigger[3]
                new_scale_min = ET.SubElement(new_tag, 'file_trigger_scale_min')
                new_scale_min.text = somefiletrigger[4]
                new_range_max = ET.SubElement(new_tag, 'file_trigger_range_max')
                new_range_max.text = somefiletrigger[5]
                new_range_min = ET.SubElement(new_tag, 'file_trigger_range_min')
                new_range_min.text = somefiletrigger[6]
                new_unit = ET.SubElement(new_tag, 'file_trigger_unit')
                new_unit.text = somefiletrigger[7]
                new_samp_start = ET.SubElement(new_tag, 'file_trigger_samp_start')
                new_samp_start.text = somefiletrigger[8]
                new_opc_id = ET.SubElement(new_tag, 'file_trigger_OPC_ID')
                new_opc_id.text = somefiletrigger[9]
                new_file_path = ET.SubElement(new_tag, 'file_trigger_file_path')
                new_file_path.text = somefiletrigger[10]
                new_read_row = ET.SubElement(new_tag, 'file_trigger_read_row')
                new_read_row.text = somefiletrigger[11]
                new_read_column = ET.SubElement(new_tag, 'file_trigger_read_column')
                new_read_column.text = somefiletrigger[12]
                file_trigger_addtoindex += 1

            g.hold_table_data_periodic = []
            g.hold_table_data_tag_trigger = []
            g.hold_table_data_file_trigger = []
            tree.write(open(g.newFile.name, 'wb'))

    return render_template('newButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)


@app.route('/loadButton', methods=['GET', 'POST'])
def loadButton_page():
    dFlag=True
    if request.method == "POST":
        if "loadFile" in request.form:
            g.rememberLoadFile = str(request.files['confFile']).split("'")[1]
            g.loadedFile = ET.parse(request.files['confFile'])
            root = g.loadedFile.getroot()
            for i in root.find('OPC_Servers').findall('OPC_Server'):
                g.listbox.append([i.find('id').text,
                                i.find('type').text,
                                i.find('address').text,
                                i.find('server').text,
                                i.find('redundancy').text,
                                i.find('red_address').text,
                                i.find('red_server').text,
                                i.find('active_server').text])
            
            sttimesgroups = root.find('timed_trig').find('st_times').findall('*')
            sptimestags = root.find('timed_trig').find('sp_times').findall('*')
            tagtriggerdata = root.find('tag_trig').findall('*')
            filetriggerdata = root.find('file_trig').findall('*')
            for j_tag in sttimesgroups:
                for i_tag in j_tag.findall('*'):
                    g.table_data[0].append([str(len(g.table_data[0])), i_tag.find('t_name').text, i_tag.find('t_addr').text, j_tag.tag.split('_')[1], i_tag.find('scale_min').text, i_tag.find('scale_max').text, 
                                        i_tag.find('range_min').text, i_tag.find('range_max').text, i_tag.find('unit').text, i_tag.find('samp_start').text, i_tag.find('OPC_ID').text])
            for k_tag in sptimestags:
                g.table_data[0].append([str(len(g.table_data[0])), k_tag.find('t_name').text, k_tag.find('t_addr').text, k_tag.find('period').text, k_tag.find('scale_min').text, k_tag.find('scale_max').text, 
                                    k_tag.find('range_min').text, k_tag.find('range_max').text, k_tag.find('unit').text, k_tag.find('samp_start').text, k_tag.find('OPC_ID').text])
            for g_tag in tagtriggerdata:
                g.table_data[1].append([str(len(g.table_data[1])), g_tag.find('tag_trigger_name').text, g_tag.find('tag_trigger_addr').text, g_tag.find('tag_trigger_scale_max').text, g_tag.find('tag_trigger_scale_min').text,
                                    g_tag.find('tag_trigger_range_max').text, g_tag.find('tag_trigger_range_min').text, g_tag.find('tag_trigger_unit').text, 
                                    g_tag.find('tag_trigger_samp_start').text, g_tag.find('tag_trigger_OPC_ID').text, g_tag.find('tag_trigger_value').text, g_tag.find('tag_trigger_ts').text])
            for f_tag in filetriggerdata:
                g.table_data[2].append([str(len(g.table_data[2])), f_tag.find('file_trigger_name').text, f_tag.find('file_trigger_addr').text, f_tag.find('file_trigger_scale_max').text, f_tag.find('file_trigger_scale_min').text,
                                    f_tag.find('file_trigger_range_max').text, f_tag.find('file_trigger_range_min').text, f_tag.find('file_trigger_unit').text, 
                                    f_tag.find('file_trigger_samp_start').text, f_tag.find('file_trigger_OPC_ID').text, f_tag.find('file_trigger_file_path').text, 
                                    f_tag.find('file_trigger_read_row').text, f_tag.find('file_trigger_read_column').text])

            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow, 
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)
        
        elif "remove" in request.form:
            arr = request.form['remove'].split(',')
            tree = g.loadedFile
            root = tree.getroot()
            abraham = root.find('timed_trig')
            if arr[1] == 'pr':
                if len(g.table_data[0]) > 0:
                    del g.table_data[0][int(arr[0])]
                    if arr[3][1:-1] in g.times:
                        for ids in abraham.find('st_times').findall("*"):
                            for mytags in ids.findall("*"):
                                if mytags.find('t_name').text == arr[2][1:-1]:
                                    ids.remove(mytags)
                    else:
                        for ids in abraham.find('sp_times').findall("*"):
                            for mytags in ids.findall("*"):
                                if mytags.find('t_name').text == arr[2][1:-1]:
                                    ids.remove(mytags)
                    for i in range(len(g.table_data[0])):
                        g.table_data[0][i][0] = str(i)
            elif arr[1] == 'tt':
                if len(g.table_data[1]) > 0:
                    del g.table_data[1][int(arr[0])]
                    for i in range(len(g.table_data[1])):
                        g.table_data[1][i][0] = str(i)
                    for ids in tree.find('tag_trig').findall("*"):
                        if ids.find('tag_trigger_name').text == arr[2][1:-1]:
                            tree.find('tag_trig').remove(ids)
            elif arr[1] == 'ft':
                if len(g.table_data[2]) > 0:
                    del g.table_data[2][int(arr[0])]
                    for i in range(len(g.table_data[2])):
                        g.table_data[2][i][0] = str(i)
                    for ids in tree.find('file_trig').findall("*"):
                        if ids.find('file_trigger_name').text == arr[2][1:-1]:
                            tree.find('file_trig').remove(ids)

            tree.write(open(g.rememberLoadFile, 'wb'))
            
            return render_template('loadButton.html', listbox=g.listbox, 
                                            opc_list=g.opc_list, 
                                            opc_list_2=g.opc_list_2, 
                                            times=g.times, 
                                            tag_info=g.tag_info, 
                                            table_data=g.table_data,
                                            selectedRow=g.selectedRow, 
                                            periodic_display=g.periodic_display,
                                            tag_trigger_display=g.tag_trigger_display,
                                            file_trigger_display=g.file_trigger_display,
                                            tag_trigger_info=g.tag_trigger_info)

        elif "server_remove" in request.form:
            tre = g.loadedFile
            tree = tre.getroot()
            abraham = tree.find('OPC_Servers')
            ishmael = abraham.findall('OPC_Server')
            if len(g.listbox) > 0:
                del g.listbox[int(request.form.get('server_remove'))]
                for opcs in ishmael:
                    if opcs.find('id').text == request.form['server_remove']:
                        abraham.remove(opcs)
                        break
                ishmael = abraham.findall('OPC_Server')
                for svs in range(len(g.listbox)):
                    g.listbox[svs][0] = str(svs)
                for o in range(len(ishmael)):
                    ishmael[o].find('id').text = str(o) 

                tre.write(open(g.rememberLoadFile, 'wb'))
                return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow, 
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)
        
        elif "defineServer" in request.form:
            tre = g.loadedFile
            tree = tre.getroot()
            servers = tree.find('OPC_Servers')
            sList = servers.findall('OPC_Server')
            new = ET.SubElement(servers, 'OPC_Server')
            newid = ET.SubElement(new, 'id')
            newid.text = str(len(sList))
            newtype = ET.SubElement(new, 'type')
            newtype.text = request.form['da_ua']
            newaddress = ET.SubElement(new, 'address')
            newaddress.text = request.form['ogSaddress']
            newserver = ET.SubElement(new, 'server')
            newserver.text = request.form['ogSname']
            newredundancy = ET.SubElement(new, 'redundancy')
            newredaddress = ET.SubElement(new, 'red_address')
            newredserver = ET.SubElement(new, 'red_server')
            newactiveserver = ET.SubElement(new, 'active_server')
            newactiveserver.text = '0'
            if 'redundantCheckbox' in request.form:
                newredundancy.text = request.form['redundantCheckbox']
                newredaddress.text = request.form['redSaddress']
                newredserver.text = request.form['redSname']
            else:
                newredundancy.text = '0'
                newredaddress.text = request.form['ogSaddress']
                newredserver.text = request.form['ogSname']

            tre.write(open(g.rememberLoadFile, 'wb'))
            g.listbox.append([newid.text,
                    newtype.text,
                    newaddress.text,
                    newserver.text,
                    newredundancy.text,
                    newredaddress.text,
                    newredserver.text,
                    newactiveserver.text])
  

        elif "ipaddrEnter" in request.form:
            g.opc = OpenOPC.open_client(request.form["ipaddr"])
            for opcS in g.opc.servers():
                g.listbox.append(opcS)

            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow, 
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)
        

        elif "serverEnter" in request.form:
            g.opc = OpenOPC.open_client('127.0.0.1')
            g.opc.connect(request.form["serverSelect"].split(',')[3][2:-1])
            g.opc_list = g.opc.list()
            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "periodicB" in request.form:
            if g.periodic_display == 'block':
                g.periodic_display = 'none'
            else:
                g.periodic_display = 'block'
            g.tag_trigger_display = 'none'
            g.file_trigger_display = 'none'
            g.tag_info[1], g.tag_info[2], g.tag_info[3] = ("", "", "")
            
            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "tag_triggerB" in request.form:
            g.periodic_display = 'none'
            if g.tag_trigger_display == 'block':
                g.tag_trigger_display = 'none'
            else:
                g.tag_trigger_display = 'block'
            g.file_trigger_display = 'none'
            g.tag_info[1], g.tag_info[2], g.tag_info[3] = ("", "", "")
            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "file_triggerB" in request.form:
            g.periodic_display = 'none'
            g.tag_trigger_display = 'none'
            if g.file_trigger_display == 'block':
                g.file_trigger_display = 'none'
            else:
                g.file_trigger_display = 'block'
            g.tag_info[1], g.tag_info[2], g.tag_info[3] = ("", "", "")
            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitForm" in request.form:
            g.tag_info[1] = request.form['submitForm']
            list_buffer = request.form['submitForm'] + '*.*'
            g.opc_list_2 = g.opc.list(list_buffer, recursive=True)
            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitForm2" in request.form:
            g.tag_info[2] = "." + request.form['submitForm2']
            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)
                                            
        elif "submitForm_tagT11" in request.form:
            g.tag_trigger_info[0][1] = request.form['submitForm_tagT11']
            list_buffer = request.form['submitForm_tagT11'] + '*.*'
            g.opc_list_2 = g.opc.list(list_buffer, recursive=True)
            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitForm2_tagT12" in request.form:
            g.tag_trigger_info[0][2] = "." + request.form['submitForm2_tagT12']
            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitForm_tagT21" in request.form:
            g.tag_trigger_info[1][1] = request.form['submitForm_tagT21']
            list_buffer = request.form['submitForm_tagT21'] + '*.*'
            g.opc_list_2 = g.opc.list(list_buffer, recursive=True)
            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitForm2_tagT22" in request.form:
            g.tag_trigger_info[1][2] = "." + request.form['submitForm2_tagT22']
            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitForm_tagT31" in request.form:
            g.tag_trigger_info[2][1] = request.form['submitForm_tagT31']
            list_buffer = request.form['submitForm_tagT31'] + '*.*'
            g.opc_list_2 = g.opc.list(list_buffer, recursive=True)
            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitForm2_tagT32" in request.form:
            g.tag_trigger_info[2][2] = "." + request.form['submitForm2_tagT32']
            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "submitbutt" in request.form and request.form["submitbutt"] == "Add Tag":
            nameHere = request.form['unique_name_input']
            addrHere = g.tag_info[1]+g.tag_info[2]
            g.scaleMinMax = (request.form["scaleMin"], request.form["scaleMax"])
            g.rangeMinMax = (request.form["rangeMin"], request.form["rangeMax"])
            unit = request.form["unit"]
            sampstart = str(datetime.datetime.now())
            opc_id = request.form['serverSelect'].split(',')[0][2:-1]
            g.hold_table_data_periodic.append([str(len(g.table_data[0])), nameHere, addrHere, g.tag_info[3], 
                                               g.scaleMinMax[0], g.scaleMinMax[1], g.rangeMinMax[0], g.rangeMinMax[1], unit, sampstart, opc_id])

            return render_template('loadButton.html', listbox=g.listbox,
                                                      opc_list=g.opc_list,
                                                      opc_list_2=g.opc_list_2, 
                                                      times=g.times,
                                                      tag_info=g.tag_info, 
                                                      table_data=g.table_data,
                                                      selectedRow=g.selectedRow,
                                                      periodic_display=g.periodic_display,
                                                      tag_trigger_display=g.tag_trigger_display,
                                                      file_trigger_display=g.file_trigger_display,
                                                      tag_trigger_info=g.tag_trigger_info)

        elif "submitbutt_file" in request.form and request.form["submitbutt_file"] == "Add Tag":
            nameHere = request.form['unique_name_inputF']
            xx = request.form['x_input']
            yy = request.form['y_input']
            addrHere = g.tag_info[1]+g.tag_info[2]
            g.scaleMinMax = (request.form["scaleMinF"], request.form["scaleMaxF"])
            g.rangeMinMax = (request.form["rangeMinF"], request.form["rangeMaxF"])
            unit = request.form["unitF"]
            sampstart = str(datetime.datetime.now())
            opc_id = request.form['serverSelect'].split(',')[0][2:-1]
            g.hold_table_data_file_trigger.append([str(len(g.table_data[2])), nameHere, addrHere, g.scaleMinMax[0], g.scaleMinMax[1], 
                                                   g.rangeMinMax[0], g.rangeMinMax[1], unit, sampstart, 'test_file_path', opc_id, xx, yy])

            return render_template('loadButton.html', listbox=g.listbox,
                                                      opc_list=g.opc_list,
                                                      opc_list_2=g.opc_list_2, 
                                                      times=g.times,
                                                      tag_info=g.tag_info, 
                                                      table_data=g.table_data,
                                                      selectedRow=g.selectedRow,
                                                      periodic_display=g.periodic_display,
                                                      tag_trigger_display=g.tag_trigger_display,
                                                      file_trigger_display=g.file_trigger_display,
                                                      tag_trigger_info=g.tag_trigger_info)

        elif "submitbutt_tagT18" in request.form and request.form["submitbutt_tagT18"] == "Save Tag":
            g.tag_trigger_scaleMinMax[0] = (request.form["scaleMin_tagT19"], request.form["scaleMax_tagT19"])
            g.tag_trigger_rangeMinMax[0] = (request.form["rangeMin_tagT19"], request.form["rangeMax_tagT19"])
            unit = request.form["unit_tagT19"]
            g.tag_trigger_temp[0] = [str(len(g.table_data[1])) , request.form['unique_name_input_tagTI'], g.tag_trigger_info[0][1]+g.tag_trigger_info[0][2],
                                    g.tag_trigger_scaleMinMax[0][0], g.tag_trigger_scaleMinMax[0][1], g.tag_trigger_rangeMinMax[0][0], g.tag_trigger_rangeMinMax[0][1], 
                                    unit, str(datetime.datetime.now()), request.form['serverSelect'].split(',')[0][2:-1]]
            return render_template('loadButton.html', listbox=g.listbox,
                                                      opc_list=g.opc_list,
                                                      opc_list_2=g.opc_list_2, 
                                                      times=g.times,
                                                      tag_info=g.tag_info, 
                                                      table_data=g.table_data,
                                                      selectedRow=g.selectedRow,
                                                      periodic_display=g.periodic_display,
                                                      tag_trigger_display=g.tag_trigger_display,
                                                      file_trigger_display=g.file_trigger_display,
                                                      tag_trigger_info=g.tag_trigger_info)

        elif "submitbutt_tagT28" in request.form and request.form["submitbutt_tagT28"] == "Save Tag":
            g.tag_trigger_scaleMinMax[1] = (request.form["scaleMin_tagT29"], request.form["scaleMax_tagT29"])
            g.tag_trigger_rangeMinMax[1] = (request.form["rangeMin_tagT29"], request.form["rangeMax_tagT29"])
            unit = request.form["unit_tagT29"]
            g.tag_trigger_temp[1] = [str(len(g.table_data)+1), request.form['unique_name_input_tagTII'], g.tag_trigger_info[1][1]+g.tag_trigger_info[1][2],
                                    g.tag_trigger_scaleMinMax[1][0], g.tag_trigger_scaleMinMax[1][1], g.tag_trigger_rangeMinMax[1][0], g.tag_trigger_rangeMinMax[1][1], 
                                    unit, str(datetime.datetime.now()), request.form['serverSelect'].split(',')[0][2:-1]]
            return render_template('loadButton.html', listbox=g.listbox,
                                                      opc_list=g.opc_list,
                                                      opc_list_2=g.opc_list_2, 
                                                      times=g.times,
                                                      tag_info=g.tag_info, 
                                                      table_data=g.table_data,
                                                      selectedRow=g.selectedRow,
                                                      periodic_display=g.periodic_display,
                                                      tag_trigger_display=g.tag_trigger_display,
                                                      file_trigger_display=g.file_trigger_display,
                                                      tag_trigger_info=g.tag_trigger_info)

        elif "submitbutt_tagT38" in request.form and request.form["submitbutt_tagT38"] == "Save Tag":
            g.tag_trigger_scaleMinMax[2] = (request.form["scaleMin_tagT39"], request.form["scaleMax_tagT39"])
            g.tag_trigger_rangeMinMax[2] = (request.form["rangeMin_tagT39"], request.form["rangeMax_tagT39"])
            unit = request.form["unit_tagT39"]
            g.tag_trigger_temp[2] = [str(len(g.table_data)+2), request.form['unique_name_input_tagTIII'], g.tag_trigger_info[2][1]+g.tag_trigger_info[2][2],
                                    g.tag_trigger_scaleMinMax[2][0], g.tag_trigger_scaleMinMax[2][1], g.tag_trigger_rangeMinMax[2][0], g.tag_trigger_rangeMinMax[2][1], 
                                    unit, str(datetime.datetime.now()), request.form['serverSelect'].split(',')[0][2:-1]]
            return render_template('loadButton.html', listbox=g.listbox,
                                                      opc_list=g.opc_list,
                                                      opc_list_2=g.opc_list_2, 
                                                      times=g.times,
                                                      tag_info=g.tag_info, 
                                                      table_data=g.table_data,
                                                      selectedRow=g.selectedRow,
                                                      periodic_display=g.periodic_display,
                                                      tag_trigger_display=g.tag_trigger_display,
                                                      file_trigger_display=g.file_trigger_display,
                                                      tag_trigger_info=g.tag_trigger_info)

        elif "submitbutt_tagTsend" in request.form and request.form["submitbutt_tagTsend"] == "Add Tags":
            for held in g.tag_trigger_temp:
                g.hold_table_data_tag_trigger.append(held)
            g.tag_trigger_temp = [[],[],[]]
            g.tag_trigger_scaleMinMax = [(0,0),(0,0),(0,0)]
            g.tag_trigger_rangeMinMax = [(0,0),(0,0),(0,0)]
            return render_template('loadButton.html', listbox=g.listbox,
                                                      opc_list=g.opc_list,
                                                      opc_list_2=g.opc_list_2, 
                                                      times=g.times,
                                                      tag_info=g.tag_info, 
                                                      table_data=g.table_data,
                                                      selectedRow=g.selectedRow,
                                                      periodic_display=g.periodic_display,
                                                      tag_trigger_display=g.tag_trigger_display,
                                                      file_trigger_display=g.file_trigger_display,
                                                      tag_trigger_info=g.tag_trigger_info)
        
        elif "times_submit" in request.form  and request.form["times"] == "std_times":
            g.tag_info[3] = request.form['standartTimes']
            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)

        elif "times_submit" in request.form and request.form["times"] == "sp_times":
            g.tag_info[3] = request.form['specialTimesInput'] + "s"
            return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info) 

        elif "saveAll" in request.form:
            tre = g.loadedFile
            tree = tre.getroot()
            new_periodic = g.hold_table_data_periodic
            new_tag_trigger = g.hold_table_data_tag_trigger
            new_file_trigger = g.hold_table_data_file_trigger
            hold_time = ""
            addHere_periodic = tree.find('timed_trig')
            periodic_addtoindex = 0
            addHere_tag_trigger = tree.find('tag_trig')
            tag_trigger_addtoindex = 0
            addHere_file_trigger = tree.find('file_trig')
            file_trigger_addtoindex = 0

            for i in new_periodic:
                g.table_data[0].append(i)
            for i in new_tag_trigger:
                g.table_data[1].append(i)
            for i in new_file_trigger:
                g.table_data[2].append(i)
            for sometag in new_periodic:
                if sometag[3] in g.times:
                    hold_time = addHere_periodic.find('st_times')
                    find_group = hold_time.find('group_'+sometag[3])
                    new_tag = ET.SubElement(find_group, 'tag_'+str(int(g.table_row_count)+periodic_addtoindex))
                    new_t_name = ET.SubElement(new_tag, 't_name')
                    new_t_name.text = sometag[1]
                    new_t_addr = ET.SubElement(new_tag, 't_addr')
                    new_t_addr.text = sometag[2]
                    new_scale_max = ET.SubElement(new_tag, 'scale_max')
                    new_scale_max.text = sometag[4]
                    new_scale_min = ET.SubElement(new_tag, 'scale_min')
                    new_scale_min.text = sometag[5]
                    new_range_max = ET.SubElement(new_tag, 'range_max')
                    new_range_max.text = sometag[6]
                    new_range_min = ET.SubElement(new_tag, 'range_min')
                    new_range_min.text = sometag[7]
                    new_unit = ET.SubElement(new_tag, 'unit')
                    new_unit.text = sometag[8]
                    new_samp_start = ET.SubElement(new_tag, 'samp_start')
                    new_samp_start.text = sometag[9]
                    new_opc_id = ET.SubElement(new_tag, 'OPC_ID')
                    new_opc_id.text = sometag[10]
                else:
                    hold_time = addHere_periodic.find('sp_times')
                    find_group = hold_time.find(sometag[3])
                    new_tag = ET.SubElement(find_group, 'tag_'+str(int(g.table_row_count)+periodic_addtoindex))
                    new_t_name = ET.SubElement(new_tag, 't_name')
                    new_t_name.text = sometag[1]
                    new_t_addr = ET.SubElement(new_tag, 't_addr')
                    new_t_addr.text = sometag[2]
                    new_scale_max = ET.SubElement(new_tag, 'scale_max')
                    new_scale_max.text = sometag[4]
                    new_scale_min = ET.SubElement(new_tag, 'scale_min')
                    new_scale_min.text = sometag[5]
                    new_range_max = ET.SubElement(new_tag, 'range_max')
                    new_range_max.text = sometag[6]
                    new_range_min = ET.SubElement(new_tag, 'range_min')
                    new_range_min.text = sometag[7]
                    new_unit = ET.SubElement(new_tag, 'unit')
                    new_unit.text = sometag[8]
                    new_samp_start = ET.SubElement(new_tag, 'samp_start')
                    new_samp_start.text = sometag[9]
                    new_opc_id = ET.SubElement(new_tag, 'OPC_ID')
                    new_opc_id.text = sometag[10]
                    new_period = ET.SubElement(new_tag, 'period')
                    new_period.text = sometag[3]
                periodic_addtoindex += 1
            
            for sometagtrigger in new_tag_trigger:
                new_tag = ET.SubElement(addHere_tag_trigger, 'tag_trig_'+str(len(g.table_data[1])+tag_trigger_addtoindex))
                new_t_name = ET.SubElement(new_tag, 'tag_trigger_name')
                new_t_name.text = sometagtrigger[1]
                new_t_addr = ET.SubElement(new_tag, 'tag_trigger_addr')
                new_t_addr.text = sometagtrigger[2]
                new_scale_max = ET.SubElement(new_tag, 'tag_trigger_scale_max')
                new_scale_max.text = sometagtrigger[3]
                new_scale_min = ET.SubElement(new_tag, 'tag_trigger_scale_min')
                new_scale_min.text = sometagtrigger[4]
                new_range_max = ET.SubElement(new_tag, 'tag_trigger_range_max')
                new_range_max.text = sometagtrigger[5]
                new_range_min = ET.SubElement(new_tag, 'tag_trigger_range_min')
                new_range_min.text = sometagtrigger[6]
                new_unit = ET.SubElement(new_tag, 'tag_trigger_unit')
                new_unit.text = sometagtrigger[7]
                new_samp_start = ET.SubElement(new_tag, 'tag_trigger_samp_start')
                new_samp_start.text = sometagtrigger[8]
                new_opc_id = ET.SubElement(new_tag, 'tag_trigger_OPC_ID')
                new_opc_id.text = sometagtrigger[9]
                new_value = ET.SubElement(new_tag, 'tag_trigger_value')
                new_value.text = 'ns=5;s=Counter1'
                new_ts = ET.SubElement(new_tag, 'tag_trigger_ts')
                new_ts.text = 'ns=5;s=Sinusoid1'
                tag_trigger_addtoindex += 1

            for somefiletrigger in new_file_trigger:
                new_tag = ET.SubElement(addHere_file_trigger, 'file_trig_'+str(len(g.table_data[2])+file_trigger_addtoindex))
                new_t_name = ET.SubElement(new_tag, 'file_trigger_name')
                new_t_name.text = somefiletrigger[1]
                new_t_addr = ET.SubElement(new_tag, 'file_trigger_addr')
                new_t_addr.text = somefiletrigger[2]
                new_scale_max = ET.SubElement(new_tag, 'file_trigger_scale_max')
                new_scale_max.text = somefiletrigger[3]
                new_scale_min = ET.SubElement(new_tag, 'file_trigger_scale_min')
                new_scale_min.text = somefiletrigger[4]
                new_range_max = ET.SubElement(new_tag, 'file_trigger_range_max')
                new_range_max.text = somefiletrigger[5]
                new_range_min = ET.SubElement(new_tag, 'file_trigger_range_min')
                new_range_min.text = somefiletrigger[6]
                new_unit = ET.SubElement(new_tag, 'file_trigger_unit')
                new_unit.text = somefiletrigger[7]
                new_samp_start = ET.SubElement(new_tag, 'file_trigger_samp_start')
                new_samp_start.text = somefiletrigger[8]
                new_opc_id = ET.SubElement(new_tag, 'file_trigger_OPC_ID')
                new_opc_id.text = somefiletrigger[9]
                new_file_path = ET.SubElement(new_tag, 'file_trigger_file_path')
                new_file_path.text = somefiletrigger[10]
                new_read_row = ET.SubElement(new_tag, 'file_trigger_read_row')
                new_read_row.text = somefiletrigger[11]
                new_read_column = ET.SubElement(new_tag, 'file_trigger_read_column')
                new_read_column.text = somefiletrigger[12]
                file_trigger_addtoindex += 1

            g.hold_table_data_periodic = []
            g.hold_table_data_tag_trigger = []
            g.hold_table_data_file_trigger = []
            tre.write(open(g.rememberLoadFile, 'wb'))

    return render_template('loadButton.html', listbox=g.listbox, 
                                              opc_list=g.opc_list, 
                                              opc_list_2=g.opc_list_2, 
                                              times=g.times, 
                                              tag_info=g.tag_info, 
                                              table_data=g.table_data,
                                              selectedRow=g.selectedRow,
                                              periodic_display=g.periodic_display,
                                              tag_trigger_display=g.tag_trigger_display,
                                              file_trigger_display=g.file_trigger_display,
                                              tag_trigger_info=g.tag_trigger_info)