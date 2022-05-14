import sys, threading, os
import json
import tkinter as tk
from tkinter.constants import END, GROOVE
from tkinter.font import Font
from PyQt5.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from PyQt5.QtGui import QIcon
import psutil
from plyer import notification
import time


pathico = os.getcwd() + "\icon.ico"
pathjson = os.getcwd() + "\stored.json"

quited = False
usage = 0

def notify(message, sec = 5):
    notification.notify(
        title = "Battery Notifier",
        message = message,
        app_icon = pathico,
        timeout = sec
    )

def load_dump(do = 0, data = {"Max Battery": 80, "Min Battery": 40, "Depletion": "No Data", "Charging": "No Data"}):
    if do == 0 or do == "load":
        f = open(pathjson,)
        temp = json.load(f)
        f.close()
        return temp
    elif do == 1 or do == "dump":
        f = open(pathjson, "w")
        json.dump(data, f, indent= 1)
        f.truncate()
        f.close()

batteryJSON = load_dump()

def varmenu():
    
    root = tk.Tk()
    root.iconphoto(False, tk.PhotoImage(file= (os.getcwd() + "\icon.png")))
    root.geometry('320x220+1000+600')
    root.resizable(False, False)
    root.title('Battery Notifier')
    
    def update(name: list, text = [], refresh = False):
        if root.state() != "normal":
            return
        batteryJSON = load_dump()
        for i in range(len(name)):
            if refresh:
                text = refresh[i] + ": " + str(batteryJSON[refresh[i]]) + " per/min"
                name[i]["text"] = text
            else:   
                name[i]["text"] = text[i]
            
    def edit():
        global batteryJSON

        if maxbattery.get() <= 50:
            batteryJSON["Max Battery"] = 50
        elif maxbattery.get() >= 95:
            batteryJSON["Max Battery"] = 95
        else:
            batteryJSON["Max Battery"] = maxbattery.get()
        
        if minbattery.get() >= 45:
            batteryJSON["Min Battery"] = 45
        elif minbattery.get() <= 10:
            batteryJSON["Min Battery"] = 10
        else:
            batteryJSON["Min Battery"] = minbattery.get()
        
        update([maxwidget], ["Current: {}".format(batteryJSON["Max Battery"])])
        update([minwidget], ["Current: {}".format(batteryJSON["Min Battery"])])
        load_dump(1, batteryJSON)

    maxbattery = tk.IntVar()
    minbattery = tk.IntVar()

    font = Font(root, family= "Arial", size= 10)
    font2 = Font(root, family= "Arial", size= 8)
    tk.Label(root, text= 'Max Battery', font= font, pady= 5).place(x = 45, y = 30)

    maxwidget = tk.Label(root, text= 'Current: {}'.format(batteryJSON["Max Battery"]), font= font2, pady= 5)
    maxwidget.place(x = 210, y = 30)
    e1 = tk.Entry(root, textvariable= maxbattery, width= 5, font= ("bold", 10))
    e1.delete(0, END)
    e1.insert(0, str(batteryJSON["Max Battery"]))
    e1.place(x= 150, y= 35)

    tk.Label(root, text= 'Min Battery', font= font, pady= 5).place(x = 45, y = 70)
    minwidget = tk.Label(root, text= 'Current: {}'.format(batteryJSON["Min Battery"]), font= font2, pady= 5)
    minwidget.place(x = 210, y = 70)
    e2 = tk.Entry(root, textvariable= minbattery, width= 5, font= ("bold", 10))
    e2.delete(0, END)
    e2.insert(0, str(batteryJSON["Min Battery"]))
    e2.place(x= 150, y= 75)
    
    dep = tk.Label(root, text= ("Depletion: " + ((str(batteryJSON["Depletion"]) + " per/min") if batteryJSON["Depletion"] > 0 else "No Data")), font= font2)
    dep.place(x= 20, y= 180)

    char = tk.Label(root, text= ("Charging: " + ((str(batteryJSON["Charging"]) + " per/min") if batteryJSON["Charging"] > 0 else "No Data")), font= font2)
    char.place(x= 180, y= 180)

    refresh = tk.Button(root, text= "⟲", borderwidth= 1, padx=5, pady=2, command= lambda: update([dep, char], refresh= ["Depletion", "Charging"]))
    refresh.place(x= 0, y= 0)
    SUB = tk.Button(root, text='Confirm', borderwidth= 1, command= edit)
    SUB.place(x= 80, y= 130)
    
    close_button = tk.Button(root, text="Close", borderwidth= 1, padx= 5, command= root.destroy)
    close_button.place(x= 200, y= 130)

    root.update()
    root.mainloop()

def isLogged():
    for proc in psutil.process_iter():
        if(proc.name() == "LogonUI.exe"):
            return False
    return True

def tellBattery():
    battery = psutil.sensors_battery()
    return battery.percent

def pluggedIn():
    battery = psutil.sensors_battery()
    return battery.power_plugged

def updateJSON(val, batteryJSON, var_time):
    if batteryJSON[val] == 0 or batteryJSON[val] == "No Data":
        batteryJSON[val] = round((batteryJSON[val] + 1 / ((time.time() - var_time) * 0.0166667)), 2)
    else:
        batteryJSON[val] = round((batteryJSON[val] + 1 / ((time.time() - var_time) * 0.0166667)) / 2, 2)
    
    load_dump(1, batteryJSON)
    return time.time()

def main(high, low, times, jump, charging, var_time, start_time, sleep = 15):
    global quited

    if quited:
        notify("Service Ended\nUsed for {}".format(time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)), 10))
        return
    
    batteryJSON = load_dump()
    upper = batteryJSON["Max Battery"]
    lower = batteryJSON["Min Battery"]

    if  charging != pluggedIn():
        jump = True
        charging = pluggedIn()

    percent = tellBattery()
    logged = isLogged()

    high = max(high, percent)
    low = min(low, percent)

    if not logged:
        jump = True

    if high - low > 0 and not charging and logged:
        if not jump:
            var_time = updateJSON("Depletion", batteryJSON, var_time)
            high = low
        else:
            jump = False
            high = low
            var_time = time.time()
            
    elif high - low > 0 and charging and logged:
        if not jump:
            var_time = updateJSON("Charging", batteryJSON, var_time)
            low = high
        else:
            jump = False
            low = high
            var_time = time.time()

    
    if percent >= upper and charging and times < 3 and sleep >= 15:
        times += 1
        notify("Battery at {} Plug out now.\nCharging rate: {} percent/min".format(percent, batteryJSON["Charging"]))
        sleep = 0
    elif percent >= upper and not charging:
        times = 0

    elif percent <= lower and not charging and times < 3 and sleep >= 15:
        times += 1
        notify("Battery at {} Plug in now.\nDepletion rate: {} percent/min".format(percent, batteryJSON["Depletion"]))
        sleep = 0
    elif percent <= lower and charging:
        times = 0
    
    elif batteryJSON["Max Battery"] > percent > batteryJSON["Min Battery"]:
        times = 0
    
    sleep += 1
    threading.Timer(1, main, args= [high, low, times, jump, charging, var_time, start_time, sleep]).start()
    

def trayIcon():
    global quited

    def quitnow():
        global quited
        app.quit()
        quited = True

    app = QApplication(sys.argv)

    tray_icon = QSystemTrayIcon(QIcon(pathico), parent= app)
    tray_icon.setToolTip("Battery Notifier")
    tray_icon.show()

    menu = QMenu()

    callmain = menu.addAction("Edit variables")
    callmain.triggered.connect(varmenu)

    exitAction = menu.addAction("Exit")
    exitAction.triggered.connect(quitnow)

    tray_icon.setContextMenu(menu)

    sys.exit(app.exec_())


notify("Service Started", 3)
t = time.time()

main(-1e9, 1e9, 0, True, pluggedIn(), t, t)
trayIcon()
