import threading
import com


class Service:
    def __init__(self, socket, addr, database, lock):
        # a socket usable to send and receive data on the connection
        self.socket = socket
        # (ip, port)
        self.addr = addr
        self.database = database
        self.lock = threading.Lock()
        self.username = None

    def Register(self, data):
        username = data['username']
        password = data['password']
        success = True

        print(username)
        print(password)

        if username is None or password is None:
            success = False
        else:
            if self.database.addUser(username, password):
                self.username = username
                self.password = password
                self.database.online(username)
                print("Welcome", username)
            else:
                success = False

        com.Send(self.socket, 'Register', {'success': success})

    # authenticate and save username, password to service
    def Login(self, data):
        username = data['username']
        password = data['password']
        success = True
        print('Login: ', username, password)

        if username is None or password is None:
            success = False
        else:
            if self.database.Login(username, password):
                self.username = username
                self.password = password
                self.database.online(username)
                print("Welcome", username)
            else:
                success = False

        com.Send(self.socket, 'Register', {'success': success})

    def showFriend(self):
        friendDict = self.database.showFriend(self.username)
        if friendDict == None:
            com.Send(self.socket, 'showFriend', {'success': False})
        else:
            # send friend list
            com.Send(self.socket, 'showFriend', {
                     'success': True, 'friendDict': friendDict})

    def showFriendRequest(self):
        requestList = self.database.showFriendRequest(self.username)
        if requestList == None:
            com.Send(self.socket, 'showFriendRequest', {'success': False})

        else:
            # send request list
            com.Send(self.socket, 'showFriendRequest', {
                     'success': True, 'requestList': requestList})

    def addFriend(self, data):
        username = data['username']
        if self.database.addFriend(self.username, username):
            com.Send(self.socket, 'addFriend', {'success': True})
        else:
            com.Send(self.socket, 'addFriend', {'success': False})

    def acceptFriendRequest(self, data):
        username = data['username']
        accept = data['accept']

        if self.database.acceptFriendRequest(self.username, username, accept):
            com.Send(self.socket, 'acceptFriendRequest', {'success': True})
        else:
            com.Send(self.socket, 'acceptFriendRequest', {'success': False})

    def setPort(self, data):
        # host, port of who?? may be client is connecting with service but they don't use addr
        host = data['host']
        port = data['port']
        print('Set Port: ', host, port)

        self.listen_host = host
        self.listen_port = int(port)
        print(self.listen_host, self.listen_port)

        self.database.setPort(
            self.username, self.listen_host, self.listen_port)

    # get (host, port) of friend by username
    def requestPort(self, data):
        username = data['username']
        print('requestPort: ', username)

        if not self.database.isRegistered(username):  # unregistered username
            com.Send(self.socket, 'requestPort', {'success': False})
            return

        listFriend = self.database.userFriend[self.username]
        if username not in listFriend:   # not friend
            com.Send(self.socket, 'requestPort', {'success': False})
            return

        if username not in self.database.port_dict:
            print(self.database.port_dict)
            com.Send(self.socket, 'requestPort', {'success': False})
        else:
            host, port = self.database.port_dict[username]
            com.Send(self.socket, 'requestPort', {
                     'success': True, 'host': host, 'port': port})

    def __call__(self):
        while True:
            req = com.Receive(self.socket)
            event = req['event']
            data = req['data']

            if event == 'close':
                self.lock.acquire()
                self.close_response()
                self.lock.release()
                break
            elif event == 'addFriend':
                self.lock.acquire()
                self.addFriend(data)
                self.lock.release()
            elif event == 'acceptFriendRequest':
                self.lock.acquire()
                self.acceptFriendRequest(data)
                self.lock.release()
            elif event == 'showFriendRequest':
                self.lock.acquire()
                self.showFriendRequest()
                self.lock.release()
            elif event == 'showFriend':
                self.lock.acquire()
                self.showFriend()
                self.lock.release()
            elif event == 'setPort':
                self.lock.acquire()
                self.setPort(data)
                self.lock.release()
            elif event == 'requestPort':
                self.lock.acquire()
                self.requestPort(data)
                self.lock.release()
            elif event == 'shutdown':
                if self.username == 'admin':
                    return True

        print('close: ', self.addr)

    def send_accept(self):
        com.Send(self.socket, 'accept')

    def send_close(self):
        com.Send(self.socket, 'close')

# user is offiline
    def close_response(self):
        self.database.offline(self.username)
        self.socket.close()

    def verify(self):
        while True:
            req = com.Receive(self.socket)
            if req['event'] == 'Register':
                self.Register(req['data'])
                break
            elif req['event'] == 'Login':
                self.Login(req['data'])
                break
