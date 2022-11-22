import json

HEADER_LENGTH = 10


def Receive_message(s):
    message_header = s.recv(HEADER_LENGTH)

    if not len(message_header):
        return {'header': None, 'data': None}

    # Convert header to int value
    message_length = int(message_header.decode('utf-8').strip())
    message = s.recv(message_length).decode('utf-8')
    print(message_length, message)

    return {'header': message_header, 'data': message}


def Send_message(s, message):
    message = message.encode('utf-8')
    message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
    print(len(f"{len(message):<{HEADER_LENGTH}}"))

    s.send(message_header + message)


def Send(s, event, data={}):
    ob = {
        'event': event,
        'data': data
    }

    message = json.dumps(ob)
    message = message.encode('utf-8')
    message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')

    s.send(message_header + message)


def Receive(s):
    message_header = s.recv(HEADER_LENGTH)

    if not len(message_header):
        return None

    # Convert header to int value
    message_length = int(message_header.decode('utf-8').strip())
    message = s.recv(message_length).decode('utf-8')
    data = json.loads(message)

    return data
