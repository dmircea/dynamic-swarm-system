import queue

class Node_Info:
    def __init__(self, name):
        #   Storage for name and message history.
        #   May be used to store hashed password if security is taken into account
        
        self.name = name

        #   Need to make sure that a folder by this name
        self.HISTORY_DUMP_PATH = 'dump_logs/'

        #   A queue of the 20 most recent messages / 20 by default
        self.message_history = queue.Queue(20)

    def add_message(self, message):
        if(self.message_history.full() == False):
            self.message_history.put_nowait(message)
        else:
            self.message_history.get_nowait()
            self.message_history.put_nowait(message)

    def get_oldest_message(self, message):
        if(self.message_history.empty() == True):
            return None
        return self.message_history.get_nowait()

    def dump_message_history(self, file_name = '?'):
        if (file_name == '?'):
            file_name = self.name + '.txt'

        with open(self.HISTORY_DUMP_PATH + file_name, 'a+') as dump_file:
            dump_file.write('\n')
            while(self.message_history.empty() == False):
                dump_file.write(str(self.message_history.get_nowait()) + '\n')
