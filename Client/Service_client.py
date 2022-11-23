import threading
import socket
import os
import com

HEADER_LENGTH = 10
HOST = "192.168.2.15"
DEVICE_HOST = '192.168.0.103'
Destination = 'download/'


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

    #####
    def Receive_byte(self):
        data_header = self.socket.recv(HEADER_LENGTH)

        if not len(data_header):
            return {'header': None, 'data': None}

        # Convert header to int value
        data_length = int(data_header.decode('utf-8').strip())

        # Return an object of message header and message data
        return {'header': data_header, 'data': self.socket.recv(data_length)}

    ######
    def Send_byte(self, data):
        data_header = f"{len(data):<{HEADER_LENGTH}}".encode('utf-8')
        self.socket.send(data_header + data)

    def connectTo(self, addr):
        self.socket.connect(addr)

    def Send_SMS(self, message):
        com.Send(self.socket, 'sendSMS', {'message': message})
        self.message_list.write('Me: ' + message + '\n')

    def Receive_SMS(self):
        message = com.Receive(self.socket)['data']['message']
        self.message_list.write(self.peer + ': ' + message + '\n')
        return message

    ###
    def Send_File(self, filename):
        if os.path.exists(filename):
            com.Send_message(self.socket, "sendFile")
            com.Send_message(self.socket, filename)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("", 0))
            host = self.ip
            port = s.getsockname()[1]
            s.listen()
            com.Send_message(self.socket, host)
            port = f"{port:<{HEADER_LENGTH}}".encode('utf-8')
            self.socket.send(port)
            conn, addr = s.accept()
            thread = threading.Thread(
                target=self.Send_File_thread, args=(filename, conn))
            thread.start()
        else:
            print('No such file')
            return False

    #####
    def Receive_File(self):
        filename = com.Receive_message(self.socket)['data']
        filename = filename.split('/')[-1]
        filename = Destination + filename
        host = com.Receive_message(self.socket)['data']
        port = self.socket.recv(HEADER_LENGTH)
        port = int(port.decode('utf-8').strip())
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(host)
        print(port)
        s.connect((host, port))

        thread = threading.Thread(
            target=self.Receive_File_thread, args=(filename, s))
        thread.start()

    ######
    def Send_File_thread(self, filename, conn):
        with open(filename, "rb") as in_file:
            while True:
                data = in_file.read(2048)
                if not data:
                    break
                conn.send(data)
        conn.close()

    #######
    def Receive_File_thread(self, filename, conn):
        with open(filename, "wb") as out_file:
            while True:
                print('reading...')
                data = conn.recv(1024)
                if not data:
                    break
                out_file.write(data)
        print('readed')
        conn.close()

    def run(self):
        while True:
            print('run: ', len(self.buffer))
            if len(self.buffer) == 0:
                res = com.Receive(self.socket)
                event = res['event']

                # send username to peer
                if event == 'Verify':
                    self.on_verify()

                # receive sms from peer
                elif event == 'sendSMS':
                    mess = self.Receive_SMS()
                    print(mess)

                elif event == 'sendFile':
                    self.Receive_File()

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
        com.Send(self.socket, 'Verify')
        data = com.Receive(self.socket)['data']['username']

        return data

    def on_verify(self):
        com.Send(self.socket, 'Verify', {'username': self.username})
