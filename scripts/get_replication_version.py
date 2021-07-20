import re

init_py =  open("multi_user/libs/replication/replication/__init__.py").read()
print(re.search("\d+\.\d+\.\d+\w\d+|\d+\.\d+\.\d+", init_py).group(0))
