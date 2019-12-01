import json
import numpy as np
from metric_learn import NCA
import pickle
data = json.load(open("dataset_medium.json",'r'))
sample = list()
target = list()
for i in range(0,len(data['file_path'])):
    temp = list()
    temp.append(data['nbbs'][i])
    temp.append(data['outdegree'][i])
    temp.append(data['nlocals'][i])
    temp.append(data['edges'][i])
    temp.append(data['nargs'][i])
    temp.append(data['T'][i])
    temp.append(data['A'][i])
    temp.append(data['L'][i])
    temp.append(data['All'][i])
    sample.append(temp)
    target.append(data['file_path'][i] + data['function_name'][i])
X = np.array(sample)
y = np.array(target)
print(X)
print(y)
print("Len X = ",len(X),"len Y is ",len(y))
nca = NCA(init=None, max_iter=100, n_components=None, num_dims='deprecated', preprocessor=None, random_state=42, tol=None, verbose=False)
nca.fit(X, y)
# Print Mahalanobis Matrix
# To implement kNN using Mahalanobis metric read metric_learn
distance_metric = nca.get_mahalanobis_matrix()
distance_metric_function = nca.get_metric()
print(distance_metric)
pickle.dump(distance_metric, open("distance_metric.pickle", 'wb'))
pickle.dump(distance_metric_function, open("distance_metric_func.pickle", 'wb'))
