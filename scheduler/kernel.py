### Fill in the following information before submitting
# Group id: 3
# Members: Brayden Rudisill, Rhea Jethvani

from dataclasses import dataclass
from logging import Logger

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
    time_used: int = 0
    process_type: str = "Foreground"


@dataclass
class Kernel:
    """Represents the Kernel of the simulation.
    - The simulator will create an instance of this object and use it to respond to
        syscalls and interrupts.
    - DO NOT modify the name of this class or remove it."""
    def __init__(self, scheduling_algorithm: str, logger: Logger):
        self.scheduling_algorithm = scheduling_algorithm
        self.logger = logger

        self.ready_queue: list[PCB] = []
        self.waiting_queue: list[PCB] = []
        self.idle_pcb: PCB = PCB(None, 0)
        self.running: PCB = self.idle_pcb

        self.time_elapsed: int = 0
        self.level_time: int = 0
        self.fg_queue: list[PCB] = []
        self.bg_queue: list[PCB] = []
        self.current_level: str = "Foreground"

        self.semaphores: dict[int, int] = {}
        self.sema_blocked: dict[int, list[PCB]] = {}
        self.mutexes: dict[int, bool] = {}
        self.mutex_blocked: dict[int, list[PCB]] = {}
        self.mutex_owner: dict[int, list[PCB]] = {}

    
    def new_process_arrived(self, new_process: PID, priority: int, process_type: str) -> PID:
        """Triggered every time a new process has arrived.
        - new_process is this process's PID.
        - priority is the priority of new_process.
        - DO NOT rename or delete this method. DO NOT change its arguments.
        """
        # self.logger.log(f"Ready queue len: {len(self.ready_queue)} when process {new_process} arrived")
        new_pcb = PCB(priority, new_process, process_type=process_type)

        if self.scheduling_algorithm == "Multilevel":
            # self.logger.log(f"Multilevel checking")

            if process_type == "Foreground":
                self.fg_queue.append(new_pcb)
            else:
                self.bg_queue.append(new_pcb)
            if self.running == self.idle_pcb:
                self.running = self.choose_next_process()
        elif self.running == self.idle_pcb:
            # self.logger.log(f"Was IDLE, now {new_pcb.pid}")
            self.running = new_pcb
        elif self.scheduling_algorithm == "Priority" and new_pcb < self.running:
            # self.logger.log(f"Priority switch to {new_pcb.pid}")
            self.add_to_queue(self.running)
            self.running = new_pcb
        else:
            # self.logger.log(f"Adding to queue {new_pcb.pid}")
            self.add_to_queue(new_pcb)

        return self.running.pid

    def add_to_queue(self, pcb: PCB):
        if self.scheduling_algorithm == "Priority":
            from heapq import heappush
            heappush(self.ready_queue, pcb)
        else:
            self.ready_queue.append(pcb)

    def choose_next_process(self):
        """This is where you can select the next process to run.
        - Not directly called by the simulator and is purely for your convenience.
        - Feel free to modify this method as you see fit.
        - It is not required to actually use this method, but it is recommended.
        """
        if self.scheduling_algorithm == "Multilevel":
            return self.choose_multilevel()
        if not self.ready_queue:
            return self.idle_pcb
        if self.scheduling_algorithm in ["FCFS", "RR"]:
            return self.ready_queue.pop(0)
        if self.scheduling_algorithm == "Priority":
            from heapq import heappop
            return heappop(self.ready_queue)
    
    def choose_multilevel(self):
        if self.current_level == "Foreground":
            if self.fg_queue:
                return self.fg_queue.pop(0)
            elif self.bg_queue:
                self.current_level = "Background"
                self.level_time = 0
                return self.bg_queue.pop(0)
        else:
            if self.bg_queue:
                return self.bg_queue.pop(0)
            elif self.fg_queue:
                self.current_level = "Foreground"
                self.level_time = 0
                return self.fg_queue.pop(0)
        return self.idle_pcb

    def syscall_exit(self) -> PID:
        old_pid = self.running.pid
        self.running = self.choose_next_process()
        # self.logger.log(f"Process {old_pid} exited; switched to {self.running.pid}")
        return self.running.pid

    def syscall_set_priority(self, new_priority: int) -> PID:
        self.running.priority = new_priority
        if self.scheduling_algorithm == "Priority":
            if self.ready_queue and self.ready_queue[0] < self.running:
                self.add_to_queue(self.running)
                self.running = self.choose_next_process()
        return self.running.pid

    def syscall_init_semaphore(self, semaphore_id: int, initial_value: int):
        self.semaphores[semaphore_id] = initial_value
        self.sema_blocked[semaphore_id] = []

    def syscall_semaphore_p(self, semaphore_id: int) -> PID:
        self.semaphores[semaphore_id] -= 1
      # self.logger.log(f"{self.semaphores[semaphore_id]=}")

        if self.semaphores[semaphore_id] < 0:
            self.sema_blocked[semaphore_id].append(self.running)
            self.running = self.choose_next_process()
        return self.running.pid

    def syscall_semaphore_v(self, semaphore_id: int) -> PID:
        self.semaphores[semaphore_id] += 1
      # self.logger.log(f"{self.semaphores[semaphore_id]=}")
      # self.logger.log(f"{self.ready_queue=}")
      # self.logger.log(f"{self.running=}")
        if self.scheduling_algorithm == "Priority":
            self.sema_blocked[semaphore_id].sort()

        if self.sema_blocked[semaphore_id]:
            unblocked = self.sema_blocked[semaphore_id].pop(0)
            if unblocked < self.running:
                self.add_to_queue(self.running)
                self.running = unblocked
            else:
                self.add_to_queue(unblocked)

        return self.running.pid

    def syscall_init_mutex(self, mutex_id: int):
        self.mutexes[mutex_id] = True
        self.mutex_blocked[mutex_id] = []
        self.mutex_owner[mutex_id] = None

    def syscall_mutex_lock(self, mutex_id: int) -> PID:
        if self.mutexes[mutex_id]:
            self.mutexes[mutex_id] = False
            self.mutex_owner[mutex_id] = self.running
        else:
            self.mutex_blocked[mutex_id].append(self.running)
            self.running = self.choose_next_process()
        return self.running.pid

    def syscall_mutex_unlock(self, mutex_id: int) -> PID:
        if self.mutex_owner.get(mutex_id) == self.running:
            if self.mutex_blocked[mutex_id]:
                if self.scheduling_algorithm == "Priority":
                    self.mutex_blocked[mutex_id].sort()
                next_proc = self.mutex_blocked[mutex_id].pop(0)
                self.mutex_owner[mutex_id] = next_proc
                self.add_to_queue(next_proc)
            else:
                self.mutexes[mutex_id] = True
                self.mutex_owner[mutex_id] = None
        return self.running.pid

    def timer_interrupt(self) -> PID:
        self.time_elapsed += 10
        self.running.time_used += 10

        if self.scheduling_algorithm == "RR":
            if self.running.time_used >= 40:
                self.running.time_used = 0
                self.ready_queue.append(self.running)
                self.running = self.choose_next_process()
                # self.logger.log(f"Interrupting for {self.running.pid}")

        elif self.scheduling_algorithm == "Multilevel":
            self.level_time += 10
            if self.current_level == "Foreground":
                if self.running.time_used >= 40:
                    self.running.time_used = 0
                    self.fg_queue.append(self.running)
                    self.running = self.choose_next_process()
            if self.level_time >= 200:
                if (self.current_level == "Foreground" and self.bg_queue) or \
                   (self.current_level == "Background" and self.fg_queue):
                    self.running.time_used = 0
                    self.current_level = "Background" if self.current_level == "Foreground" else "Foreground"
                    self.level_time = 0
                    self.running = self.choose_next_process()

        return self.running.pid
