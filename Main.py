import os, sys, string, random
from StringExtensions import *

TEXT_INDICATOR = '-t='
INPUT_INDICATOR = '-i='
OUTPUT_INDICATOR = '-o='
REMAP_CODE = '''m={}
for(o of [Element,Node,String,Array,Document]){p=o.prototype
for(n of Object.getOwnPropertyNames(p)){s=0
e=n.length-1
a=n[s]
while(a in m){s++
a=n[s]+n[e]
e--}try{p[a]=p[n]
m[a]=1}catch(e){}}}'''
OKAY_NAME_CHARS = list(string.ascii_letters + '$_')
OKAY_NAME_CHARS.remove('m')
WHITESPACE_EQUIVALENT = string.whitespace + ';'
MEMBER_REMAP = {}
_thisDir = os.path.split(os.path.abspath(__file__))[0]
memberRemap = open(os.path.join(_thisDir, 'MemberRemap'), 'r').read()
for line in memberRemap.split('\n'):
	clauses = line.split()
	MEMBER_REMAP[clauses[0]] = clauses[1]
text = ''
output = ''
outputPath = None
unusedNames = []
unusedNames.extend(OKAY_NAME_CHARS)
mangledMembers = {}
currentClause = ''
prevClause = ''
indicesOfEnclosingStringStartEnd = None

for arg in sys.argv:
	if arg.startswith(TEXT_INDICATOR):
		text += arg[len(TEXT_INDICATOR) :]
	elif arg.startswith(INPUT_INDICATOR):
		text += open(arg[len(INPUT_INDICATOR) :], 'r').read()
	elif arg.startswith(OUTPUT_INDICATOR):
		outputPath = arg[len(OUTPUT_INDICATOR) :]

for i, char in enumerate(text):
	if not indicesOfEnclosingStringStartEnd:
		indicesOfEnclosingStringStartEnd = indicesOfEnclosingStringStartEndStartEnd(text, i)
	if not indicesOfEnclosingStringStartEnd or i > indicesOfEnclosingStringStartEnd[1]:
		endClauseChars = string.punctuation.replace('_', '').replace('$', '') + WHITESPACE_EQUIVALENT
		for digit in string.digits:
			if currentClause.startswith(digit):
				endClauseChars += string.digits
				break
		if char in endClauseChars:
			if currentClause in mangledMembers:
				output = output[: -len(currentClause)] + mangledMembers[currentClause]
			if prevClause in ['let', 'var', 'function'] and currentClause not in mangledMembers:
				while len(unusedNames) == 0:
					unusedName = random.choice(OKAY_NAME_CHARS) + random.choice(OKAY_NAME_CHARS)
					if unusedName not in MEMBER_REMAP.values() and unusedName not in mangledMembers and unusedName not in ['if', 'do']:
						unusedNames.append(unusedName)
				mangledMembers[currentClause] = unusedNames.pop(random.randint(0, len(unusedNames) - 1))
				output = output[: -len(currentClause)] + mangledMembers[currentClause]
			elif prevClause == 'for':
				
			prevClause = currentClause
			currentClause = ''
		else:
			currentClause += char
	if (indicesOfEnclosingStringStartEnd and i < indicesOfEnclosingStringStartEnd[1]) or (char not in WHITESPACE_EQUIVALENT and i == 0) or (char in WHITESPACE_EQUIVALENT and (text[i - 1] not in WHITESPACE_EQUIVALENT or prevClause in ['return', 'let', 'var', 'function', 'else', 'of'])) or char in string.ascii_letters + string.digits + string.punctuation:
		output += char
remappedOutput = output
for key, value in MEMBER_REMAP.items():
	remappedOutput = remappedOutput.replace('.' + key, '.' + value)
	remappedOutput = remappedOutput.replace('[' + key + ']', '[' + value + ']')
remappedOutput = REMAP_CODE + remappedOutput
if len(output) > len(remappedOutput):
	output = remappedOutput
if outputPath:
	open(outputPath, 'w').write(output)
else:
	print(output)