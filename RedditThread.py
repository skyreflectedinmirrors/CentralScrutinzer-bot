import threading
import CentralScrutinizer
import Policies
class RedditThread(object):
    """
    A class designed to be used as a thread in the Central Scrutinizer
    takes care of some basics such as pausing / exiting etc.

    :type owner: CentralScrutinizer.CentralScrutinizer
    :type policy: Policies.DefaultPolicy
    """
    def __init__(self, owner, policy):
        self.owner = owner
        self.policy = policy
        self.wait = threading.Event()
        self.exit = threading.Event()
        self.instances = [0 for i in range(policy.Errors_Before_Halt)]

    def check_status(self):
        #push back an instance
        self.instances.insert(0, 0)
        self.instances = self.instances[:self.policy.Errors_Before_Halt]
        #check for pause
        while self.wait.is_set():
            self.wait.wait(self.policy.Pause_Period)
        #check for exit
        if self.exit.is_set():
            self.__shutdown()
            return False
        return True

    def __log_error(self):
        self.instances[0] = 1
        if sum(self.instances) == self.policy.Errors_Before_Halt:
            self.owner.request_pause()

    def run(self):
        raise NotImplementedError