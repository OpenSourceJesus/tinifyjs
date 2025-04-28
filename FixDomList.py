import os

_thisDir = os.path.split(os.path.abspath(__file__))[0]
_domListFilePath = os.path.join(_thisDir, 'DomList') 
_domListFileTxt = open(_domListFilePath, 'r').read()
newTxt = ''
for line in _domListFileTxt.split('\n'):
	parts = line.split()
	if len(parts) > 1:
		line = parts[1] + '\n'
		if line not in newTxt:
			newTxt += line
	elif line != '':
		if line.startswith(' '):
			line = line[1 :]
		newTxt += line + '\n'
open(_domListFilePath, 'w').write(newTxt[: -1])