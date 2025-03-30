import os, sys, time, requests, subprocess, matplotlib.pyplot as plot

def GenPlot (dict_ : {}):
	spacing = .1
	currentXLoc = spacing / 2
	xLocs = []
	width = 1 / len(dict_) - spacing
	for i in range(len(dict_)):
		currentXLoc += width + spacing / len(dict_)
		xLocs.append(currentXLoc)
	plot.bar(x = xLocs, height = dict_.values(), width = width, tick_label = dict_.keys(), color = ['black', 'red', 'green', 'blue', 'yellow', 'purple'])
	plot.show()

timeResults = {}
sizeResults = {}
inputPath = '/tmp/tinifyjs Benchmark Input.js'
time_ = time.perf_counter()
from Main import *
timeResults['tinifyjs'] = time.perf_counter() - time_
open(inputPath, 'w').write(txt)
if compress:
	sizeResults['tinifyjs'] = len(Compress(outputPath))
else:
	sizeResults['tinifyjs'] = len(txt)
outputPathPrefix = '/tmp/tinifyjs Benchmark Output'
time_ = time.perf_counter()
js = subprocess.run(['uglifyjs', inputPath, '-m'], capture_output = True).stdout
timeResults['uglifyjs'] = time.perf_counter() - time_
outputPath = outputPathPrefix + '_uglifyjs.js'
open(outputPath, 'wb').write(js)
if compress:
	sizeResults['uglifyjs'] = len(Compress(outputPath))
else:
	sizeResults['uglifyjs'] = len(js)
outputPath = outputPathPrefix + '_roadroller.js'
time_ = time.perf_counter()
subprocess.run(['npx', 'roadroller', inputPath, '-o', outputPath])
timeResults['roadroller'] = time.perf_counter() - time_
if compress:
	sizeResults['roadroller'] = len(Compress(outputPath))
else:
	sizeResults['roadroller'] = len(open(outputPath, 'r').read())
time_ = time.perf_counter()
js = subprocess.run(['terser', inputPath, '--compress', '--m', '--mangle-props'], capture_output = True).stdout
timeResults['terser'] = time.perf_counter() - time_
outputPath = outputPathPrefix + '_terser.js'
open(outputPath, 'wb').write(js)
if compress:
	sizeResults['terser'] = len(Compress(outputPath))
else:
	sizeResults['terser'] = len(js)
outputPath = outputPathPrefix + '_closure.js'
time_ = time.perf_counter()
subprocess.run(['npx', 'google-closure-compiler', '--js=' + inputPath, '--js_output_file=' + outputPath])
timeResults['closure'] = time.perf_counter() - time_
if compress:
	sizeResults['closure'] = len(Compress(outputPath))
else:
	sizeResults['closure'] = len(open(outputPath, 'r').read())
outputPath = outputPathPrefix + '_javascript-minifier.js'
time_ = time.perf_counter()
response = requests.post('https://www.toptal.com/developers/javascript-minifier/api/raw', data = dict(input = js)).text
timeResults['javascript-minifier'] = time.perf_counter() - time_
js = '{}'.format(response)
open(outputPath, 'w').write(js)
if compress:
	sizeResults['javascript-minifier'] = len(Compress(outputPath))
else:
	sizeResults['javascript-minifier'] = len(js)

GenPlot (sizeResults)
GenPlot (timeResults)