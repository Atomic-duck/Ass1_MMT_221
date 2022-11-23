import socket
import threading
import Database
import Service

PORT = 13000


class Server:
    def __init__(self, numthread=10):
        # create a socket using TCP port and ipv4
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # this will allow you to immediately restart a TCP server
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # this makes the server listen to requests coming from other computers on the network
        self.socket.bind(("", PORT))

        #####
        self.numthread = numthread
        # create a centralized database object
        self.database = Database.Database()
        # create a a primitive lock that is not owned by a particular thread when locked
        self.lock = threading.Lock()
        #
        self.serviceList = {}
        self.shutdown = False
        # self.admin_socket = None
        # self.admin_addr = None

    def Listen(self):
        # listen for incomming connections
        self.socket.listen()
        print("Listening for incoming messages..")

    def Run(self):
        self.Listen()

        while True:
            self.lock.acquire()
            if not self.shutdown:
                # Accept a connection
                self.lock.release()
                conn, addr = self.socket.accept()
                print("Connected by: ", addr)
            else:
                self.lock.release()
                break

            # assign socket of client to a Service
            service = Service.Service(conn, addr, self.database, self.lock)
            # create a new thread run Verify_thread function
            thread = threading.Thread(
                target=self.Verify_thread, args=(service,))
            thread.start()

        self.shutdownAllService()
        self.socket.close()

    def Verify_thread(self, service):
        # Start thread
        # Args: Service object
        self.lock.acquire()
        # kill service when the server shutdown or the number of services exceeds numthread
        if len(self.serviceList) >= self.numthread or self.shutdown == True:
            self.lock.release()
            service.send_close()
            service.close_response()
            return
        self.lock.release()

        # send "accept" event
        service.send_accept()
        # Login / register
        service.verify()
        username = service.username

        if username is not None:
            self.lock.acquire()
            # save servive by username
            self.serviceList[username] = service
            self.lock.release()

            # run service.__call__(), return true when username is admin and sent shutdown
            if service():
                self.lock.acquire()
                self.shutdown = True
                self.socket.close()
                self.lock.release()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(("", PORT))
                s.close()

            self.lock.acquire()
            del self.serviceList[username]
            self.lock.release()

    def shutdownAllService(self):
        for _ in self.serviceList:
            _.lock.acquire()
            _.send_close()
            _.close_response()
            _.lock.release()
