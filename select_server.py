import queue
import select
import socket
import threading

_g_SETOPT_VAL = 1
_g_initialized = False


def server_logic(server, kill_sock):
    inputs = [server, kill_sock]
    outputs = []
    message_queues = {}
    done = False

    while inputs and not done:
        readable, writable, exceptional = select.select(inputs,
                                                        outputs,
                                                        inputs)

        for s in readable:
            if s is server:
                print('SERVER: Waiting on connection')

                connection, cli_addr = s.accept()

                print('SERVER: New connection (%s, %s)'
                      % (cli_addr[0], cli_addr[1]))

                connection.setblocking(False)
                inputs.append(connection)
                message_queues[connection] = queue.Queue()

            elif s is kill_sock:
                print('SERVER: Received kill signal')
                done = True
                kill_sock.recv(1024)  # Receive dummy data
                kill_sock.close()

            else:
                data = s.recv(1024)
                addr = s.getsockname()

                print('SERVER: Data %s received from: (%s, %s)'
                      % (data, addr[0], addr[1]))

                if data:
                    message_queues[s].put(data)
                    if s not in outputs:
                        outputs.append(s)

                else:
                    if s in outputs:
                        outputs.remove(s)

                    inputs.remove(s)
                    s.close()
                    del message_queues[s]

        for s in writable:
            try:
                next_msg = message_queues[s].get_nowait()
            except queue.Empty:
                outputs.remove(s)
            else:
                addr = s.getsockname()
                print('SERVER: Sending %s to: (%s, %s)'
                      % (next_msg, addr[0], addr[1]))

                s.send(next_msg)

        for s in exceptional:
            print('SERVER: Exceptional socket encountered')
            inputs.remove(s)

            if s in outputs:
                outputs.remove(s)

            s.close()
            del message_queues[s]

    for s in inputs:
        s.close()

    for s in outputs:
        s.close()


def init(port):
    global _g_initialized
    global _g_server_thread
    global _g_kill_sock_r  # Receives kill signal
    global _g_kill_sock_s  # Sends kill signal

    if _g_initialized:
        raise RuntimeError('Server already initialized')

    # Init Server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, _g_SETOPT_VAL)
    server.setblocking(False)

    server_addr = ('', port)
    server.bind(server_addr)
    server.listen(5)

    # Init kill socket pair
    kill_sock, _g_kill_sock_s = socket.socketpair(family=socket.AF_INET)

    kill_sock.setsockopt(socket.SOL_SOCKET,
                         socket.SO_REUSEADDR,
                         _g_SETOPT_VAL)

    _g_kill_sock_s.setsockopt(socket.SOL_SOCKET,
                              socket.SO_REUSEADDR,
                              _g_SETOPT_VAL)

    _g_server_thread = threading.Thread(target=server_logic,
                                        args=(server, kill_sock))

    _g_initialized = True
    print('SERVER: Initialized')


def start():
    if not _g_initialized:
        raise RuntimeError("Server not initialized")

    _g_server_thread.start()
    print("SERVER: Thread started")


def signal_stop():
    _g_kill_sock_s.send(b'1')  # Signal kill socket
    _g_server_thread.join()

    print('SERVER: Stopped')
