import socket
import struct
import sys
import queue
import time

from datetime import datetime

from .Node_Info import Node_Info

CENTRAL_HOST = 'localhost'
CENTRAL_PORT = 8001

NODE_HOST = 'localhost'
NODE_PORT = 8000

NUMBER_OF_NODES = 50
MAX_ATTEMPTS_AT_SENDING = 3

#   Pack the sock name into sendable bytes
#   sock_name is a tuple of host and port
def pack_sock_name(sock_name):
    host = sock_name[0].encode('utf-8')
    addr = str(sock_name[1]).encode('utf-8')
    return host + b' ' + addr

class Node_Comm:
    def __init__(self, name, bind_anywhere = True):
        #   Looked into bluetooth(pybluez), and bluetoothsocket. None worked
        #   as intended on emulated nodes.
        #   The pybluez libary had an issue (which I fixed unoficially with community help),
        #   however, it is likely to only work with separate physical machines
        #   since the devices are discovered by machine rather than port or address.
        #   There is no implemented method to emulate the physical nodes as ports or addresses.
        self.comm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.comm_socket.settimeout(3)
        self.central_computer_addr = None
        self.listening = True

        #   All sibling nodes go here --> will be the same as Central computer
        #       A name to a tuple pair of connection and address(host+port)
        self.other_nodes = {}
        #   Also keep track of who the leader is
        #   leader link is an address pair
        self.leader_link = None
        #   leader name is the key name in the dict in bytes
        self.leader_name = None
        #   describes whether or not the current node is the leader
        self.is_leader = False
        self.info = Node_Info(name)

        #   Set up a speaking socket and set a timeout of 3 seconds
        #   This socket is used when speaking to other known nodes
        #   Must create a separate connection here using a different node
        self.node_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #   Bind the speaker somewhere
        if(bind_anywhere):
            self.node_listener.bind((NODE_HOST, 0))
        else:
            self.node_listener.bind((NODE_HOST, NODE_PORT))
        
        self.node_listener.settimeout(2)
        self.node_communication_buffer = queue.Queue()
        self.central_communication_buffer = queue.Queue()


    #   This will be used to check if another known node is still up and running
    #   It will attempt to connect to a node
    #       If successful withing N attempts -> return True
    #       Otherwise return false
    def ping(self, node = None, number_of_tries = 1):
        #   Make sure a node is given
        #   Reminder: a node is a name in bytes
        if (node == None):
            print('DEBUG: no node given')
            return False

        if (node not in self.other_nodes.keys()):
            print('DEBUG: node not a neighbor')
            return False

        #   Limit attempts and check ack message
        ack = self.send_message(node, b'on|')

        #   Close speaker
        #   self.speaker.close()

        #   Check if unsuccessful
        if(ack == b'bad'):
            print('Ping not successful...')
            return False

        #   Check if wrong message
        if(ack != b'good'):
            print('Ping returned different message...')
            return False

        print('Ping successful...')
        return True

    #   Enroll in the Central Computer
    def enroll_to_central_comp(self):
        print('Enrolling to central computer...')
        self.comm_socket.connect((CENTRAL_HOST, CENTRAL_PORT))
        self.comm_socket.sendall(bytes(self.info.name, 'utf-8'))
        # ack = self.comm_socket.recv(1024)
        # print('Received: ',ack)
        self.central_computer_addr = self.comm_socket.getsockname()

    #   Send a message to all other nodes about being the leader
    #   node parameter is just the name of the node to send it to
    #   TODO: using speaker which has timeout here
    #           make sure to add in try - catch later
    def inform_others_of_leadership(self, node = None):
        #   Check to make sure this IS a leader
        if(self.is_leader == False):
            return

        #   If no node, send to all other nodes
        message = b'leading ' + self.info.name.encode('utf-8') + b'|'
        if(node == None):
            for node_name in self.other_nodes.keys():
                self.other_nodes[node_name][0].sendall(message)
        #   Otherwise send only to that node
        else:
            self.other_nodes[node][0].sendall(message)


    #   This will be used to send a message to another node(s)
    def send_message(self, node_name, message, return_message = True):
        #   TODO finish this function
        if(len(self.other_nodes) == 0):
            print('No neighbors to send message...')
            return

        attempt = 1
        send_success = False

        while(attempt <= MAX_ATTEMPTS_AT_SENDING):
            try:
                #   Send the data here assuming timeout exists
                self.other_nodes[node_name][0].sendall(message + '|')
                send_success = True
            except:
                print('Attempt to send:', str(attempt))
                attempt += 1

        attempt = 1

        if(send_success and return_message):
            while(attempt <= MAX_ATTEMPTS_AT_SENDING):
                try:
                    ack = self.other_nodes[node_name][0].recv(1024)
                    return ack
                except:
                    print('Attempt to get:', str(attempt))
                    attempt += 1

            return b'bad'




    #   Function used to listen  to Central Computer commands
    #   All commands used in command line are sent here
    def listen(self):
        while(self.listening):

            try:
                mess = self.comm_socket.recv(1024)
                date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + '\n'
                
                #   Add the message to the buffer
                self.central_communication_buffer.put_nowait((mess, date))
            except socket.timeout as t:
                pass

        #   This section is outside the while but still inside the listen function
        return '&@'

    
    def stop_listen(self):
        self.listening = False

    def start_listen(self):
        self.listening = True

    def dump_history_to_file(self):
        pass

    #   In charge of node to node communication. If a message must be sent to another
    #   node (and th enode knows about it) it will be sent using the other_nodes dictionary
    #   HOWEVER, receiving connections to other nodes will be done here using the 
    #   node_listener socket.
    def listen_to_nodes(self):
        print(self.info.name ,'starts listening to other nodes on:', self.node_listener.getsockname())

        command_found = False
        while(self.listening):
            self.node_listener.listen(NUMBER_OF_NODES)

            try:
                conn, addr = self.node_listener.accept()
            except:
                continue

            mess = conn.recv(1024)

            date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + '\n'

            #   Set up the message and date in the bufer
            self.node_communication_buffer.put_nowait((mess, date, conn, addr))
            
        
    #   Solve the buffer message one at a time
    #       Is a threaded function using the queue buffer    
    def solve_buffer(self):
        while(self.listening):
            if self.node_communication_buffer.empty():
                time.sleep(0.1)
            else:
                mess, date, conn, addr = self.node_communication_buffer.get_nowait()

                print(b'Node ' + self.info.name.encode('utf-8') + b' received ' + mess)

                command_found = False

                print('MESSAGE THAT WE RECEIVED', mess)

                #   In case we get multiple simulatenous messages
                #   We use a '|' to split up the 
                for message in mess.strip().split(b'|'):
                    if(message == b''):
                        continue
                    #   Check first for commands that can be sent between nodes
                    if(message[0:7] == b'leading'):
                        #   Message format: b'leading <name>'
                        #       Only name because node should be know so we can get other info
                        name = message[8:]

                        print('MESSAGE THAT WE RECEIVED BUT INSIDE IF STMT', message)

                        self.info.add_message((name.decode('utf-8') + ' leading', date))

                        self.is_leader = False
                        #   Next time a ping happens use the name with the dict
                        self.leader_name = name
                        command_found = True

                    #   Check for a ping message from another node
                    if(message[0:2] == b'on'):

                        name = message[3:]

                        self.info.add_message(("pinged by " + name.decode('utf-8'), date))

                        self.other_nodes[name][0].sendall(b'good')
                        self.send_message(name, b'good', return_message=False)

                        command_found = True


                    #   If no command is found consider it a name
                    if(not command_found):
                        #   Add the name to the dictionary
                        if message not in self.other_nodes.keys():
                            self.other_nodes[message] = (conn, addr)
                            print(b'Node ' + self.info.name.encode('utf-8') + b' added ' + message + b' to its neighbors')
                        else:
                            print('Node already exists...')

            #   Check the central computer message buffer
            if self.central_communication_buffer.empty():
                time.sleep(0.1)
            else:

                message, date = self.central_communication_buffer.get_nowait()

                for mess in message.split(b'|'):
                    message_match = False

                    if(mess != b''):
                        print(self.info.name ,b'received', mess)
                    else:
                        continue

                    #   Listen for ack --> only message that is sent from
                    #       Central computer as acknoledgement for enrolling
                    if(mess == b'ack'):
                        print('Node', self.info.name, 'acknoledged by Central Computer.')
                        continue

                    #   List of all message that can be checked and acted on
                    #       1. log --> log yourself in the common node file
                    #       2. dump history --> take node message history and dump it to a file
                    #       3. on --> Usually checked by other nodes who ping but can be sent 
                    #               by central computer too
                    #       4. &@ --> sent by default when using the shutdown functionality
                    #               by central computer --> symbol representing node termination

                    #   At this point, check what the message was and act accordingly
                    if(mess == b'log'):
                        with open('logger.txt', 'a+') as f:
                            if self.is_leader:
                                f.write(self.info.name + ' logged test from central computer as leader: ')
                            else:
                                f.write(self.info.name + ' logged test from central computer: ')
                            f.write(date)

                        self.info.add_message(("log", date))

                        self.comm_socket.sendall(b'acknowledged logging')

                        message_match = True
                    
                    # if(mess == b'yield test'):
                    #     self.comm_socket.sendall(b'acknowledged yield')
                    #     return "some message yielding?"

                    #     message_match = True

                    #   Make current node, dump all history into a txt file.
                    if(mess == b'dump history'):
                        self.info.add_message(("dump history", date))
                        self.info.dump_message_history()
                        self.comm_socket.sendall(b'acknowledged dump history')

                        message_match = True

                    #   Received a ping message so send answer back
                    if(mess == b'on'):
                        self.info.add_message(("pinged", date))
                        self.comm_socket.sendall(b'good')

                        message_match = True

                    #   Supposed to return the packed host+addr from speaker
                    if(mess == b'getlistener'):
                        self.info.add_message(("getlistener", date))

                        self.comm_socket.sendall(pack_sock_name(self.node_listener.getsockname()))

                        message_match = True

                    #   Forces a node to become the leader
                    #       If a leader exists then "usurp" that leader
                    if(mess == b'lead'):
                        self.info.add_message(("lead", date))
                        #   If already leader
                        if self.is_leader:
                            self.comm_socket.sendall(b'already leader')
                        #   If no leader found but is not leader
                        elif self.leader_name == None:
                            self.is_leader = True
                            #   self.leader_name = 
                            self.leader_link = self.node_listener.getsockname()
                            self.comm_socket.sendall(b'now leading')
                        #   If leader exists, usurp him
                        #       Send message to all other nodes about new leader self
                        else:
                            #   TODO: can be tested once we can set up more nodes with 
                            #       different leaders
                            self.is_leader = True
                            self.leader_link = self.node_listener.getsockname()
                            self.inform_others_of_leadership()
                            self.comm_socket.sendall(b'usurped leader')

                        message_match = True

                    #   Special message from central computer to check leader by name
                    if(mess == b'who leads'):
                        self.info.add_message(("who leads", date))
                        ans = b''
                        if self.is_leader:
                            ans = b'I am the leader!'
                        elif self.leader_name == None:
                            ans = b'No leader found.'
                        else:
                            ans = self.leader_name + b' is my leader'

                        self.comm_socket.sendall(ans)

                        message_match = True

                    #   Show all nodes this node knows
                    if(mess == b'show near'):
                        self.info.add_message(("show near", date))

                        ans = b''

                        for node_name in self.other_nodes.keys():
                            ans += node_name + b' '
                            print('Name:', node_name, '-- pair:', str(self.other_nodes[node_name]))

                        print('\n\n')
                        self.comm_socket.sendall(ans)

                        message_match = True


                    #   Is followed by a new node that must be added to the list
                    if(mess[0:4] == b'node'):
                        #   Message format: b'node <name> <host> <port>'
                        mess_info = mess[5:].strip().split(b' ', 2)
                        #   Set up addresss as a tuple
                        addr = (mess_info[1].decode('utf-8'), int(mess_info[2].decode('utf-8')))
                        
                        print(mess_info[0])
                        print('\n',addr,'\n')
                        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.other_nodes[mess_info[0]] = (temp_sock, addr)
                        self.other_nodes[mess_info[0]][0].settimeout(2)
                        self.other_nodes[mess_info[0]][0].connect(addr)
                        self.other_nodes[mess_info[0]][0].sendall(self.info.name.encode('utf-8') + b'|')

                        self.info.add_message(("node " + mess_info[0].decode('utf-8') + " added", date))
                        
                        if(self.is_leader):
                            self.inform_others_of_leadership(mess_info[0])
                        elif self.leader_name == mess_info[0]:
                            self.leader_link = self.other_nodes[self.leader_name][1]

                        self.comm_socket.sendall(b'Node added in ' + self.info.name.encode('utf-8'))
                        message_match = True

                    #   Special message to inform other of leadership position
                    if(mess[0:7] == b'leading'):
                        print('FOUND LEADING MESSAGE IN THE OTHER PART')

                        message_match = True

                    #   Received a ping "command"
                    #   This means the central computer is making this node send a ping 
                    #   to another node --> check if node exists, then ping
                    if(mess[0:4] == b'ping'):
                        #   TODO: must first complet node config in central computer
                        #       so that nodes can know other nodes
                        #   format: ping <name>
                        name = mess[5:]

                        if(self.ping(name)):
                            self.comm_socket.sendall(b'ping successful')
                        else:
                            self.comm_socket.sendall(b'ping failed')


                        message_match = True


                    if(mess == b'&@'):
                        #   This is done in case the user wants logs dumped
                        #   at node termination
                        self.info.add_message(("shutting down", date))

                        self.comm_socket.sendall(b'Shutting down')

                        break

                    #   Check the message_match
                    #   If false, received message did not match any of the "rules"
                    #   Send back an ack with no action found about given message
                    if(message_match == False):
                        self.comm_socket.sendall(b'No known action for message.')
                       
