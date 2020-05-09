import queue
import select
import socket
import time
import threading

_g_SETOPT_VAL = 1
_g_initialized = False
_g_RECV_BUF_SZ = 1024


def server_logic(server, kill_sock):
    inputs = [server, kill_sock]
    outputs = []
    message_queues = {}
    done = False

    while inputs and not done:
        # Wait for socket to contain data
        readable, writable, exceptional = select.select(inputs,
                                                        outputs,
                                                        inputs)

        for s in readable:
            if s is server:
                # Accept the new connection
                connection, cli_addr = s.accept()

                print('SERVER: New connection (%s, %s)'
                      % (cli_addr[0], cli_addr[1]))

                # Add connection to inputs
                connection.setblocking(False)
                inputs.append(connection)

                # Add queue to hold outgoing messages for socket
                message_queues[connection] = queue.Queue()

            elif s is kill_sock:
                # Kill the server
                print('SERVER: Received kill signal')
                done = True
                kill_sock.recv(_g_RECV_BUF_SZ)  # Flush socket data
                kill_sock.close()

            else:
                # Receive data from the socket
                data = s.recv(_g_RECV_BUF_SZ)
                addr = s.getsockname()

                if data:
                    print('SERVER: Data %s received from: (%s, %s)'
                          % (data, addr[0], addr[1]))
                    time.sleep(0.25)  # Add in processing delay

                    # Queue reply
                    message_queues[s].put(b'102')

                    if s not in outputs:
                        outputs.append(s)

                else:
                    # Close and cleanup the socket if no data
                    if s in outputs:
                        outputs.remove(s)

                    inputs.remove(s)
                    s.close()
                    del message_queues[s]

        for s in writable:
            try:
                # Get the queued message for this socket
                next_msg = message_queues[s].get_nowait()
            except queue.Empty:
                # No message queued, remove the socket
                outputs.remove(s)
            else:
                # Send the queued message over the connection
                addr = s.getsockname()
                print('SERVER: Sending %s to: (%s, %s)'
                      % (next_msg, addr[0], addr[1]))

                s.send(next_msg)

        for s in exceptional:
            # Something went wrong with the socket, clean it up
            print('SERVER: Exceptional socket encountered')
            inputs.remove(s)

            if s in outputs:
                outputs.remove(s)

            s.close()
            del message_queues[s]

    # Exiting, clean up sockets
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
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, _g_SETOPT_VAL)
    server.setblocking(False)

    server_addr = ('', port)  # Listen on all interfaces

    server.bind(server_addr)  # Bind to the socket
    server.listen(5)  # Allow queue of 5 clients

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
    _g_server_thread.join()  # Wait to return until server is closed

    print('SERVER: Stopped')
