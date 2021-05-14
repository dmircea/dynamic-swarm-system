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
            continue
        elif(message == 'quit'):
            break
        elif(message == 'quit all'):
            quit_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            quit_sock.connect(('localhost',8000))
            quit_sock.sendall(b'quit')
            break

        n = Node.Node(message)
        n.setup_node()
        all_nodes.append(n)


    #   After while loop is broken out of
    print('Waiting on nodes to terminate...')
    for node in all_nodes:
        node.terminate()

if __name__ == '__main__':
    main()
