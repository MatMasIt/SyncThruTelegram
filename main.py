import requests
import json
import demjson
import datetime
import telebot
from printer import Printer
import time


def store_update(store: list, data: dict):
    for idx, printer in enumerate(store):
        if printer["serial_num"] == data["serial_num"]:
            printer[int(idx)] = data
            return
    store.append(data)


def store_get_printer_by_serial_num(store: list, serial_num: str):
    for printer in store:
        if printer["serial_num"] == serial_num:
            return printer
    return None


def store_get():
    try:
        with open("store.json", "r") as store_file:
            return json.loads(store_file.read())["data"]
    except Exception as e:
        return []


def store_set(data: list):
    with open("store.json", "w+") as store_file:
        store_file.write(json.dumps(
            {"data": data, "last_update": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}))


if __name__ == "__main__":
    with open("config.json", "r") as config_file:
        config = json.loads(config_file.read())
        token = config["telegram_bot_token"]
        bot = telebot.TeleBot(token, parse_mode="markdown")
        while True:
            store_data = store_get()
            for printer in config["printers"]:
                ip = printer["ip"]
                # pull persistent data from store
                p = store_get_printer_by_serial_num(
                    store_data, printer["serial_num"])
                reachedTonLevels = {}
                reachedDrumLevels = {}
                reachedTrayLevels = {}
                if p is not None and printer["dynamic_ip"]:
                    if p["ip"] is not None:
                        ip = p["ip"]
                    if "reachedTonLevels" in p:
                        reachedTonLevels = p["reachedTonLevels"]
                    if "reachedDrumLevels" in p:
                        reachedDrumLevels = p["reachedDrumLevels"]
                    if "reachedTrayLevels" in p:
                        reachedTrayLevels = p["reachedTrayLevels"]
                # build and update printer
                p = Printer(config,
                            ip, printer["serial_num"], printer["dynamic_ip"], bot,
                            printer["toner"], printer["drum"], printer["tray"],
                            printer["alert_levels"], reachedTonLevels, reachedDrumLevels, reachedTrayLevels)
                p.update()
                store_update(store_data, p.to_dict()) # replace printer data in store
            store_set(store_data) # persist store
            time.sleep(config["update_interval"])
