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
ADD_FOR_LOOPS_CODE = '''s=-1
while(True){s=j.find('@',s+1)
if(s<0)break
m=j.find('~',s)
o=j.find('^',m)
e=j.find('#',m)
if(o<0||o>e)j=j.replace(j.slice(s,e+1),'for('+j.slice(s,m)+' of '+s.slice(m+1,e)+')')
else j=j.replace(j.slice(s,e+1),'for('+j.slice(s,o)+''+s.slice(o+1,m)+s.slice(m+1,e)+')')}'''
OKAY_NAME_CHARS = list(string.ascii_letters + '$_')
OKAY_NAME_CHARS.remove('m')
WHITESPACE_EQUIVALENT = string.whitespace + ';'
MEMBER_REMAP = {}
_thisDir = os.path.split(os.path.abspath(__file__))[0]
memberRemap = open(os.path.join(_thisDir, 'MemberRemap'), 'r').read()
for line in memberRemap.split('\n'):
	parts = line.split()
	MEMBER_REMAP[parts[0]] = parts[1]
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

def Compress (filePath : str):
	cmd = ['gzip', '--keep', '--force', '--verbose', '--best', outputPath]
	subprocess.check_call(cmd)
	jsZipped = open(outputPath + '.gz', 'rb').read()
	return base64.b64encode(jsZipped).decode('utf-8')

def MergeVarDeclarations (code : str):
	varKeywordIndex = -1 
	while True:
		varKeywordIndex = code.find('var', varKeywordIndex + 1)
		if varKeywordIndex == -1:
			break
		if not IndicesOfEnclosingStringStartEnd(code, varKeywordIndex) and (varKeywordIndex == 0 or code[varKeywordIndex - 1] in string.whitespace + string.punctuation):
			pass

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
noForLoopsOutput = output
forIndex = -1
while True:
	forIndex = noForLoopsOutput.find('for', forIndex + 1)
	if forIndex == -1:
		break
	if not IndicesOfEnclosingStringStartEnd(noForLoopsOutput, forIndex) and (forIndex == 0 or noForLoopsOutput[forIndex - 1] in string.whitespace + string.punctuation):
		leftParenthesisIndex = noForLoopsOutput.find('(', forIndex)
		betweenForAndParenthesis = noForLoopsOutput[forIndex + 3 : leftParenthesisIndex]
		if len(betweenForAndParenthesis) == 0 or betweenForAndParenthesis.isspace():
			rightParenthesisIndex = IndexOfMatchingRightChar(noForLoopsOutput, '(', ')', leftParenthesisIndex)
			forClause = noForLoopsOutput[forIndex : rightParenthesisIndex + 1]
			if ' of ' in forClause:
				parts = forClause.split(' of ')
				noForLoopsOutput = noForLoopsOutput[: forIndex] + '@' + parts[0].strip() + '~' + parts[1].strip() + '#' + noForLoopsOutput[rightParenthesisIndex + 1 :]
			else:
				parts = forClause.split(';')
				if len(parts) > 2:
					part = parts[0]
					indexOfEquals = part.find('=')
					part1 = part[forIndex + len('for') : indexOfEquals].strip()
					part2 = part[indexOfEquals : -1].strip()
					part = parts[1]
					inequalityIndex = IndexOfAny(part, ['<', '>'])
					part3 = part[: inequalityIndex]
					part4 = part[inequalityIndex : -1]
					part = parts[2]
					operationIndex = IndexOfAny(part, ['++', '--', '+=', '-='])
					part5 = part[: operationIndex]
					noForLoopsOutput = noForLoopsOutput[: forIndex] + '@' + part1 + '~' + part2 + '`' + part3 + '^' + part4 + '\\' + part5 + '#' + noForLoopsOutput[rightParenthesisIndex + 1 :]
					print('YAY', noForLoopsOutput[: forIndex] + '@' + part1 + '~' + part2 + '`' + part3 + '^' + part4 + '\\' + part5 + '#')
					pass
remappedOutput = output
for key, value in MEMBER_REMAP.items():
	remappedOutput = remappedOutput.replace('.' + key, '.' + value)
	remappedOutput = remappedOutput.replace('[' + key + ']', '[' + value + ']')
remappedOutput = REMAP_CODE + remappedOutput
if len(output) > len(remappedOutput):
	output = remappedOutput
open(outputPath, 'w').write(output)
jsBytes = Compress(outputPath)
open(outputPath, 'w').write(noForLoopsOutput)
notForLoopsJsBytes = Compress(outputPath)
outputWithDecompression = '''u=async(u,t)=>{d=new DecompressionStream('gzip')
r=await fetch('data:application/octet-stream;base64,'+u)
b=await r.blob()
s=b.stream().pipeThrough(d)
o=await new Response(s).blob()
return await o.text()}
u("",1).then((j)=>{eval(j)})'''
if len(jsBytes) > len(notForLoopsJsBytes + ADD_FOR_LOOPS_CODE):
	print(noForLoopsOutput)
	jsBytes = notForLoopsJsBytes
	outputWithDecompression = outputWithDecompression.replace('eval', ADD_FOR_LOOPS_CODE + '\neval')
else:
	print(output)
outputWithDecompression = outputWithDecompression.replace('""', '"' + jsBytes + '"')
if len(output) > len(outputWithDecompression):
	output = outputWithDecompression
open(outputPath, 'w').write(output)
cmd = ['gzip', '--keep', '--force', '--verbose', '--best', outputPath]
subprocess.check_call(cmd)
print(output)