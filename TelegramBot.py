import asyncio
import os, logging, socket, time, codecs
from threading import Thread
from telegram.ext import Application, Updater, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update, Bot

class ClientData:
    def __init__(self, client : socket, address):
        self.client : socket = client
        self.address = address
        self.playerName : str = None
        self.playerID : int = -1
    
    def Close(self):
        self.client.close()

class MyTCPServer:
    def __init__(self):
        self.IP : str = "127.0.0.1"
        self.port : int = 49857
        self.server : socket = None
        self.clients : list[ClientData] = []
        self.AcceptThread : Thread = None
        self.BindedPlayer : str = ""
        self.AcceptWorldChannel : str = None
        self.emojiDic = EmojiDic()
    
    def Start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.IP, self.port))
        self.server.listen(10)
        # print('Server start at: {}:{}'.format(self.IP, self.port))
        print("Waiting for connection from SWPE...")
        self.AcceptThread = Thread(target = self.AcceptClient)
        self.AcceptThread.start()
        
    def AcceptClient(self):
        while True:
            try:
                client, address = self.server.accept()
            except:
                return
            # print('Have a connection from: ' + (str)(address))
            clientData  = ClientData(client, address)
            self.clients.append(clientData)
            newThread = Thread(target = self.ClientHandle, args = (clientData,))
            newThread.start()
    
    def ClientHandle(self, clientData : ClientData):
        playerName = None
        playerID = None
        while True:
            # Recv Message Format: SWPE|||Channel|||ID|||Name|||Message
            try: recvMsg = clientData.client.recv(8192)
            except: recvMsg = ""
            if len(recvMsg) == 0: # connection closed
                try: clientData.client.close()
                except: pass
                self.clients.remove(clientData)
                print(playerName + ' closed connection.')
                asyncio.run(sendMsg(myID, playerName + " 已離開伺服器"))
                if playerID == self.AcceptWorldChannel:
                    self.AcceptWorldChannel = None
                return
            if (self.AcceptWorldChannel == None):
                self.AcceptWorldChannel = playerName
            decodedMsg : str = recvMsg.decode(encoding = 'UTF-8')
            msgs = decodedMsg.split('\r\n')
            for msg in msgs:
                if (msg == None or msg == ''): continue
                splitedMsg = msg.split('|||')
                #print('Server Received Message: ' + msg)

                if splitedMsg[0] == 'SWPE':
                    if splitedMsg[3] == 'N/A':
                        try: splitedMsg[3] = playerIDList.get((int)(splitedMsg[2]))
                        except: pass
                    else:
                        if (splitedMsg[1] != "密頻"): 
                            checkAndSaveID((int)(splitedMsg[2]), splitedMsg[3])

                    splitedMsg.pop(0)

                    if splitedMsg[0] == "系統公告":
                        splitedMsg.pop(1)
                        splitedMsg.pop(1)
                    elif splitedMsg[0] == "密頻":
                        if (splitedMsg[1] == (str)(clientData.playerID)):
                            splitedMsg[2] = "我對 " + splitedMsg[2] + " 說: "
                        elif (splitedMsg[1] == '0'):
                            splitedMsg[1] = ""
                            splitedMsg[2] = "發送失敗信息: "
                        else:
                            splitedMsg[2] = splitedMsg[2] + " 對我說: "
                    
                    reply = ""
                    for sssss in splitedMsg:
                        if (sssss == None):
                            continue
                        else:
                            for key, value in self.emojiDic.items():
                                sssss = sssss.replace(key, value)
                            reply += sssss + " "

                    if channel.get(splitedMsg[0]):
                        if splitedMsg[0] == "世頻" or splitedMsg[0] == "陣頻" or splitedMsg[0] == "系統公告":
                            if self.AcceptWorldChannel == playerName:
                                asyncio.run(sendMsg(myID, playerName + " ~ " + reply))
                        else:
                            asyncio.run(sendMsg(myID, playerName + " ~ " + reply))

                elif splitedMsg[0] == "SWPENAME":
                    try:
                        playerName = splitedMsg[1]
                        playerID = (int)(splitedMsg[2])
                        clientData.playerName = playerName
                        clientData.playerID = playerID
                        print('Connected player: {} ({})'.format(playerName, playerID))
                        asyncio.run(sendMsg(myID, "{} ({}) 已連接至伺服器".format(playerName, playerID)))
                    except:
                        print('Failed to Initialize Name')

    def BindPlayer(self, playerName : str):
        if (playerName == None): return
        for data in self.clients: 
            if (data.playerName == playerName):
                    self.BindedPlayer = data.playerName
                    break

    async def Send(self, msg : str):
        # Send Message Format: SWPE|||Channel|||ID|||Message
        foundTarget = False
        for data in self.clients:
            if (data.playerName == self.BindedPlayer):
                try:
                    foundTarget = True
                    data.client.send(msg.encode(encoding = 'UTF-8'))
                except:
                    print("Error on Send")
                    await sendMsg(myID, '發送對話失敗')
                break
        if not foundTarget:
            print('No Player are binded')
            await sendMsg(myID, '沒有綁定帳號')

    def Close(self):
        for client in self.clients:
            try: client.Close()
            except Exception as e: print("client.Close() Error: " + str(e))
        self.clients = []
        try: self.server.shutdown(0)
        except Exception as e: print("self.server.shutdown(0) Error: " + str(e))
        try: self.server.close()
        except Exception as e: print("self.self.server.close() " + str(e))
        self.server = None
        

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

myServer: MyTCPServer = None
#path = 'C:/Users/Administrator/Documents/Python Project/TelegramBot'
path = os.getcwd()
myID: int = 0
application : Application
channel = {'系統公告': True, '密頻': True, '全頻': True, '輕頻': True, '團頻': True, '盟頻': True, '隊頻': True, '世頻': True, '陣頻': True}
playerIDList = dict()
SayChannel = None

def checkAndSaveID(ID: int, name: str):
    if (name == 'N/A' or name == None or ID == None or ID < 10000): return
    if (ID in playerIDList):
         return
    else:
        playerIDList[ID] = name
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


def readID():
    try:
        file = open(path + '/PlayerID', mode = 'r', encoding = 'utf-8-sig')
        lines = file.read().replace('\r\n', '\n').split('\n')
        for line in lines:
            try:
                splited = line.split('|||')
                id = (int)(splited[0])
                playerIDList[id] = splited[1]
            except:
                continue
        file.close()
    except Exception as e:
        try: file.close()
        except: pass
        print("readID Error: " + str(e))

def readChannel():
    try:
        file = open(path + '/Channel.ini', mode = 'r', encoding = 'utf-8-sig')
        line = file.readline()
        if (line == None or line == ""): return

        splited = line.split('|')
        count = 0
        for key, value in channel.items():
            if splited[count] == '0': 
                channel[key] = False
            count += 1
        file.close()
    except Exception as e:
        try: file.close()
        except: pass
        print("readChannel Error: " + str(e))

def saveChannel():
    file = open(path + '/Channel.ini', mode = 'w', encoding = 'utf-8-sig')
    count = 0
    for key, value in channel.items():
        writeData = ''
        if value: 
            writeData = '1'
        else: writeData = '0'
        if count != 8: 
            writeData = writeData + '|'
        file.write(writeData)
        count += 1
    file.close()
    

def printRecvMsg(update : Update):
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

async def Start(update : Update, context : CallbackContext):
    printRecvMsg(update)
    if (update.message.from_user.id == myID): 
        readID()
        print("Reloaded playerIDList")
    await update.message.reply_text('Hi there is Saki Saki BOT!!!')

async def Say(update : Update, context : CallbackContext):
    printRecvMsg(update)
    if (update.message.from_user.id == myID):

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
                await myServer.Send("SWPE|||密頻|||{}|||{}".format(splitedMsg[2], splitedMsg[3]))
            else:
                foundID = False
                for key, value in playerIDList.items():
                    if value == splitedMsg[2]:
                        foundID = True
                        await myServer.Send("SWPE|||密頻|||{}|||{}".format(key, splitedMsg[3]))
                        break
                if not foundID:
                    await update.message.reply_text("找不到該名玩家，請以玩家編號進行密語")
        else:
            await myServer.Send("SWPE|||{}|||NULL|||{}".format(splitedMsg[1], splitedMsg[2]))
    else: 
        await update.message.reply_text(text="This is a private bot")

async def Close(update : Update, context : CallbackContext):
    printRecvMsg(update)
    if (update.message.from_user.id == myID):
        channelList1 = ['系統公告', '密頻', '全頻', '輕頻', '團頻']
        channelList2 = ['盟頻', '隊頻', '世頻', '陣頻']
        await update.message.reply_text(text = '請選擇想開關的頻道',
            reply_markup = InlineKeyboardMarkup
            (
                [
                    [InlineKeyboardButton(name, callback_data = "Close" + name) for name in channelList1],
                    [InlineKeyboardButton(name, callback_data = "Close" + name) for name in channelList2]
                ]
            )
        )
    else: 
        await update.message.reply_text(text="This is a private bot")

async def LockChannel(update : Update, context : CallbackContext):
    printRecvMsg(update)
    if (update.message.from_user.id == myID):
        channelList1 = ['密頻', '全頻', '輕頻', '團頻']
        channelList2 = ['盟頻', '隊頻', '世頻', '陣頻']
        await update.message.reply_text(text = '請選擇想鎖定的頻道',
            reply_markup = InlineKeyboardMarkup
            (
                [
                    [InlineKeyboardButton(name, callback_data = 'Lock' + name) for name in channelList1],
                    [InlineKeyboardButton(name, callback_data = 'Lock' + name) for name in channelList2]
                ]
            )
        )
    else: 
        await update.message.reply_text(text="This is a private bot")

async def UnlockChannel(update : Update, context : CallbackContext):
    printRecvMsg(update)
    global SayChannel
    SayChannel = None
    await update.message.reply_text(text = '已解鎖綁定頻道')

async def BindPlayer(update : Update, context : CallbackContext):
    printRecvMsg(update)
    if update.message.from_user.id == myID:
        clients = myServer.clients
        markupList = []
        for data in clients:
            markupList.append([InlineKeyboardButton(data.playerName, callback_data = 'Player' + data.playerName)])
        await update.message.reply_text(text = '請選擇想綁定的玩家', reply_markup = InlineKeyboardMarkup(markupList))
    else: 
        await update.message.reply_text(text="This is a private bot")

async def ShowEmoji(update : Update, context : CallbackContext):
    printRecvMsg(update)
    if (update.message.from_user.id == myID):
        myText = ''
        emojiDic = EmojiDic()
        for key, value in emojiDic.items():
            myText = myText + '{}  =   {}\n'.format(key, value)
        await update.message.reply_text(text = myText)
    else: 
        await update.message.reply_text(text="This is a private bot")

async def Callback_Close(update : Update, context : CallbackContext):
    recvData = update.callback_query.data

    closedChannel = recvData.replace('Close', '')
    channel[closedChannel] = not channel.get(closedChannel)
    reply = ""
    for key, value in channel.items():
        if value: 
            value = "開"
        else: 
            value = "關"
        reply += "{}: {}\n".format(key, value)
    await update.callback_query.edit_message_text(text = reply)
    saveChannel()

async def Callback_Say(update : Update, context : CallbackContext):
    recvData = update.callback_query.data

    global SayChannel
    if recvData == "Say密頻":
        await update.callback_query.edit_message_text(text = '請輸入玩家ID或名稱')
        SayChannel = "ID密頻"
    else:
        await update.callback_query.edit_message_text(text = '請輸入訊息')
        SayChannel = recvData.replace('Say', '')

async def Callback_Lock(update : Update, context : CallbackContext):
    recvData = update.callback_query.data

    global SayChannel
    if recvData == "Lock密頻":
        await update.callback_query.edit_message_text(text = '請輸入玩家ID或名稱')
        SayChannel = "LockID密頻"
    else:
        SayChannel = recvData
        await update.callback_query.edit_message_text(text = '已鎖定' + recvData.replace('Lock', ''))

async def Callback_Player(update : Update, context : CallbackContext):
    recvData = update.callback_query.data

    playerName = recvData.replace('Player', '')
    myServer.BindPlayer(playerName)
    await update.callback_query.edit_message_text(text = '已綁定帳號: ' + playerName)

async def Callback_NotProcessed(update : Update, context : CallbackContext):
    recvData = update.callback_query.data

    await update.callback_query.edit_message_text(text = recvData)

async def MsgHandle(update : Update, context : CallbackContext):
    if update.message.text.startswith('/'):
        return
    printRecvMsg(update)
    if update.message.from_user.id != myID: 
        await update.message.reply_text(text="This is a private bot")
        return

    global SayChannel
    if SayChannel != None:
        splitedMsg = SayChannel.split('|||')

        if SayChannel == "ID密頻":
            SayChannel = "密頻|||" + update.message.text
            await update.message.reply_text(text = '請輸入訊息')

        elif SayChannel == "LockID密頻":
            SayChannel = "Lock密頻|||" + update.message.text
            if not update.message.text.isdigit():
                foundID = False
                for key, value in playerIDList.items():
                    if value == update.message.text:
                        foundID = True
                        break
                if not foundID:
                    SayChannel = None
                    await update.message.reply_text("找不到該名玩家，請以玩家編號進行密語")
                else:
                    await update.message.reply_text(text = '已鎖定密頻, 玩家名稱: ' + update.message.text)
            else:
                await update.message.reply_text(text = '已鎖定密頻, 玩家ID: ' + update.message.text)
            
        else:
            if splitedMsg[0].startswith('Lock'):
                splitedMsg[0] = splitedMsg[0].replace('Lock', '')
            else:
                SayChannel = None
            splitedMsg.append(update.message.text)
            if splitedMsg[0] == '密頻':
                if splitedMsg[1].isdigit():
                    await myServer.Send("SWPE|||密頻|||{}|||{}".format(splitedMsg[1], splitedMsg[2]))
                else:
                    foundID = False
                    for key, value in playerIDList.items():
                        if value == splitedMsg[1]:
                            foundID = True
                            await myServer.Send("SWPE|||密頻|||{}|||{}".format(key, splitedMsg[2]))
                            break
                    if not foundID:
                        await update.message.reply_text("找不到該名玩家，請以玩家編號進行密語")
            else:
                await myServer.Send("SWPE|||{}|||NULL|||{}".format(splitedMsg[0], splitedMsg[1]))


def Error(update : Update, context : CallbackContext):
    printRecvMsg(update)
    logger.warning('Update "%s" caused error "%s"', update, context.error)

async def sendMsg(userID : int, msg : str):
    try: 
        await application.bot.send_message(chat_id = userID, text = msg)
    except Exception as e: 
        print("Bot Send Message Failed" + str(e))
    
def EmojiDic():
    emojiDic : dict[str, str] = dict()
    emojiDic['@|'] = '{疑惑 😐}'
    emojiDic[':$'] = '{有點害羞 😊}'
    emojiDic['>|'] = '{V字眉 🤨}'
    emojiDic['-"'] = '{畫線 😨}'
    emojiDic['XD'] = '{XD 😆}'
    emojiDic['TT'] = '{大哭 😭}'
    emojiDic[':D'] = '{大笑 😆}'
    emojiDic[':S'] = '{懷疑 😒}'
    emojiDic['=='] = '{無言 😑}'
    emojiDic['8D'] = '{咬你喔 🦷}'
    emojiDic['%#'] = '{水汪汪眼睛 🥺}'
    emojiDic['8('] = '{有點怪怪的 🥶}'
    emojiDic[':)'] = '{笑 😊}'
    emojiDic['^T'] = '{流淚 😭}'
    emojiDic['>@'] = '{很生氣 😡}'
    emojiDic[':('] = '{心情不好 😔}'
    emojiDic[':!'] = '{嘆氣 😔}'
    emojiDic['JL'] = '{雙手合十 🥺}'
    emojiDic['8o'] = '{呆掉 😦}'
    emojiDic[':['] = '{耍自閉 😳}'
    emojiDic[':m'] = '{吹口哨 😚}'
    emojiDic[':o'] = '{嚇到呆掉 😱}'
    emojiDic['|T'] = '{吐出來了 🤮}'
    emojiDic['"_'] = '{印堂發黑 😰}'
    emojiDic['*:'] = '{想殺人了 😠}'
    emojiDic['j-'] = '{滴汗 😥}'
    emojiDic[':P'] = '{吐舌頭 😋}'
    emojiDic['|E'] = '{呵呼 😶}'
    emojiDic['zZ'] = '{打瞌睡 😴}'
    emojiDic['@#'] = '{混亂 🤯}'
    return emojiDic

def main():
    # Start Read Token and Admin ID
    try:
        file = open(path + "/BotInfo.txt", mode = "r", encoding = "utf8")
        lines = file.read().replace("\ufeff", "").replace("\r\n", "\n").split("\n")
        Token = lines[0]
        adminID = lines[1]
        global myID, application
        myID = 0
        try:
            myID = int(adminID)
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

    readID()
    readChannel()

    global myServer
    myServer = MyTCPServer()
    myServer.Start()
    

    application.add_handler(CommandHandler("start", Start))
    application.add_handler(CommandHandler("close", Close))
    application.add_handler(CommandHandler("say", Say))
    application.add_handler(CommandHandler("lockchannel", LockChannel))
    application.add_handler(CommandHandler("unlockchannel", UnlockChannel))
    application.add_handler(CommandHandler("bindplayer", BindPlayer))
    application.add_handler(CommandHandler("showemoji", ShowEmoji))

    application.add_handler(CallbackQueryHandler(Callback_Close, pattern="^Close"))
    application.add_handler(CallbackQueryHandler(Callback_Say, pattern="^Say"))
    application.add_handler(CallbackQueryHandler(Callback_Lock, pattern="^Lock"))
    application.add_handler(CallbackQueryHandler(Callback_Player, pattern="^Player"))
    application.add_handler(CallbackQueryHandler(Callback_NotProcessed))

    application.add_handler(MessageHandler(filters.TEXT, MsgHandle))

    """
    # not used
    conversation_handler = (ConversationHandler(
        entry_points=[CommandHandler("lockchannel", LockChannel)], 
        states={range(1): [CallbackQueryHandler(Answer)]}, 
        fallbacks=[CommandHandler("lockchannel", LockChannel)]
        ))
    application.add_handler(conversation_handler)
    """
    application.add_error_handler(Error)
    application.run_polling()
    application.idle()
    myServer.Close()

if __name__ == '__main__':
    main()
