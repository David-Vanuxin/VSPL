import sys
import re

class SyntaxErr(Exception):
    def __init__(self, msg="", str_number=0, code_str=""):
        message = f"Ошибка синтаксиса на строке {str_number+1}:\n{code_str}\n{msg}"
        super().__init__(message)


class RuntimeErr(Exception):
    def __init__(self, cmd, msg):
        message = f"Ошибка времени выполнения\n{str(cmd)}\n{msg}"
        super().__init__(message)

class Command(object):
	def __init__(self, command, cmd_number):
		super(Command, self).__init__()
		self.number = cmd_number
		self.operands = []
		self.src_code = command

		if command[0:2] == "//":
			self.cmd_type = "comment"
			return

		res = re.match(r"^\S+", command)
		if res != None: self.cmd_type = res.group(0)
		else:
			return None

		command = re.sub(self.cmd_type + " ", "", command)
		command = re.sub(r"\s+", "", command)

		self.operands = command.split(",")

		for i in range(0, len(self.operands)):
			if self.operands[i][0] == "#":
				try:
					if len(self.operands[i]) > 1: 
						self.operands[i] = ("memcell", int(self.operands[i][1:]))
					else:
						raise SyntaxErr()
				except (ValueError, SyntaxErr):
					raise SyntaxErr("Недопустимые символы для записи номера ячейки памяти", self.number, self.src_code)
				else:
					continue

			try: 
				self.operands[i] = ("int", int(self.operands[i]))
			except ValueError:
			 	raise SyntaxErr("Недопустимые символы для записи чисел", self.number, self.src_code)

	def __str__(self):
		return f'строка {self.number + 1}: {self.src_code}'


class Process(object):
	def __init__(self, commands, debug_mode):
		super(Process, self).__init__()

		self.debug_mode = debug_mode

		self.memory = dict()

		self.cmds_list = []

		n = 0
		for cmd in commands:
			if cmd == "":
				raise SyntaxErr("Пустых строк не должно быть", n, "...")

			try:
				self.cmds_list.append(Command(cmd, n))
			except SyntaxErr as e:
				print(e)
				print()
			n += 1

	def run(self):
		n = 0
		while True:
			if n == len(self.cmds_list):
				break

			cmd = self.cmds_list[n]

			if cmd.cmd_type != "comment" and self.debug_mode:
				print(cmd.number + 1, cmd.operands, self.memory)

			if cmd.cmd_type == "comment":
				n += 1
				continue
			elif cmd.cmd_type == "out":
				self.output(cmd)
			elif cmd.cmd_type == "store":
				self.store(cmd)
			elif cmd.cmd_type == "get":
				self.get(cmd)
			elif cmd.cmd_type == "eql":
				self.compare(cmd, 0)
			elif cmd.cmd_type == "less":
				self.compare(cmd, 1)
			elif cmd.cmd_type == "more":
				self.compare(cmd, 2)
			elif cmd.cmd_type == "goto":
				n = cmd.operands[0][1] - 1
				continue
			elif cmd.cmd_type == "jmp":
				if self.memory[cmd.operands[0][1]] == 1:
					n = cmd.operands[1][1] - 1
					continue
			elif cmd.cmd_type == "add":
				self.addition(cmd, 0)
			elif cmd.cmd_type == "sub":
				self.addition(cmd, 1)
			elif cmd.cmd_type == "not":
				self.logical_not(cmd)
			elif cmd.cmd_type == "and":
				self.and_or(cmd, 0)
			elif cmd.cmd_type == "or":
				self.and_or(cmd, 1)
			else:
				print(f"Неизвестная команда '{cmd.cmd_type}'")
				sys.exit(3)

			n += 1

	def output(self, cmd):
		for op in cmd.operands:
			if op[0] == "int": 
				print(op[1])
			elif op[0] == "memcell":
				print(self.memory[op[1]])
				# self.memory[op[1]] += 1 

	def store(self, cmd):
		if cmd.operands[0][0] != 'memcell':
			try:
				self.memory[cmd.operands[1][1]] = cmd.operands[0][1]
			except KeyError:
				raise RuntimeErr(cmd, f"Ошибка доступа к памяти по адресу {cmd.operands[1][1]}")
		else:
			try:
				self.memory[cmd.operands[1][1]] = self.memory[cmd.operands[0][1]]
			except KeyError:
				raise RuntimeErr(cmd, f"Ошибка доступа к памяти по адресу {cmd.operands[1][1]} либо {cmd.operands[0][1]}")

	def get(self, cmd):
		inp = input("> ")
		try:
			self.memory[cmd.operands[0][1]] = int(inp)
		except ValueError:
			raise RuntimeErr(cmd, f'строка "{inp}" не подходит под символьное представление числа')

	def compare(self, cmd, flag):
		x = cmd.operands[0]
		y = cmd.operands[1]
		z = cmd.operands[2]

		if cmd.operands[0][0] == 'memcell':
			x = self.memory[x[1]]
		else: x = cmd.operands[0][1]

		if cmd.operands[1][0] == 'memcell':
			y = self.memory[y[1]]
		else: y = cmd.operands[1][1]

		if flag == 0:
			self.memory[z[1]] = int(x == y)
		elif flag == 1:
			self.memory[z[1]] = int(x < y)
		elif flag == 2:
			self.memory[z[1]] = int(x > y)

	def addition(self, cmd, flag):
		x = cmd.operands[0]
		y = cmd.operands[1]
		z = cmd.operands[2]

		if cmd.operands[0][0] == 'memcell':
			x = self.memory[x[1]]
		else: x = cmd.operands[0][1]

		if cmd.operands[1][0] == 'memcell':
			y = self.memory[y[1]]
		else: y = cmd.operands[1][1]

		if flag == 0:
			self.memory[z[1]] = int(x + y)
		elif flag == 1:
			self.memory[z[1]] = int(x - y)

	def logical_not(self, cmd):
		if cmd.operands[0][0] == 'memcell':
			x = self.memory[cmd.operands[0][1]]

		if x == 1: self.memory[cmd.operands[0][1]] = 0
		elif x == 0: self.memory[cmd.operands[0][1]] = 1
		else:
			raise RuntimeErr(cmd, f'оператор "not" применим только к значениям 0 и 1, передано: {x}')

	def and_or(self, cmd, flag):
		x = cmd.operands[0]
		y = cmd.operands[1]
		z = cmd.operands[2]

		if cmd.operands[0][0] == 'memcell':
			x = self.memory[x[1]]

		if cmd.operands[1][0] == 'memcell':
			y = self.memory[y[1]]

		if (x == 1 or x == 0) and (y == 1 or y == 0):
			if flag == 0:
				self.memory[z[1]] = x and y
			else:
				self.memory[z[1]] = x or y
		else:
			raise RuntimeErr(cmd, f'операторы "and" и "or" применимы только к значениям 0 и 1, переданы значения: {x} и {y}')

help_messange = f"""Very cool programming language by David Vanukhin
Usage: parser.py [script] [options]
	--debug  Print string number, operands and memory per every command
	--help   Print this help"""

def main():
	if len(sys.argv) < 2 or sys.argv[1] == "--help":
		print(help_messange)
		sys.exit(1)

	debug_mode = False
	if len(sys.argv) > 2 and sys.argv[2] == '--debug':
		debug_mode = True

	with open(sys.argv[1], "r") as file:
		code = file.read()

	commands = code.split("\n")

	try:
		proc = Process(commands, debug_mode)
		proc.run()
	except (RuntimeErr, SyntaxErr) as err:
		print(err)
		sys.exit(2)
	except KeyboardInterrupt:
		sys.exit(0)

if __name__ == '__main__':
	main()