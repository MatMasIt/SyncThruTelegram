import telebot
import json
# load config
with open("config.json", "r") as jsonconf:
    conf = json.loads(jsonconf.read())
    TOKEN = conf["telegram_bot_token"]
    USER_ID = conf["telegram_user_id"]


# printer data in understandable form
def readout(store_data: dict):
    text = ""
    for printer in store_data["data"]:
        text += "Printer *"+printer["model_name"]+"* _" + \
            printer["serial_num"]+"_ @ "+printer["ip"]
        if printer["dynamic_ip"]:
            text += " (dynamic)"
        text += ":\n\nTONERS\n"
        for toner in printer["toners"]:
            text += "*"+toner["color"]+"* "+str(toner["remaining_percent"])+"% ("+str(
                toner["pages_total"])+" pages printed so far)\n"
        text += "\nDRUMS\n"
        for drum in printer["drums"]:
            text += "*"+drum["color"]+"* "+str(drum["remaining_percent"])+"% \n"
        text += "\nTRAYS\n"
        for tray in printer["trays"]:
            text += "*"+str(tray["tray_no"])+"* "+str(("???" if tray["paper_level"]
                                                       == 0 else tray["paper_level"]))+"/"+str(tray["capacity"])+"\n"
        if len(printer["alerts"]):
            text += "\nALERTS\n"
        for alert in printer["alerts"]:
            text += "*"+alert["code"]+"* "+alert["desc"]+"\n"
        text+="\n\n\n"
    text += "Last update: "+store_data["last_update"]+"\n"
    return text
bot = telebot.TeleBot(TOKEN, parse_mode="markdown")


# just an echo bot
@bot.message_handler(func=lambda m: True)
def echo_all(message):
    if message.chat.id != USER_ID:
        return
    with open("store.json", "r") as store_file:
        store_data = json.loads(store_file.read())
        t = readout(store_data)
        bot.reply_to(message, t)

bot.polling()