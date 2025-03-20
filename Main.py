import os, sys, string, random, subprocess, tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser

JS_LANG = Language(tsjs.language())
PARSER = Parser(JS_LANG)
TEXT_INDICATOR = '-t='
INPUT_INDICATOR = '-i='
OUTPUT_INDICATOR = '-o='
OUTPUT_PREFIX = 'F="function ";R="return ";D="delete ";W="while(";C="class ";E="else{";e="else ";d=document;w=window;m=Math;eval(`'
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
JS_NAMES = ['style', 'document', 'window', 'Math']
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
currentFunc = None
unusedNames = {}
unusedNames[currentFuncName] = []
unusedNames[currentFuncName].extend(OKAY_NAME_CHARS)
mangledMembers = {}
mangledMembers[currentFuncName] = {}
usedNames = {}
usedNames[currentFuncName] = ['F', 'R', 'D', 'W', 'C', 'E', 'e', 'd', 'w', 'm', 'M', 'if', 'do', 'of', 'in']

def WalkTree (node):
	global output, nodeTxt, currentFunc, unusedNames, unusedNames, mangledMembers, remappedOutput, currentFuncName
	nodeTxt = node.text.decode('utf-8')
	print(node.type, nodeTxt)
	if node.parent:
		siblingIdx = node.parent.children.index(node)
		nextSiblingType = None
		if len(node.parent.children) > siblingIdx + 1:
			nextSiblingType = node.parent.children[siblingIdx + 1].type
	if node.children == []:
		mangleOrRemapResults = TryMangleOrRemapNode(node)
		remappedNodeTxt = mangleOrRemapResults[0]
		if mangleOrRemapResults[1]:
			nodeTxt = remappedNodeTxt
		isOfOrIn = node.type in ['of', 'in']
		if isOfOrIn:
			AddToOutputs (' ')
		elif node.type in ['let', 'var', 'const'] or (node.type == ';' and AtEndOfHierarchy(node.parent, node) and node.parent.parent.text.decode('utf-8').endswith('}')):
			nodeTxt = ''
			remappedNodeTxt = nodeTxt
		elif node.type == 'function':
			nodeTxt = '${F}'
			remappedNodeTxt = nodeTxt
			# nodeTxt += ' '
			# remappedNodeTxt = nodeTxt
		elif node.type == 'return':
			nodeTxt = '${R}'
			remappedNodeTxt = nodeTxt
			# nodeTxt += ' '
			# remappedNodeTxt = nodeTxt
		elif node.type == 'delete':
			nodeTxt = '${D}'
			remappedNodeTxt = nodeTxt
			# nodeTxt += ' '
			# remappedNodeTxt = nodeTxt
		elif node.type == 'while':
			nodeTxt = '${W}'
			remappedNodeTxt = nodeTxt
		elif node.type == 'class':
			nodeTxt = '${C}'
			remappedNodeTxt = nodeTxt
			# nodeTxt += ' '
			# remappedNodeTxt = nodeTxt
		elif node.type == 'else':
			if nextSiblingType == '{':
				nodeTxt = '${E}'
			else:
				nodeTxt = '${e}'
			remappedNodeTxt = nodeTxt
			# nodeTxt += ' '
			# remappedNodeTxt = nodeTxt
		output += nodeTxt
		remappedOutput += remappedNodeTxt
		if currentFunc and AtEndOfHierarchy(currentFunc, node):
			currentFuncName = ''
			currentFunc = None
		elif (node.type == 'identifier' and node.parent.type == 'function_declaration') or (node.type == 'property_identifier' and node.parent.type == 'method_definition'):
			currentFuncName = nodeTxt
			currentFunc = node.parent
			unusedNames[nodeTxt] = []
			unusedNames[nodeTxt].extend(OKAY_NAME_CHARS)
			for usedName in usedNames['']:
				if usedName in unusedNames[nodeTxt]:
					unusedNames[nodeTxt].remove(usedName)
			usedNames[nodeTxt] = usedNames['']
			mangledMembers[nodeTxt] = mangledMembers['']
		if nextSiblingType and (isOfOrIn or node.type == 'new') and nextSiblingType not in ['{', 'array']:
			AddToOutputs (' ')
	for child in node.children:
		WalkTree (child)
	if node.type in ['lexical_declaration', 'variable_declaration', 'expression_statement'] and not nodeTxt.endswith(';') and nextSiblingType != '}' and node.end_byte < len(text) - 1:
		AddToOutputs (';')

def AddToOutputs (add : str):
	global output, remappedOutput
	output += add
	remappedOutput += add

def TryMangleOrRemapNode (node) -> (str, None):
	nodeTxt = node.text.decode('utf-8')
	if node.type == 'identifier':
		if nodeTxt == 'document':
			return ('d', True)
		elif nodeTxt == 'window':
			return ('w', True)
		elif nodeTxt == 'Math':
			return ('m', True)
		return (TryMangleNode(node), True)
	elif node.type == 'property_identifier':
		if nodeTxt in MEMBER_REMAP:
			return (MEMBER_REMAP[nodeTxt], False)
		else:
			parentNodeTxt = node.parent.text.decode('utf-8')
			if node.parent.type == 'method_definition' and parentNodeTxt not in usedNames[currentFuncName] + JS_NAMES:
				return (TryMangleNode(node), True)
			else:
				siblingIdx = node.parent.children.index(node)
				if siblingIdx > 1 and node.parent.children[siblingIdx - 2].type == 'this':
					return (TryMangleNode(node), True)
	return (nodeTxt, None)

def TryMangleNode (node) -> str:
	nodeTxt = node.text.decode('utf-8')
	if nodeTxt in JS_NAMES:
		return nodeTxt
	if len(nodeTxt) > 1:
		mangledMembers_ = mangledMembers[currentFuncName]
		if nodeTxt not in mangledMembers_:
			usedNames_ = usedNames[currentFuncName]
			while unusedNames[currentFuncName] == []:
				unusedName = random.choice(OKAY_NAME_CHARS) + random.choice(OKAY_NAME_CHARS)
				if unusedName not in MEMBER_REMAP.values() and unusedName not in mangledMembers_ and unusedName not in usedNames_:
					unusedNames[currentFuncName].append(unusedName)
			mangledMembers[currentFuncName][nodeTxt] = unusedNames[currentFuncName].pop(random.randint(0, len(unusedNames[currentFuncName]) - 1))
			if mangledMembers[currentFuncName][nodeTxt] not in usedNames_:
				usedNames[currentFuncName].append(mangledMembers[currentFuncName][nodeTxt])
		if nodeTxt in mangledMembers[currentFuncName]:
			nodeTxt = mangledMembers[currentFuncName][nodeTxt]
	elif nodeTxt not in usedNames[currentFuncName]:
		usedNames[currentFuncName].append(nodeTxt)
	return nodeTxt

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

jsBytes = text.encode('utf-8')
tree = PARSER.parse(jsBytes, encoding = 'utf8')
WalkTree (tree.root_node)
output = OUTPUT_PREFIX + output + '`)'
open(outputPath, 'w').write(output)
jsBytes = Compress(outputPath)
remappedOutput = OUTPUT_PREFIX + REMAP_CODE + remappedOutput + '`)'
# remappedOutput = REMAP_CODE + remappedOutput
open(outputPath, 'w').write(remappedOutput)
remappedJsBytesLen = len(Compress(outputPath))
if len(jsBytes) < remappedJsBytesLen:
	print(output)
	open(outputPath, 'w').write(output)
	open(outputPath + '.gz', 'wb').write(jsBytes)
else:
	print(remappedOutput)