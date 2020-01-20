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


class VM:
    """A FizzBuzzLang virtual machine

    This VM supports 3 types (modes) of operations:
    - Data-space manipulation (methods statring with ds_)
    - I/O (methods statring with io_)
    - Flow control (methods statring with fc_)
    """

    def __init__(self, *, debug=False):
        self.stack = [0]  # Memory stack
        self.sp = 0  # Data-space pointer
        # TODO: replace stored_sp1 and stored_sp2 with a fixed-length list
        self.stored_sp1 = 0  # Stored location 1
        self.stored_sp2 = 0  # Stored location 2
        self.ip = 0  # Instruction pointer
        self.labels = {}  # Location labels
        self.debug = debug  # Debug mode enabled?

    def ds_pointer_forward(self):
        """Move the pointer one step forwards in the data-space

        Extend the stack as needed, padding it with zeros.
        """
        self.sp += 1
        if self.sp == len(self.stack):
            self.stack.append(0)

    def ds_pointer_backward(self):
        """Move the pointer one step backwards in the data-space

        If already at the start, stay in place.
        """
        self.sp = max(self.sp - 1, 0)

    def ds_duplicate_element(self):
        """Duplicate the pointed to stack element and move pointer forward

        If pointing to the top of the stack, it will be extended.
        Otherwise, the next element will be overwritten.

        TODO: Address the fact that this op is currently undocumented
        """
        self.ds_pointer_forward()
        self.stack[self.sp] = self.stack[self.sp-1]

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

    def ds_store(self, stored_location_id):
        """Store the current pointer position in one of the stored locations
        """
        if stored_location_id == 1:
            self.stored_sp1 = self.sp
        elif stored_location_id == 2:
            self.stored_sp2 = self.sp

    def ds_jump_to(self, stored_location_id):
        """Move pointer position to the value in one of the stored locations
        """
        if stored_location_id == 1:
            self.sp = self.stored_sp1
        elif stored_location_id == 2:
            self.sp = self.stored_sp2

class FizzBuzzLang:
    """
    The main class. All methods are private except for run_file
    """
    def __init__(self, *, debug=False):
        self.vm = VM(debug=debug)

    def _parse_tokens(self, line, file, linenum):
        """Parse a single line into tokens

        The only permitted non-code lines are "//" comments and whitespace
        """
        if line.strip().startswith("//") or not line.strip():
            return 0, 0, []

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

        return mode, submode, args

    def _op_stack(self, submode, args):
        """Execute a Data-space manipulation operation
        """
        if submode == 1:
            if args[0] == "FIZZ":
                self.vm.ds_pointer_forward()
            elif args[0] == "BUZZ":
                self.vm.ds_pointer_backward()
            elif args[0] == "FIZZBUZZ":
                self.vm.ds_duplicate_element()

        elif submode == 2:
            if args[0] == "FIZZ":
                if len(args) > 1 and args[1] == "FIZZ":
                    self.vm.ds_add(stored_location_id=1)
                elif len(args) > 1 and args[1] == "BUZZ":
                    self.vm.ds_add(stored_location_id=2)
                else:
                    self.vm.ds_add()
            elif args[0] == "BUZZ":
                if len(args) > 1 and args[1] == "FIZZ":
                    self.vm.ds_subtract(stored_location_id=1)
                elif len(args) > 1 and args[1] == "BUZZ":
                    self.vm.ds_subtract(stored_location_id=2)
                else:
                    self.vm.ds_subtract()
            elif args[0] == "FIZZBUZZ":
                if len(args) > 1 and args[1] == "FIZZ":
                    self.vm.ds_modulus(stored_location_id=1)
                elif len(args) > 1 and args[1] == "BUZZ":
                    self.vm.ds_modulus(stored_location_id=2)
                else:
                    self.vm.ds_modulus()

        elif submode == 3:
            if args[0] == "FIZZ":
                self.vm.ds_store(stored_location_id=1)
            elif args[0] == "BUZZ":
                self.vm.ds_store(stored_location_id=2)
            elif args[0] == "FIZZBUZZ":
                if args[1] == "FIZZ":
                    self.vm.ds_jump_to(stored_location_id=1)
                else:
                    self.vm.ds_jump_to(stored_location_id=2)

    def _op_io(self, submode, args):
        """Execute an Input/Output operation
        """
        stored_loc = self.vm.sp
        locargs = len(args) > 1
        if locargs:
            if args[1] == "FIZZ":
                stored_loc = self.vm.stored_sp1
            else:
                stored_loc = self.vm.stored_sp2
        if submode == 1:
            print(self.vm.stack[stored_loc])
        elif submode == 2:
            print(chr(self.vm.stack[stored_loc]), end="")
        elif submode == 3:
            if locargs and args[0] == "FIZZBUZZ":
                varnum = "".join("0" if fb == "FIZZ" else "1"
                                 for fb in args[1:])
                self.vm.stack[self.vm.sp] = int(varnum, 2)
            else:
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
                self.vm.stack[self.vm.sp] = val

    def _op_flow(self, submode, args):
        """Execute a Flow Control operation
        """
        if submode == 1:
            if args[0] not in self.vm.labels:
                self.vm.labels[args[0]] = self.vm.ip
            self.vm.ip += 1
        elif submode == 2:
            if args[1] not in self.vm.labels:
                print("Error: label does not exist!")
                return

            jump = (args[0] == "FIZZ" and self.vm.stack[self.vm.sp] != 0 or
                    args[0] == "BUZZ" and self.vm.stack[self.vm.sp] == 0 or
                    args[0] == "FIZZBUZZ")
            if jump:
                self.vm.ip = self.vm.labels[args[1]]
            else:
                self.vm.ip += 1

        if submode == 3:
            return 0

    def run_file(self, filename):
        """Parse the FizzBuzzLang script and attempt to execute it
        """

        with open(filename) as prog:
            code = prog.readlines()

        while True:
            if self.vm.ip == len(code):
                print("Error: Expected statement")
                break

            mode, submode, args = self._parse_tokens(
                code[self.vm.ip], filename, self.vm.ip)
            if mode == 1:
                self._op_stack(submode, args)
                self.vm.ip += 1
            elif mode == 2:
                self._op_io(submode, args)
                self.vm.ip += 1
            elif mode == 3:
                bv = self._op_flow(submode, args)
                if bv == 0:
                    break
            else:
                self.vm.ip += 1

            if self.vm.debug:
                print(self.vm.labels, self.vm.stored_sp1, self.vm.stored_sp2)
                print(mode, submode, args)
                print(self.vm.stack, self.vm.sp, self.vm.ip)
