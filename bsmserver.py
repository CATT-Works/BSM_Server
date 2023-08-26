"""Main file that starts the bsm-server.
You may check the arguments with: --help
"""
import argparse

import socket
import threading
import json

from time import time
from bsmmsg.msgobj import MsgObjects

parser = argparse.ArgumentParser(description='Runs the BSM server')

parser.add_argument(
    '--host',
    type=str,
    default='127.0.0.1',
    help='IP of the host with the BSM server. Default=127.0.0.1')

parser.add_argument('-p', '--port',
                    type=int,
                    default=65432,
                    help='BSM server port. Default=65432'
                    )

parser.add_argument('--data_buffer',
                    type=int,
                    default=4096,
                    help='Size of data buffer in bytes. Default=4096'
                    )

parser.add_argument('--object_lifetime',
                    type=int,
                    default=20,
                    help='Object lifetime in seconds. Default=20'
                    )

parser.add_argument(
    '--end_thread_time',
    type=int,
    default=10,
    help="end a thread if didn't receive anything for X seconds. Default=10")

parser.add_argument('--ok',
                    type=str,
                    default='Ok.',
                    help="Ok message. Default=Ok."
                    )

parser.add_argument('-v', '--verbose',
                    type=int,
                    default=0,
                    help="Verbose for debugging purposes"
                    )


def push_data(request):
    """process push request

    Args:
        request (str): json with the request
    Returns:
        str: OK message from args.ok or error message
    """
    global msgObjects
    json_msgs = json.loads(request['msg'])
    if args.verbose >= 2:
        print("json_msgs:", type(json_msgs), json_msgs)
    if isinstance(json_msgs, dict):
        json_msgs = [json_msgs]
    ret = sum([msgObjects.push_object(json_msg) for json_msg in json_msgs])
    msgObjects.sort_objects()
    if ret > 0:
        return f"ERROR: Failed to push {ret} / {len(json_msgs)} objects."
    return args.ok


def pull_data(conn):
    """process pull request
    Args:
        conn: connection handle
    """
    my_msg = msgObjects.pull_bsm()
    if args.verbose >= 2:
        print("PULL:", my_msg)
    my_msg = str.encode(my_msg)
    conn.sendall(my_msg)


def check_data(conn, request):
    """process check request
    Args:
        conn: connection handle
        request (str): json with the request
    """
    if 'last_updated' in request:
        my_msg = {'msgs': msgObjects.get_bsms(
            last_updated=request['last_updated'])}
    else:
        my_msg = {'msgs': msgObjects.get_bsms()}
    my_msg = json.dumps(my_msg)
    my_msg = str.encode(my_msg)
    conn.sendall(my_msg)


def connection(conn_nr, conn, addr):
    """Process connection request
    Args:
        conn_nr (int): Number of connection
        conn: connection handle
        addr (str): connection address
    """
    last_received = time()
    global buff
    global counter
    if args.verbose >= 1:
        print(f"Connection nr: {conn_nr}, c: {conn}, addr: {addr}")
    while True:
        data = conn.recv(args.data_buffer)
        if args.verbose >= 2:
            print(f"Conn {conn_nr}, addr: {addr}, Data received: {data}")
        if len(data) == 0:
            if time() - last_received < args.end_thread_time:
                continue
            if args.verbose >= 1:  # End thread if not conected for a while
                print(f"\nDisconnecting session nr {conn_nr}.")
            break
        last_received = time()
        request = json.loads(data)
        if "mode" not in request:
            conn.sendall(str.encode('ERROR: No "mode" in request.'))
            continue
        if request['mode'] == 'push':
            ret = push_data(request)
            conn.sendall(str.encode(ret))
        elif request['mode'] == 'pull':
            pull_data(conn)
        elif request['mode'] == 'check':
            check_data(conn, request)
        else:
            conn.sendall(str.encode('ERROR: Value for "mode" unknown.'))


if __name__ == '__main__':
    connection_counter = 0
    args = parser.parse_args()
    msgObjects = MsgObjects(args.object_lifetime)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((args.host, args.port))
        s.listen()
        while True:
            conn_received, conn_addr = s.accept()
            connection_counter += 1
            t = threading.Thread(target=connection, args=(
                connection_counter, conn_received, conn_addr))
            t.start()
