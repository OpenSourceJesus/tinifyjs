import os, sys, string, random, subprocess, tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser

JS_LANG = Language(tsjs.language())
PARSER = Parser(JS_LANG)
TEXT_INDICATOR = '-t='
INPUT_INDICATOR = '-i='
OUTPUT_INDICATOR = '-o='
OUTPUT_PREFIX = 'F="function ";F="return ";W="while(";E="else{";d=document;w=window;m=Math;eval(`'
REMAP_CODE = '''M={}
for(o of [Element,Node,String,Array,Document,Window]){p=o.prototype
for(n of Object.getOwnPropertyNames(p)){s=0
e=n.length-1
a=n[s]
${W}a in M){s++
a=n[s]+n[e]
e--}try{p[a]=p[n]
M[a]=1}catch(e){}}}'''
OKAY_NAME_CHARS = list(string.ascii_letters + '_')
JS_NAMES = ['Math', 'document', 'style', 'window']
WHITESPACE_EQUIVALENT = string.whitespace + ';'
MEMBER_REMAP = {}
_thisDir = os.path.split(os.path.abspath(__file__))[0]
_memberRemap = open(os.path.join(_thisDir, 'MemberRemap'), 'r').read()
for line in _memberRemap.split('\n'):
	parts = line.split()
	MEMBER_REMAP[parts[0]] = parts[1]
text = ''
output = ''
remappedOutput = ''
outputPath = '/tmp/tinifyjs Output.js'
currentFuncName = ''
currentFuncText = ''
currentFunc = None
currentRemappedFuncText = ''
currentFuncVarsDeclrsText = ''
currentRemappedFuncVarsDeclrsText = ''
currentVarDeclrText = ''
currentVarDeclr = None
currentRemappedVarDeclrText = ''
globalVarsDeclrsText = ''
globalRemappedVarsDeclrsText = ''
unusedNames = {}
unusedNames[currentFuncName] = []
unusedNames[currentFuncName].extend(OKAY_NAME_CHARS)
mangledMembers = {}
mangledMembers[currentFuncName] = {}
usedNames = {}
usedNames[currentFuncName] = ['F', 'R', 'W', 'E', 'd', 'w', 'm', 'M', 'if', 'do', 'of', 'in']

def WalkTree (node):
	global output, nodeText, currentFunc, mangledMembers, currentFuncName, remappedOutput, currentFuncText, currentVarDeclr, currentVarDeclrText, globalVarsDeclrsText, currentRemappedFuncText, globalRemappedVarsDeclrsText, currentRemappedVarDeclrText, currentFuncVarsDeclrsText, currentRemappedFuncVarsDeclrsText
	nodeText = node.text.decode('utf-8')
	print(node.type, nodeText)
	if node.children == []:
		mangleOrRemapResults = TryMangleOrRemapNode(node)
		remappedNodeText = mangleOrRemapResults[0]
		if mangleOrRemapResults[1]:
			nodeText = remappedNodeText
		isOfOrIn = node.type in ['of', 'in']
		if isOfOrIn:
			AddToOutputs (' ')
		elif node.type in ['let', 'var', 'const']:
			nodeText = 'var '
			remappedNodeText = nodeText
		elif node.type == 'function':
			nodeText = '${F}'
			remappedNodeText = nodeText
		elif node.type == 'return':
			nodeText = '${R}'
			remappedNodeText = nodeText
		elif node.type == 'while':
			nodeText = '${W}'
			remappedNodeText = nodeText
		elif node.type == 'else':
			nodeText = '${E}'
			remappedNodeText = nodeText
		if not currentFunc and not not currentVarDeclr:
			output += nodeText
			remappedOutput += remappedNodeText
		else:
			if currentVarDeclr:
				currentVarDeclrText += nodeText
				currentRemappedVarDeclrText += remappedNodeText
				if AtEndOfHierarchy(currentVarDeclr, node):
					currentFuncVarsDeclrsText += currentVarDeclrText + ','
					currentRemappedFuncVarsDeclrsText += currentRemappedVarDeclrText + ','
					currentVarDeclrText = ''
					currentRemappedVarDeclrText = ''
					currentVarDeclr = None
			if currentFunc and AtEndOfHierarchy(currentFunc, node):
				output += currentFuncVarsDeclrsText + currentFuncText
				remappedOutput += currentRemappedFuncVarsDeclrsText + currentRemappedFuncText
				currentFuncName = ''
				currentFuncText = ''
				currentFunc = None
				currentFuncVarsDeclrsText = ''
				currentRemappedFuncVarsDeclrsText = ''
				currentRemappedFuncText = ''
		siblingIdx = node.parent.children.index(node)
		if len(node.parent.children) > siblingIdx + 1:
			nextSiblingType = node.parent.children[siblingIdx + 1].type
			if node.type in ['new', 'delete'] or ((isOfOrIn or node.type in ['return', 'class', 'function','else']) and nextSiblingType not in ['{', '[']):
				AddToOutputs (' ')
		if (node.type == 'identifier' and node.parent.type == 'function_declaration') or (node.type == 'property_identifier' and node.parent.type == 'method_definition'):
			currentFuncName = nodeText
			currentFunc = node.parent
			unusedNames[nodeText] = []
			unusedNames[nodeText].extend(OKAY_NAME_CHARS)
			for unusedName in unusedNames['']:
				if unusedName in unusedNames[nodeText]:
					unusedNames[nodeText].remove(unusedName)
			usedNames[nodeText] = usedNames['']
			mangledMembers[currentFuncName] = mangledMembers['']
	elif node.type == 'variable_declarator':
		currentVarDeclr = node
	for n in node.children:
		WalkTree (n)
	if node.type in ['lexical_declaration', 'variable_declaration', 'expression_statement'] and not nodeText.endswith(';') and node.end_byte < len(text) - 1:
		AddToOutputs (';')

def AddToOutputs (add : str):
	global output, currentFuncText, remappedOutput, globalVarsDeclrsText, currentVarDeclrText, currentRemappedFuncText, globalRemappedVarsDeclrsText, currentRemappedVarDeclrText
	if currentVarDeclr:
		if currentFunc:
			globalVarsDeclrsText += add
			globalRemappedVarsDeclrsText += add
		else:
			currentVarDeclrText += add
			currentRemappedVarDeclrText += add
	elif currentFunc:
		currentFuncText += add
		currentRemappedFuncText += add
	else:
		output += add
		remappedOutput += add

def TryMangleOrRemapNode (node) -> ():
	nodeText = node.text.decode('utf-8')
	if node.type == 'identifier':
		if nodeText == 'document':
			return ('d', True)
		elif nodeText == 'window':
			return ('w', True)
		elif nodeText == 'Math':
			return ('m', True)
		return (TryMangleNode(node), True)
	elif node.type == 'property_identifier':
		if nodeText in MEMBER_REMAP:
			return (MEMBER_REMAP[nodeText], False)
		else:
			parentNodeText = node.parent.text.decode('utf-8')
			if node.parent.type in ['method_definition'] and parentNodeText not in usedNames[currentFuncName] + JS_NAMES:
				return (TryMangleNode(node), True)
			else:
				siblingIdx = node.parent.children.index(node)
				if siblingIdx > 1 and node.parent.children[siblingIdx - 2].type == 'this':
					return (TryMangleNode(node), True)
	return (nodeText, None)

def TryMangleNode (node) -> str:
	nodeText = node.text.decode('utf-8')
	if nodeText in JS_NAMES:
		return nodeText
	if len(nodeText) > 1:
		usedNames_ = usedNames[currentFuncName]
		mangledMembers_ = mangledMembers[currentFuncName]
		if nodeText not in mangledMembers_:
			while unusedNames[currentFuncName] == []:
				unusedName = random.choice(OKAY_NAME_CHARS) + random.choice(OKAY_NAME_CHARS)
				if unusedName not in MEMBER_REMAP.values() and unusedName not in mangledMembers_ and unusedName not in usedNames_:
					unusedNames[currentFuncName].append(unusedName)
			mangledMembers[currentFuncName][nodeText] = unusedNames[currentFuncName].pop(random.randint(0, len(unusedNames[currentFuncName]) - 1))
			if mangledMembers[currentFuncName][nodeText] not in usedNames_:
				usedNames[currentFuncName].append(mangledMembers[currentFuncName][nodeText])
		if nodeText in mangledMembers[currentFuncName]:
			nodeText = mangledMembers[currentFuncName][nodeText]
	elif nodeText not in usedNames[currentFuncName]:
		usedNames[currentFuncName].append(nodeText)
	return nodeText

def AtEndOfHierarchy (root, node) -> bool:
	while True:
		if root.children == []:
			return root == node
		root = root.children[len(root.children) - 1]
		if root == node and root.children == []:
			return True
	return False

def Compress (filePath : str) -> str:
	cmd = ['gzip', '--keep', '--force', '--verbose', '--best', filePath]
	subprocess.check_call(cmd)
	return open(filePath + '.gz', 'rb').read()

for arg in sys.argv:
	if arg.startswith(TEXT_INDICATOR):
		text += arg[len(TEXT_INDICATOR) :]
	elif arg.startswith(INPUT_INDICATOR):
		text += open(arg[len(INPUT_INDICATOR) :], 'r').read()
	elif arg.startswith(OUTPUT_INDICATOR):
		outputPath = arg[len(OUTPUT_INDICATOR) :]

jsBytes = bytes(text, 'utf8')
tree = PARSER.parse(jsBytes, encoding = 'utf8')
WalkTree (tree.root_node)
output = OUTPUT_PREFIX + globalVarsDeclrsText + output + '`)'
open(outputPath, 'w').write(output)
jsBytesLen = len(Compress(outputPath))
remappedOutput = OUTPUT_PREFIX + REMAP_CODE + globalRemappedVarsDeclrsText + remappedOutput + '`)'
open(outputPath, 'w').write(remappedOutput)
remappedJsBytesLen = len(Compress(outputPath))
if jsBytesLen > remappedJsBytesLen:
	print(output)
	open(outputPath, 'w').write(output)
	Compress (outputPath)
else:
	print(remappedOutput)