import itertools
import os

t = ["1", "2", "3", "5", "6"]
c = list(itertools.permutations(t, 5))
unq = set(c)
for i in unq:
	content = "Public speaking is very easy.\n1 2 6 24 120 720\n1 b 214\n9\nopekmq\n4 {}\n".format(' '.join(i))
	with open("soluce.txt", "w+") as f:
		f.write(content)
	os.system('./bomb soluce.txt > result')
	with open('result') as f:
		if 'BOOM' not in f.read():
			print(content.replace("\n", "").replace(" ", ""))
