import os

_thisDir = os.path.split(os.path.abspath(__file__))[0]
_memberRemapFilePath = os.path.join(_thisDir, 'MemberRemap') 
_memberRemapFileText = open(_memberRemapFilePath, 'r').read()
memberRemap = {}
dontUseNames = []
for line in _memberRemapFileText.split('\n'):
	parts = line.split()
	if parts != []:
		name = parts[0]
		newName = parts[1]
		if len(parts) > 2:
			parts.remove(name)
			line = name + ' ' + newName
		if len(name) < 3:
			dontUseNames.append(name)
		if name in memberRemap:
			if line.startswith(name + ' '):
				dontUseNames.append(name)
				break
		else:
			memberRemap[name] = newName
for name in dontUseNames:
	del memberRemap[name]
sortedNames = sorted(memberRemap.keys(), key = len, reverse = True)
sortedMemberRemap = dict(zip(sortedNames, [memberRemap[key] for key in sortedNames]))
newText = ''
for name, newName in sortedMemberRemap.items():
	newText += name + ' ' + newName + '\n'
open(_memberRemapFilePath, 'w').write(newText[: -1])