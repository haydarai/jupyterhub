# TODO: Fix errors like /home/<user> does not exist
import asyncio
import errno
import json
from json import loads
import zmq
import subprocess

from os import path, makedirs
from pathlib import Path
from threading import Timer
from time import strftime
from multiprocessing import Process
from zmq.eventloop import ioloop, zmqstream
ioloop.install()

def split_idents_from_msg_list(msg_list):
    DELIM = b"<IDS|MSG>"
    idx = msg_list.index(DELIM)
    return msg_list[:idx], msg_list[idx+1:]


def deserialize(msg_list):
    # if not len(msg_list) >= 5:
    #     raise TypeError("malformed message, must have at least 5 elements")
    message = {}
    header = loads(msg_list[1].decode('utf-8'))
    # from dateutil import parser
    # message['header'] = parser.parse(header['date']).isoformat(' ')
    # message['msg_id'] = header['msg_id']
    # message['msg_type'] = header['msg_type']
    # message['parent_header'] = loads(msg_list[2])
    # message['metadata'] = loads(msg_list[3])
    message['session'] = header['session']
    message['username'] = header['username']
    message['content'] = loads(msg_list[4].decode('utf-8'))
    return message


def process_message(msg_list):
    # Record an IOPub message arriving from a kernel
    # TODO: For some reason the kernel id is not published and session id is different
    # To figure out: why and how jupyter notebook knows which notebook to display output based on the message
    _, fed_msg_list = split_idents_from_msg_list(msg_list)
    msg = deserialize(fed_msg_list)

    if 'code' in msg['content']:
        print('code...')
        fname = strftime("%Y-%m-%d") + '-' + msg['session'] + ".py"
        log_dir = path.join('/srv/jupyterhub', 'log')
        filename = path.join(log_dir, fname)
        notnew = path.exists(filename)
        try:
            if not path.isdir(log_dir):
                print('makedir...', log_dir)
                makedirs(log_dir)
            f = open(filename, 'a')
            print("Logging to", filename, "... ")
            if not notnew:
                f.write(u"#!/usr/bin/env python\n")
                pass
            f.write(u"# " + msg['username'] + ' at ' +
                    strftime('%H:%M:%S') + "\n")
            f.write(u"" + msg['content']['code'] + "\n")
            # TODO: only close it when the process is shutdown by keeping track of the opened file
            f.close()
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        except RuntimeError:
            print("File opening failed")
            raise


def connect_socket(port_sub):
    context = zmq.Context()
    socket_sub = context.socket(zmq.SUB)
    socket_sub.connect("tcp://localhost:%s" % port_sub)
    socket_sub.setsockopt(zmq.SUBSCRIBE, b'')
    # required otherwise event_loop doesn't exists
    asyncio.set_event_loop(asyncio.new_event_loop())
    stream_sub = zmqstream.ZMQStream(socket_sub)
    stream_sub.on_recv(process_message)
    print("Connected to publisher with port %s" % port_sub)
    ioloop.IOLoop.current().start()  # start io loop at the end


class AuditLog():
    def __init__(self):
        self.current_ports = []
        self.processes_by_port = {}

        self.read_ports()
        self.auto_refresh()

    def read_ports(self):
        subprocess.call("./get_all_ports.sh", shell=True, stderr=subprocess.DEVNULL)
        try:
            with open('./ports.json') as json_data:
                data = json.load(json_data)
                for entry in data:
                    if 'iopub_port' in entry:
                        p = entry['iopub_port']
                        if p not in self.current_ports:
                            self.current_ports.append(p)
                            print('Connecting to ' +
                                'tcp://127.0.0.1:' + str(p) + ' ...')
                            process = Process(target=connect_socket, args=(p,))
                            process.start()
                            self.processes_by_port[p] = process
        except:
            pass

    def auto_refresh(self):
        Timer(0.5, self.auto_refresh).start()

        self.read_ports()

log = AuditLog()