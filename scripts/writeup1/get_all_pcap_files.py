import os
import re

main = {}

for file in os.listdir("ft_fun"):
	with open(f"ft_fun/{file}", "r") as f:
		code = f.read()
		# print(code)
		result = re.findall(r'//file([0-9]*)', code)
		main[int(result[0])] = code

with open("main.c", "w+") as f:
	for value in sorted(main.items()):
		f.write(str(value[1]) + "\n")
