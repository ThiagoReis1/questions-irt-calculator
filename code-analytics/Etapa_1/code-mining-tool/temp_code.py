from numpy import *
compra = input("compras").upper().split(",")
qtds = zeros(4, dtype=int)
for x in compra:
	if x == "A":
		qtds[0]+=1
	if x == "B":
		qtds[1]+=1
	if x == "L":
		qtds[2]+=1
	elif x == "H":
		qtds[3]+=1
print(qtds)
