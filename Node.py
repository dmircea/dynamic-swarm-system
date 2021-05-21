#   Import the information and communication modules
import Node_Materials.Node_Comm as Comm
# import Node_Materials.Node_Info as Info
import threading
#   This class will deal with the actual basic capabilities of nodes
#   It will make use of communication and information to speak with other nodes
class Node:

    def __init__(self, name):
        #   Initialize the comm and info here as part of self for future uses
        self.communication = Comm.Node_Comm(name)
        
        #   THread to listen to the messages from central computer
        self.listen_thread = threading.Thread(target = self.receive_message, name = "central_listen")
        self.listen_to_node_thread = threading.Thread(target = self.communication.listen_to_nodes, name = "node_listen")
        self.solve_message_thread = threading.Thread(target = self.communication.solve_buffer, name = "buffer_thread")
        #   Leader is an address tuple
        #   Is set to None if this node is the leader   


    #   This is the very first function that gets called once init is complete
    #   Meant to check for any nodes in the "vicinity" and remember them
    def setup_node(self):
        try:
            self.communication.enroll_to_central_comp()
        except:
            print('Could not connect to central computer.')
            return False
        self.communication.start_listen()
        self.listen_thread.start()
        self.listen_to_node_thread.start()
        self.solve_message_thread.start()

        return True

    #   Ping the leader and check if it is still up
    def is_leader_up(self):

        #   If this node is leader than leader is up by default
        if(self.communication.is_leader):
            return True
        #   Check if leader non-existent or not answering
        elif(self.communication.leader_link == None or 
            self.communication.ping(self.communication.leader_link) == False):
            return False

        #   If it gets this far than the leader ping was successful
        return True

    def find_neighbor(self):
        #   TODO: if other_nodes is less than 3 AND this node is not root
        #           scan for other nodes: if other node has same leader
        #                                   

        pass

    def make_known(self, node):
        #   TODO: add_itself to other nodes in the swarm
        pass

    def hold_election(self):
        #   TODO: 
        #       1. If leader does not respond (this is the is_leader_up function) 
        #               this functions happens
        #       2. This node sends election message to every process
        #       3. If no one responds withing a time T the this node elects itself as leader      
        #           --> Send messages to all other nodes about being the leader
        #       4. Else if an answer is received from other process Q
        #           This node waits another time T to receive message that Q became leader
        #           If q doesn't respond restart the "hold_election()" algorithm.
        pass

    #   This function is still under design (personal criticism)
    #   Originally, thought I should have one to listen to any messages nodes
    #   may send, HOWEVER it may be taken care of in comm instead.
    def receive_message(self):
        print("Beginning to listen...")

        comm_result = ""
        
        while(self.communication.listening):
            comm_result = self.communication.listen()

            if(comm_result == '&@'):
                print('Node \"' + self.communication.info.name + '\" ending communication...')
                self.communication.stop_listen()
                continue
            
            #   If it gets here a message wants the node to do something with node information
            #   This will be where position arguments are taken care of in consensus
            

    def terminate(self):
        self.communication.stop_listen()
        self.listen_thread.join()
        self.listen_to_node_thread.join()
        self.solve_message_thread.join()
        #   Close all neighor connections
        temp_name_holder = []
        for node_name in self.communication.other_nodes.keys():
            self.communication.other_nodes[node_name][0].close()
            temp_name_holder.append(node_name)

        for name in temp_name_holder:
            del self.communication.other_nodes[name]
