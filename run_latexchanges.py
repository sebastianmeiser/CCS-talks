import sys, time
import os
import subprocess

WHOAMIFILE = "whoami.txt"

MACROTEMPLATES = ["NEW","REPLACE","MESSAGE","REMOVE"]

def scan_for_initials(files):
	# Scanning for \usepackage[...]{uchanges}
	for f  in files:
		ifile =  open(f,"r")
		for line in ifile:
			if "\\usepackage" in line and "{uchanges}" in line:
				print("found package uchanges in file "+f)
				if "users=" not in line:
					print("However, parameter [users=...] is missing")
				else:
					initials = line[line.find("users=")+6:]
					initials = initials[:initials.find("]")]
					print("Initials: "+initials)
					return initials
		ifile.close()

def get_timestamp():
	return time.strftime("%y%m%d")

# Replaces simple macros by their more complex versions	
def replace_simple(initials, string):
	global MACROTEMPLATES
	for mac in MACROTEMPLATES:
		for i in initials:
			others = "".join([j for j in initials if j != i])
			string = string.replace("\\"+mac+i+"{", "\\"+mac+i+"for{"+others+"}{"+get_timestamp()+"}{")
	return string

def parse_for_par(ctr,line,remove_par):
	for i in range(len(line)):
		c = line[i]
		if c == "}":
			if ctr == 0:
				if remove_par == "+":
					return 0,line[:i]+line[i+1:],""
				elif remove_par == "-":
					return 0,line[i+1:],""
				elif remove_par == "-+":
					return parse_for_par(0,line[i+1:],"{")
			else:
				ctr -=1
		if c == "{":
			if remove_par == "{":
				return parse_for_par(0,line[i+1:],"+")
			else:
				ctr+=1
	if remove_par == "+":
		return ctr, line, remove_par
	else:
		assert(remove_par != "")
		return ctr, "\n", remove_par
		
	
# Parses and modifies a complete file. For every line, replace_simple is applied and redundant macros are removed.
def do_file(ins,fname):

	#open the file of interest
	infile = open(fname,"r")

	#open temporary output file
	outfile = open(fname+".tmp","w")
	
	# We will remember whether or not we removed a macro. Since we only remove one at a time, this will help us get a fixpoint.
	removed_macro = False
	remove_par = ""
	counter = 0
	for line in infile:
		line = replace_simple(ins,line)
		if remove_par != "":
			counter,line,remove_par = parse_for_par(0,line,remove_par)
		else:
			for i in initials:
				if remove_par!="":
					continue
				pos=mylen = 0
				# NEW statements
				if "\\NEW"+i+"for{}" in line:
					pos = line.find("\\NEW"+i+"for{}")
					remove_par = "+"
					mylen = 10
				# REMOVE statements
				elif "\\REMOVE"+i+"for{}" in line:
					pos = line.find("\\REMOVE"+i+"for{}")
					remove_par="-"
					mylen = 13
				elif "\\REPLACE"+i+"for{}" in line:
					pos = line.find("\\REPLACE"+i+"for{}")
					remove_par="-+"
					mylen = 14
				elif "\\MESSAGE"+i+"for{}" in line:
					pos = line.find("\\MESSAGE"+i+"for{}")
					remove_par="-"
					mylen = 14
					
				if remove_par!="":
					print("Removing a macro in file "+fname)

					removed_macro=True
					line_pre = line[:pos]
					line_rest= line[pos+mylen:]
					
					#remove timestamp part and the opening parenthesis
					line_rest= line_rest[line_rest.find("}")+2:]
					counter,line_rest,remove_par = parse_for_par(0,line_rest,remove_par)
					line = line_pre + line_rest

		outfile.write(line)
	infile.close()
	outfile.close()
	
	os.remove(fname)
	os.rename(fname+".tmp", fname)

	# If we removed a macro, we repeat the procedure (to capture nested macros)
	if removed_macro:
		do_file(ins,fname)
	
while True:
	texfiles = []

	for path, subdirs, files in os.walk("."):
		for name in files:
			if name[-4:] == ".tex":
				texfiles.append(os.path.join(path, name).replace("\\","/").replace("./",""))

	#print("Running the script for these files:"+str(texfiles))

	# Scan the files for \usepackage[users=XZY]{uchanges} and write XZY into initials
	initials = scan_for_initials(texfiles)			
	print("inits: "+str(initials))

	# find out who the user is, i.e., read or create if not exists the file WHOAMIFILE with a line \iam X
	initial=""
	if not os.path.isfile(WHOAMIFILE):
		print("File whoami.txt not found.")
		if sys.version_info.major < 3:
			initial = raw_input("Who are you? (please enter your initial): ")
		else:
			initial = input("Who are you? (please enter your initial): ")
		initial = initial.lstrip()[0].upper()
		whofile = open(WHOAMIFILE,"w")
		whofile.write("\iam "+initial)
		whofile.close()
		print("Okay, stored your initial as "+initial)
	else:
		ifile = open(WHOAMIFILE,"r")
		for line in ifile:
			initial = line.strip()[-1]
			print("File "+WHOAMIFILE+" found; you are "+initial)

	if initial not in initials:
		print("Your initial "+initial+" is not in the initials "+initials)


	for t in texfiles:
		do_file(initials,t)
	print("Sleeping for 5 minutes.")
	time.sleep(300)

