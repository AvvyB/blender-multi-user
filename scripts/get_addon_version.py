import re

init_py =  open("multi_user/__init__.py").read()
version = re.search("\d+, \d+, \d+", init_py).group(0)
digits = version.split(',')
print('.'.join(digits).replace(" ",""))