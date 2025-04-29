### Fill in the following information before submitting
# Group id: 3
# Members: Brayden Rudisill, Rhea Jethvani

from dataclasses import dataclass, field
from heapq import heappush, heappop


PID = int
"""PID is just an integer.
- It is used to make it clear when a integer is expected to be a valid PID.
"""


@dataclass(order=True)
class PCB:
    """Represents the PCB of processes.
    It is only here for your convenience and can be modified however you see fit.
    """
    priority: int | None
    pid: PID


@dataclass
class Kernel:
    """Represents the Kernel of the simulation.
    - The simulator will create an instance of this object and use it to respond to
        syscalls and interrupts.
    - DO NOT modify the name of this class or remove it."""
    scheduling_algorithm: str
    ready_queue: list[PCB] = field(default_factory=list)
    waiting_queue: list[PCB] = field(default_factory=list)
    idle_pcb: PCB = PCB(None, 0)
    running: PCB = idle_pcb

    def new_process_arrived(self, new_process: PID, priority: int) -> PID:
        """Triggered every time a new process has arrived.
        - new_process is this process's PID.
        - priority is the priority of new_process.
        - DO NOT rename or delete this method. DO NOT change its arguments.
        """
        new_pcb = PCB(priority, new_process)

        if self.running is self.idle_pcb:
            self.running = new_pcb
        elif self.scheduling_algorithm == "Priority" and new_pcb < self.running:
            self.add_to_queue(self.running)
            self.running = new_pcb
        else:
            self.add_to_queue(new_pcb)

        return self.running.pid

    def add_to_queue(self, pcb: PCB):
        match self.scheduling_algorithm:
            case "Priority":
                heappush(self.ready_queue, pcb)
            case "FCFS":
                self.ready_queue.append(pcb)

    def syscall_exit(self) -> PID:
        """Triggered every time the current process performs an exit syscall.
        - DO NOT rename or delete this method. DO NOT change its arguments.
        """
        self.running = self.choose_next_process()
        return self.running.pid

    def syscall_set_priority(self, new_priority: int) -> PID:
        """Triggered when the currently running process requests to change its priority.
        - DO NOT rename or delete this method. DO NOT change its arguments.
        """
        self.running.priority = new_priority

        if self.scheduling_algorithm == "Priority" and self.ready_queue[0] < self.running:
            self.add_to_queue(self.running)
            self.running = self.choose_next_process()

        return self.running.pid

    def choose_next_process(self):
        """This is where you can select the next process to run.
        - Not directly called by the simulator and is purely for your convenience.
        - Feel free to modify this method as you see fit.
        - It is not required to actually use this method, but it is recommended.
        """
        if len(self.ready_queue) == 0:
            return self.idle_pcb

        match self.scheduling_algorithm:
            case "FCFS":
                return self.ready_queue.pop(0)
            case "Priority":
                return heappop(self.ready_queue)
