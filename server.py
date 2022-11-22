import socket
import threading
import com

print_lock = threading.Lock()

# thread function


def threaded(c):
    while True:

        # data received from client
        data = com.Receive(c)
        if not data:
            print('Bye')
            break

        print(data)
        com.Send(c, 'res', 'ok')

    # connection closed
    c.close()


def Main():
    host = ""
    port = 12345

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    print("socket binded to port", port)

    s.listen(5)
    print("socket is listening")

    # establish connection with client
    c, addr = s.accept()
    print('Connected to :', addr[0], ':', addr[1])

    # Start a new thread and return its identifier
    thread = threading.Thread(target=threaded, args=(c,))
    thread.start()


if __name__ == '__main__':
    Main()
