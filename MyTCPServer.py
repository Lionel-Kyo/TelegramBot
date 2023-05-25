import time
import asyncio
import socket
import threading
from threading import Thread

from ClientData import ClientData
from EmojiDict import get_emoji_dict

class MyTCPServer:
    def __init__(self):
        self.ip : str = "127.0.0.1"
        self.port : int = 49857
        self.server : socket = None
        self.clients : list[ClientData] = []
        self.accept_thread : Thread = None
        self.binded_player : str = ""
        self.accept_world_channel : str = None


        self.emoji_dict = get_emoji_dict()
        self.send_msg = None
        self.channel = { "系統公告": True, "密頻": True, "全頻": True, "輕頻": True, "團頻": True, "盟頻": True, "隊頻": True, "世頻": True, "陣頻": True, "登入資訊": True, "重連資訊": True}
        self.player_ids = {}
        self.botId = 0
        self.path = ""
        self.__started = False
    
    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.ip, self.port))
        self.server.listen(10)
        # print('Server start at: {}:{}'.format(self.IP, self.port))
        print("Waiting for connection from S-WPE...")
        self.accept_thread = Thread(target = self.accept_client)
        self.accept_thread.start()
        
    def accept_client(self):
        self.__started = True
        while True:
            try:
                client, address = self.server.accept()
            except:
                self.__started = False
                return
            # print('Have a connection from: ' + (str)(address))
            clientData  = ClientData(client, address)
            self.clients.append(clientData)
            newThread = Thread(target = self.client_handle, args = (clientData,))
            newThread.start()
    
    def client_handle(self, clientData : ClientData):
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
                self.send_msg(self.botId, playerName + " 已離開伺服器")
                if playerID == self.accept_world_channel:
                    self.accept_world_channel = None
                return
            if self.accept_world_channel is None:
                self.accept_world_channel = playerName
            decodedMsg : str = recvMsg.decode(encoding = 'UTF-8')
            msgs = decodedMsg.split('\r\n')
            for msg in msgs:
                if msg is None or msg == "":
                    continue
                splitedMsg = msg.split('|||')
                #print('Server Received Message: ' + msg)

                if splitedMsg[0] == 'SWPE':
                    if splitedMsg[3] == 'N/A':
                        try: splitedMsg[3] = self.player_ids.get((int)(splitedMsg[2]))
                        except: pass
                    else:
                        if splitedMsg[1] != "密頻": 
                            self.check_and_save_id((int)(splitedMsg[2]), splitedMsg[3])

                    splitedMsg.pop(0)

                    if splitedMsg[0] == "系統公告" or splitedMsg[0] == "登入資訊" or splitedMsg[0] == "斷線資訊":
                        splitedMsg.pop(1)
                        splitedMsg.pop(1)
                    elif splitedMsg[0] == "密頻":
                        if splitedMsg[1] == str(clientData.playerID):
                            splitedMsg[2] = "我對 " + splitedMsg[2] + " 說: "
                        elif splitedMsg[1] == '0':
                            splitedMsg[1] = ""
                            splitedMsg[2] = "發送失敗信息: "
                        else:
                            splitedMsg[2] = splitedMsg[2] + " 對我說: "
                    
                    reply = ""
                    for sssss in splitedMsg:
                        if sssss is None:
                            continue
                        else:
                            for key, value in self.emoji_dict.items():
                                sssss = sssss.replace(key, value)
                            reply += sssss + " "

                    is_channel_open = self.channel.get(splitedMsg[0], None)

                    if is_channel_open is None or is_channel_open:
                        if splitedMsg[0] == "世頻" or splitedMsg[0] == "陣頻" or splitedMsg[0] == "系統公告":
                            if self.accept_world_channel == playerName:
                                self.send_msg(self.botId, playerName + " ~ " + reply)
                        else:
                            self.send_msg(self.botId, playerName + " ~ " + reply)

                elif splitedMsg[0] == "SWPENAME":
                    try:
                        playerName = splitedMsg[1]
                        playerID = (int)(splitedMsg[2])
                        clientData.playerName = playerName
                        clientData.playerID = playerID
                        print('Connected player: {} ({})'.format(playerName, playerID))
                        self.send_msg(self.botId, "{} ({}) 已連接至伺服器".format(playerName, playerID))
                    except:
                        print('Failed to Initialize Name')

    def bind_player(self, playerName : str):
        if playerName is None:
            return
        for data in self.clients: 
            if data.playerName == playerName:
                    self.binded_player = data.playerName
                    break

    def send(self, msg : str):
        # Send Message Format: SWPE|||Channel|||ID|||Message
        foundTarget = False
        for data in self.clients:
            if data.playerName == self.binded_player:
                try:
                    foundTarget = True
                    data.client.send(msg.encode(encoding = 'UTF-8'))
                except:
                    print("Error on Send")
                    self.send_msg(self.botId, '發送對話失敗')
                break
        if not foundTarget:
            print('No Player are binded')
            self.send_msg(self.botId, '沒有綁定帳號')

    def close(self):
        for client in self.clients:
            try: client.Close()
            except Exception as e: print("client.Close() Error: " + str(e))
        self.clients = []
        try: self.server.shutdown(0)
        except Exception as e: print("self.server.shutdown(0) Error: " + str(e))
        try: self.server.close()
        except Exception as e: print("self.self.server.close() " + str(e))
        self.server = None

    def check_and_save_id(self, ID: int, name: str):
        if name is None or name == 'N/A' or ID is None or ID < 10000: 
            return
        if ID in self.player_ids:
            return
        else:
            self.player_ids[ID] = name
            saved = False
            tryTime = 0
            while not saved:
                try:
                    file = open(self.path + '/PlayerID', mode = 'a', encoding = 'utf-8-sig')
                    file.write('{}|||{}\n'.format(ID ,name))
                    file.close()
                    saved = True
                except Exception as e:
                    print("Error on check and save ID: " + str(e))
                    tryTime += 1
                    time.sleep(0.01)
                    if tryTime > 20:
                        break
    
    @property
    def started(self):
        return self.__started