#1
''''
lista = [7.5, 8.0, 6.0, 9.5, 5.0]
lista.append(8.5)
lista[4] = 6.5
print (lista)
print (min(lista)) 
print (max(lista))
'''
#2
"""
alunos1 = ["Pedro", "Rai", "Marcos", "Bernardo"]
for alunos in enumerate(alunos1):
    print(alunos)
"""
#3
"""
numeros = [3, 17, 8, 42, 5, 100, 23, 66, 11, 99]
for num in numeros:
    if num % 2 == 0:
        print(num)
print("------------------")
for num2 in numeros:
    if num2 >= 20:
        print(num2)
print("------------------")
num3 = sum(numeros)
print (num3)
"""

#4
'''
lista = list(range(11))
print (lista)
print (lista[:4])
print (lista[8:])
for par in lista:
    if par % 2 == 0:
        print(par)
'''
#5

'''
turma = [
    ["Ana", 8.5],
    ["Beto", 7.0],
    ["Carlos", 9.2],
    ["Diana", 6.5]
]


for aluno in turma:
    nome = aluno[0]
    nota = aluno[1]
    print(f"{nome} tirou {nota}")
'''
#6
"""
turma = [
    ["Ana", 8.5],
    ["Beto", 7.0],
    ["Carlos", 9.2],
    ["Diana", 6.5],
    ["1", 1.5],
    ["2", 5.5],
    ["3", 4.5]
]


for aluno in turma:
    nome = aluno[0]
    nota = aluno[1]
    print(f"{nome} tirou {nota}")
print("---------------")
for aluno in turma:
    if aluno > 6:
        print(list[6:])
"""

#tupla ------

#7
"""
aluno = ('Lucas', '3A', 8.7)
nome, turma, media = aluno
print(f"Aluno: {nome} | Turma: {turma} | Média: {media}")
"""
#8

produtos = [('Camiseta', 49.90), ('Calça', 89.90), ('Tênis', 199.90)]
for nome, preco in produtos:
    print(f"Produto: {nome} | Preço: R$ {preco:.2f}")
