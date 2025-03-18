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
unusedNames = []
unusedNames.extend(OKAY_NAME_CHARS)
mangledMembers = {}
usedNames = []

def WalkTree (node):
	global output, nodeText, remappedOutput, remappedNodeText
	nodeText = node.text.decode('utf-8')
	print(node.type, nodeText)
	remappedNodeText = nodeText
	if len(node.children) == 0:
		isOf = node.type == 'of'
		if node.type == 'identifier':
			TryMangleNode (node)
		elif node.type == 'property_identifier':
			if nodeText in MEMBER_REMAP:
				remappedNodeText = MEMBER_REMAP[nodeText]
			else:
				siblingIdx = node.parent.children.index(node)
				if siblingIdx > 1 and node.parent.children[siblingIdx - 2].type == 'this':
					TryMangleNode (node)
		elif isOf:
			AddToOutputs (' ')
		output += nodeText
		remappedOutput += remappedNodeText
		if isOf or node.type in ['return', 'class', 'function']:
			siblingIdx = node.parent.children.index(node)
			if len(node.parent.children) > siblingIdx + 1 and node.parent.children[siblingIdx + 1].type in ['identifier', 'binary_expression', 'call_expression', 'member_expression', 'subscript_expression', 'false', 'true']:
				AddToOutputs (' ')
		elif node.type == 'else':
			siblingIdx = node.parent.children.index(node)
			if len(node.parent.children) > siblingIdx + 1 and node.parent.children[siblingIdx + 1].type in ['if_statement', 'lexical_declaration', 'variable_declaration']:
				AddToOutputs (' ')
		elif node.type == 'new':
			AddToOutputs (' ')
	for n in node.children:
		WalkTree (n)
	if node.type in ['lexical_declaration', 'variable_declaration', 'expression_statement'] and not nodeText.endswith(';'):
		AddToOutputs (';')
	elif node.type in ['var', 'let']:
		AddToOutputs (' ')

def AddToOutputs (add : str):
	global output, remappedOutput
	output += add
	remappedOutput += add

def TryMangleNode (node):
	global nodeText, remappedNodeText
	if len(nodeText) > 1:
		if nodeText not in mangledMembers:
			while len(unusedNames) == 0:
				unusedName = random.choice(OKAY_NAME_CHARS) + random.choice(OKAY_NAME_CHARS)
				if unusedName not in MEMBER_REMAP.values() and unusedName not in mangledMembers and unusedName not in usedNames and unusedName not in ['if', 'do', 'of', 'in']:
					unusedNames.append(unusedName)
			mangledMembers[nodeText] = unusedNames.pop(random.randint(0, len(unusedNames) - 1))
			if mangledMembers[nodeText] not in usedNames:
				usedNames.append(mangledMembers[nodeText])
		if nodeText in mangledMembers:
			nodeText = mangledMembers[nodeText]
			remappedNodeText = nodeText
	elif nodeText not in usedNames:
		usedNames.append(nodeText)

def Compress (filePath : str):
	cmd = ['gzip', '--keep', '--force', '--verbose', '--best', outputPath]
	subprocess.check_call(cmd)
	jsZipped = open(outputPath + '.gz', 'rb').read()
	return base64.b64encode(jsZipped).decode('utf-8')

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
outputWithDecompression = '''u=async(u,t)=>{d=new DecompressionStream('gzip')
r=await fetch('data:application/octet-stream;base64,'+u)
b=await r.blob()
s=b.stream().pipeThrough(d)
o=await new Response(s).blob()
return await o.text()}
u("%s",1).then((j)=>{eval(j)})''' %jsBytes
# if len(output) > len(outputWithDecompression):
# 	output = outputWithDecompression
print(output)
open(outputPath, 'w').write(output)
Compress (outputPath)