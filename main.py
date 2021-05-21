#   This is the graduate project of Mircea Dumitrache, student at California State University, Fullerton.
#   All information about this project can be found in the appropriate file named "manual.txt"

import socket
import struct
import sys

import Node
import os
# import Scripts.Central_Computer.py as central

all_nodes = []
with open('logger.txt', 'w') as f:
    f.write('Logging begin here: \n')

def main():

    message = ""

    while(True):
        #   quit when input is quit.
        #   quit all will also send a message to central compputer to shutdown
        message = input("Please enter the name of the node or a command (like \"help\"): \n")

        #   Check for empty message
        if(len(message) == 0):
            print('No message received...')
            continue

        #   Check for length limit of name
        if(len(message) > 20):
            print('Name is far too long...')
            continue

        #   Check for any spaces in the name
        if(' ' in message):
            print('Name contains a space when it should be one word...')
            continue

        if(message == 'clear'):
            #   Simple solution found here: 
            #       https://stackoverflow.com/questions/2084508/clear-terminal-in-python
            #       Thank you!
            os.system('cls||clear')
            continue

        if(message == 'help'):
            #   Print out help stuff than continue
            print('\n')
            print('Any message except commands will be assumed to be a name. A node will be created,'
                'based on that name and will be setup. Please be aware that the set up includes',
                'enrollment to the Central Computer.')
            print('Messages are limited to be up to 20 characters and more than 0 characters.')
            print('Messages must NOT include spaces the must all be one word.\n')
            print('clear --> will clear the screen')
            print('quit --> will quit out of this program and wait on the nodes to finish')
            print('quit_all --> will send a quit signal to the central computer\n')
            print('While it is allowed, naming a node after a specific command used by the',
                'Central Computer may have uninteded consequences.')
            print('\n')
            continue
        elif(message == 'quit'):
            print('Quitting the main component.')
            break
        elif(message == 'quit_all'):
            print('Sending shutdown signal to central computer.')
            #   Print out help stuff than continue
            quit_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            quit_sock.connect(('localhost',8001))
            quit_sock.sendall(b'quit')
            break

        n = Node.Node(message)
        if(n.setup_node() == False):
            print('Something happened and the node was not added...')
        else:
            all_nodes.append(n)


    #   After while loop is broken out of
    print('Waiting on nodes to terminate...')
    for node in all_nodes:
        node.terminate()

if __name__ == '__main__':
    main()
