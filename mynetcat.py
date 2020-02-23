#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import selectors
import select
from socket import *
import sys
import subprocess
import argparse


sel = selectors.DefaultSelector()

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("host", help="host to connect to", action="store", nargs = '?', default='localhost')
    parser.add_argument("port", type=int, help="port to connect to", action="store")
    parser.add_argument("--listen", "-l", help="bind and listen for incoming connections", action="store_true")
    parser.add_argument("--shell", "-c", help="initialise a command shell", action="store_true")
    parser.add_argument("--execute", "-e", help="execute the given file", action="store")
    parser.add_argument("--upload", "-u", help="upload file to destination", action="store")
    parser.add_argument("--verbose", "-v", help="verbose", action="store_true")
    args = parser.parse_args()
    return args

def accept(sock, mask):
    conn, addr = sock.accept()
    print('accepted', conn, 'from', addr)
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn, mask):
    data = conn.recv(1024)
    if data:
        print(data.decode())
        buffer = input().encode() + b'\n'
        conn.send(buffer)
    else:
        print('closing', conn)
        sel.unregister(conn)
        conn.close()

def connect_host(host, port):
    s = socket(AF_INET, SOCK_STREAM)
    try:
        s.connect((host, port))
        logging.info(f"[+] Connection to {host}:{port} was successful")
    except:
        logging.critical('Failed to connect. Ditching...')
        exit()

    while True:
        socket_list = [sys.stdin, s]
        read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])

        for sock in read_sockets:
            if sock == s:
                data = sock.recv(4096)
                if not data:
                    logging.error ("Connection closed")
                    exit()
                else:
                    sys.stdout.write(data.decode())
            else:
                # user input
                msg = sys.stdin.readline()
                s.send(msg.encode())

def just_listen(conn):
    logging.debug("Just listening...")
    while True:
        socket_list = [sys.stdin, conn]
        read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])

        for sock in read_sockets:
            if sock == conn:
                data = conn.recv(4096)
                if not data:
                    logging.info("Connection closed")
                    return
                else:
                    sys.stdout.write(data.decode())
            else:
                # user input
                msg = sys.stdin.readline()
                conn.send(msg.encode())

def upload(conn, filename):
   with open(filename, 'rb') as f:
       conn.send(f.read())


def execute_file(conn, executable):
    cmd = list(executable.split())
    logging.info(f"cmd {cmd}")
    logging.info(f"executable {executable}")
    out = subprocess.check_output(executable, shell=True)
    conn.send(out)

def spawn_shell(conn):
    while True:
        conn.send(b"Shell> ")
        data = conn.recv(1024)
        cmd = data.decode()
        logging.debug(f"cmd: {cmd}")
        logging.debug(f"data: {data}")
        try:
            out = subprocess.check_output(cmd, shell=True)
            conn.send(out)
        except KeyboardInterrupt :
            break
        except:
            continue

def main():
    args = parse_arguments()

    if args.verbose:
        logging.basicConfig(format='%(funcName)s():%(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(funcName)s():%(message)s', level=logging.CRITICAL)

    if args.listen:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            s.bind((args.host, args.port))
            s.listen()
            conn, addr = s.accept()
            with conn:
                logging.info(f"Connection by {addr}")
                if args.upload:
                    upload(conn, args.upload)
                elif args.execute:
                    execute_file(conn, args.execute)
                elif args.shell:
                    spawn_shell(conn)
                else:
                    just_listen(conn)

    else:           # connect to host, port
        connect_host(args.host, args.port)


if __name__ == '__main__':
    main()
