import sys, random
from itertools import permutations

TEXT_INDICATOR = '-t='
INPUT_INDICATOR = '-i='
RAND_CHAR_COUNT_INDICATOR = '-n='
txt = ''

def GetInfoToAddStrs (txt : str, strs : []):
	output = []
	txtWithoutStrs = txt
	strsCounts = []
	for string in strs:
		strIndex = -1
		strCount = 0
		while True:
			strIndex = txt.find(string, strIndex + len(string))
			if strIndex < 0:
				strsCounts.append(strCount)
				break
			strCount += 1
			txtWithoutStrs = txtWithoutStrs.replace(string, '')
	stepCount = 2
	while True:
		output = []
		for i in range(stepCount):
			output.extend(list(range(len(txt))))
			stepsPermutations = list(permutations(output, stepCount))
			for stepsPermutation in stepsPermutations:
				stepsPermutation_ = list(stepsPermutation)
				txtWithoutStrs_ = txtWithoutStrs
				for i, string in enumerate(strs):
					for i2 in range(strsCounts[i]):
						insertAt = stepsPermutation_[0] % (len(txtWithoutStrs_) + 1)
						txtWithoutStrs_ = txtWithoutStrs_[: insertAt] + string + txtWithoutStrs_[insertAt :]
						for i3 in range(len(stepsPermutation_) - 1, 0, -1):
							stepsPermutation_[i3 - 1] += stepsPermutation_[i3]
				if txtWithoutStrs_ == txt:
					return strsCounts + [stepsPermutation]
		stepCount += 1
	return None

for arg in sys.argv:
	if arg.startswith(TEXT_INDICATOR):
		txt += arg[len(TEXT_INDICATOR) :]
	elif arg.startswith(INPUT_INDICATOR):
		txt += open(arg[len(INPUT_INDICATOR) :], 'r').read()
	elif arg.startswith(RAND_CHAR_COUNT_INDICATOR):
		for i in range(int(arg[len(RAND_CHAR_COUNT_INDICATOR) :])):
			txt += random.choice(['0', '1'])

print(txt)
print(GetInfoToAddStrs(txt, ['1']))