def GetEnclosingIndices (string : str, encloser : str, charIndex : int):
	if charIndex < len(encloser) or charIndex == len(string) - len(encloser):
		return None
	isEnclosed = False
	prevIndexOfEncloser = -1
	indexOfEncloser = -1
	while True:
		indexOfEncloser = string.find(encloser, indexOfEncloser + 1)
		if indexOfEncloser > charIndex:
			if isEnclosed:
				return (prevIndexOfEncloser, indexOfEncloser)
			else:
				return None
		elif indexOfEncloser != -1:
			isEnclosed = not isEnclosed
		elif isEnclosed:
			return (prevIndexOfEncloser, indexOfEncloser)
		else:
			return None
		prevIndexOfEncloser = indexOfEncloser

def IsInString (string : str, charIndex : int):
	if charIndex == 0 or charIndex == len(string) - 1:
		return False
	enclosingSingleQuoteIndices = GetEnclosingIndices(string, "'", charIndex)
	enclosingDoubleQuoteIndices = GetEnclosingIndices(string, '"', charIndex)
	if enclosingSingleQuoteIndices:
		if not GetEnclosingIndices(string, '"', enclosingSingleQuoteIndices[0]) and not GetEnclosingIndices(string, '"', enclosingSingleQuoteIndices[1]):
			return True
	elif enclosingDoubleQuoteIndices:
		if not GetEnclosingIndices(string, "'", enclosingDoubleQuoteIndices[0]) and not GetEnclosingIndices(string, "'", enclosingDoubleQuoteIndices[1]):
			return True
	else:
		return False