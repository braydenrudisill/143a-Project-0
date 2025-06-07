### Fill in the following information before submitting
# Group id: 3
# Members: Brayden Rudisill, Rhea Jethvani
from heapq import heappop, heappush
from dataclasses import dataclass, field
from logging import Logger
from typing import Literal


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
class Semaphore:
    value: int
    waiting: list[PCB] = field(default_factory = list)
    def acquire_by(self, pcb: PCB) -> bool:
        """Returns false if process needs to wait."""
        self.value -= 1

        if should_wait := self.value < 0:
            self.waiting.append(pcb)

        return not should_wait

    def release(self):
        self.value += 1

@dataclass
class Mutex:
    waiting: list[PCB] = field(default_factory = list)
    owner: PCB | None = None
    def lock_by(self, pcb: PCB) -> bool:
        """Returns false if process needs to wait."""
        if should_wait := self.owner is not None:
            self.waiting.append(pcb)
        else:
            self.owner = pcb
        return not should_wait

    def release(self):
        self.owner = None

@dataclass
class MMU:
    available_memory : list[range] = field(default_factory = list)
    reserved_memory: dict[PID, range] = field(default_factory = dict)
    logger: Logger | None = None
    def translate(self, address: int, pid: PID) -> int | None:
        mem = self.reserved_memory[pid]
        phys_addr = address - 0x20000000 + mem.start
        return phys_addr if phys_addr in mem else None

    def reserve(self, num_bytes: int, pid: PID) -> bool:
        for block in self.available_memory:
            if len(block) >= num_bytes:
                self.available_memory.remove(block)
                self._add_available(range(block.start+num_bytes, block.stop))
                self.reserved_memory[pid] = range(block.start, block.start + num_bytes)
                return True
        return False

    def free(self, pid: PID):
        freed_block = self.reserved_memory.pop(pid)

        remaining_blocks = []
        for block in self.available_memory:
            if block.stop == freed_block.start:
                freed_block = range(block.start, freed_block.stop)
            elif block.start == freed_block.stop:
                freed_block = range(freed_block.start, block.stop)
            else:
                remaining_blocks.append(block)

        self.available_memory = remaining_blocks
        self._add_available(freed_block)

    def _add_available(self, r):
        self.available_memory.append(r)
        self.available_memory.sort(key = lambda b: (len(b), b.start))


@dataclass
class Kernel:
    """Represents the Kernel of the simulation.
    - The simulator will create an instance of this object and use it to respond to
        syscalls and interrupts.
    - DO NOT modify the name of this class or remove it."""
    def __init__(self, scheduling_algorithm: str, logger: Logger, mmu: MMU, memory_size: int):
        self.scheduling_algorithm = scheduling_algorithm
        self.logger = logger
        self.mmu = mmu
        self.mmu.available_memory = [range(memory_size)]
        self.mmu.logger = logger
        self.mmu.reserve(10_485_760, 0)  # 10 MiB

        self.ready_queue: list[PCB] = []
        self.idle_pcb: PCB = PCB(None, 0)
        self.running: PCB = self.idle_pcb

        self.time_elapsed: int = 0
        self.level_time: int = 0
        self.fg_queue: list[PCB] = []
        self.bg_queue: list[PCB] = []
        self.current_level: str = "Foreground"

        self.semaphores: dict[int, Semaphore] = {}
        self.mutexes: dict[int, Mutex] = {}

    
    def new_process_arrived(self, new_process: PID, priority: int, process_type: str, memory_needed: int) -> PID | Literal[-1]:
        """Triggered every time a new process has arrived.
        - new_process is this process's PID.
        - priority is the priority of new_process.
        - DO NOT rename or delete this method. DO NOT change its arguments.
        """

        if not self.mmu.reserve(memory_needed, new_process):
            return -1

        new_pcb = PCB(priority, new_process, process_type=process_type)

        if self.scheduling_algorithm == "Multilevel":

            if process_type == "Foreground":
                self.fg_queue.append(new_pcb)
            else:
                self.bg_queue.append(new_pcb)
            if self.running == self.idle_pcb:
                self.time_elapsed = 0
                self.running = self.choose_next_process()
        elif self.running == self.idle_pcb:
            # self.logger.log(f"Was IDLE, now {new_pcb.pid}")
            self.time_elapsed = 0
            self.running = new_pcb
        elif self.scheduling_algorithm == "Priority" and new_pcb < self.running:
            # self.logger.log(f"Priority switch to {new_pcb.pid}")
            self.add_to_queue(self.running)
            self.time_elapsed = 0
            self.running = new_pcb
        else:
            # self.logger.log(f"Adding to queue {new_pcb.pid}")
            self.add_to_queue(new_pcb)

        return self.running.pid

    def add_to_queue(self, pcb: PCB):
        if self.scheduling_algorithm == "Priority":
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

        self.level_time = 0
        return self.idle_pcb

    def syscall_exit(self) -> PID:
        self.mmu.free(self.running.pid)
        if self.scheduling_algorithm != "Multilevel":
            self.time_elapsed = 0
        elif self.current_level == "Foreground":
            self.time_elapsed = 0

        self.running = self.choose_next_process()
        return self.running.pid

    def syscall_set_priority(self, new_priority: int) -> PID:
        self.running.priority = new_priority
        if self.scheduling_algorithm == "Priority":
            if self.ready_queue and self.ready_queue[0] < self.running:
                self.add_to_queue(self.running)
                self.running = self.choose_next_process()
        return self.running.pid

    def syscall_init_semaphore(self, semaphore_id: int, initial_value: int):
        self.semaphores[semaphore_id] = Semaphore(initial_value)

    def syscall_semaphore_p(self, semaphore_id: int) -> PID:
        if self.semaphores[semaphore_id].acquire_by(self.running):
            return self.running.pid

        self.set_running(self.choose_next_process())
        return self.running.pid

    def syscall_semaphore_v(self, semaphore_id: int) -> PID:
        sem = self.semaphores[semaphore_id]
        sem.release()

        if self.scheduling_algorithm == "Priority":
            if sem.waiting:
                sem.waiting.sort()
                next_p = sem.waiting.pop(0)
                if self.running >= next_p:
                    self.add_to_queue(self.running)
                    self.set_running(next_p)
                else:
                    self.add_to_queue(next_p)
            return self.running.pid

        if sem.waiting:
            sem.waiting.sort(key=lambda pcb: pcb.pid)
            self.add_to_queue(sem.waiting.pop(0))

        return self.running.pid

    def syscall_init_mutex(self, mutex_id: int):
        self.mutexes[mutex_id] = Mutex()

    def syscall_mutex_lock(self, mutex_id: int) -> PID:
        if not self.mutexes[mutex_id].lock_by(self.running):
            self.set_running(self.choose_next_process())

        return self.running.pid

    def set_running(self, pcb: PCB):
        self.time_elapsed = 0
        self.running = pcb

    def syscall_mutex_unlock(self, mutex_id: int) -> PID:

        mut = self.mutexes[mutex_id]
        if mut.owner is self.running:
            if mut.waiting:
                if self.scheduling_algorithm == "Priority":
                    mut.waiting.sort()

                next_proc = mut.waiting.pop(0)
                mut.owner = next_proc
                if self.scheduling_algorithm == "Priority" and next_proc < self.running:
                    self.add_to_queue(self.running)
                    self.set_running(next_proc)
                else:
                    self.add_to_queue(next_proc)
            else:
                mut.owner = None

        return self.running.pid

    def timer_interrupt(self) -> PID:
        if self.running == self.idle_pcb:
            return self.running.pid
        if self.scheduling_algorithm == "RR":
            self.time_elapsed += 10
            if self.time_elapsed >= 40:
                self.add_to_queue(self.running)
                self.set_running(self.choose_next_process())

        elif self.scheduling_algorithm == "Multilevel":
            self.level_time += 10
            if self.current_level == "Foreground":
                self.time_elapsed += 10


            if (self.level_time >= 200 and
                ((self.current_level == "Foreground" and self.bg_queue) or
                   (self.current_level == "Background" and self.fg_queue))):

                if self.current_level == "Foreground":
                    if self.time_elapsed >= 40:
                        self.time_elapsed = 0
                        self.fg_queue.append(self.running)
                    else:
                        self.fg_queue.insert(0, self.running)
                elif self.current_level == "Background":
                    self.bg_queue.insert(0, self.running)

                self.current_level = "Background" if self.current_level == "Foreground" else "Foreground"
                self.level_time = 0

                self.running = self.choose_next_process()
            else:
                if self.level_time >= 200:
                    self.level_time = 0

                if self.current_level == "Foreground":
                    if self.time_elapsed >= 40:
                        self.fg_queue.append(self.running)
                        self.set_running(self.choose_next_process())

        return self.running.pid