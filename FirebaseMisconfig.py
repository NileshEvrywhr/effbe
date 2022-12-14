#!/usr/bin/python3

import os
import sys
import ntpath
import re
import urllib3
import hashlib
from icecream import ic
ic.configureOutput("DEBUG ‣ ")

rootDir = os.path.expanduser("~") + "/.SourceCodeAnalyzer/" #ConfigFolder ~/.SourceCodeAnalyzer/
projectDir = ""
apkFilePath = ""
apkFileName = ""
firebaseProjectList = []
inScopeUrls = []
apkHash = ""
apktoolPath = "./Dependencies/apktool_2_6_1.jar"

def isNewInstallation():

	if (os.path.exists(rootDir) == False):
		ic("new installation detected")
		os.mkdir(rootDir)
		return True
	else:
		return False

def isValidPath(apkFilePath):

	global apkFileName
	ic("checking if the APK file path is valid")
	
	if (os.path.exists(apkFilePath) == False):
		print("Incorrect APK file path found. Please try again with correct file name.")
		exit(1)
	else:
		print("APK File Found.")
		apkFileName = ntpath.basename(apkFilePath)

def reverseEngineerApplication(apkFileName):
	
	global projectDir
	ic("initiating APK Decompilation Process.")
	projectDir = rootDir + apkFileName + "_" + hashlib.md5().hexdigest()
	
	if (os.path.exists(projectDir) == True):
		print("The same APK is already decompiled. Skipping decompilation and proceeding with scanning application.")
		return projectDir
	os.mkdir(projectDir)
	print("Decompiling the APK file using APKtool.")
	result = os.system("java -jar " + apktoolPath + " d " + "--output " + '"' + projectDir + "/apktool/" + '"' + ' "' + apkFilePath + '"' + '>/dev/null')
	
	if (result!=0):
		print("Apktool failed with exit status "+str(result)+". Please Try Again.")
		exit(1)
	ic("successfully decompiled the application. proceeding with enumeraing firebase project names from the application code.")

def findFirebaseProjectNames():

	global firebaseProjectList
	regex = b"https*://(.+?)\.firebaseio.com"
	
	for dir_path, dirs, file_names in os.walk(rootDir + apkFileName + "_" + hashlib.md5().hexdigest()):
		for file_name in file_names:
			fullpath = os.path.join(dir_path, file_name)			
			with open(fullpath, "rb") as f: 	
				contents = f.read()
				
				temp = re.findall(regex, contents)

				# matches = re.finditer(regex, contents, re.MULTILINE)
				# for matchNum, match in enumerate(matches, start=1):
				# 	print ("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchNum, start = match.start(), end = match.end(), match = match.group()))
				# 	for groupNum in range(0, len(match.groups())):
				# 		groupNum = groupNum + 1
				# 		print ("Group {groupNum} found at {start}-{end}: {group}".format(groupNum = groupNum, start = match.start(groupNum), end = match.end(groupNum), group = match.group(groupNum)))

				if (len(temp) != 0):
					print(f"{file_name}: {len(temp)} Firebase Instance(s) Found")
					ic(fullpath)
					with open("Projects.txt", "ab") as file:
						for proj in temp:
							# writes to Projects.txt							
							file.write(proj + b'\n')

							# adds to internal list for further scanning
							ins = "".join([chr(x) for x in proj])
							firebaseProjectList.append(ins)
		

	if (len(firebaseProjectList) == 0):
		print("No Firebase Project Found. Taking an exit!\nHave an nice day.")
		exit(0)

def printFirebaseProjectNames():
	print("Found " + str(len(firebaseProjectList)) + " Project References in the application. Printing the list of Firebase Projects found.")
	print(firebaseProjectList)
	
def scanInstances():
	ic.enable()
	ic("Scanning Firebase Instance(s)")
	for proj in firebaseProjectList:
		url = 'https://' + proj + '.firebaseio.com/.json'
		try:
			# NOT using python requests bcoz it has certain disadvantages w.r.t certificate management for HTTPS URLs 
			http = urllib3.PoolManager()
			response = http.request('GET', url)

			if (response.status == 200):
				print(f"Misconfigured Firebase Instance Found: {proj} {url}")
				with open("MisconfiguredProjects.txt","a") as f:
					f.write(f"{proj} - {url}\n")
			else:
				print(f"{proj}: {response.status} {response.reason}")
				
		except urllib3.exceptions.LocationParseError as err:
			print(f"label empty or too long, not sure how we got this: {err}")
			continue
		except urllib3.exceptions.SSLError as err:
			print(f"SSL is doing its thing: {err}")
			continue

if (len(sys.argv) < 3):
	print("Please provide the required arguments to initiate scanning.")
	print("Usage: python3 FirebaseMisconfig.py [options]")
	print("\t-p/--path <apkPathName>")
	print("\t-f/--firebase <commaSeperatedFirebaseProjectName>")
	print("Please try again!!") 
	exit(1);

if (sys.argv[1] == "-p" or sys.argv[1] == "--path"):
	apkFilePath = sys.argv[2];
	isNewInstallation()
	isValidPath(apkFilePath)
	reverseEngineerApplication(apkFileName)
	findFirebaseProjectNames()
	printFirebaseProjectNames()
	scanInstances()

if (sys.argv[1] == "-f" or sys.argv[1] == "--firebase"):
	firebaseProjectList = sys.argv[2].split(",")
	isNewInstallation()
	scanInstances()

if (sys.argv[1] == "-l" or sys.argv[1] == "--list"):
	filename = sys.argv[2]

	with open(filename, "r") as f:
		projects = f.readlines()
		for project in projects:
			firebaseProjectList.append(project[:-1])
	isNewInstallation()
	scanInstances()
