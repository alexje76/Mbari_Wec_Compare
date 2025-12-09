for i in range(2, 9):
    print(i, end="")
    print('.0, ', end="")
    print(i, end="")
    print('.0, ', end="")
    print(i, end="")
    print('.0, ', end="")

for i in range(2, 9):
    print(round(i* .142, 3),', ', end="", sep='')
    print(round(i* .142/2, 3),', ', end="", sep='')
    print(round(i* .142/4, 3),', ', end="", sep='')