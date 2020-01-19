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

    def ds_duplicate_data_item(self):
        """Duplicate the pointed to stack element and move pointer forward

        If pointing to the top of the stack, it will be extended.
        Otherwise, the next item will be overwritten.

        TODO: Address the fact that this op is currently undocumented
        """
        self.ds_pointer_forward()
        self.stack[self.sp] = self.stack[self.sp-1]


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
                self.vm.ds_duplicate_data_item()

        elif submode == 2:
            locargs = len(args) > 1
            if locargs:
                if args[1] == "FIZZ":
                    stored_loc = self.vm.stored_sp1
                else:
                    stored_loc = self.vm.stored_sp2

            if args[0] == "FIZZ":
                if locargs:
                    self.vm.stack[self.vm.sp] += self.vm.stack[stored_loc]
                else:
                    self.vm.stack[self.vm.sp] += 1
            elif args[0] == "BUZZ":
                if locargs:
                    self.vm.stack[self.vm.sp] -= self.vm.stack[stored_loc]
                else:
                    self.vm.stack[self.vm.sp] -= 1
            elif args[0] == "FIZZBUZZ":
                if self.vm.sp + 1 == len(self.vm.stack):
                    self.vm.stack.append(0)
                if locargs:
                    divisor = self.vm.stack[stored_loc]
                else:
                    divisor = self.vm.stack[self.vm.sp - 1]
                self.vm.stack[self.vm.sp + 1] = self.vm.stack[self.vm.sp] % divisor
                self.vm.sp += 1

        elif submode == 3:
            if args[0] == "FIZZ":
                self.vm.stored_sp1 = self.vm.sp
            elif args[0] == "BUZZ":
                self.vm.stored_sp2 = self.vm.sp
            elif args[0] == "FIZZBUZZ":
                if args[1] == "FIZZ":
                    self.vm.sp = self.vm.stored_sp1
                else:
                    self.vm.sp = self.vm.stored_sp2

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
