import requests
import demjson
import ipaddress

from toner import Toner
from drum import Drum
from tray import Tray
from alert import Alert


class SerialNumException(Exception):
    pass


class Printer:
    def __init__(self, config: dict, ip: str, serial_num: str, dynamic_ip: bool, bot,
                 toner_alerts: bool, drum_alerts: bool, tray_alerts: bool, alert_levels: list[int],
                 reachedTonLevels: dict, reachedDrumLevels: dict, reachedTrayLevels: dict):
        self.config = config
        self.ip = ip
        self.serial_num = serial_num
        self.dynamic_ip = dynamic_ip
        self.model_name = "????"
        self.toners = []
        self.drums = []
        self.trays = []
        self.alerts = []
        self.uptime = 0
        self.bot = bot
        self.toner_alerts = toner_alerts
        self.drum_alerts = drum_alerts
        self.tray_alerts = tray_alerts
        self.alert_levels = alert_levels
        self.reachedTonLevels = reachedTonLevels
        self.reachedDrumLevels = reachedDrumLevels
        self.reachedTrayLevels = reachedTrayLevels

    def __update_data(self, custom_ip=None) -> bool:
        # this is pretty much a reverse-engineered version of the web api
        ip = self.ip
        if custom_ip is not None:
            ip = custom_ip
        home_url = 'http://'+ip+'/sws/app/information/home/home.json'
        try:
            r = requests.get(home_url)
            text = r.content.decode("utf8")
            home_data = demjson.decode(text)
            self.model_name = home_data["identity"]["model_name"]
            if home_data["identity"]["serial_num"] != self.serial_num:
                raise SerialNumException()
            for component in home_data.keys():
                if "drum_" in component: 
                    color = component.replace("drum_", "")
                    drum = home_data[component]
                    if not drum["opt"]:
                        continue
                    self.drums.append(Drum(color, drum["remaining"]))
                    if self.drum_alerts: # check if alerts are enabled
                        drumLevels = []
                        for level in self.alert_levels:
                            if drum["remaining"] <= level: # check alert levels reached
                                drumLevels.append(level)
                        if color not in self.reachedDrumLevels.keys():
                            self.reachedDrumLevels[color] = [] # add color key to dict if not present
                        if len(drumLevels) and min(drumLevels) not in self.reachedDrumLevels["color"]: # check if alert level reached is not already in dict
                            dyn = ""
                            if self.dynamic_ip:
                                dyn = "(dynamic)"
                            rem = drum["remaining"]
                            # send telegram message
                            self.bot.send_message(
                                self.config["telegram_user_id"], f"Drum {color} of printer {self.serial_num} @ {self.ip} {dyn} is at {rem}%")
                        # add alert level to dict
                        self.reachedDrumLevels["color"] = drumLevels
                if "tray" in component:
                    tray_no = int(component.replace("tray", ""))
                    tray = home_data[component]
                    if not tray["opt"]:
                        continue
                    self.trays.append(
                        Tray(tray_no, tray["capa"], tray["paper_level"]))
                    if self.tray_alerts:
                        trayLevels = []
                        for level in self.alert_levels:
                            if tray["paper_level"] <= level:
                                trayLevels.append(level)
                        tray_key = f"t{tray_no}"
                        if tray_key not in self.reachedTrayLevels.keys():
                            self.reachedTrayLevels[tray_key] = []
                        if len(trayLevels) and min(trayLevels) not in self.reachedTrayLevels[tray_key]:
                            dyn = ""
                            if self.dynamic_ip:
                                dyn = "(dynamic)"
                            lev = tray["paper_level"]
                            self.bot.send_message(
                                self.config["telegram_user_id"], f"Tray {tray_no} of printer {self.serial_num} @ {self.ip} {dyn} is at {lev} pages")
                        self.reachedTrayLevels[tray_key] = trayLevels
                if "toner_" in component:
                    color = component.replace("toner_", "")
                    ton = home_data[component]
                    if not ton["opt"]:
                        continue
                    self.toners.append(
                        Toner(color, ton["cnt"], ton["remaining"]))
                    if color not in self.reachedTonLevels.keys():
                        self.reachedTonLevels[color] = []
                    if self.toner_alerts:
                        tonLevels = []
                        for level in self.alert_levels:
                            if ton["remaining"] <= level:
                                tonLevels.append(level)
                        if len(tonLevels) and min(tonLevels) not in self.reachedTonLevels[color]:
                            dyn = ""
                            if self.dynamic_ip:
                                dyn = "(dynamic)"
                            rem = ton["remaining"]
                            self.bot.send_message(
                                self.config["telegram_user_id"], f"Toner {color} of printer {self.serial_num} @ {self.ip} {dyn} is at {rem}%")
                        self.reachedTonLevels[color] = tonLevels

            alert_url = 'http://'+ip+'/sws/app/information/activealert/activealert.json'
            r = requests.get(alert_url)
            text = r.content.decode("utf8")
            alert_data = demjson.decode(text)
            self.uptime = alert_data["sysuptime"]
            for alert in alert_data["recordData"]:
                self.alerts.append(
                    Alert(alert["severity"], alert["code"], alert["desc"], alert["sysuptime"]))
            return True
        except requests.exceptions.HTTPError as errh:
            print("Http Error:", errh)
        except requests.exceptions.ConnectionError as errc:
            print("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            print("OOps: Something Else", err)
        except SerialNumException:
            print("Serial Num mismatch")
        except demjson.JSONError:
            print("JSON error")
        return False

    def ip_scan_lan(self):
        # Scan the local network for the printer
        if self.dynamic_ip:
            network = ipaddress.ip_network('192.168.1.0/24')
            for ip in network:
                # Ignore e.g. 192.168.1.0 and 192.168.1.255
                if ip == network.broadcast_address or ip == network.network_address:
                    continue
                print(ip)
                if self.__update_data(str(ip)):
                    print("OK")
                    self.ip = str(ip)
                    return True
        return False

    def to_dict(self) -> dict:
        # Convert the printer object to a dict
        di = {}
        di["ip"] = self.ip
        di["serial_num"] = self.serial_num
        di["dynamic_ip"] = self.dynamic_ip
        di["model_name"] = self.model_name
        di["uptime"] = self.uptime
        di["reachedDrumLevels"] = self.reachedDrumLevels
        di["reachedTrayLevels"] = self.reachedTrayLevels
        di["reachedTonLevels"] = self.reachedTonLevels
        di["toners"] = []
        di["drums"] = []
        di["trays"] = []
        di["alerts"] = []
        for toner in self.toners:
            di["toners"].append(dict(toner.__dict__))
        for drum in self.drums:
            di["drums"].append(dict(drum.__dict__))
        for tray in self.trays:
            di["trays"].append(dict(tray.__dict__))
        for alert in self.alerts:
            di["alerts"].append(dict(alert.__dict__))
        return di

    def update(self):
        if not self.__update_data(str(self.ip)):
            return self.ip_scan_lan()
        else:
            return True
