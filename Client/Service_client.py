import threading
import socket
import os
import com
from pathlib import Path

HEADER_LENGTH = 10
HOST = "192.168.2.15"
DEVICE_HOST = '192.168.0.103'
downloads_path = str(Path.home() / "Downloads\\") + '\\'


# a service for each conection to a friend (peer to peer)
class Service_client(threading.Thread):
    def __init__(self, socket, buff, message_list, username, peer=None, ip=''):
        super(Service_client, self).__init__()
        self.socket = socket
        self.username = username
        # username of friend
        if peer is not None:
            self.peer = peer
        else:
            self.peer = self.verify()
        #
        self.buffer = buff
        self.message_list = message_list
        self.ip = ip

    def connectTo(self, addr):
        self.socket.connect(addr)

    def Send_SMS(self, message):
        com.Send(self.socket, 'sendSMS', {'message': message})
        self.message_list.write('Me: ' + message + '\n')

    def Receive_SMS(self, data):
        message = data['message']
        self.message_list.write(self.peer + ': ' + message + '\n')
        return message

    ###
    def Send_File(self, filename):
        if os.path.exists(filename):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("", 0))
            s.listen()

            com.Send(self.socket, "sendFile", {
                     'filename': filename, 'host': self.ip, 'port': s.getsockname()[1]})
            conn, addr = s.accept()

            thread = threading.Thread(
                target=com.Send_File, args=(conn, filename))
            thread.start()
        else:
            print('No such file')
            return False

    #####
    def Receive_File(self, data):
        filename = downloads_path + data['filename'].split('/')[-1]
        print('File: ', filename)
        host = data['host']
        port = int(data['port'])

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))

        thread = threading.Thread(
            target=com.Receive_File, args=(s, filename))
        thread.start()

    def run(self):
        while True:
            if len(self.buffer) == 0:
                try:
                    com.Send(self.socket, "Idle")
                except:
                    self.close_response()
                    print('close not safe')
                    break

                res = com.Receive(self.socket)
                event = res['event']
                data = res['data']

                # send username to peer
                if event == 'Verify':
                    self.on_verify()

                # receive sms from peer
                elif event == 'sendSMS':
                    mess = self.Receive_SMS(data)
                    print('recieve: ', mess)

                elif event == 'sendFile':
                    # must insert data
                    self.Receive_File(data)

                elif event == 'close':
                    self.close_response()
                    print('close')
                    break

            else:
                event, content = self.buffer.string()
                if event == 'SendSMS':
                    self.Send_SMS(content)

                elif event == 'SendFile':
                    self.Send_File(content)

                elif event == 'close':
                    self.close()
                    print('close')
                    break

                self.buffer.assign('', '')

        self.buffer.off()

    def accept(self):
        com.Send(self.socket, 'accept')

    def close(self):
        com.Send(self.socket, 'close')
        data = self.socket.recv(1024)
        while data:
            data = self.socket.recv(1024)
        self.socket.close()

    def close_response(self):
        self.message_list.write(self.peer + ' is offline! \n')
        self.socket.close()

    def verify(self):
        data = {}

        com.Send(self.socket, 'Verify')
        event = 'Idle'
        while event == 'Idle':
            res = com.Receive(self.socket)
            event = res['event']
            data = res['data']

        print('verify: ', data)
        return data['username']

    def on_verify(self):
        com.Send(self.socket, 'Verify', {'username': self.username})
