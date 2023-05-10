import asyncio
import codecs
import logging
import os
import socket
import time
from threading import Thread

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, MessageHandler,
                          Updater, filters)

from EmojiDict import get_emoji_dict
from MyTCPServer import MyTCPServer

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

my_server: MyTCPServer = None
path: str = os.getcwd()
application : Application
say_channel = None

def check_and_save_id(ID: int, name: str):
    if (name == 'N/A' or name == None or ID == None or ID < 10000): return
    if (ID in my_server.player_ids):
         return
    else:
        my_server.player_ids[ID] = name
        saved = False
        tryTime = 0
        while not saved:
            try:
                file = open(path + '/PlayerID', mode = 'a', encoding = 'utf-8-sig')
                file.write('{}|||{}\n'.format(ID ,name))
                file.close()
                saved = True
            except Exception as e:
                print("Error on check and save ID: " + str(e))
                tryTime += 1
                time.sleep(0.01)
                if (tryTime > 20):
                    break


def read_id():
    try:
        file = open(path + '/PlayerID', mode = 'r', encoding = 'utf-8-sig')
        lines = file.read().replace('\r\n', '\n').split('\n')
        for line in lines:
            try:
                splited = line.split('|||')
                id = (int)(splited[0])
                my_server.player_ids[id] = splited[1]
            except:
                continue
        file.close()
    except Exception as e:
        try: file.close()
        except: pass
        print("readID Error: " + str(e))

def read_channel():
    try:
        file = open(path + '/Channel.ini', mode = 'r', encoding = 'utf-8-sig')
        line = file.readline()
        if (line == None or line == ""): return

        splited = line.split('|')
        count = 0
        for key, value in my_server.channel.items():
            if splited[count] == '0': 
                my_server.channel[key] = False
            count += 1
        file.close()
    except Exception as e:
        try: file.close()
        except: pass
        print("readChannel Error: " + str(e))

def save_channel():
    file = open(path + '/Channel.ini', mode = 'w', encoding = 'utf-8-sig')
    count = 0
    for key, value in my_server.channel.items():
        writeData = ''
        if value: 
            writeData = '1'
        else: writeData = '0'
        if count != 8: 
            writeData = writeData + '|'
        file.write(writeData)
        count += 1
    file.close()
    

def print_recv_msg(update : Update):
    if update is None or update.message is None:
        return
    update.message.from_user
    user = update.message.from_user
    if user == None:
        return
    firstName = ""
    lastName = ""
    if user.first_name != None:
        firstName = user.first_name
    if user.last_name != None:
        lastName = user.last_name
    fullName = firstName + lastName
    print('Message received from {} / {}(UserID: {} ChatID: {}): {}'.format(fullName, user.username, user.id, update.message.chat_id, update.message.text))

async def start_handle(update : Update, context : CallbackContext):
    print_recv_msg(update)
    if (update.message.from_user.id == my_server.botId): 
        read_id()
        print("Reloaded playerIDList")
    await update.message.reply_text('Hi there is Saki Saki BOT!!!')

async def say_handle(update : Update, context : CallbackContext):
    print_recv_msg(update)
    if (update.message.from_user.id == my_server.botId):

        splitedMsg = update.message.text.split(' ')
        if len(splitedMsg) != 3 and len(splitedMsg) != 4:
            channelList1 = ['密頻', '全頻', '輕頻', '團頻']
            channelList2 = ['盟頻', '隊頻', '世頻', '陣頻']
            await update.message.reply_text(text = '請選擇想開關的頻道',
                reply_markup = InlineKeyboardMarkup
                (
                    [
                        [InlineKeyboardButton(name, callback_data = 'Say' + name) for name in channelList1],
                        [InlineKeyboardButton(name, callback_data = 'Say' + name) for name in channelList2]
                    ]
                )
            )
            return
        if len(splitedMsg[1]) == 1:
            splitedMsg[1] = splitedMsg[1] + '頻'
        if splitedMsg[1] == '密頻':
            if splitedMsg[2].isdigit():
                await my_server.send("SWPE|||密頻|||{}|||{}".format(splitedMsg[2], splitedMsg[3]))
            else:
                foundID = False
                for key, value in my_server.player_ids.items():
                    if value == splitedMsg[2]:
                        foundID = True
                        await my_server.send("SWPE|||密頻|||{}|||{}".format(key, splitedMsg[3]))
                        break
                if not foundID:
                    await update.message.reply_text("找不到該名玩家，請以玩家編號進行密語")
        else:
            await my_server.send("SWPE|||{}|||NULL|||{}".format(splitedMsg[1], splitedMsg[2]))
    else: 
        await update.message.reply_text(text="This is a private bot")

async def close_handle(update : Update, context : CallbackContext):
    print_recv_msg(update)
    if (update.message.from_user.id == my_server.botId):
        channels1 = ['系統公告', '密頻', '全頻', '輕頻', '團頻']
        channels2 = ['盟頻', '隊頻', '世頻', '陣頻']
        await update.message.reply_text(text = '請選擇想開關的頻道',
            reply_markup = InlineKeyboardMarkup
            (
                [
                    [InlineKeyboardButton(name, callback_data = "Close" + name) for name in channels1],
                    [InlineKeyboardButton(name, callback_data = "Close" + name) for name in channels2]
                ]
            )
        )
    else: 
        await update.message.reply_text(text="This is a private bot")

async def lock_channel_handle(update : Update, context : CallbackContext):
    print_recv_msg(update)
    if (update.message.from_user.id == my_server.botId):
        channels1 = ['密頻', '全頻', '輕頻', '團頻']
        channels2 = ['盟頻', '隊頻', '世頻', '陣頻']
        await update.message.reply_text(text = '請選擇想鎖定的頻道',
            reply_markup = InlineKeyboardMarkup
            (
                [
                    [InlineKeyboardButton(name, callback_data = 'Lock' + name) for name in channels1],
                    [InlineKeyboardButton(name, callback_data = 'Lock' + name) for name in channels2]
                ]
            )
        )
    else: 
        await update.message.reply_text(text="This is a private bot")

async def unlock_channel_handle(update : Update, context : CallbackContext):
    print_recv_msg(update)
    global say_channel
    say_channel = None
    await update.message.reply_text(text = '已解鎖綁定頻道')

async def bind_player_handle(update : Update, context : CallbackContext):
    print_recv_msg(update)
    if update.message.from_user.id == my_server.botId:
        clients = my_server.clients
        markupList = []
        for data in clients:
            markupList.append([InlineKeyboardButton(data.playerName, callback_data = 'Player' + data.playerName)])
        await update.message.reply_text(text = '請選擇想綁定的玩家', reply_markup = InlineKeyboardMarkup(markupList))
    else: 
        await update.message.reply_text(text="This is a private bot")

async def show_emoji_handle(update : Update, context : CallbackContext):
    print_recv_msg(update)
    if (update.message.from_user.id == my_server.botId):
        myText = ''
        emojiDic = get_emoji_dict()
        for key, value in emojiDic.items():
            myText = myText + '{}  =   {}\n'.format(key, value)
        await update.message.reply_text(text = myText)
    else: 
        await update.message.reply_text(text="This is a private bot")

async def callback_close(update : Update, context : CallbackContext):
    recvData = update.callback_query.data

    closedChannel = recvData.replace('Close', '')
    my_server.channel[closedChannel] = not my_server.channel.get(closedChannel)
    reply = ""
    for key, value in my_server.channel.items():
        if value: 
            value = "開"
        else: 
            value = "關"
        reply += "{}: {}\n".format(key, value)
    await update.callback_query.edit_message_text(text = reply)
    save_channel()

async def callback_say(update : Update, context : CallbackContext):
    recvData = update.callback_query.data

    global say_channel
    if recvData == "Say密頻":
        await update.callback_query.edit_message_text(text = '請輸入玩家ID或名稱')
        say_channel = "ID密頻"
    else:
        await update.callback_query.edit_message_text(text = '請輸入訊息')
        say_channel = recvData.replace('Say', '')

async def callback_lock(update : Update, context : CallbackContext):
    recvData = update.callback_query.data

    global say_channel
    if recvData == "Lock密頻":
        await update.callback_query.edit_message_text(text = '請輸入玩家ID或名稱')
        say_channel = "LockID密頻"
    else:
        say_channel = recvData
        await update.callback_query.edit_message_text(text = '已鎖定' + recvData.replace('Lock', ''))

async def callback_player(update : Update, context : CallbackContext):
    recvData = update.callback_query.data

    playerName = recvData.replace('Player', '')
    my_server.bind_player(playerName)
    await update.callback_query.edit_message_text(text = '已綁定帳號: ' + playerName)

async def callback_not_processed(update : Update, context : CallbackContext):
    recvData = update.callback_query.data

    await update.callback_query.edit_message_text(text = recvData)

async def msg_handle(update : Update, context : CallbackContext):
    if update.message.text.startswith('/'):
        return
    print_recv_msg(update)
    if update.message.from_user.id != my_server.botId: 
        await update.message.reply_text(text="This is a private bot")
        return

    global say_channel
    if say_channel != None:
        splitedMsg = say_channel.split('|||')

        if say_channel == "ID密頻":
            say_channel = "密頻|||" + update.message.text
            await update.message.reply_text(text = '請輸入訊息')

        elif say_channel == "LockID密頻":
            say_channel = "Lock密頻|||" + update.message.text
            if not update.message.text.isdigit():
                foundID = False
                for key, value in my_server.player_ids.items():
                    if value == update.message.text:
                        foundID = True
                        break
                if not foundID:
                    say_channel = None
                    await update.message.reply_text("找不到該名玩家，請以玩家編號進行密語")
                else:
                    await update.message.reply_text(text = '已鎖定密頻, 玩家名稱: ' + update.message.text)
            else:
                await update.message.reply_text(text = '已鎖定密頻, 玩家ID: ' + update.message.text)
            
        else:
            if splitedMsg[0].startswith('Lock'):
                splitedMsg[0] = splitedMsg[0].replace('Lock', '')
            else:
                say_channel = None
            splitedMsg.append(update.message.text)
            if splitedMsg[0] == '密頻':
                if splitedMsg[1].isdigit():
                    await my_server.send("SWPE|||密頻|||{}|||{}".format(splitedMsg[1], splitedMsg[2]))
                else:
                    foundID = False
                    for key, value in my_server.player_ids.items():
                        if value == splitedMsg[1]:
                            foundID = True
                            await my_server.send("SWPE|||密頻|||{}|||{}".format(key, splitedMsg[2]))
                            break
                    if not foundID:
                        await update.message.reply_text("找不到該名玩家，請以玩家編號進行密語")
            else:
                await my_server.send("SWPE|||{}|||NULL|||{}".format(splitedMsg[0], splitedMsg[1]))


def error_handle(update : Update, context : CallbackContext):
    print_recv_msg(update)
    logger.warning('Update "%s" caused error "%s"', update, context.error)

async def send_msg(userID : int, msg : str):
    try: 
        await application.bot.send_message(chat_id = userID, text = msg)
    except Exception as e: 
        print("Bot Send Message Failed: " + str(e))

def main():
    global my_server
    my_server = MyTCPServer()
    my_server.send_msg = send_msg
    # Start Read Token and Admin ID
    try:
        file = open(path + "/BotInfo.txt", mode = "r", encoding = "utf8")
        lines = file.read().replace("\ufeff", "").replace("\r\n", "\n").split("\n")
        Token = lines[0]
        adminID = lines[1]
        global application
        my_server.botId = 0
        try:
           my_server.botId = int(adminID)
        except:
            print("無法找到適合的ID, 請對bot發言,再把你的UserID貼在BotInfo.txt的第二行上。")
        file.close()
        application = Application.builder().token(Token).build()
    except Exception as e:
        try: file.close()
        except: pass
        print("Read Token and Admin ID Error: " + str(e))
        print("無法找到適合的Token 或 ID")
        time.sleep(3)
        return
    # End Read Token and Admin ID

    read_id()
    read_channel()

    my_server.start()
    

    application.add_handler(CommandHandler("start", start_handle))
    application.add_handler(CommandHandler("close", close_handle))
    application.add_handler(CommandHandler("say", say_handle))
    application.add_handler(CommandHandler("lockchannel", lock_channel_handle))
    application.add_handler(CommandHandler("unlockchannel", unlock_channel_handle))
    application.add_handler(CommandHandler("bindplayer", bind_player_handle))
    application.add_handler(CommandHandler("showemoji", show_emoji_handle))

    application.add_handler(CallbackQueryHandler(callback_close, pattern="^Close"))
    application.add_handler(CallbackQueryHandler(callback_say, pattern="^Say"))
    application.add_handler(CallbackQueryHandler(callback_lock, pattern="^Lock"))
    application.add_handler(CallbackQueryHandler(callback_player, pattern="^Player"))
    application.add_handler(CallbackQueryHandler(callback_not_processed))

    application.add_handler(MessageHandler(filters.TEXT, msg_handle))

    """
    # not used
    conversation_handler = (ConversationHandler(
        entry_points=[CommandHandler("lockchannel", LockChannel)], 
        states={range(1): [CallbackQueryHandler(Answer)]}, 
        fallbacks=[CommandHandler("lockchannel", LockChannel)]
        ))
    application.add_handler(conversation_handler)
    """
    application.add_error_handler(error_handle)
    application.run_polling()
    application.idle()
    my_server.close()

if __name__ == '__main__':
    main()
