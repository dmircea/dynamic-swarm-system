# dynamic-swarm-system

### Project members:
- Mircea Dumitrache

### Current files included
The following is a set of files included in the project and a short description
of them.
- main.py
  - This file includes the main component and makes use of the node component
  - This is one of the two files that must be executed for the system to work
- Node.py
  - This file is imported into main.py
  - Represents one node in the system and makes use of the files in the Node_Materials folder
  - Uses multi-threading to keep up with listening and sending messages.
- Central Computer
  - This file includes the Central Computer component use to observe the system
  - This component may also be used to manipulate the system
  - Uses multi-threading which allow listening to new nodes while performing its other functions
  - Contains a simple command line interface for use.
- central_log.txt
  - File used for logging message or information by the central computer
- logger.txt
  - File used for logging node information used by all nodes that are told to log.
- dump_logs
  - Folder in which all dump logs are contained.
  - The files contain a short message history of all nodes that dumped their messages.
- Node_Materials
  - This file contains two components being used inside of Node.py
  - Node_Comm.py
    - This file deals with all forms of communication to other nodes or to the Central Computer
    - This is where the multithreading happens
  - Node_Info.py
    - This file keeps track of information that the node has dealt with
    - It contains the name of the node
    - It contains the 20 most recent message and the ability to dump those messages in a text file

### Project Use