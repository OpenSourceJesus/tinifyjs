import sys, requests, subprocess
from Main import *

results = {}
inputPath = '/tmp/tinifyjs Benchmark Input.js'
open(inputPath, 'w').write(text)
results['tinifyjs'] = len(open(outputPath + '.gz', 'rb').read())
outputPathPrefix = '/tmp/tinifyjs Benchmark Output'
js = subprocess.run(['uglifyjs', inputPath, '-m'], capture_output = True).stdout
outputPath = outputPathPrefix + '_uglifyjs.js'
open(outputPath, 'wb').write(js)
results['uglifyjs'] = len(Compress(outputPath))
outputPath = outputPathPrefix + '_roadroller.js'
subprocess.run(['npx', 'roadroller', inputPath, '-o', outputPath])
results['roadroller'] = len(Compress(outputPath))
js = subprocess.run(['terser', inputPath, '--compress', '--m', '--mangle-props'], capture_output = True).stdout
outputPath = outputPathPrefix + '_terser.js'
open(outputPath, 'wb').write(js)
results['terser'] = len(Compress(outputPath))
outputPath = outputPathPrefix + '_closure.js'
subprocess.run(['npx', 'google-closure-compiler', '--js=' + inputPath, '--js_output_file=' + outputPath])
results['closure'] = len(Compress(outputPath))
response = requests.post('https://www.toptal.com/developers/javascript-minifier/api/raw', data = dict(input = js)).text
outputPath = outputPathPrefix + '_javascript-minifier.js'
open(outputPath, 'w').write('{}'.format(response))
results['javascript-minifier'] = len(Compress(outputPath))
print(results)