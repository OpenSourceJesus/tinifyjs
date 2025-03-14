def IndexOfAny (string : str, findAny : list[str], startIndex = 0):
	output = len(string)
	for find in findAny:
		indexOfFind = string.find(find, startIndex)
		if indexOfFind != -1:
			output = min(indexOfFind, output)
	if output == len(string):
		return -1
	return output

def IndexOfMatchingRightChar (string : str, leftChar : str, rightChar : str, charIndex : int):
	parenthesisTier = 1
	indexOfParenthesis = charIndex
	while indexOfParenthesis != -1:
		indexOfParenthesis = IndexOfAny(string, [ leftChar, rightChar ], indexOfParenthesis + 1)
		if indexOfParenthesis != -1:
			if string[indexOfParenthesis] == leftChar:
				parenthesisTier += 1
			else:
				parenthesisTier -= 1
				if parenthesisTier == 0:
					return indexOfParenthesis
	return -1

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

# I doubt this method works in all cases
def IndicesOfEnclosingStringStartEnd (string : str, charIndex : int):
	enclosingBacktickIndices = IndicesOfEnclosingChars(string, '`', charIndex)
	if enclosingBacktickIndices:
		return enclosingBacktickIndices
	enclosingSingleQuoteIndices = IndicesOfEnclosingChars(string, "'", charIndex)
	enclosingDoubleQuoteIndices = IndicesOfEnclosingChars(string, '"', charIndex)
	if enclosingSingleQuoteIndices:
		if not IndicesOfEnclosingChars(string, '"', enclosingSingleQuoteIndices[0]) and not IndicesOfEnclosingChars(string, '"', enclosingSingleQuoteIndices[1]):
			return enclosingSingleQuoteIndices
	elif enclosingDoubleQuoteIndices:
		if not IndicesOfEnclosingChars(string, "'", enclosingDoubleQuoteIndices[0]) and not IndicesOfEnclosingChars(string, "'", enclosingDoubleQuoteIndices[1]):
			return enclosingDoubleQuoteIndices
	return None