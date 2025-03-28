import os, sys, string, random, subprocess, tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser

JS_LANG = Language(tsjs.language())
PARSER = Parser(JS_LANG)
TEXT_INDICATOR = '-t='
INPUT_INDICATOR = '-i='
OUTPUT_INDICATOR = '-o='
ARGS_INDICATORS = ['', '', '', '', '', '', '', '', '	', '']
IDXS_INDICATORS = ['', '', '', '']
MEMBER_REMAP = {}
_thisDir = os.path.split(os.path.abspath(__file__))[0]
_memberRemap = open(os.path.join(_thisDir, 'MemberRemap'), 'r').read()
for line in _memberRemap.split('\n'):
	parts = line.split()
	MEMBER_REMAP[parts[0]] = parts[1]
OUTPUT_PREFIX = 'a="function ";b="return ";c="delete ";d="while(";e="class ";f="else{";g="else ";h=document;i=window;j=Math;'
REMAP_CODE = '''À={}
for(o of [Element,Node,String,Array,Document,Window]){p=o.prototype
for(n of Object.getOwnPropertyNames(p)){s=0
e=n.length-1
a=n[s]
while(a in À){s++
a=n[s]+n[e]
e--}try{p[a]=p[n]
À[a]=1}catch(e){}}}'''
ARGS_CONDENSE_CODE = 'ý=' + str(ARGS_INDICATORS).replace(' ', '') + '\nú=' + str(IDXS_INDICATORS).replace(' ', '') + '''
û(ý,'(',')')
ý=ü
û(ú,'[',']')
function û(a,s,e){for(p=0;p<ÿ.length;p++){c=ÿ[p]
l=ý.indexOf(c)
if(l>-1){ü+=s
p++
for(i=0;i<l;i++){ü+=ÿ[p]
if(i<l-1){ü+=','
p++}}ü+=e}else ü+=c}}'''
REMAPPED_ARGS_CONDENSE_CODE = ARGS_CONDENSE_CODE
# for name, newName in MEMBER_REMAP.items():
# 	REMAPPED_ARGS_CONDENSE_CODE = REMAPPED_ARGS_CONDENSE_CODE.replace(name, newName)
OKAY_NAME_CHARS = list(string.ascii_letters + '$_')
JS_NAMES = ['style', 'document', 'window', 'Math']
WHITESPACE_EQUIVALENT = string.whitespace + ';'
txt = ''
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
usedNames[currentFuncName] = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'if', 'do', 'of', 'in']
skipNodesAtPositions = []

def WalkTree (node):
	global output, nodeTxt, currentFunc, unusedNames, unusedNames, mangledMembers, remappedOutput, currentFuncName, skipNodesAtPositions
	nodeTxt = node.text.decode('utf-8')
	print(node.type, nodeTxt)
	if node.parent:
		siblings = node.parent.children
		siblingIdx = siblings.index(node)
		nextSiblingType = None
		if len(siblings) > siblingIdx + 1:
			nextSiblingType = siblings[siblingIdx + 1].type
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
			nodeTxt = '${a}'
			remappedNodeTxt = nodeTxt
		elif node.type == 'return':
			nodeTxt = '${b}'
			remappedNodeTxt = nodeTxt
		elif node.type == 'delete':
			nodeTxt = '${c}'
			remappedNodeTxt = nodeTxt
		elif node.type == 'while':
			nodeTxt = '${d}'
			remappedNodeTxt = nodeTxt
		elif node.type == 'class':
			nodeTxt = '${e}'
			remappedNodeTxt = nodeTxt
		elif node.type == 'else':
			if nextSiblingType == '{':
				nodeTxt = '${f}'
			else:
				nodeTxt = '${g}'
			remappedNodeTxt = nodeTxt
		elif node.type == '(':
			argCnt = 0
			for sibling in siblings[1 : -1]:
				if sibling.type != ',':
					argCnt += 1
					if sibling.children != [] or len(TryMangleNode(sibling)) > 1:
						argCnt = 0
						skipNodesAtPositions = []
						break
				else:
					skipNodesAtPositions.append(sibling.end_byte)
			if argCnt > 0 and argCnt < len(ARGS_INDICATORS):
				nodeTxt = ''
				remappedNodeTxt = ''
				AddToOutputs (ARGS_INDICATORS[argCnt])
				skipNodesAtPositions.append(siblings[len(siblings) - 1].end_byte)
		elif node.type == '[':
			idxCnt = 0
			for sibling in siblings[1 : -1]:
				if sibling.type != ',':
					idxCnt += 1
					if sibling.children != [] or len(TryMangleNode(sibling)) > 1:
						idxCnt = 0
						skipNodesAtPositions = []
						break
				else:
					skipNodesAtPositions.append(sibling.end_byte)
			if idxCnt > 0 and idxCnt < len(IDXS_INDICATORS):
				nodeTxt = ''
				remappedNodeTxt = ''
				AddToOutputs (IDXS_INDICATORS[idxCnt])
				skipNodesAtPositions.append(siblings[len(siblings) - 1].end_byte)
		if node.end_byte not in skipNodesAtPositions and not (nodeTxt.endswith(';') and node.end_byte == len(txt) - 1):
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
	if node.type in ['lexical_declaration', 'variable_declaration', 'expression_statement'] and not nodeTxt.endswith(';') and nextSiblingType != '}' and node.end_byte < len(txt) - 1:
		AddToOutputs (';')

def AddToOutputs (add : str):
	global output, remappedOutput
	output += add
	remappedOutput += add

def TryMangleOrRemapNode (node) -> (str, None):
	nodeTxt = node.text.decode('utf-8')
	if node.type == 'identifier':
		if nodeTxt == 'document':
			return ('h', True)
		elif nodeTxt == 'window':
			return ('i', True)
		elif nodeTxt == 'Math':
			return ('j', True)
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
				if unusedName not in list(MEMBER_REMAP.values()) + list(mangledMembers_.keys()) + usedNames_:
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
		txt += arg[len(TEXT_INDICATOR) :]
	elif arg.startswith(INPUT_INDICATOR):
		txt += open(arg[len(INPUT_INDICATOR) :], 'r').read()
	elif arg.startswith(OUTPUT_INDICATOR):
		outputPath = arg[len(OUTPUT_INDICATOR) :]

jsBytes = txt.encode('utf-8')
tree = PARSER.parse(jsBytes, encoding = 'utf8')
WalkTree (tree.root_node)
output = OUTPUT_PREFIX + '\ný=`' + output + '`\n' + ARGS_CONDENSE_CODE + 'eval(ü)'
open(outputPath, 'w').write(output)
jsBytes = Compress(outputPath)
remappedOutput = OUTPUT_PREFIX + REMAP_CODE + '\ný=`' + remappedOutput + '`\n' + REMAPPED_ARGS_CONDENSE_CODE + 'eval(ü)'
open(outputPath, 'w').write(remappedOutput)
remappedJsBytesLen = len(Compress(outputPath))
if len(jsBytes) < remappedJsBytesLen:
	print(output)
	open(outputPath, 'w').write(output)
	open(outputPath + '.gz', 'wb').write(jsBytes)
else:
	print(remappedOutput)