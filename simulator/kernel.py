### Fill in the following information before submitting
# Group id: 3
# Members: Brayden Rudisill, Rhea Jethvani

from collections import deque
from dataclasses import dataclass, field


PID = int
"""PID is just an integer.
- It is used to make it clear when a integer is expected to be a valid PID.
"""


@dataclass
class PCB:
    """Represents the PCB of processes.
    It is only here for your convenience and can be modified however you see fit.
    """
    pid: PID


@dataclass
class Kernel:
    """Represents the Kernel of the simulation.
    - The simulator will create an instance of this object and use it to respond to
        syscalls and interrupts.
    - DO NOT modify the name of this class or remove it."""
    scheduling_algorithm: str
    ready_queue: deque[PCB] = field(default_factory=deque)
    waiting_queue: deque[PCB] = field(default_factory=deque)
    running: PCB = 0
    idle_pcb: PCB = 0

    def new_process_arrived(self, new_process: PID, priority: int) -> PID:
        """Triggered every time a new process has arrived.
        - new_process is this process's PID.
        - priority is the priority of new_process.
        - DO NOT rename or delete this method. DO NOT change its arguments.
        """
        # TODO: Implement
        return self.running.pid

    def syscall_exit(self) -> PID:
        """Triggered every time the current process performs an exit syscall.
        - DO NOT rename or delete this method. DO NOT change its arguments.
        """
        # TODO: Implement
        return self.running.pid

    def syscall_set_priority(self, new_priority: int) -> PID:
        """Triggered when the currently running process requests to change its priority.
        - DO NOT rename or delete this method. DO NOT change its arguments.
        """
        # TODO: Implement
        return self.running.pid

    def choose_next_process(self):
        """This is where you can select the next process to run.
        - Not directly called by the simulator and is purely for your convenience.
        - Feel free to modify this method as you see fit.
        - It is not required to actually use this method, but it is recommended.
        """
        if len(self.ready_queue) == 0:
            return self.idle_pcb
        
        if self.scheduling_algorithm == "FCFS":
            self.running = self.idle_pcb
        elif self.scheduling_algorithm == "Priority":
            self.running = self.idle_pcb
