import ast, csv

num = int(raw_input("How many files? "))
ofile = csv.writer(file('otraining.csv', 'w'))
dfile = csv.writer(file('dtraining.csv', 'w'))


o_training_data = []
d_training_data = []

for i in range(1, num):
	file = open(str(i), "r")
	for line in file:
                partitionedLine = line.partition(' = ')
                name = partitionedLine[0]
                features = ast.literal_eval(partitionedLine[2])
		if name == 'basicQlearningAgent':
			o_training_data.append(features.values())
		else:
			d_training_data.append(features.values())

print o_training_data
ofile.writerows(o_training_data)
dfile.writerows(d_training_data)	
