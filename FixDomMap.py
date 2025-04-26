import os

_thisDir = os.path.split(os.path.abspath(__file__))[0]
_memberRemapFilePath = os.path.join(_thisDir, 'DomMap') 
_memberRemapFileTxt = open(_memberRemapFilePath, 'r').read()
memberRemap = {}
memberRemapWithNameCopies = []
for line in _memberRemapFileTxt.split('\n'):
	parts = line.split()
	if parts != []:
		name = parts[0]
		newName = parts[1]
		if len(parts) > 2:
			parts.remove(name)
			name = parts[0]
			newName = parts[1]
			line = name + ' ' + newName
		if len(name) > 2 and len(newName) < 3:
			if name in memberRemap:
				if line.startswith(name + ' '):
					memberRemapWithNameCopies.append(name)
			else:
				memberRemap[name] = newName
for i, name in enumerate(memberRemapWithNameCopies):
	if i < len(memberRemapWithNameCopies) - 1 and name in memberRemapWithNameCopies[i + 1 :] and name in memberRemap:
		del memberRemap[name]
sortedNames = sorted(memberRemap.keys(), key = len, reverse = True)
sortedDomMap = dict(zip(sortedNames, [memberRemap[key] for key in sortedNames]))
newTxt = ''
for name, newName in sortedDomMap.items():
	if newName not in ['if', 'do', 'of', 'in']:
		newTxt += name + ' ' + newName + '\n'
open(_memberRemapFilePath, 'w').write(newTxt[: -1])