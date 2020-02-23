#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import argparse
from socket import *
import select

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", "-l", help="local port to listen", action="store", required=True)
    parser.add_argument("--host", "-r", help="remote host to connect to", action="store", required=True)
    parser.add_argument("--port", "-p", help="remote port to connect to", action="store", required=True)
    parser.add_argument("--verbose", "-v", help="do you need to debug mate?", action="store_true")
    args = parser.parse_args()
    return args

def dump(data):
    for i in range(0, len(data), 16):
        dumpee = data[i:i+16]
        hexdumped = ' '.join([f'{byte:02x}' for byte in dumpee])
        out = f'{i:05X}   {hexdumped:48}   {dumpee.decode("unicode-escape")}'
        print(out)

def main():
    args = parse_arguments()

    if args.verbose:
        logging.basicConfig(format='%(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)

    rsock = socket(AF_INET, SOCK_STREAM)
    rsock.connect((args.host, int(args.port)))
    logging.debug(rsock)

    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", int(args.local)))
    sock.listen(5)
    logging.debug(sock)

    lsock, addr = sock.accept()
    logging.debug(lsock)
    socket_list = [rsock, lsock]
    logging.debug(f"Socket list: {socket_list}")
    while True:
        read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])
        for sock in read_sockets:
            if sock == rsock:
                # Remote server sent us something
                data = rsock.recv(4096)
                if data:
                    if args.verbose:
                        logging.info(f"[SERVER] {len(data)} bytes")
                        dump(data)
                    lsock.send(data)
                    pass
                else:
                    logging.info("Remote server closed connection")
                    rsock.close()
            else: # sock == lsock
                  # Remote client sent us something
                data = lsock.recv(4096)
                if data:
                    if args.verbose:
                        logging.info(f"[CLIENT] {len(data)} bytes")
                        dump(data)
                    rsock.send(data)
                    pass
                else:
                    logging.info("Remote client closed connection")
                    lsock.close()

if __name__ == '__main__':
    #  test = b'kalispera gamwta mou ola kai loipa \x22\x83\x8c'
    #  dump(test)
    main()
