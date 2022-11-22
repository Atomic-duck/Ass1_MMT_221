import socket
import com


def Main():
    host = 'localhost'
    port = 12345

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    while True:
        message = input('message: ')
        if message == 'exit':
            break

        data = {
            'message': message
        }

        com.Send(s, 'sms', data)
        res = com.Receive(s)
        print('Received from the server :')
        print(res)

      #   # message sent to server
      #   Send_message(s, message)

      #  # message received from server
      #   data = Receive_message(s)

      #   print('Received from the server :')
      #   print(data)

    # close the connection
    s.close()


if __name__ == '__main__':
    Main()
