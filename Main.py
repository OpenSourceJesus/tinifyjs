import os, sys, string, random, subprocess, tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser

JS_LANG = Language(tsjs.language())
PARSER = Parser(JS_LANG)
TEXT_INDCTR = '-t='
INPUT_INDCTR = '-i='
OUTPUT_INDCTR = '-o='
DONT_COMPRESS_INDCTR = '-n'
ARGS_INDCTRS = []
for i in range(1, 11):
	ARGS_INDCTRS.append(i)
IDXS_INDCTRS = [0]
for i in range(11, 14):
	IDXS_INDCTRS.append(i)
MEMBER_REMAP = {}
_thisDir = os.path.split(os.path.abspath(__file__))[0]
_memberRemap = open(os.path.join(_thisDir, 'MemberRemap'), 'r').read()
for line in _memberRemap.split('\n'):
	parts = line.split()
	MEMBER_REMAP[parts[0]] = parts[1]
DOM_REMAP_CODE = '''a={}
for(o of [Element,Node,String,Array,Document,Window]){p=o.prototype
for(n of Object.getOwnPropertyNames(p)){s=0
e=n.length-1
b=n[s]
while(b in a){s++
b=n[s]+n[e]
e--}try{p[b]=p[n]
a[b]=1}catch(e){}}}'''
REMAP_CHARS = {1 : 'function ', 2 : 'return ', 3 : 'delete ', 4 : 'while(', 5 : 'class ', 6 : 'else{', 7 : 'else ', 8 : 'document', 9 : 'window', 11 : 'Math'}
REMAP_CODE = 'a=' + str(REMAP_CHARS).replace(' ', '') + '''for(c of d){for([k,v] of a){a=a.replace(String.fromCharCode()(k),v)}}'''
ARGS_CONDENSE_CODE = 'b=' + str(ARGS_INDCTRS).replace(' : ', ':').replace(', ', ',') + '\nc=' + str(IDXS_INDCTRS).replace(' ', '') + '''
d=''
for(p=0;p<a.length;p++){c=a[p]
l=b.indexOf(c.charCodeAt(0))
if(l>-1){d+=f
p++
for(i=0;i<l;i++){d+=a[p]
if(i<l-1){d+=','
p++}}d+=')'}else d+=c}'''
REMAPPED_ARGS_CONDENSE_CODE = ARGS_CONDENSE_CODE
# for name, newName in MEMBER_REMAP.items():
# 	REMAPPED_ARGS_CONDENSE_CODE = REMAPPED_ARGS_CONDENSE_CODE.replace(name, newName)
OKAY_NAME_CHARS = list(string.ascii_letters + '$_')
JS_NAMES = ['style', 'document', 'window', 'Math']
WHITESPACE_EQUIVALENT = string.whitespace + ';'
txt = ''
output = ''
domRemappedOutput = ''
outputPath = '/tmp/tinifyjs Output.js'
currentFuncName = ''
currentFunc = None
unusedNames = {}
unusedNames[currentFuncName] = []
unusedNames[currentFuncName].extend(OKAY_NAME_CHARS)
mangledMembers = {}
mangledMembers[currentFuncName] = {}
usedNames = {}
usedNames[currentFuncName] = ['if', 'do', 'of', 'in']
skipNodesAtPositions = []
compress = True

def WalkTree (node):
	global output, nodeTxt, currentFunc, unusedNames, mangledMembers, domRemappedOutput, currentFuncName, globalVarsCntLeft, skipNodesAtPositions
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
		domRemappedNodeTxt = mangleOrRemapResults[0]
		if mangleOrRemapResults[1]:
			nodeTxt = domRemappedNodeTxt
		isOfOrIn = node.type in ['of', 'in']
		if isOfOrIn:
			AddToOutputs (' ')
		elif node.type in ['let', 'var', 'const'] or (node.type == ';' and AtEndOfHierarchy(node.parent, node) and node.parent.parent.text.decode('utf-8').endswith('}')):
			nodeTxt = ''
			domRemappedNodeTxt = nodeTxt
		elif node.type == 'function':
			nodeTxt = chr(1)
			domRemappedNodeTxt = nodeTxt
		elif node.type == 'return':
			nodeTxt = chr(2)
			domRemappedNodeTxt = nodeTxt
		elif node.type == 'delete':
			nodeTxt = chr(3)
			domRemappedNodeTxt = nodeTxt
		elif node.type == 'while':
			nodeTxt = chr(4)
			domRemappedNodeTxt = nodeTxt
		elif node.type == 'class':
			nodeTxt = chr(5)
			domRemappedNodeTxt = nodeTxt
		elif node.type == 'else':
			if nextSiblingType == '{':
				nodeTxt = chr(6)
			else:
				nodeTxt = chr(7)
			domRemappedNodeTxt = nodeTxt
		elif node.type == '(':
			CondenseArgs (node, ARGS_INDCTRS)
		# elif node.type == '[':
		# 	CondenseArgs (node, IDXS_INDCTRS)
		if node.end_byte not in skipNodesAtPositions and not (nodeTxt.endswith(';') and node.end_byte == len(txt) - 1):
			output += nodeTxt
			domRemappedOutput += domRemappedNodeTxt
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
	global output, domRemappedOutput
	output += add
	domRemappedOutput += add

def TryMangleOrRemapNode (node) -> (str, None):
	nodeTxt = node.text.decode('utf-8')
	if node.type == 'identifier':
		if nodeTxt == 'document':
			return (chr(8), True)
		elif nodeTxt == 'window':
			return (chr(9), True)
		elif nodeTxt == 'Math':
			return (chr(11), True)
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
				mangledMember = mangledMembers[currentFuncName][nodeTxt]
				usedNames[currentFuncName].append(mangledMember)
		if nodeTxt in mangledMembers[currentFuncName]:
			nodeTxt = mangledMembers[currentFuncName][nodeTxt]
	elif nodeTxt not in usedNames[currentFuncName]:
		usedNames[currentFuncName].append(nodeTxt)
	return nodeTxt

def CondenseArgs (node, argsCntsIndctrsVals : list):
	global skipNodesAtPositions
	siblings = node.parent.children
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
	if argCnt >= 0 and argCnt < len(argsCntsIndctrsVals):
		nodeTxt = ''
		domRemappedNodeTxt = ''
		AddToOutputs (chr(argsCntsIndctrsVals[argCnt]))
		skipNodesAtPositions.append(node.end_byte)
		skipNodesAtPositions.append(siblings[len(siblings) - 1].end_byte)

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
	if arg.startswith(TEXT_INDCTR):
		txt += arg[len(TEXT_INDCTR) :]
	elif arg.startswith(INPUT_INDCTR):
		txt += open(arg[len(INPUT_INDCTR) :], 'r').read()
	elif arg.startswith(OUTPUT_INDCTR):
		outputPath = arg[len(OUTPUT_INDCTR) :]
	elif arg == DONT_COMPRESS_INDCTR:
		compress = False

jsBytes = txt.encode('utf-8')
tree = PARSER.parse(jsBytes, encoding = 'utf8')
WalkTree (tree.root_node)
output = 'a=`' + output + '`\n' + ARGS_CONDENSE_CODE + '\n'+ REMAP_CODE + '\neval(d)'
open(outputPath, 'w').write(output)
if compress:
	jsBytes = Compress(outputPath)
else:
	jsBytes = output
domRemappedOutput = DOM_REMAP_CODE + 'a=`' + domRemappedOutput + '`\n' + REMAPPED_ARGS_CONDENSE_CODE + '\n' + REMAP_CODE + '\neval(d)'
open(outputPath, 'w').write(domRemappedOutput)
if compress:
	remappedJsBytesLen = len(Compress(outputPath))
else:
	remappedJsBytesLen = len(domRemappedOutput)
if len(jsBytes) < remappedJsBytesLen:
	print(output)
	open(outputPath, 'w').write(output)
	if compress:
		open(outputPath + '.gz', 'wb').write(jsBytes)
else:
	print(domRemappedOutput)