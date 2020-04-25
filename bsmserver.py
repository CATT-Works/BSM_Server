import argparse

import os
import sys

import socket
import threading
import json

from time import time
from bsmmsg.msgobj import MsgObjects

parser = argparse.ArgumentParser(description='Runs the BSM server')

parser.add_argument('--host',
                    type=str,
                    default='127.0.0.1',
                    help='IP of the host with the BSM server. Default=127.0.0.1'
                   )

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

parser.add_argument('--end_thread_time',
                    type=int,
                    default=10,
                    help="end a thread if didn't receive anything for X seconds. Default=10"
                   )

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
    global msgObjects
    json_msgs = json.loads(request['msg'])
    if args.verbose >= 2:
        print ("json_msgs:", type(json_msgs), json_msgs)
    if isinstance(json_msgs, dict):
        json_msgs = [json_msgs]
    ret = sum([msgObjects.push_object(json_msg) for json_msg in json_msgs])
    msgObjects.sort_objects()
    if ret > 0:
        return "ERROR: Failed to push {} / {} objects.".format(ret, len(json_msgs))
    return args.ok


def pull_data(conn, request):
    myMsg = msgObjects.pull_bsm()
    if args.verbose >=2:
        print ("PULL:", myMsg)
    myMsg = str.encode(myMsg)
    conn.sendall(myMsg)


def check_data(conn, request):
    myMsg = {'msgs': msgObjects.get_bsms()}
    myMsg = json.dumps(myMsg)
    myMsg = str.encode(myMsg)
    conn.sendall(myMsg)


def connection(nr, conn, addr):
    last_received = time()
    global buff
    global counter
    if args.verbose >= 1:
        print ("Connection nr: {}, c: {}, addr: {}".format(nr, conn, addr))
    while True:
        data = conn.recv(args.data_buffer)
        if args.verbose >= 2 :
            print("Conn {}, addr: {}, Data received: {}".format(nr, addr, data))
        if len(data) == 0:
            if time() - last_received < args.end_thread_time:
                continue
            else:  # End thread if not conected for a while
                if args.verbose >= 1:
                    print ("\nDisconnecting session nr {}.".format(nr))
                break
        last_received = time()
        request = json.loads(data)
        if not "mode" in request:
            conn.sendall(str.encode('ERROR: No "mode" in request.'))
            continue
        if request['mode'] == 'push':
            ret = push_data(request)
            conn.sendall(str.encode(ret))
        elif request['mode'] == 'pull':
            pull_data(conn, request)
        elif request['mode'] == 'check':
            check_data(conn, request)
        else:
            conn.sendall(str.encode('ERROR: Value for "mode" unknown.'))


if __name__ == '__main__':
    connr = 0
    args = parser.parse_args()
    msgObjects = MsgObjects(args.object_lifetime)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((args.host, args.port))
        s.listen()
        while True:
            conn, addr = s.accept()
            connr += 1
            t = threading.Thread(target=connection, args=(connr, conn, addr))
            t.start()



	
