import os, sys, math, string, random, subprocess, tree_sitter_javascript as tsjs
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
PRINT_DOM_MAP_CODE = '''for (o of [Element, Node, Array, String, Window, Document, XMLHttpRequest, EventTarget])
{
	p = o.prototype
	console.log(o)
	for (n of Object.getOwnPropertyNames(p))
	{
		try
		{
			console.log(p[n].name, n)
		}
		catch(e)
		{
		}
	}
}'''
DOM_AND_CSS_MAP_CODE = '''for(o of[Element,Node,Array,String,Window,Document,XMLHttpRequest,EventTarget]){p=o.prototype
for(n of Object.getOwnPropertyNames(p)){try{p[n[0]]=p[n]
p[n[n.length-1]]=p[n]
p[n[Math.ceil(n.length/2)]]=p[n]
p[n[Math.ceil(n.length*.6)]+n[Math.ceil(n.length/4)]]=p[n]
p[n[Math.ceil(n.length/3)]+n[Math.ceil(n.length*.8)]]=p[n]
p[n[0]+n[Math.ceil(n.length/2)]+n[n.length-2]]=p[n]}catch(e){}}}for(n in document.body.style){f=eval(function(a){this.style[`_{n}`]=a})
Element.prototype['_'+n[0]+n[n.length-1]]=f}'''
FUNC_REPLACE_CODE = '''a=`function ${n}(`
for(b=97;b<105;b++)a+=String.fromCharCode(b)+','
a+='){var '
for(b=105;b<123;b++)b+=String.fromCharCode(b)+'=0,'
a+=';'
for(b=65;b<90;b++){c=String.fromCharCode(b)
a+=`var ${c}=window.${c}${c};`}
a+= body+`}`'''
_thisDir = os.path.split(os.path.abspath(__file__))[0]
domList = open(os.path.join(_thisDir, 'DomList'), 'r').read()
VAR_REPLACE_CHAR_VAL = 17
WINDOW_REPLACE_CHAR_VAL = 18
ARGS_AND_IDXS_CONDENSE_CODE = '''d=''
CA(''' + str(ARGS_INDCTRS).replace(' : ', ':').replace(', ', ',') + ''','(',')')
a=d
d=''
CA(''' + str(IDXS_INDCTRS).replace(' ', '') + ''','[',']')
function CA(e,f,g){for(p=0;p<a.length;p++){c=a[p]
l=e.indexOf(c.charCodeAt(0))
if(l>-1){d+=f
p++
for(i=0;i<=l;i++){d+=a[p]
if(i<l){d+=','
p++}}d+=g}else d+=c}}'''
FUNC_START_CHAR_VAL = 19
FUNC_END_CHAR_VAL = 20
OKAY_NAME_CHARS = list(string.ascii_letters)
DONT_MANGLE_SUB_MEMBERS = ['Math', 'JSON', 'console']
DONT_MANGLE = DONT_MANGLE_SUB_MEMBERS + ['window', 'document', 'String', 'cancel', 'requestAnimationFrame', 'parseInt', 'parseFloat', 'cssText', 'charCodeAt', 'Infinity', 'if', 'do', 'of', 'in']
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
mangledNames = {}
mangledNames[currentFuncName] = {}
usedNames = {}
usedNames[currentFuncName] = ['_', '$', 'CA']
skipNodesAtPositions = []
# varsCnts = {}
# userClassFuncsCnts = {}
# maxLocalVarsCnt = 0
domMap = {}
userClassFuncs = []
compress = True
debug = False
usedDomNames = []

def WalkTreePass1 (node):
	global currentFunc
	nodeTxt = node.text.decode('utf-8')
	print(node.type, nodeTxt)
	# isIdentifier = node.type == 'identifier'
	# if node.type == 'assignment_expression':
	# 	AddToVarCount (node.children[0])
	# elif isIdentifier:
	# 	AddToVarCount (node)
	if node.type == 'property_identifier' and node.parent.type == 'method_definition' and node.parent.parent.type == 'class_body':
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
	global output, currentFunc, usedNames, unusedNames, mangledNames, currentFuncTxt, currentFuncName, currentFuncVarsNames, skipNodesAtPositions
	nodeTxt = node.text.decode('utf-8')
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
		# if nodeTxt == 'style':
		# 	parent2 = node.parent.parent
		# 	parentIdx = parent2.children.index(node.parent)
		# 	if len(parent2.children) > parentIdx + 1:
		# 		node2 = parent2.children[parentIdx + 1]
		# 		if node2.text == b'.':
		# 			node3 = parent2.children[parentIdx + 2]
		# 			node3Txt = node3.text.decode('utf-8')
		# 			skipNodesAtPositions.append(node.end_byte)
		# 			skipNodesAtPositions.append(node2.end_byte)
		# 			skipNodesAtPositions.append(node3.end_byte)
		# 			AddToOutput ('_' + node3Txt[0] + node3Txt[-1])
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
		# elif not debug and nextSibling:
		# 	if node.type == '(' and nextSibling.type != 'binary_expression':
		# 		CondenseArgs (node, ARGS_INDCTRS)
		# 	elif node.type == '[' and nextSibling.type != 'array':
		# 		CondenseArgs (node, IDXS_INDCTRS)
		if node.end_byte not in skipNodesAtPositions and not (nodeTxt.endswith(';') and node.end_byte == len(txt) - 1) and node.type != 'function':
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
			AddToOutput (chr(FUNC_START_CHAR_VAL) + funcBodyPrefix + currentFuncTxt[funcBodyStartIdx :] + chr(FUNC_END_CHAR_VAL))
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
			mangledNames[nodeTxt] = dict(mangledNames[''])
		if nextSibling and (isOfOrIn or node.type in ['new', 'case', 'class', 'delete', 'return'] or (node.type == 'else' and nextSibling.type in ['if_statement', 'lexical_declaration', 'variable_declaration', 'expression_statement'])) and nextSibling.type not in ['{', 'array']:
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
	if nodeTxt in DONT_MANGLE:
		return nodeTxt
	if node.type == 'identifier':
		return TryMangleNode(node)
	elif node.type == 'property_identifier':
		siblingIdx = node.parent.children.index(node)
		if node.parent.children[siblingIdx - 2].text.decode('utf-8') not in DONT_MANGLE_SUB_MEMBERS:
			if nodeTxt in userClassFuncs and (node.parent.type in ['method_definition', 'member_expression'] or (siblingIdx > 1 and node.parent.children[siblingIdx - 2].type == 'this')):
				return TryMangleNode(node)
			elif len(nodeTxt) > 2 and ((siblingIdx < len(node.parent.children) - 1 and node.parent.children[siblingIdx + 1] == '()') or node.parent.parent.type == 'call_expression'):
				if nodeTxt not in usedDomNames:
					usedDomNames.append(nodeTxt)
				nodeTxt = domMap[nodeTxt]
	return nodeTxt

def TryMangleNode (node) -> str:
	nodeTxt = node.text.decode('utf-8')
	if len(nodeTxt) == 1 or nodeTxt in DONT_MANGLE:
		return nodeTxt
	usedNames_ = usedNames[currentFuncName] + usedNames['']
	siblingIdx = node.parent.children.index(node)
	inVarDeclrn = siblingIdx > 0 and node.parent.children[siblingIdx - 1].type in ['const', 'var', 'let']
	if nodeTxt not in usedNames_ or inVarDeclrn:
		unusedNameIdx = 0
		if currentFunc and (unusedNames[currentFuncName] != [] or inVarDeclrn):
			unusedNameIdx = random.randint(0, len(unusedNames[currentFuncName]) - 1)
		else:
			while unusedNames[currentFuncName] == [] or nodeTxt not in usedNames_ or inVarDeclrn:
				unusedName = random.choice(OKAY_NAME_CHARS) + random.choice(OKAY_NAME_CHARS)
				if unusedName not in DONT_MANGLE + usedNames_:
					unusedNames[currentFuncName].append(unusedName)
					unusedNameIdx = len(unusedNames[currentFuncName]) - 1
					break
		mangledName = unusedNames[currentFuncName].pop(unusedNameIdx)
		mangledNames[currentFuncName][nodeTxt] = mangledName
		usedNames[currentFuncName].append(mangledName)
		if currentFuncName != '':
			mangledNames[''][nodeTxt] = mangledName
			usedNames[''].append(mangledName)
	nodeTxt = mangledNames[currentFuncName][nodeTxt]
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

def GetDomMap (name : str):
	output = []
	output.append(name[0])
	output.append(name[-1])
	output.append(name[math.ceil(len(name) / 2)])
	if len(name) > math.ceil(len(name) * .6):
		output.append(name[math.ceil(len(name) * .6)] + name[math.ceil(len(name) / 4)])
		if len(name) > math.ceil(len(name) * .8):
			output.append(name[math.ceil(len(name) / 3)] + name[math.ceil(len(name) * .8)])
	output.append(name[0] + name[math.ceil(len(name) / 2)] + name[-2])
	return output

def Compress (filePath : str) -> str:
	cmd = ['gzip', '--keep', '--force', '--verbose', '--best', filePath]
	subprocess.check_call(cmd)
	return open(filePath + '.gz', 'rb').read()

# def GetTerserCommand (filePath : str):
# 	return ['terser', filePath, '-o', filePath, '-c', 'booleans_as_integers,ecma=2025,keep_fargs=false,unsafe,unsafe_arrows,unsafe_comps,unsafe_Function,unsafe_math,unsafe_symbols,unsafe_methods,unsafe_proto,unsafe_regexp,unsafe_undefined', '-m', 'eval,toplevel', '--mangle-props', 'builtins,keep_quoted="strict"']

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

domMapTxt = open(os.path.join(_thisDir, 'DomMap'), 'r').read()
for line in domMapTxt.split('\n'):
	clauses = line.split()
	domName = clauses[0]
	mapToIdx = int(clauses[1])
	if len(domName) <= math.ceil(len(domName) * .6) and mapToIdx > 2:
		mapToIdx -= 1
	if len(domName) <= math.ceil(len(domName) * .8) and mapToIdx > 3:
		mapToIdx -= 1
	domMap[domName] = GetDomMap(domName)[mapToIdx]
jsBytes = txt.encode('utf-8')
tree = PARSER.parse(jsBytes, encoding = 'utf8')
WalkTreePass1 (tree.root_node)
# for funcName in varsCnts:
# 	funcVarsCnts = varsCnts[funcName]
# 	funcVarsCnts = dict(sorted(funcVarsCnts.items(), key = lambda x : x[1]))
# 	if funcName != '':
# 		maxLocalVarsCnt = max(maxLocalVarsCnt, list(funcVarsCnts.values())[-1])
# 	varsCnts[funcName] = funcVarsCnts
WalkTreePass2 (tree.root_node)
if debug:
	output = DOM_AND_CSS_MAP_CODE + output
else:
	# output = DOM_AND_CSS_MAP_CODE + 'a=`' + output + '`\n' + ARGS_AND_IDXS_CONDENSE_CODE + '\neval(d)'
	output = DOM_AND_CSS_MAP_CODE + 'a=`' + output + '`\n' + FUNC_REPLACE_CODE + '\neval(a)'
open(outputPath, 'w').write(output)
if compress:
	Compress (outputPath)
print(usedDomNames)