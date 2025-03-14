import sys, requests, subprocess
from Main import *

results = {}

def Compress (filePath : str, resultId : str):
    cmd = ['gzip', '--keep', '--force', '--verbose', '--best', filePath]
    subprocess.check_call(cmd)
    results[resultId] = len(open(filePath + '.gz', 'rb').read())

inputPath = '/tmp/tinifyjs Benchmark Input.js'
open(inputPath, 'w').write(text)
results['tinifyjs'] = len(open(outputPath, 'r').read())
outputPathPrefix = '/tmp/tinifyjs Benchmark Output'
js = subprocess.run(['uglifyjs', inputPath, '-m'], capture_output = True).stdout
outputPath = outputPathPrefix + '_uglifyjs.js'
open(outputPath, 'wb').write(js)
Compress (outputPath, 'uglifyjs')
js = subprocess.run(['terser', inputPath, '--compress', '--m', '--mangle-props'], capture_output = True).stdout
outputPath = outputPathPrefix + '_terser.js'
open(outputPath, 'wb').write(js)
Compress (outputPath, 'terser')
outputPath = outputPathPrefix + '_roadroller.js'
subprocess.run(['npx', 'roadroller', inputPath, '-o', outputPath])
Compress (outputPath, 'roadroller')
response = requests.post('https://www.toptal.com/developers/javascript-minifier/api/raw', data = dict(input = js)).text
outputPath = outputPathPrefix + '_javascript-minifier.js'
open(outputPath, 'w').write('{}'.format(response))
Compress (outputPath, 'javascript-minifier')
print(results)