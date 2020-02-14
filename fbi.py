"""
    FizzBuzzLang Interpreter
    Copyright (C) 2020 Matt Rudge (mrudge@gmail.com)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


class FBSyntaxError(SyntaxError):
    def __init__(self, line, filename="", linenum=1, token="", expected=""):
        error = f"Expected {expected} token but got '{token}'"
        colnum = line.index(token) + 1
        super().__init__(error, (filename, linenum, colnum, line))


class FBRuntimeError(RuntimeError):
    pass


class VM:
    """A FizzBuzzLang virtual machine to be used by the Interpreter

    This VM supports 3 types (modes) of operations:
    - Data-space manipulation (methods statring with ds_)
    - I/O (methods statring with io_)
    - Flow control (methods statring with fc_)
    """

    def __init__(self):
        self.stack = [0]  # Memory stack
        self.sp = 0  # Data-space pointer
        # TODO: replace stored_sp1 and stored_sp2 with a fixed-length list
        self.stored_sp1 = 0  # Stored location 1
        self.stored_sp2 = 0  # Stored location 2
        self.ip = 0  # Instruction pointer
        self.labels = {}  # Instruction pointer labels

    def ds_pointer_forward(self):
        """Move the pointer one step forwards in the data-space

        Extend the stack as needed, padding it with zeros.
        """
        self.sp += 1
        if self.sp == len(self.stack):
            self.stack.append(0)
        self.ip += 1

    def ds_pointer_backward(self):
        """Move the pointer one step backwards in the data-space

        If already at the start, stay in place.
        """
        self.sp = max(self.sp - 1, 0)
        self.ip += 1

    def ds_duplicate_element(self):
        """Duplicate the pointed to stack element and move pointer forward

        If pointing to the top of the stack, it will be extended.
        Otherwise, the next element will be overwritten.

        TODO: Address the fact that this op is currently undocumented
        """
        self.ds_pointer_forward()
        self.stack[self.sp] = self.stack[self.sp-1]
        self.ip += 1

    def ds_add(self, stored_location_id=0):
        """Perform addition at the current pointer position

        The addend can be taken from one of two stored locations
        designated by providing stored_location_id of 1 or 2.
        Otherwise, the addend will be the fixed value 1.
        """
        addend = [1,
                  self.stack[self.stored_sp1],
                  self.stack[self.stored_sp2],
                  ][stored_location_id]
        self.stack[self.sp] += addend
        self.ip += 1

    def ds_subtract(self, stored_location_id=0):
        """Perform subtraction at the current pointer position

        The subtrahend can be taken from one of two stored locations
        designated by providing stored_location_id of 1 or 2.
        Otherwise, the subtrahend will be the fixed value 1.
        """
        subtrahend = [1,
                      self.stack[self.stored_sp1],
                      self.stack[self.stored_sp2],
                      ][stored_location_id]
        self.stack[self.sp] -= subtrahend
        self.ip += 1

    def ds_modulus(self, stored_location_id=0):
        """Perform modulus operation at the current pointer position

        This operation calculates the modulus of the value stored at the
        current pointer position and the position immediately preceding it,
        and stores the result in the position immediately following it.
        If stored_location_id is provided, use that as the divisor position.

        TODO: Discuss why the semantics for this op are different from others
        """
        self.ds_pointer_forward()
        divisor = [self.stack[self.sp - 2],
                   self.stack[self.stored_sp1],
                   self.stack[self.stored_sp2],
                   ][stored_location_id]
        self.stack[self.sp] = self.stack[self.sp - 1] % divisor
        self.ip += 1

    def ds_store(self, stored_location_id):
        """Store the current pointer position in one of the stored locations
        """
        if stored_location_id == 1:
            self.stored_sp1 = self.sp
        elif stored_location_id == 2:
            self.stored_sp2 = self.sp
        self.ip += 1

    def ds_move_to(self, stored_location_id):
        """Move data-space pointer to the value in one of the stored locations
        """
        if stored_location_id == 1:
            self.sp = self.stored_sp1
        elif stored_location_id == 2:
            self.sp = self.stored_sp2
        self.ip += 1

    def io_print_value(self, stored_location_id=0):
        """Print the value at the current pointer position or storage location
        """
        value = [self.stack[self.sp],
                 self.stack[self.stored_sp1],
                 self.stack[self.stored_sp2],
                 ][stored_location_id]
        print(value)
        self.ip += 1

    def io_print_character(self, stored_location_id=0):
        """Print the current pointer position or storage location as character
        """
        value = [self.stack[self.sp],
                 self.stack[self.stored_sp1],
                 self.stack[self.stored_sp2],
                 ][stored_location_id]
        print(chr(value), end="")
        self.ip += 1

    def io_character_input(self):
        """Read either an integer or a character from Standard Input

        The provided input is stored in the current pointer position.

        The decimal representation of the character will be stored.
        If more than one character or a floating point number is provided,
        then 0 will be stored in the current data-space pointer location.

        TODO: Refactor this method once there's a suitable test case(s)
        """
        user_input = input("> ")
        try:
            val = int(user_input)
        except ValueError:
            try:
                val = float(user_input)
                val = 0
            except ValueError:
                val = str(user_input)
                val = ord(val) if len(user_input) == 1 else 0
        self.stack[self.sp] = val
        self.ip += 1

    def io_store_binary(self, binary_input):
        """Store a binary value in the current pointer position.
        """
        self.stack[self.sp] = int(binary_input, 2)
        self.ip += 1

    def fc_create_label(self, label):
        """Create a label at the current instruction

        An attempt to override an existing label will be ignored
        """
        if label not in self.labels:
            self.labels[label] = self.ip
        self.ip += 1

    def fc_jump(self, label):
        """Jump to the label unconditionally
        """
        if label not in self.labels:
            raise FBRuntimeError(f"Jump attempt to undefined label '{label}'")
        self.ip = self.labels[label]

    def fc_jump_if_zero(self, label):
        """Jump to the label if the current location value is zero
        """
        if self.stack[self.sp] == 0:
            self.fc_jump(label)
        else:
            self.ip += 1

    def fc_jump_if_non_zero(self, label):
        """Jump to the label if the current location value is NOT zero
        """
        if self.stack[self.sp] != 0:
            self.fc_jump(label)
        else:
            self.ip += 1


class Interpreter:
    """
    The main iterpreter class. All methods are private except for run_file
    """

    def __init__(self, *, debug=False):
        self.vm = VM()
        self.debug = debug  # When enabled debug mode provides verbose logging

    def _run_line(self, line, file, linenum):
        """Parse a single line into tokens and execute the operation

        The only permitted non-code lines are "//" comments and whitespace
        """
        if line.strip().startswith("//") or not line.strip():
            self.vm.ip += 1
            return

        tokens = line.split()

        mode = {"FIZZ": 1, "BUZZ": 2, "FIZZBUZZ": 3}.get(tokens[0])
        if not mode:
            raise FBSyntaxError(line, file, linenum, tokens[0], "mode")

        submode = {"FIZZ": 1, "BUZZ": 2, "FIZZBUZZ": 3}.get(tokens[1])
        if not submode:
            raise FBSyntaxError(line, file, linenum, tokens[1], "submode")

        args = tokens[2:]
        for i, arg in enumerate(args):
            is_label = mode == 3 and submode in (1, 2) and i == len(args)-1
            if not is_label and arg not in ("FIZZ", "BUZZ", "FIZZBUZZ"):
                raise FBSyntaxError(line, file, linenum, arg, "argument")

        # Data-space manipulation operations:
        if tokens == ["FIZZ", "FIZZ", "FIZZ"]:
            self.vm.ds_pointer_forward()
        if tokens == ["FIZZ", "FIZZ", "BUZZ"]:
            self.vm.ds_pointer_backward()
        if tokens == ["FIZZ", "FIZZ", "FIZZBUZZ"]:
            self.vm.ds_duplicate_element()

        if tokens == ["FIZZ", "BUZZ", "FIZZ"]:
            self.vm.ds_add()
        if tokens == ["FIZZ", "BUZZ", "FIZZ", "FIZZ"]:
            self.vm.ds_add(stored_location_id=1)
        if tokens == ["FIZZ", "BUZZ", "FIZZ", "BUZZ"]:
            self.vm.ds_add(stored_location_id=2)

        if tokens == ["FIZZ", "BUZZ", "BUZZ"]:
            self.vm.ds_subtract()
        if tokens == ["FIZZ", "BUZZ", "BUZZ", "FIZZ"]:
            self.vm.ds_subtract(stored_location_id=1)
        if tokens == ["FIZZ", "BUZZ", "BUZZ", "BUZZ"]:
            self.vm.ds_subtract(stored_location_id=2)

        if tokens == ["FIZZ", "BUZZ", "FIZZBUZZ"]:
            self.vm.ds_modulus()
        if tokens == ["FIZZ", "BUZZ", "FIZZBUZZ", "FIZZ"]:
            self.vm.ds_modulus(stored_location_id=1)
        if tokens == ["FIZZ", "BUZZ", "FIZZBUZZ", "BUZZ"]:
            self.vm.ds_modulus(stored_location_id=2)

        if tokens == ["FIZZ", "FIZZBUZZ", "FIZZ"]:
            self.vm.ds_store(stored_location_id=1)
        if tokens == ["FIZZ", "FIZZBUZZ", "BUZZ"]:
            self.vm.ds_store(stored_location_id=2)

        if tokens == ["FIZZ", "FIZZBUZZ", "FIZZBUZZ", "FIZZ"]:
            self.vm.ds_move_to(stored_location_id=1)
        if tokens == ["FIZZ", "FIZZBUZZ", "FIZZBUZZ", "BUZZ"]:
            self.vm.ds_move_to(stored_location_id=2)

        # Input/Output operations
        if tokens == ["BUZZ", "FIZZ"]:
            self.vm.io_print_value()
        if tokens == ["BUZZ", "FIZZ", "FIZZ"]:
            self.vm.io_print_value(stored_location_id=1)
        if tokens == ["BUZZ", "FIZZ", "BUZZ"]:
            self.vm.io_print_value(stored_location_id=2)

        if tokens == ["BUZZ", "BUZZ"]:
            self.vm.io_print_character()
        if tokens == ["BUZZ", "BUZZ", "FIZZ"]:
            self.vm.io_print_character(stored_location_id=1)
        if tokens == ["BUZZ", "BUZZ", "BUZZ"]:
            self.vm.io_print_character(stored_location_id=2)

        if tokens == ["BUZZ", "FIZZBUZZ"]:
            self.vm.io_character_input()
        if tokens[:2] == ["BUZZ", "FIZZBUZZ"] and len(tokens) > 2:
            binary_input = "".join("0" if arg == "FIZZ" else "1"
                                   for arg in args[1:])
            self.vm.io_store_binary(binary_input)

        # Flow Control operations
        if tokens[:2] == ["FIZZBUZZ", "FIZZ"] and len(tokens) == 3:
            self.vm.fc_create_label(args[0])

        if tokens[:3] == ["FIZZBUZZ", "BUZZ", "FIZZ"] and len(tokens) == 4:
            self.vm.fc_jump_if_non_zero(args[1])
        if tokens[:3] == ["FIZZBUZZ", "BUZZ", "BUZZ"] and len(tokens) == 4:
            self.vm.fc_jump_if_zero(args[1])
        if tokens[:3] == ["FIZZBUZZ", "BUZZ", "FIZZBUZZ"] and len(tokens) == 4:
            self.vm.fc_jump()

        if tokens == ["FIZZBUZZ", "FIZZBUZZ"]:
            self.vm.ip = -1

    def run_file(self, filename):
        """Parse the FizzBuzzLang script and attempt to execute it
        """

        with open(filename) as prog:
            code = prog.readlines()

        while True:
            if self.vm.ip == -1:  # intentional exit
                break
            if self.vm.ip == len(code):
                raise FBRuntimeError(
                    "Unexpected end of program before FIZZBUZZ FIZZBUZZ")
                break


            self._run_line(code[self.vm.ip], filename, self.vm.ip)


            if self.debug:
                print(f"Interpreting line {self.vm.ip}: '{code[self.vm.ip]}'")
                print(f"Labels: {self.vm.labels}")
                print(f"Stored locations: sp1={self.vm.stored_sp1} "
                      f"sp2={self.vm.stored_sp2}")
                print(f"Stack position=self.vm.sp, stack:{self.vm.stack}")
