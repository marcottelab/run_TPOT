import os
import argparse
import numpy as np
import pandas as pd
import sklearn.metrics
from sklearn.externals import joblib

parser = argparse.ArgumentParser("Predict using a serialized sklearn model")
parser.add_argument("--datafile", required=True, help="Feature file, no labels, ids are in first two columns")
parser.add_argument("--serialized_model", required=True, help="Trained sklearn model serialized with joblib")
parser.add_argument("--outfile", required=True, help="Outfile. Writes tab-delimited file of ID1,ID2,P(1)")
parser.add_argument("--id_cols", type=int, nargs="+", dest="index_cols", required=False, default=[0,1], help="Which column(s) contain(s) row identifiers, default=[0,1]")

args = parser.parse_args()

assert os.path.isfile(args.datafile), "Datafile {} not found".format(args.datafile)
assert os.path.isfile(args.serialized_model), "Serialized model {} not found".format(args.serialized_model)

print("Loading model")
model = joblib.load(args.serialized_model)

print("Loading data")

df = pd.read_csv(args.datafile,index_col=args.index_cols).fillna(0)
data = df.values
print(model)
print(data)
print(data.shape)
print(model.steps[0])#[1]._n_features)

print("Predicting model")
#p_1 = model.predict_proba(df.values)[:,1]
p_1 = model.predict_proba(data)[:,1]

print("Writing prediction")
outdf = pd.DataFrame({"P_1":  p_1}, index=df.index).sort_values("P_1",ascending=False)
outdf.to_csv(args.outfile, sep="\t")
