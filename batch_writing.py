for i in range(2, 72, 1):
    i=i/2
    print(i, end="")
    print(', ', end="")
    print(i, end="")
    print(', ', end="")
    print(i, end="")
    print(', ', end="")

for i in range(2, 72, 1):
    i=i/2
    print(round(i* .142, 3),', ', end="", sep='')
    print(round(i* .142/2, 3),', ', end="", sep='')
    print(round(i* .142/4, 3),', ', end="", sep='')