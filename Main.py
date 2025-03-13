import os, sys, string
from StringExtensions import *

TEXT_INDICATOR = '-t='
INPUT_INDICATOR = '-i='
OUTPUT_INDICATOR = '-o='
REMAP_CODE = '''m={}
for(o of [Element,Node,String,Array,Document]){for(n of Object.getOwnPropertyNames(o.prototype)){s=0
e=n.length-1
a=n[s]
while(a in m){s++
a=n[s]+n[e]
e--}try{o.prototype[a]=o.prototype[n]
m[a]=1}catch(e){}}}'''
_thisDir = os.path.split(os.path.abspath(__file__))[0]
text = ''
output = ''
outputPath = None

for arg in sys.argv:
	if arg.startswith(TEXT_INDICATOR):
		text += arg[len(TEXT_INDICATOR) :]
	elif arg.startswith(INPUT_INDICATOR):
		text += open(arg[len(INPUT_INDICATOR) :], 'r').read()
	elif arg.startswith(OUTPUT_INDICATOR):
		outputPath = arg[len(OUTPUT_INDICATOR) :]

unusedNames = list(string.ascii_letters)
unusedNames.remove('m')
lastUnusedNameValue = 128
mangledMembers = {}
currentClause = ''
prevClause = ''
indicesOfEnclosingString = None
for i, char in enumerate(text):
	if not indicesOfEnclosingString:
		indicesOfEnclosingString = IndicesOfEnclosingStringQuotes(text, i)
	if char in string.punctuation.replace('_', '').replace('$', '') + string.whitespace:
		if currentClause in mangledMembers:
			output = output[: -len(currentClause)] + mangledMembers[currentClause] + output[-len(currentClause) :]
		for char2 in string.whitespace:
			prevClause = prevClause.replace(char2, '')
		if prevClause in ['let', 'var', 'function'] and currentClause not in mangledMembers:
			if len(unusedNames) == 0:
				unusedNames.append(chr(lastUnusedNameValue))
				lastUnusedNameValue += 1
			print(prevClause, currentClause)
			mangledMembers[currentClause] = unusedNames.pop()
			output = output[: -len(currentClause)] + mangledMembers[currentClause]
		prevClause = currentClause
		currentClause = ''
	elif char in string.whitespace or not indicesOfEnclosingString or i > indicesOfEnclosingString[1]:
		currentClause += char
	if (indicesOfEnclosingString and i < indicesOfEnclosingString[1]) or (char not in string.whitespace and (i == 0 or (char not in string.whitespace or text[i - 1] not in string.whitespace))) or (char in string.whitespace and prevClause in ['return', 'let', 'var', 'function', 'else', 'of']):
		output += char
remappedOutput = output
memberRemap = open(os.path.join(_thisDir, 'MemberRemap'), 'r').read()
for line in memberRemap.split('\n'):
	clauses = line.split()
	remappedOutput = remappedOutput.replace('.' + clauses[0], '.' + clauses[1])
	remappedOutput = remappedOutput.replace('[' + clauses[0] + ']', '[' + clauses[1] + ']')
remappedOutput = REMAP_CODE + remappedOutput
if len(output) > len(remappedOutput):
	output = remappedOutput
if outputPath:
	open(outputPath, 'w').write(output)
else:
	print(output)