def IndicesOfEnclosingChars (string : str, encloser : str, charIndex : int):
	if charIndex < len(encloser) or charIndex >= len(string) - len(encloser):
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

# I doubt this method works in all situations
def IndicesOfEnclosingStringQuotes (string : str, charIndex : int):
	enclosingSingleQuoteIndices = IndicesOfEnclosingChars(string, "'", charIndex)
	enclosingDoubleQuoteIndices = IndicesOfEnclosingChars(string, '"', charIndex)
	if enclosingSingleQuoteIndices:
		if not IndicesOfEnclosingChars(string, '"', enclosingSingleQuoteIndices[0]) and not IndicesOfEnclosingChars(string, '"', enclosingSingleQuoteIndices[1]):
			return enclosingSingleQuoteIndices
	elif enclosingDoubleQuoteIndices:
		if not IndicesOfEnclosingChars(string, "'", enclosingDoubleQuoteIndices[0]) and not IndicesOfEnclosingChars(string, "'", enclosingDoubleQuoteIndices[1]):
			return enclosingDoubleQuoteIndices
	return None