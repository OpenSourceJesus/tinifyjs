import os, sys, atexit, random
from datetime import datetime
from itertools import permutations

TEXT_INDICATOR = '-t='
INPUT_INDICATOR = '-i='
RAND_TXT_LEN_INDICATOR = '-n='
DATA_DIR_PATH = os.path.join(os.path.expanduser('~'), 'tinifyjs Data')
INIT_TIME = datetime.now()
txt = ''
stepCnt = 2
startStepsPermutation = 0
currentStepsPermutation = 0
totalTime = INIT_TIME - INIT_TIME

def GetInfoToAddStrs (txt : str, strs : []):
	global stepCnt, startStepsPermutation
	txtWithoutStrs = txt
	strsCnts = []
	for string in strs:
		strIdx = -1
		strCnt = 0
		txtWithoutStrs = txtWithoutStrs.replace(string, '')
		while True:
			strIdx = txt.find(string, strIdx + len(string))
			if strIdx < 0:
				break
			strCnt += 1
		strsCnts.append(strCnt)
	potentialStepValues = list(range(len(txt) + 1)) + list(range(-1, -len(txt) - 1, -1))
	while True:
		stepsPermutations = list(permutations(potentialStepValues, stepCnt))
		for currentStepsPermutation, stepsPermutation in enumerate(stepsPermutations[startStepsPermutation :]):
			print(currentStepsPermutation)
			stepsPermutation_ = list(stepsPermutation)
			txtWithoutStrs_ = txtWithoutStrs
			for i2, string in enumerate(strs):
				for i3 in range(strsCnts[i2]):
					insertAt = stepsPermutation_[0] % (len(txtWithoutStrs_) + 1)
					txtWithoutStrs_ = txtWithoutStrs_[: insertAt] + string + txtWithoutStrs_[insertAt :]
					for i4 in range(len(stepsPermutation_) - 1, 0, -1):
						stepsPermutation_[i4 - 1] += stepsPermutation_[i4]
			if txtWithoutStrs_ == txt:
				return strsCnts + [stepsPermutation]
		startStepsPermutation = 0
		stepCnt += 1

for arg in sys.argv:
	if arg.startswith(TEXT_INDICATOR):
		txt += arg[len(TEXT_INDICATOR) :]
	elif arg.startswith(INPUT_INDICATOR):
		txt += open(arg[len(INPUT_INDICATOR) :], 'r').read()
	elif arg.startswith(RAND_TXT_LEN_INDICATOR):
		for i in range(int(arg[len(RAND_TXT_LEN_INDICATOR) :])):
			txt += random.choice(['0', '1'])

def OnExit ():
	saveInfo = str(stepCnt) + ',' + str(currentStepsPermutation) + ',' + str(datetime.now() - INIT_TIME + totalTime)
	if os.path.isdir(dataFilePath):
		dataTxt = '\n'.join(dataTxt.split('\n')[: -1]) + saveInfo
	else:
		dataTxt = txt + '\n' + saveInfo
	open(dataFilePath, 'w').write(dataTxt)

print(txt)
if not os.path.isdir(DATA_DIR_PATH):
	os.mkdir(DATA_DIR_PATH)
dataTxt = ''
dataFilePath = ''
for item in os.listdir(DATA_DIR_PATH):
	if os.path.isfile(item):
		dataTxt = open(item, 'r').read()
		if dataTxt.startswith(txt):
			dataFilePath = item
			break
if dataFilePath:
	loadInfo = dataTxt.split('\n')[-1].split(',')
	stepCnt = int(loadInfo[0])
	startStepsPermutation = int(loadInfo[1])
	totalTime = datetime(loadInfo[2])
else:
	dataFilePath = os.path.join(DATA_DIR_PATH, str(INIT_TIME))
txt_ = txt
chars = []
while txt_:
	char = txt_[0]
	chars.append(char)
	txt_ = txt_.replace(char, '')
atexit.register(OnExit)
print(GetInfoToAddStrs(txt, chars))