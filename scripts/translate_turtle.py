import turtle
import time

s = turtle.getscreen()
t = turtle.Turtle()
turtle.title("Turtle Translator")
t.home()
t.left(90)
time.sleep(2)
with open("turtle", "r") as file:
	content = file.readlines()
	for i in content:
		i = i.strip()
		if i == "":
			time.sleep(2)
			t.clear()
			t.home()
			t.left(90)
			t.clear()
		if "droite" in i:
			t.right(int(i.split(" ")[-2]))
		if "gauche" in i:
			t.left(int(i.split(" ")[-2]))
		if "Avance" in i:
			t.forward(int(i.split(" ")[-2]))
		if "Recule" in i:
			t.backward(int(i.split(" ")[-2]))
