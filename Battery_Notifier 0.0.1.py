import sys, threading, os
import json
import tkinter as tk
from tkinter.constants import END
from tkinter.font import Font
from PyQt5.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from PyQt5.QtGui import QIcon
import psutil
from plyer import notification
import time

# JSON Looks like
#{
# "Max Battery": 80,
# "Min Battery": 45,
# "Interval": 30
#}
#--------------------

#gets directory of the json and icon file
pathico = os.getcwd() + "\icon.ico"
pathjson = os.getcwd() + "\stored.json"

quited = False


def notify(message, sec = 5):
    """Gives out notification whenever called with message and duration of notification as args"""
    notification.notify(
        title = "Battery Notifier",
        message = message,
        app_icon = pathico,
        timeout = sec
    )

def load_dump(do = 0, data = None):
    """Loads and Dumps data in the JSON file, takes do('dumps' == 0 or 'load' == 1) and data(when dumping required) as args"""
    if do == 0 or do == "load":
        f = open(pathjson,)
        #load json file
        temp = json.load(f)
        f.close()
        return temp
    elif do == 1 or do == "dump":
        f = open(pathjson, "w")
        #dump data in json file
        json.dump(data, f, indent= 1)
        f.truncate()
        f.close()

batteryJSON = load_dump()

def varmenu():
    """Executes when User selects 'Edit Variable' from the tray icon, this updates the default values"""
    global batteryJSON

    root = tk.Tk()
    root.iconphoto(False, tk.PhotoImage(file= (os.getcwd() + "\icon.png")))
    root.geometry('320x220+1000+600')
    root.resizable(False, False)
    root.title('Battery Notifier')
    
    def edit():
        """This makes sure valid values get accepted"""
        global batteryJSON

        if maxbattery.get() <= 50:
            batteryJSON["Max Battery"] = 50
        elif maxbattery.get() >= 95:
            batteryJSON["Max Battery"] = 95
        else:
            batteryJSON["Max Battery"] = maxbattery.get()
        
        if minbattery.get() >= 50:
            batteryJSON["Min Battery"] = 50
        elif minbattery.get() <= 10:
            batteryJSON["Min Battery"] = 10
        else:
            batteryJSON["Min Battery"] = minbattery.get()
        
        if interval.get() >= 300:
            batteryJSON["Interval"] = 300
        elif interval.get() <= 15:
            batteryJSON["Interval"] = 15
        else:
            batteryJSON["Interval"] = interval.get()
        
        #Update text widgets
        maxwidget["text"] = "Current: {}".format(batteryJSON["Max Battery"])
        minwidget["text"] = "Current: {}".format(batteryJSON["Min Battery"])
        interwid["text"] = "Current: {}".format(batteryJSON["Interval"])

        #dump the updated data
        load_dump(1, batteryJSON)

    maxbattery = tk.IntVar()
    minbattery = tk.IntVar()
    interval = tk.IntVar()

    
    font = Font(root, family= "Arial", size= 10)
    font2 = Font(root, family= "Arial", size= 8)

    #Text widgets for max battery
    tk.Label(root, text= 'Max Battery', font= font, pady= 5).place(x = 45, y = 30)
    maxwidget = tk.Label(root, text= 'Current: {}'.format(batteryJSON["Max Battery"]), font= font2, pady= 5)
    maxwidget.place(x = 210, y = 30)
    #entry for max battery
    e1 = tk.Entry(root, textvariable= maxbattery, width= 5, font= ("bold", 10))
    e1.place(x= 150, y= 35)

    #Text widgets for min battery
    tk.Label(root, text= 'Min Battery', font= font, pady= 5).place(x = 45, y = 70)
    minwidget = tk.Label(root, text= 'Current: {}'.format(batteryJSON["Min Battery"]), font= font2, pady= 5)
    minwidget.place(x = 210, y = 70)
    #entry for min battery
    e2 = tk.Entry(root, textvariable= minbattery, width= 5, font= ("bold", 10))
    e2.place(x= 150, y= 75)

    #Text widgets for interval
    tk.Label(root, text= 'Interval', font= font, pady= 5).place(x = 45, y = 110)
    interwid = tk.Label(root, text= 'Current: {}'.format(batteryJSON["Interval"]), font= font2, pady= 5)
    interwid.place(x = 210, y = 110)
    #entry for interval
    e3 = tk.Entry(root, textvariable= interval, width= 5, font= ("bold", 10))
    e3.place(x= 150, y= 115)

    #Confirm Button, calls edit fuction to update the data
    SUB = tk.Button(root, text='Confirm', borderwidth= 1, command= edit)
    SUB.place(x= 80, y= 170)
    
    #button to close the tkinter window
    close_button = tk.Button(root, text="Close", borderwidth= 1, padx= 5, command= root.destroy)
    close_button.place(x= 200, y= 170)

    #mainloop
    root.update()
    root.mainloop()


def tellBattery():
    """returns the battery percent"""
    battery = psutil.sensors_battery()
    return battery.percent

def pluggedIn():
    """returns a bool whether power is plugged in or not"""
    battery = psutil.sensors_battery()
    return battery.power_plugged

def main(start_time):
    """Checks and notifies if battery reaches the set limits"""
    global quited, batteryJSON
    
    batteryJSON = load_dump()
    upper = batteryJSON["Max Battery"]
    lower = batteryJSON["Min Battery"]

    percent = tellBattery()
    charging = pluggedIn()
    
    #battery checking
    if percent >= upper and charging:
        notify("Battery at {} Plug out now.".format(percent))
        time.sleep(batteryJSON["Interval"] - 5)

    elif percent <= lower and not charging:
        notify("Battery at {} Plug in now.".format(percent))
        time.sleep(batteryJSON["Interval"] - 5)

    #Whether to execute further or not
    if not quited:
        #calls main() every 3 seconds
        threading.Timer(3, main, args= [start_time]).start()
    else:
        #Service end if this situation is reached
        notify("Service Ended\nUsed for {}".format(time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)), 10))
        load_dump(1, batteryJSON)
    

def trayIcon():
    """Creates the tray icon using PyQt5"""
    global quited

    def quitnow():
        """called when user quits the service, set quited to True which stops main from getting called again"""
        global quited
        app.quit()
        quited = True

    #app initialization
    app = QApplication(sys.argv)

    #tray icon intialization
    tray_icon = QSystemTrayIcon(QIcon(pathico), parent= app)
    tray_icon.setToolTip("Battery Notifier")
    tray_icon.show()

    #menu of tray icon
    menu = QMenu()

    #call varmenu to update data
    edit = menu.addAction("Edit variables")
    edit.triggered.connect(varmenu)

    #ends service
    exitAction = menu.addAction("Exit")
    exitAction.triggered.connect(quitnow)

    #Join the created menu with tray icon
    tray_icon.setContextMenu(menu)

    sys.exit(app.exec_())


notify("Service Started", 3)

main(time.time())
trayIcon()
