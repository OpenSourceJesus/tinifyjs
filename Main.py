import sys, os
from StringExtensions import *

TEXT_INDICATOR = '-t='
INPUT_INDICATOR = '-i='
OUTPUT_INDICATOR = '-o='
REMAP_CODE = '''m={}
for(o of [Element,Node,String]){for(n of Object.getOwnPropertyNames(o.prototype)){s=0
e=n.length-1
a=n[s]+n[e]
while(a in m){s++
e--
a=n[s]+n[e]}try{o.prototype[a]=o.prototype[n]
m[a]=1
console.log(n,a)}catch(e){}}}'''
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

indicesOfEnclosingString = None
for i, char in enumerate(text):
	if not indicesOfEnclosingString:
		indicesOfEnclosingString = IndicesOfEnclosingStringQuotes(text, i)
	if (indicesOfEnclosingString and i < indicesOfEnclosingString[1]) or (char not in '\t\n' and (i == 0 or (i > 0 and (char != ' ' or text[i - 1] != ' ')))):
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