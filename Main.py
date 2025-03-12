import sys
from StringExtensions import *

TEXT_INDICATOR = '-t='
INPUT_INDICATOR = '-i='
OUTPUT_INDICATOR = '-o='
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

for i, char in enumerate(text):
	if IsInString(text, i) or (char not in '\t\n' and (i == 0 or (i > 0 and (char != ' ' or text[i - 1] != ' ')))):
		output += char
if outputPath:
	open(outputPath, 'w').write(output)
else:
	print(output)