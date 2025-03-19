import os, sys, string, random, subprocess, tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser

JS_LANG = Language(tsjs.language())
PARSER = Parser(JS_LANG)
TEXT_INDICATOR = '-t='
INPUT_INDICATOR = '-i='
OUTPUT_INDICATOR = '-o='
REMAP_CODE = '''ms={}
for(o of [Element,Node,String,Array,Document,Window]){p=o.prototype
for(n of Object.getOwnPropertyNames(p)){s=0
e=n.length-1
a=n[s]
while(a in ms){s++
a=n[s]+n[e]
e--}try{p[a]=p[n]
ms[a]=1}catch(e){}}}'''
OKAY_NAME_CHARS = list(string.ascii_letters + '_')
OKAY_NAME_CHARS.remove('F')
OKAY_NAME_CHARS.remove('M')
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
currentFunc = None
unusedNames = {}
unusedNames[currentFuncName] = []
unusedNames[currentFuncName].extend(OKAY_NAME_CHARS + ['F', 'M'])
mangledMembers = {}
mangledMembers[currentFuncName] = {}
usedNames = {}
usedNames[currentFuncName] = []

def WalkTree (node):
	global output, nodeText, currentFunc, mangledMembers, currentFuncName, remappedOutput
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
		output += nodeText
		remappedOutput += remappedNodeText
		siblingIdx = node.parent.children.index(node)
		if len(node.parent.children) > siblingIdx + 1:
			nextSiblingType = node.parent.children[siblingIdx + 1].type
			if node.type in ['new', 'delete'] or ((isOfOrIn or node.type in ['return', 'class', 'function']) and nextSiblingType in ['identifier', 'binary_expression', 'call_expression', 'member_expression', 'subscript_expression', 'false', 'true']) or (node.type == 'else' and nextSiblingType in ['if_statement', 'lexical_declaration', 'variable_declaration', 'expression_statement', 'return', 'while']):
				AddToOutputs (' ')
		elif currentFunc and AtEndOfHierarchy(currentFunc, node):
			currentFuncName = ''
			currentFunc = None
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
	for n in node.children:
		WalkTree (n)
	if node.type in ['lexical_declaration', 'variable_declaration', 'expression_statement'] and not nodeText.endswith(';') and node.end_byte < len(text) - 1:
		AddToOutputs (';')

def AddToOutputs (add : str):
	global output, remappedOutput
	output += add
	remappedOutput += add

def TryMangleOrRemapNode (node) -> (str, bool):
	nodeText = node.text.decode('utf-8')
	if node.type == 'identifier':
		if nodeText == 'Math':
			return ('M', True)
		return (TryMangleNode(node), True)
	elif node.type == 'property_identifier':
		if nodeText in MEMBER_REMAP:
			return (MEMBER_REMAP[nodeText], False)
		else:
			parentNodeText = node.parent.text.decode('utf-8')
			if node.parent.type in ['method_definition'] or parentNodeText not in usedNames[currentFuncName] or parentNodeText not in JS_NAMES:
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
				if unusedName not in MEMBER_REMAP.values() and unusedName not in mangledMembers_ and unusedName not in usedNames_ and unusedName not in ['if', 'do', 'of', 'in', 'ms']:
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
remappedOutput = REMAP_CODE + remappedOutput
if len(output) > len(remappedOutput):
	output = remappedOutput
output = 'F="function";M=Math;eval(`' + output + '`)'
print(output)
open(outputPath, 'w').write(output)
Compress(outputPath)