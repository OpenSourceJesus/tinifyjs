import os, sys, string, base64, random, subprocess, tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser

JS_LANG = Language(tsjs.language())
PARSER = Parser(JS_LANG)
TEXT_INDICATOR = '-t='
INPUT_INDICATOR = '-i='
OUTPUT_INDICATOR = '-o='
REMAP_CODE = '''m={}
for(o of [Element,Node,String,Array,Document]){p=o.prototype
for(n of Object.getOwnPropertyNames(p)){s=0
e=n.length-1
a=n[s]
while(a in m){s++
a=n[s]+n[e]
e--}try{p[a]=p[n]
m[a]=1}catch(e){}}}'''
OKAY_NAME_CHARS = list(string.ascii_letters + '$_')
OKAY_NAME_CHARS.remove('m')
JS_NAMES = ['Math', 'document']
WHITESPACE_EQUIVALENT = string.whitespace + ';'
MEMBER_REMAP = {}
_thisDir = os.path.split(os.path.abspath(__file__))[0]
memberRemap = open(os.path.join(_thisDir, 'MemberRemap'), 'r').read()
for line in memberRemap.split('\n'):
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
usedNames = {}
usedNames[currentFuncName] = []

def WalkTree (node):
	global output, nodeText, currentFunc, remappedOutput, remappedNodeText
	nodeText = node.text.decode('utf-8')
	print(node.type, nodeText)
	remappedNodeText = nodeText
	if len(node.children) == 0:
		siblingIdx = node.parent.children.index(node)
		if (node.type == 'identifier' and siblingIdx > 0 and node.parent.children[siblingIdx - 1].type == 'function') or (node.type == 'property_identifier' and node.parent.type == 'method_definition'):
			currentFuncName = nodeText
			currentFunc = node
			unusedNames[currentFuncName] = []
			unusedNames[currentFuncName].extend(OKAY_NAME_CHARS)
			usedNames[currentFuncName] = []
		isOfOrIn = node.type in ['of', 'in']
		mangleOrRemapResults = TryMangleOrRemapNode(node)
		remappedNodeText = mangleOrRemapResults[0]
		if mangleOrRemapResults[1]:
			nodeText = remappedNodeText
		if isOfOrIn:
			AddToOutputs (' ')
		if nodeText == 'let':
			nodeText = 'var'
			remappedNodeText = 'var'
		output += nodeText
		remappedOutput += remappedNodeText
		hasNextSibling = len(node.parent.children) > siblingIdx + 1
		nextSiblingType = None
		if hasNextSibling:
			nextSiblingType = node.parent.children[siblingIdx + 1].type
		if hasNextSibling and (((isOfOrIn or node.type in ['return', 'class', 'function']) and nextSiblingType in ['identifier', 'binary_expression', 'call_expression', 'member_expression', 'subscript_expression', 'false', 'true']) or (node.type == 'else' and nextSiblingType in ['if_statement', 'lexical_declaration', 'variable_declaration'])):
			AddToOutputs (' ')
		elif node.type == 'new':
			AddToOutputs (' ')
		if currentFunc and AtEndOfHierarchy(currentFunc, node):
			currentFuncName = ''
			currentFunc = None
	for n in node.children:
		WalkTree (n)
	if node.type in ['lexical_declaration', 'variable_declaration', 'expression_statement'] and not nodeText.endswith(';') and node.end_byte < len(text) - 1:
		AddToOutputs (';')
	elif node.type in ['var', 'let']:
		AddToOutputs (' ')

def AddToOutputs (add : str):
	global output, remappedOutput
	output += add
	remappedOutput += add

def TryMangleOrRemapNode (node) -> (str, bool):
	nodeText = node.text.decode('utf-8')
	if node.type == 'identifier':
		return (TryMangleNode(node), True)
	elif node.type == 'property_identifier':
		if nodeText in MEMBER_REMAP:
			return (MEMBER_REMAP[nodeText], False)
		elif node.parent.type == 'method_definition':
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
	usedNames_ = usedNames[currentFuncName]
	if len(nodeText) > 1:
		if nodeText not in mangledMembers:
			unusedNames_ = unusedNames[currentFuncName]
			while len(unusedNames_) == 0:
				unusedName = random.choice(OKAY_NAME_CHARS) + random.choice(OKAY_NAME_CHARS)
				if unusedName not in MEMBER_REMAP.values() and unusedName not in mangledMembers and unusedName not in usedNames_ and unusedName not in ['if', 'do', 'of', 'in']:
					unusedNames[currentFuncName].append(unusedName)
			mangledMembers[nodeText] = unusedNames_.pop(random.randint(0, len(unusedNames_) - 1))
			if mangledMembers[nodeText] not in usedNames_:
				usedNames[currentFuncName].append(mangledMembers[nodeText])
		if nodeText in mangledMembers:
			nodeText = mangledMembers[nodeText]
	elif nodeText not in usedNames_:
		usedNames[currentFuncName].append(nodeText)
	return nodeText

def AtEndOfHierarchy (root, node) -> bool:
	if not root.text.decode('utf-8').endswith(node.text.decode('utf-8')):
		return False
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
print(output)
open(outputPath, 'w').write(output)
jsBytes = Compress(outputPath)
base64EncodedJsBytes = base64.b64encode(jsBytes).decode('utf-8')
outputWithDecompression = '''u=async(u,t)=>{d=new DecompressionStream('gzip')
r=await fetch('data:application/octet-stream;base64,'+u)
b=await r.blob()
s=b.stream().pipeThrough(d)
o=await new Response(s).blob()
return await o.text()}
u("%s",1).then((j)=>{eval(j)})''' %base64EncodedJsBytes
open(outputPath, 'w').write(outputWithDecompression)
jsBytesWithDecompression = Compress(outputPath)
if len(jsBytes) > len(jsBytesWithDecompression):
	output = outputWithDecompression
print(output)
open(outputPath, 'w').write(output)
Compress (outputPath)