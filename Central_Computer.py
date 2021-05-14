#   The central node will be used as a fail safe class that takes care of
#   testing and measuring the election algorithm capabilities.
import socket
import struct
import sys
import threading

#   Those should be used for any nodes that connect to central computer
CENTRAL_HOST = 'localhost'
CENTRAL_PORT = 8001

#   Pack the sock name into sendable bytes
#   sock_name is a tuple of host and port
def pack_sock_name(sock_name):
    host = sock_name[0].encode('utf-8')
    addr = str(sock_name[1]).encode('utf-8')
    return host + b' ' + addr

#   --------------------------------------------------------------
#           CENTRAL COMPUTER FOR USE TO KEEP TRACK OF NODES
#   --------------------------------------------------------------

class Central_Computer:
    def __init__(self):
        #   Should have a dictionary of all nodes that enter the system and
        #   exit the system. Will likely send a message from the nodes to this
        #   node when a node is entered and the central node will take care of
        #   taking off nodes from the system.

        #   Also, there is no way for a node that goes down to tell this central
        #   node that it went down so it won't be able to take care of actual
        #   cases. This is for testing purposes only
        self.all_nodes = {}
        self.observed_leader = ''
        self.number_port = CENTRAL_PORT

        #   Socket used to listen to new nodes
        self.receiving_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #   Set the SO_REUSEADDR to tell kernel to reuse the local socket
        #   Avoids OSError 98 - socket already in use - taken from python documentation
        self.receiving_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #   Bind the socket to the host and port
        self.receiving_socket.bind((CENTRAL_HOST, CENTRAL_PORT))
        #   Set the timeout to two seconds --> allows system to eventually 
        #   exit when continue_signal is set to false
        self.receiving_socket.settimeout(2)
        self.continue_signal = True

        #   Used to hold onto the thread for listening to new nodes function
        self.listener = None

        print('Central Comuter listening on port: ' + str(CENTRAL_PORT))

    #   Set the continue boolean to false in order to stop the thread
    #   Then join back the thread
    def terminate(self):
        self.continue_signal = False
        self.listener.join()

    #   Should be executed as a seperate thread in the background using
    #   the start listener functions. If used as is, it can add in nodes
    #   but not send anything back (and may output undefined behavior)
    def listen_for_new_nodes(self):
        # no_mess = False
        with open(file="central_log.txt", mode='w+') as file:
            while(self.continue_signal):
                #   This should be done by using another thread so that the central computer
                #   can listen for new connections as well as new messages.
                
                self.receiving_socket.listen()

                try:
                    #   Reminder: addr is a tuple pair with host and port
                    conn, addr = self.receiving_socket.accept()
                    print(conn)
                    # print(type(conn))
                    print(addr)
                    # print(type(addr))
                    # print(type(addr[0]), type(addr[1]))
                except:
                    continue


                print('Connected to ', addr)
                name = conn.recv(1024)

                print(name, type(name))

                if(name == b'quit'):
                    print('Shutting down...')
                    break

                if name not in self.all_nodes.keys():
                    self.all_nodes[name] = (conn, addr)
                    print(b'Node ' + name + b' has been added!')
                    conn.sendto(b'ack|', addr)

                    print(name, type(name))
                    self.config_node(name)
                else:
                    print('Node already present!')
                    conn.close()

                #   Log what was added
                file.write('Name received: ' + name.decode('utf-8'))
                
            temp_name_holder = []

            #   Ending of function when quitting
            #   Close connection to all nodes and keep track of names
            print("Shutting down...")
            for name in self.all_nodes.keys():
                self.all_nodes[name][0].close()
                temp_name_holder.append(name)

            #   Use names to delete all keys in dictionary
            for name in temp_name_holder:
                del self.all_nodes[name]

            #   Closing the central computer socket
            self.receiving_socket.close()

    #   Sets up the node in the system.
    #       Tells node who leader is.
    #           If first or only node, he becomes leader.
    #       Let's node know about other nodes and their addresses and ports.
    #       Node will send a message to each node to acknowledge that they exists
    #           And to have them acknowledge its own existence
    def config_node(self, name):
        #   If only node, send message to lead
        print(name, type(name))
        if(len(self.all_nodes) == 1):
            print(b'Only one node in dictionary. Setting ' + name + b' to leader.')
            self.send_message_to(name, b'lead')
            self.observed_leader = name
        #   Else tell everyone about this node
        else:
            #   Create "speaker message to retrieve speaker host+address"
            mess = b'getlistener'

            socket_info_new_node = self.send_message_to(name, mess)

            #   Go through each node in dict except for this one
            for node_name in self.all_nodes.keys():
                if node_name != name:

                    #   packs node command followed by name, formatted host and port
                    #   format: b'node <name> <host> <port>'

                    #   First use the package found for new node and 
                    #   send it to all existing nodes
                    mess_socket = b'node ' + name + b' ' + socket_info_new_node
                    print('DEBUG: node_name and message: ' ,node_name, mess_socket)
                    self.send_message_to(node_name, mess_socket)

                    #   Get package from the current exisiting nodes and
                    #   send it to new node
                    socket_info_existing_node = self.send_message_to(node_name, mess)
                    mess_socket = b'node ' + node_name + b' ' + socket_info_existing_node
                    print('DEBUG: node_name and message: ' ,name, mess_socket)

                    self.send_message_to(name, mess_socket)


    def send_message_to(self, target = "", message = b'on'):
        #   If node is not in the dictionary print error
        if(target not in self.all_nodes.keys()):
            print('No such node to send message to.')
            return

        #   Otherwise use the connection in the dictionary to send message to it.
        self.all_nodes[target][0].sendto(message + b'|', self.all_nodes[target][1])

        #   Receive acknowledgement
        ack = self.all_nodes[target][0].recv(1024)
        print(b'Received from ' + target + b': ' + ack)

        #   Change leader observed based on new node
        if ack == b'now leading' or ack == b'usurped leader':
            self.observed_leader = target
        #   If we get shutting down then terminate connection and delete node from dict
        if ack == b'Shutting down':
            self.all_nodes[target][0].close()
            del self.all_nodes[target]
            print('Connection to ' + str(target) + ' closed...')
            #   Check if last node and change observed leader to ''
            if(len(self.all_nodes) == 0):
                self.observed_leader = ''

        #   Check if message is a getter message
        if(message[0:3] == b'get'):
            return ack

    def start_listener(self):
        self.listener = threading.Thread(target = self.listen_for_new_nodes, name = "listener")
        self.listener.start()


#   --------------------------------------------------------------
#   COMMAND-LINE INTERFACE FOR USE IN CONTROLING CENTRAL COMPUTER
#   --------------------------------------------------------------
def print_help():
    #   TODO: consider adding special checkers to send all command (to check for lead
    #           so that not all nodes try to become the leader at same time)
    print('Here is a list of all commands:')
    print('help --> the command you just used (for a more thorough explanation please see manual')
    print('see all --> command to see all nodes enrolled to central computer')
    print('see <name> --> command to see information about a specific node')
    print('send all <message> --> send a message to all nodes enrolled to central computer')
    print('send <name> <message> --> send a message to a specific node')
    print('shutdown all --> sends the terminate signal to all nodes enrolled')
    print('shutdown <name> --> sends the terminate signal to a specific node')
    print('quit --> terminate remaining nodes, terminate central computer listener, then quit')
    print('\n\n')

#   the parameter is supposed to be the central computer
def command_line(comp):
    while(True):
        cmd = input("Please enter a command (or help): ")
        #   Help page command
        if cmd == "help":
            print_help()
        #   See all command --> used to see everything.
        elif cmd == "see all":
            if(len(comp.all_nodes) == 0):
                print('No nodes active...')
            for node in comp.all_nodes.keys():
                if(node == comp.observed_leader):
                    print(node + b' - leader')
                else:
                    print(node)
        #   See command --> followed by the name of a node
        elif cmd[0:3] == "see":
            name = cmd[4:].strip().encode('utf-8')
            print(name)
            if name not in comp.all_nodes.keys():
                print('No such node exists...')
            else:
                print(comp.all_nodes[name])
                if(name == comp.observed_leader):
                    print('This is the current leader.')

        #   Send all <message> command.
        elif cmd[0:8] == "send all":

            if len(comp.all_nodes) == 0:
                print('No nodes enrolled...')

            if(cmd[9:] == ''):
                print('No message found.')
                continue

            #   For sending mesages to all nodes
            mess = cmd[9:].strip().encode('utf-8')

            #   Send the message here to all nodes
            for node_name in comp.all_nodes.keys():
                print('Sending message to ' + str(node_name))
                comp.send_message_to(node_name, mess)

        #   send command --> send <name> <message> 
        #   sends a message to a node with given name
        elif cmd[0:4] == "send":
            #   For sending messages to a node
            #   Split up the rest of the command into name and message
            name = cmd[5:].strip().split(' ', 1)

            if(len(name) == 1):
                print('No message found.')
                continue

            #   Send the name (at 0) for target, and name (at 1) encoded for message
            comp.send_message_to(name[0].encode('utf-8'), name[1].encode('utf-8'))

        elif cmd == "shutdown all":
            #   For sending a shutdown signal to all nodes
            mess = b'&@'

            temp_name_list = list(comp.all_nodes.keys())

            for node_name in temp_name_list:
                comp.send_message_to(node_name, mess)

        elif cmd[0:8] == "shutdown":
            #   For sending a shutdown signal to one node
            name = cmd[9:].strip().encode('utf-8')

            comp.send_message_to(name, b'&@')

        #   For quitting the central computer
        elif cmd == "quit":
            #   Check if any nodes remaining. If so, terminate them.
            if(len(comp.all_nodes) != 0):
                temp_name_list = list(comp.all_nodes.keys())
                for node_name in temp_name_list:
                    comp.send_message_to(node_name, b'&@')

            comp.terminate()
            break
        else:
            print("Command unknown... Please type \"help\" for information.")

#   --------------------------------------------------------------
#       MAIN STARTER - IN CASE THE CENTRAL COMPUTER IS IMPORTED
#   --------------------------------------------------------------

if __name__ == "__main__":
    comp = Central_Computer()
    comp.start_listener()
    #   Call the command line function
    command_line(comp)

    

