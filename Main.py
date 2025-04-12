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
for i in range(1, 10):
	ARGS_INDCTRS.append(i)
ARGS_INDCTRS.append(11)
IDXS_INDCTRS = [12]
for i in range(14, 17):
	IDXS_INDCTRS.append(i)
DOM_AND_CSS_REMAP_CODE = '''for(o of[Element,Node,Array,String,Window,Document,XMLHttpRequest]){p=o.prototype
for(n of Object.getOwnPropertyNames(p)){try{p[n[2]+String.fromCharCode(n.length+96)]=p[n]}catch(e){}console.log(n,n[1]+String.fromCharCode(n.length+96)))}}for(n in document.body.style){f=eval(function(a){this.style[`_{n}`]=a})
Element.prototype['_'+n[0]+n[n.length-1]]=f}'''
VAR_REPLACE_CHAR_VAL = 17
WINDOW_REPLACE_CHAR_VAL = 18
ARGS_AND_IDXS_CONDENSE_CODE = 'b=' + str(ARGS_INDCTRS).replace(' : ', ':').replace(', ', ',') + '\nc=' + str(IDXS_INDCTRS).replace(' ', '') + '''
d=''
CA(b,'(',')')
a=d
d=''
CA(c,'[',']')
function CA(e,f,g){for(p=0;p<a.length;p++){c=a[p]
l=e.indexOf(c.charCodeAt(0))
if(l>-1){d+=f
p++
for(i=0;i<=l;i++){d+=a[p]
if(i<l){d+=','
p++}}d+=g}else d+=c}}'''
# FUNC_REPLACE_CHAR_VAL = 19
OKAY_NAME_CHARS = list(string.ascii_letters)
JS_NAMES = ['Math', 'window', 'document', 'JSON', 'parseInt', 'cssText', 'charCodeAt', 'if', 'do', 'of', 'in']
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
unusedNames['.'] = []
unusedNames['.'].extend(OKAY_NAME_CHARS)
mangledMembers = {}
mangledMembers[currentFuncName] = {}
mangledMembers['.'] = {}
usedNames = {}
usedNames[currentFuncName] = ['_', '$', 'CA']
usedNames['.'] = []
skipNodesAtPositions = []
# varsCnts = {}
# userClassFuncsCnts = {}
# maxLocalVarsCnt = 0
userClassFuncs = []
compress = True
debug = False

def WalkTreePass1 (node):
	# global currentFunc, currentFuncName
	# isIdentifier = node.type == 'identifier'
	# if node.type == 'assignment_expression':
	# 	AddToVarCount (node.children[0])
	# elif isIdentifier:
	# 	AddToVarCount (node)
	# if currentFunc and AtEndOfHierarchy(currentFunc, node):
	# 	currentFuncName = ''
	# 	currentFunc = None
	# elif (isIdentifier and node.parent.type == 'function_declaration') or (node.type == 'property_identifier' and node.parent.type == 'method_definition'):
	# 	currentFuncName = node.text.decode('utf-8')
	# 	currentFunc = node.parent
	nodeTxt = node.text.decode('utf-8')
	if node.type == 'property_identifier':
		if node.parent.type == 'method_definition' and node.parent.parent.type == 'class_body':
			userClassFuncs.append(nodeTxt)
	for child in node.children:
		WalkTreePass1 (child)

# def AddToVarCount (varNode):
# 	varName = varNode.text.decode('utf-8')
# 	if currentFuncName not in varsCnts:
# 		varsCnts[currentFuncName] = {varName : 1}
# 	elif varName in varsCnts[currentFuncName]:
# 		varsCnts[currentFuncName][varName] += 1
# 	else:
# 		varsCnts[currentFuncName][varName] = 1

def WalkTreePass2 (node):
	global output, currentFunc, usedNames, unusedNames, mangledMembers, currentFuncTxt, currentFuncName, currentFuncVarsNames, skipNodesAtPositions
	nodeTxt = node.text.decode('utf-8')
	print(node.type, nodeTxt)
	if node.type == ';':
		AddToOutput (nodeTxt)
		return
	if node.parent:
		siblings = node.parent.children
		siblingIdx = siblings.index(node)
		nextSibling = None
		if len(siblings) > siblingIdx + 1:
			nextSibling = siblings[siblingIdx + 1]
	if node.children == []:
		nodeTxt = TryMangleOrMapNode(node)
		if nodeTxt == 'style':
			parent2 = node.parent.parent
			parentIdx = parent2.children.index(node.parent)
			if len(parent2.children) > parentIdx + 1:
				node2 = parent2.children[parentIdx + 1]
				if node2.text == b'.':
					node3 = parent2.children[parentIdx + 2]
					node3Txt = node3.text.decode('utf-8')
					if node3Txt not in JS_NAMES:
						skipNodesAtPositions.append(node.end_byte)
						skipNodesAtPositions.append(node2.end_byte)
						skipNodesAtPositions.append(node3.end_byte)
						AddToOutput ('_' + node3Txt[0] + node3Txt[-1])
		isOfOrIn = node.type in ['of', 'in']
		inVarDeclrn = node.type in ['let', 'var', 'const']
		if isOfOrIn:
			AddToOutput (' ')
		elif inVarDeclrn or (node.type == ';' and AtEndOfHierarchy(node.parent, node) and node.parent.parent.text.decode('utf-8').endswith('}')):
			if not currentFunc or not inVarDeclrn:
				nodeTxt = ''
			if inVarDeclrn:
				varName = TryMangleNode(nextSibling)
				if currentFunc and varName not in currentFuncVarsNames + usedNames['']:
					currentFuncVarsNames.append(varName)
		elif not debug and nextSibling:
			if node.type == '(' and nextSibling.type != 'binary_expression':
				CondenseArgs (node, ARGS_INDCTRS)
			elif node.type == '[' and nextSibling.type != 'array':
				CondenseArgs (node, IDXS_INDCTRS)
		if node.end_byte not in skipNodesAtPositions and not (nodeTxt.endswith(';') and node.end_byte == len(txt) - 1):
			if inVarDeclrn:
				nodeTxt = 'var '
			AddToOutput (nodeTxt)
		if currentFunc and AtEndOfHierarchy(currentFunc, node):
			funcBodyPrefix = ''
			if not debug:
				for varName in currentFuncVarsNames:
					funcBodyPrefix += varName + ','
				if funcBodyPrefix != '':
					funcBodyPrefix = chr(VAR_REPLACE_CHAR_VAL) + funcBodyPrefix[: -1] + ';'
			funcBodyStartIdx = currentFuncTxt.find('{') + 1
			currentFuncName = ''
			currentFunc = None
			currentFuncVarsNames = []
			AddToOutput (currentFuncTxt[: funcBodyStartIdx] + funcBodyPrefix + currentFuncTxt[funcBodyStartIdx :])
			currentFuncTxt = ''
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
			mangledMembers[nodeTxt] = dict(mangledMembers[''])
		if nextSibling and (isOfOrIn or node.type in ['new', 'case', 'class', 'delete', 'return', 'function'] or (node.type == 'else' and nextSibling.type in ['if_statement', 'lexical_declaration', 'variable_declaration', 'expression_statement'])) and nextSibling.type not in ['{', 'array']:
			AddToOutput (' ')
	for child in node.children:
		WalkTreePass2 (child)
	if node.type in ['lexical_declaration', 'variable_declaration', 'expression_statement'] and not nodeTxt.endswith(';') and (not nextSibling or nextSibling.type != '}') and node.end_byte < len(txt) - 1:
		AddToOutput (';')

def AddToOutput (add : str):
	global output, currentFuncTxt
	if currentFunc:
		currentFuncTxt += add
	else:
		output += add

def TryMangleOrMapNode (node) -> str:
	nodeTxt = node.text.decode('utf-8')
	if node.type == 'identifier':
		return TryMangleNode(node)
	elif node.type == 'property_identifier':
		siblingIdx = node.parent.children.index(node)
		if node.parent.children[siblingIdx - 2].text.decode('utf-8') not in JS_NAMES:
			if nodeTxt in userClassFuncs:
				if node.parent.type in ['method_definition', 'member_expression']:
					return TryMangleNode(node)
				elif siblingIdx > 1 and node.parent.children[siblingIdx - 2].type == 'this':
					return TryMangleNode(node)
			elif (siblingIdx < len(node.parent.children) - 1 and node.parent.children[siblingIdx + 1] == '()') or node.parent.parent.type == 'call_expression' and len(nodeTxt) <= len(string.ascii_letters) and len(nodeTxt) > 2:
				nodeTxt = nodeTxt[2] + chr(len(nodeTxt) + 96)
	return nodeTxt

def TryMangleNode (node) -> str:
	nodeTxt = node.text.decode('utf-8')
	if len(nodeTxt) == 1 or nodeTxt in JS_NAMES:
		return nodeTxt
	if nodeTxt not in mangledMembers[currentFuncName]:
		usedNames_ = usedNames[currentFuncName]
		unusedNameIdx = 0
		if unusedNames[currentFuncName] != []:
			unusedNameIdx = random.randint(0, len(unusedNames[currentFuncName]) - 1)
		while not currentFunc or unusedNames[currentFuncName] == [] or nodeTxt in usedNames_:
			unusedName = random.choice(OKAY_NAME_CHARS) + random.choice(OKAY_NAME_CHARS)
			if unusedName not in usedNames_ + JS_NAMES:
				unusedNames[currentFuncName].append(unusedName)
				unusedNameIdx = len(unusedNames[currentFuncName]) - 1
				break
		mangledMembers[currentFuncName][nodeTxt] = unusedNames[currentFuncName].pop(unusedNameIdx)
		mangledMember = mangledMembers[currentFuncName][nodeTxt]
		usedNames[currentFuncName].append(mangledMember)
	nodeTxt = mangledMembers[currentFuncName][nodeTxt]
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
	if argCnt < len(argsCntsIndctrsVals):
		AddToOutput (chr(argsCntsIndctrsVals[argCnt]))
		skipNodesAtPositions.append(node.end_byte)
		skipNodesAtPositions.append(siblings[len(siblings) - 1].end_byte)
	else:
		skipNodesAtPositions = []

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

# def GetTerserCommand (filePath : str):
# 	return ['terser', filePath, '-o', filePath, '-c', 'booleans_as_integers', '-c', 'ecma=2025', '-c', 'keep_fargs=false', '-c', 'unsafe', '-c', 'unsafe_arrows', '-c', 'unsafe_comps', '-c', 'unsafe_Function', '-c', 'unsafe_math', '-c', 'unsafe_symbols', '-c', 'unsafe_methods', '-c', 'unsafe_proto', '-c', 'unsafe_regexp', '-c', 'unsafe_undefined', '-m', 'eval', '-m', 'toplevel', '--mangle-props', 'keep_quoted="strict"']

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
currentFuncName = '.'
currentFunc = 1
WalkTreePass1 (tree.root_node)
# for funcName in varsCnts:
# 	funcVarsCnts = varsCnts[funcName]
# 	funcVarsCnts = dict(sorted(funcVarsCnts.items(), key = lambda x : x[1]))
# 	if funcName != '':
# 		maxLocalVarsCnt = max(maxLocalVarsCnt, list(funcVarsCnts.values())[-1])
# 	varsCnts[funcName] = funcVarsCnts
currentFuncName = ''
currentFunc = None
WalkTreePass2 (tree.root_node)
# funcReplaceCode = '''
# a=`function ${name}(`
# for(b=97;b<105;b++)a+=String.fromCharCode(b)+','
# a+='){var '
# for(b=105;b<123;b++)b+=String.fromCharCode(b)+'=0,'
# a+=';'
# for(b=65;b<90;b++){c=String.fromCharCode(b)
# a+=`let ${c}=window.${c}${c};`}
# a+= body+'}'
# '''
if debug:
	output = DOM_AND_CSS_REMAP_CODE + output
else:
	output = DOM_AND_CSS_REMAP_CODE + 'a=`' + output + '`\n' + ARGS_AND_IDXS_CONDENSE_CODE + '\neval(d)'
open(outputPath, 'w').write(output)
if compress:
	Compress (outputPath)