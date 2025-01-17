import socket
import threading
import Database
import Service

HEADER_LENGTH = 10
HOST = ""
PORT = 13000

class Server:
    def __init__(self, numthread = 10):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((HOST, PORT))
        self.numthread = numthread
        self.database = Database.Database()
        self.lock = threading.Lock()
        self.serviceList = {}
        self.shutdown = False
        self.admin_socket = None
        self.admin_addr = None

    def Listen(self):
        #Start listen 

        self.socket.listen()

    def Run(self):
        self.Listen()
         
        while True:
            self.lock.acquire()
            if not self.shutdown:
                self.lock.release()
                conn, addr = self.socket.accept()
            else:
                self.lock.release()
                break
            print("Connected by: ", addr)
            #print("Num: ", self.serviceList)
            service = Service.Service(conn, addr, self.database, self.lock)
            thread = threading.Thread(target=self.Verify_thread, args=(service,))
            thread.start()

        self.shutdownAllService()
        self.socket.close()

    def Verify_thread(self, service):
        #Start thread
        #Args: Service object

        self.lock.acquire()
        if len(self.serviceList) >= self.numthread or self.shutdown == True:
            self.lock.release()
            service.close_response()
            return
        self.lock.release()
        service.accept()
        
        service.verify()
        username = service.username

        if username is not None:
            self.lock.acquire()
            self.serviceList[username] = service
            self.lock.release()

            if service():
                self.lock.acquire()
                self.shutdown = True
                self.socket.close()
                self.lock.release()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((HOST, PORT))
                s.close()

            self.lock.acquire()
            del self.serviceList[username]
            self.lock.release()

    def shutdownAllService(self):
        for components in self.serviceList:
            components.lock.acquire()
            components.close()
            components.lock.release()


