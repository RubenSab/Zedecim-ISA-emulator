from zedecim_isa_emulator.emulator.memory.memory import Memory
from zedecim_isa_emulator.emulator.cpu.registers import Registers
from zedecim_isa_emulator.emulator.cpu.deassembler import deassemble_word
from zedecim_isa_emulator.emulator.word import Word
from zedecim_isa_emulator.emulator.piu import PeripheralsInterfaceUnit


class CPU:

    def __init__(self, memory_size):
        self.INSTRUCTION_FUNCTIONS = {
            "and": self._bitwise_and,
            "or": self._bitwise_or,
            "xor": self._bitwise_xor,
            "not": self._bitwise_not,
            "sh": self._shift,
            "add": self._add,
            "sub": self._sub,
            "mul": self._mul,
            "div": self._int_div,
            "comp": self._compare,
            "li": self._load_immediate,
            "amc": self._add_to_memory_counter,
            "lwmc": self._load_word,
            "swmc": self._store_word,
            "piu": self._peripherals_interface_unit,
            "apceq": self._add_to_program_counter_if_X_is_equal_to_zero,
        }
        self.registers = Registers()
        self.memory_size = memory_size
        self.memory = Memory(memory_size)
        self.piu = PeripheralsInterfaceUnit(cpu=self)
        self.exit_codes = {
            Word(int('0000', 16)): 'No instructions left to execute.',
            Word(int('1000', 16)): 'Division by zero.',
            Word(int('2000', 16)): 'Custom I/O exit code 0x2000.',
            Word(int('3000', 16)): 'Custom I/O exit code 0x3000.',
            Word(int('4000', 16)): 'Custom I/O exit code 0x4000.',
            Word(int('5000', 16)): 'Custom I/O exit code 0x5000.',
            Word(int('6000', 16)): 'Custom I/O exit code 0x6000.',
            Word(int('7000', 16)): 'Custom I/O exit code 0x7000.',
            Word(int('8000', 16)): 'Custom I/O exit code 0x8000.',
            Word(int('9000', 16)): 'Custom I/O exit code 0x9000.',
        }
        self.exit_code = None


    def load_memory_from(self, filename):
        self.memory.load_memory_from(filename)


    def execute(self):
        while True:
            # --- Instruction fetch ---
            instruction = self.memory.load_word(
                int(self.memory.program_counter)
            )
            if instruction in self.exit_codes:
                self.exit_code = instruction
                break

            # --- Instruction decode ---
            parsed_instruction = deassemble_word(instruction)

            # --- Instruction execution ---
            self.execute_parsed_instruction(parsed_instruction)
            if self.exit_code:
                break


    def execute_parsed_instruction(self, instruction: dict) -> None:
        # call instruction's corresponding function from dictionary
        self.INSTRUCTION_FUNCTIONS[instruction['instruction']](
            r1 = instruction['first register'],
            r2 = instruction['second register'],
            r3 = instruction['third register'],
            immediate = instruction['immediate']
        )


    def display_state(self, base=16):
        print(
            f"{'-'*25}Memory state{'-'*24}\n"
            
            "Memory:\n"
            f"{self.memory.str_by_base(base)}\n"
            
            f"\nExit code {self.exit_code.str_by_base(base)}: "
            f"{self.exit_codes[self.exit_code]}\n"
            
            "\nMemory counter: "
            f"{self.memory.memory_counter.str_by_base(base)}\n"
            
            "Program counter: "
            f"{self.memory.program_counter.str_by_base(base)}\n"
            
            "\nRegisters:\n"
            f"{self.registers.str_by_base(base)}\n"
            f"{'-' * 61}\n"
        )


    def _bitwise_and(self, r1=None, r2=None, r3=None, immediate=None):
        self.registers.write(
            r1,
            self.registers.read(r2) & self.registers.read(r3)
        )
        self.memory.program_counter += 1

    def _bitwise_or(self, r1=None, r2=None, r3=None, immediate=None):
        self.registers.write(
            r1,
            self.registers.read(r2) | self.registers.read(r3)
        )
        self.memory.program_counter += 1

    def _bitwise_xor(self, r1=None, r2=None, r3=None, immediate=None):
        self.registers.write(
            r1,
            self.registers.read(r2) ^ self.registers.read(r3)
        )
        self.memory.program_counter += 1

    def _bitwise_not(self, r1=None, r2=None, r3=None, immediate=None):
        self.registers.write(
            r1,
            ~self.registers.read(r2)
        )
        self.memory.program_counter += 1

    def _shift(self, r1=None, r2=None, r3=None, immediate=None):
        to_shift = self.registers.read(r2)
        amount = self.registers.read(r3)
        if amount > 0:
            result = to_shift >> amount
        else:
            result = to_shift << -1*amount
        self.registers.write(r1, result)
        self.memory.program_counter += 1

    def _add(self, r1=None, r2=None, r3=None, immediate=None):
        self.registers.write(
            r1,
            self.registers.read(r2) + self.registers.read(r3)
        )
        self.memory.program_counter += 1

    def _sub(self, r1=None, r2=None, r3=None, immediate=None):
        self.registers.write(
            r1,
            self.registers.read(r2) - self.registers.read(r3)
        )
        self.memory.program_counter += 1

    def _mul(self, r1=None, r2=None, r3=None, immediate=None):
        self.registers.write(
            r1,
            self.registers.read(r2) * self.registers.read(r3)
        )
        self.memory.program_counter += 1

    def _int_div(self, r1=None, r2=None, r3=None, immediate=None):
        a = self.registers.read(r2)
        b = self.registers.read(r3)
        if b == Word(0):
            self.exit_code = Word(int('1000', 16)) # Division by zero
            return
        self.registers.write(r1, a // b)
        self.memory.program_counter += 1

    def _compare(self, r1=None, r2=None, r3=None, immediate=None):
        a = self.registers.read(r2)
        b = self.registers.read(r3)
        if a > b:
            result = Word(int('1', 16))
        elif a < b:
            result = Word(int('-1', 16))
        else:
            result = Word(int(0))
        self.registers.write(r1, result)
        self.memory.program_counter += 1

    def _load_immediate(self, r1=None, r2=None, r3=None, immediate=None):
        self.registers.write(r2, immediate)
        self.memory.program_counter += 1

    def _add_to_memory_counter(
    self, r1=None, r2=None, r3=None, immediate=None):
        self.memory.memory_counter += self.registers.read(r2) + immediate
        self.memory.program_counter += 1

    def _load_word(self, r1=None, r2=None, r3=None, immediate=None):
        self.registers.write(
            register_name = r2,
            content = self.memory.load_word(
                self.memory.memory_counter + immediate
            )
        )
        self.memory.program_counter += 1

    def _store_word(self, r1=None, r2=None, r3=None, immediate=None):
        self.memory.store_word(
            address = self.memory.memory_counter + immediate,
            content = self.registers.read(r2)
        )
        self.memory.program_counter += 1

    def _peripherals_interface_unit(
    self, r1=None, r2=None, r3=None, immediate=None):
        self.piu.execute_command(
            code = immediate,
            register_name = r2
        )
        self.memory.program_counter += 1

    def _add_to_program_counter_if_X_is_equal_to_zero(
    self, r1=None, r2=None, r3=None, immediate=None):
        if self.registers.read('X') == 0:
            self.memory.program_counter += immediate + self.registers.read(r2)
        else:
            self.memory.program_counter += 1
