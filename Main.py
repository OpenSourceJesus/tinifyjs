import os, sys, string, base64, random, subprocess
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
outputPath = '/tmp/tinifyjs Output.js'
unusedNames = []
unusedNames.extend(OKAY_NAME_CHARS)
mangledMembers = {}
usedNames = []
currentWord = ''
prevWord = ''
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
		indicesOfEnclosingStringStartEnd = IndicesOfEnclosingStringStartEnd(text, i)
	if not indicesOfEnclosingStringStartEnd or i > indicesOfEnclosingStringStartEnd[1]:
		endWordChars = string.punctuation.replace('_', '').replace('$', '') + WHITESPACE_EQUIVALENT
		for digit in string.digits:
			if currentWord.startswith(digit):
				endWordChars += string.digits
				break
		if char in endWordChars:
			if currentWord in mangledMembers:
				output = output[: -len(currentWord)] + mangledMembers[currentWord]
			if prevWord in ['let', 'var', 'function'] and currentWord not in mangledMembers and currentWord not in usedNames:
				if len(currentWord) > 1:
					while len(unusedNames) == 0:
						unusedName = random.choice(OKAY_NAME_CHARS) + random.choice(OKAY_NAME_CHARS)
						if unusedName not in MEMBER_REMAP.values() and unusedName not in mangledMembers and unusedName not in usedNames and unusedName not in ['if', 'do', 'of', 'in']:
							unusedNames.append(unusedName)
					mangledMembers[currentWord] = unusedNames.pop(random.randint(0, len(unusedNames) - 1))
					output = output[: -len(currentWord)] + mangledMembers[currentWord]
				else:
					usedNames.append(currentWord)
			prevWord = currentWord
			currentWord = ''
		else:
			currentWord += char
	if (indicesOfEnclosingStringStartEnd and i < indicesOfEnclosingStringStartEnd[1]) or (char in WHITESPACE_EQUIVALENT + string.punctuation and (text[i - 1] not in WHITESPACE_EQUIVALENT + string.punctuation or prevWord in ['return', 'while', 'else', 'for', 'let', 'var', 'function', 'if', 'do', 'of', 'in'])) or char in string.ascii_letters + string.digits + string.punctuation:
		if char in string.punctuation and text[i - 1] in WHITESPACE_EQUIVALENT:
			output = output[: -1]
		output += char
forIndex = -1
while True:
	forIndex = output.find('for', forIndex + 1)
	if forIndex == -1:
		break
	if not IndicesOfEnclosingStringStartEnd(output, forIndex):
		leftParenthesisIndex = output.find('(', forIndex)
		betweenForAndParenthesis = output[forIndex + 3 : leftParenthesisIndex]
		if len(betweenForAndParenthesis) == 0 or betweenForAndParenthesis.isspace():
			rightParenthesisIndex = IndexOfMatchingRightChar(output, '(', ')', leftParenthesisIndex)
			forClause = output[forIndex : rightParenthesisIndex + 1]
			if ' of ' in forClause:
				clauses = forClause.split(' of ')
				output = output[: forIndex] + '@' + clauses[0] + '~' + clauses[1] + '#' + output[rightParenthesisIndex + 2 :]
remappedOutput = output
for key, value in MEMBER_REMAP.items():
	remappedOutput = remappedOutput.replace('.' + key, '.' + value)
	remappedOutput = remappedOutput.replace('[' + key + ']', '[' + value + ']')
remappedOutput = REMAP_CODE + remappedOutput
if len(output) > len(remappedOutput):
	output = remappedOutput
open(outputPath, 'w').write(output)
print(output)
cmd = ['gzip', '--keep', '--force', '--verbose', '--best', outputPath]
subprocess.check_call(cmd)
jsZipped = open(outputPath + '.gz', 'rb').read()
jsBytes = base64.b64encode(jsZipped).decode('utf-8')
outputWithDecompression = '''u=async(u,t)=>{d=new DecompressionStream('gzip')
r=await fetch('data:application/octet-stream;base64,'+u)
b=await r.blob()
s=b.stream().pipeThrough(d)
o=await new Response(s).blob()
return await o.text()}
u("%s",1).then((j)=>{s=-1
while(True){s=j.find('@',s+1)
if(s<0)break
m=j.find('~',s)
e=j.find('#',m)
j=j.replace(j.slice(s,e),'for('+j.slice(s,m)+' of '+s.slice(m+1,e)+')')}
eval(j)})''' %jsBytes
if len(output) > len(outputWithDecompression):
	output = outputWithDecompression
open(outputPath, 'w').write(output)
cmd = ['gzip', '--keep', '--force', '--verbose', '--best', outputPath]
subprocess.check_call(cmd)
print(output)