import sys
from StringExtensions import *

TEXT_INDICATOR = '-t='
INPUT_INDICATOR = '-i='
OUTPUT_INDICATOR = '-o='
text = ''
OUTPUT_PREFIX = '''m={}
for(o of [Element,Node]){for(n of Object.keys(o.prototype)){a=n[0]+n[n.length-1]
try{if(!(a in m))o.prototype[a]=o.prototype[n]
m[a]=1}catch(e){}}}'''
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
outputWithPrefix = OUTPUT_PREFIX + output.replace('setAttribute', 'se').replace('getAttribute', 'ge').replace('appendChild', 'ad')
if len(output) > len(outputWithPrefix):
	output = outputWithPrefix
if outputPath:
	open(outputPath, 'w').write(output)
else:
	print(output)