#CredentialsImport - imports credentials
def CRImport(file):
	with open(file) as fdata:
		lines = fdata.readlines()
	cred = {}
	for line in lines:
		line = line.split("=")
		cred[line[0].strip()] = line[1].strip()
	return cred