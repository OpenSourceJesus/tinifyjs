import os, sys, string, random, subprocess, tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser

JS_LANG = Language(tsjs.language())
PARSER = Parser(JS_LANG)
TEXT_INDCTR = '-t='
INPUT_INDCTR = '-i='
OUTPUT_INDCTR = '-o='
DONT_COMPRESS_INDCTR = '-n'
DEBUG_INDCTR = '-d'
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
for(o of [Element,Node,String,Window]){p=o.prototype
for(n of Object.getOwnPropertyNames(p)){s=0
e=n.length-1
b=n[s]
while(b in a){s++
b=n[s]+n[e]
e--}try{p[b]=p[n]
a[b]=1}catch(e){}}}for(var n in document.body.style){var f=eval(function(a){this.style[`${n}`]=a})
Element.prototype['$'+n[0]+n[n.length-1]]=f}'''
REMAP_CHARS = {14 : 'function', 15 : 'return', 16 : 'delete', 17 : 'while', 18 : 'class', 19 : 'else', 20 : 'this', 21 : 'document', 22 : 'window', 23 : 'Math', 24 : 'switch', 25 : 'case', 26 : 'exports'}
REMAP_CODE = 'e=' + str(REMAP_CHARS).replace(' ', '') + '''
for(c of d){for([k,v] of Object.entries(e))a=a.replace(String.fromCharCode(k),v+' ')}'''
ARGS_AND_IDXS_CONDENSE_CODE = 'b=' + str(ARGS_INDCTRS).replace(' : ', ':').replace(', ', ',') + '\nc=' + str(IDXS_INDCTRS).replace(' ', '') + '''
d=''
$(b,'(',')')
a=d
d=''
$(c,'[',']')
function $(e,f,g){for(p=0;p<a.length;p++){c=a[p]
l=e.indexOf(c.charCodeAt(0))
if(l>-1){d+=f
p++
for(i=0;i<l;i++){d+=a[p]
if(i<l-1){d+=','
p++}}d+=g}else d+=c}}'''
REMAPPED_ARGS_AND_IDXS_CONDENSE_CODE = ARGS_AND_IDXS_CONDENSE_CODE
for name, newName in MEMBER_REMAP.items():
	REMAPPED_ARGS_AND_IDXS_CONDENSE_CODE = REMAPPED_ARGS_AND_IDXS_CONDENSE_CODE.replace(name, newName)
OKAY_NAME_CHARS = list(string.ascii_letters + '_')
JS_NAMES = ['style', 'document', 'window', 'Math', 'if', 'do', 'of', 'in']
WHITESPACE_EQUIVALENT = string.whitespace + ';'
txt = ''
output = ''
outputPath = '/tmp/tinifyjs Output.js'
currentFuncName = ''
currentFunc = None
currentFuncTxt = ''
currentFuncVarsNames = []
unusedNames = {}
unusedNames[currentFuncName] = []
unusedNames[currentFuncName].extend(OKAY_NAME_CHARS)
mangledMembers = {}
mangledMembers[currentFuncName] = {}
usedNames = {}
usedNames[currentFuncName] = []
usedNames[currentFuncName].extend(['$'])
skipNodesAtPositions = []
compress = True
debug = False

def WalkTree (node):
	global output, nodeTxt, currentFunc, unusedNames, mangledMembers, currentFuncTxt, currentFuncName, globalVarsCntLeft, currentFuncVarsNames, skipNodesAtPositions
	nodeTxt = node.text.decode('utf-8')
	print(node.type, nodeTxt)
	if node.parent:
		siblings = node.parent.children
		siblingIdx = siblings.index(node)
		nextSibling = None
		if len(siblings) > siblingIdx + 1:
			nextSibling = siblings[siblingIdx + 1]
	if node.children == []:
		nodeTxt = TryMangleOrRemapNode(node)
		if nodeTxt == 'style':
			parent2 = node.parent.parent
			parentIdx = parent2.children.index(node.parent)
			if len(parent2.children) > parentIdx + 1:
				node2 = parent2.children[parentIdx + 1]
				if node2.text == b'.':
					node3 = parent2.children[parentIdx + 2]
					node3Txt = node3.text.decode('utf-8')
					skipNodesAtPositions.append(node.end_byte)
					skipNodesAtPositions.append(node2.end_byte)
					skipNodesAtPositions.append(node3.end_byte)
					AddToOutput ('$' + node3Txt[0] + node3Txt[-1])
		else:
			for charValue, name in REMAP_CHARS.items():
				if nodeTxt == name:
					if debug:
						nodeTxt += ' '
					else:
						nodeTxt = chr(charValue)
					break
		isOfOrIn = node.type in ['of', 'in']
		inVarDeclrn = node.type in ['let', 'var', 'const']
		if isOfOrIn:
			AddToOutput (' ')
		elif inVarDeclrn or (node.type == ';' and AtEndOfHierarchy(node.parent, node) and node.parent.parent.text.decode('utf-8').endswith('}')):
			if inVarDeclrn and currentFunc:
				varName = TryMangleNode(nextSibling)
				if varName not in currentFuncVarsNames:
					currentFuncVarsNames.append(varName)
			nodeTxt = ''
		elif not debug:
			if node.type == '(' and nextSibling.type != 'binary_expression':
				CondenseArgs (node, ARGS_INDCTRS)
			elif node.type == '[' and nextSibling.type != 'array':
				CondenseArgs (node, IDXS_INDCTRS)
		if node.end_byte not in skipNodesAtPositions and not (nodeTxt.endswith(';') and node.end_byte == len(txt) - 1):
			if currentFunc:
				currentFuncTxt += nodeTxt
			else:
				output += nodeTxt
		if currentFunc and AtEndOfHierarchy(currentFunc, node):
			funcBodyPrefix = ''
			for varName in currentFuncVarsNames:
				funcBodyPrefix += varName + ','
			if funcBodyPrefix != '':
				funcBodyPrefix = 'var ' + funcBodyPrefix[: -1] + ';'
			funcBodyStartIdx = currentFuncTxt.find('{') + 1
			output += currentFuncTxt[: funcBodyStartIdx] + funcBodyPrefix + currentFuncTxt[funcBodyStartIdx :]
			currentFuncName = ''
			currentFunc = None
			currentFuncTxt = ''
			currentFuncVarsNames = []
		elif (node.type == 'identifier' and node.parent.type == 'function_declaration') or (node.type == 'property_identifier' and node.parent.type == 'method_definition'):
			currentFuncName = nodeTxt
			currentFunc = node.parent
			unusedNames[nodeTxt] = []
			unusedNames[nodeTxt].extend(OKAY_NAME_CHARS)
			for usedName in usedNames['']:
				if usedName in unusedNames[nodeTxt]:
					unusedNames[nodeTxt].remove(usedName)
			usedNames[nodeTxt] = []
			usedNames[nodeTxt].extend(usedNames[''])
			mangledMembers[nodeTxt] = mangledMembers['']
		if nextSibling and (isOfOrIn or node.type == 'new') and nextSibling.type not in ['{', 'array']:
			AddToOutput (' ')
	for child in node.children:
		WalkTree (child)
	if node.type in ['lexical_declaration', 'variable_declaration', 'expression_statement'] and not nodeTxt.endswith(';') and (not nextSibling or nextSibling.type != '}') and node.end_byte < len(txt) - 1:
		AddToOutput (';')

def AddToOutput (add : str):
	global output, currentFuncTxt
	if currentFunc:
		currentFuncTxt += add
	else:
		output += add

def TryMangleOrRemapNode (node) -> str:
	nodeTxt = node.text.decode('utf-8')
	if node.type == 'identifier':
		if not debug:
			if nodeTxt == 'document':
				return chr(8)
			elif nodeTxt == 'window':
				return chr(9)
			elif nodeTxt == 'Math':
				return chr(11)
		return TryMangleNode(node)
	elif node.type == 'property_identifier':
		if nodeTxt in MEMBER_REMAP:
			return MEMBER_REMAP[nodeTxt]
		else:
			parentNodeTxt = node.parent.text.decode('utf-8')
			if node.parent.type == 'method_definition' and parentNodeTxt not in usedNames[currentFuncName] + JS_NAMES:
				return TryMangleNode(node)
			else:
				siblingIdx = node.parent.children.index(node)
				if siblingIdx > 1 and node.parent.children[siblingIdx - 2].type == 'this':
					return TryMangleNode(node)
	return nodeTxt

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
				if unusedName not in list(MEMBER_REMAP.values()) + usedNames_ + JS_NAMES:
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
		domRemappedNodeTxt = nodeTxt
		AddToOutput (chr(argsCntsIndctrsVals[argCnt]))
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
	elif arg == DEBUG_INDCTR:
		debug = True

jsBytes = txt.encode('utf-8')
tree = PARSER.parse(jsBytes, encoding = 'utf8')
WalkTree (tree.root_node)
outputPrefix = 'a=`'
outputSuffix = '`'
evalCode = '\neval(d)'
if debug:
	outputPrefix = ''
	outputSuffix = ''
	evalCode = ''
output = DOM_REMAP_CODE + outputPrefix + output + outputSuffix + '\n' + REMAPPED_ARGS_AND_IDXS_CONDENSE_CODE + '\n' + REMAP_CODE + evalCode
open(outputPath, 'w').write(output)
if compress:
	Compress (outputPath)