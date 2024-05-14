'''test function for reading txt'''
with open('exports/CORNING SHELL.txt', mode='r', encoding='utf-8') as file:    
    items = file.readlines()
    for i, item in enumerate(items):
        print(i, item)
