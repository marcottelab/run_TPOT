import os
import numpy as np
import pandas as pd 
import sklearn.metrics
#from sklearn.externals import joblib
import joblib

def trim_pipeline(pipeline_file, pipeline_outfile):
    #TPOT export exports a pipeline with steps we don't need

    with open(pipeline_file, "r") as f: 
       with open(pipeline_outfile, "w") as o:       
          pipeline = f.read().split("\n\n")
          pipeline = "{}\n\n{}".format(pipeline[0], pipeline[2])
          o.write(pipeline)

def eval_train(exported_pipeline, training_infile, serialized_trained_model="fitted_model.p", index_cols=[0,1], groupcol = None):
    
    assert os.path.exists(training_infile), "{} not found".format(training_infile)
    
    print("Reading training data")
    train = pd.read_csv(training_infile, index_col=index_cols)
    if groupcol:
       group = train.pop(groupcol)

    print(train)

    train_label = train.pop("label").values
    train_data = train.values
    
    print("Training model")
    exported_pipeline.fit(train_data, train_label)

    print("Writing model")
    joblib.dump(exported_pipeline, serialized_trained_model)
    plaintext_fname =  "{}.txt".format(serialized_trained_model)
    with open(plaintext_fname, "w") as f:
       f.write(str(exported_pipeline))


    print("Recording feature importances")
    names = train.columns

    sel_method = exported_pipeline.steps[0][0]
    featimp  = exported_pipeline.steps[0][1].estimator_.feature_importances_

    featimp_fname = "{}.featureimportances".format(serialized_trained_model)

    numfeats = len(featimp)
    rank = range(1, numfeats)
   
    ordering = sorted(zip(map(lambda x: round(x, 4), featimp), names, [sel_method]*numfeats), reverse=True)
    
    df = pd.DataFrame(ordering, columns = ["score", "feature", "featsel_method"])
    df.index.name="rank"
    df = df.reset_index() 
    df.to_csv(featimp_fname, index=False)


    print("Calculating training average precision")
    train_fit_probs = exported_pipeline.predict_proba(train_data)[:,1]
    train_aps = sklearn.metrics.average_precision_score(train_label,train_fit_probs)
    print("Training set average precision score: {}".format(train_aps))
    
    del train
    del train_data
    return(exported_pipeline)


def eval_test(exported_pipeline, test_infile, pr_curve_outfile="test_PRC.csv", results_df_outfile="test_resultsDF.csv", index_cols=[0,1] ):   

    assert os.path.exists(test_infile), "{} not found".format(test_infile)
    print("Reading test data")
    test = pd.read_csv(test_infile, index_col=index_cols)
    test_label = test.pop("label")
    test_data = test.values
    
    test_probs = exported_pipeline.predict_proba(test_data)[:,1]
    
    test_aps = sklearn.metrics.average_precision_score(test_label, test_probs)
    print("Test set average precision score: {}".format(test_aps))
    
    test_p, test_r, thresholds = sklearn.metrics.precision_recall_curve(test_label, test_probs)
    
    test_PRC = pd.DataFrame({"precision": test_p, "recall": test_r, "threshold": thresholds}).sort_values("recall")
    test_PRC.to_csv(pr_curve_outfile,index=False)
    
    test_DF = pd.DataFrame({"label":test_label,"P_1":test_probs}, index=test.index).sort_values("P_1", ascending=False)
    test_DF["FDR"] = 1 - (test_DF.label.cumsum() / (np.arange(test_DF.shape[0]) + 1))
    test_DF.to_csv(results_df_outfile)
    
    


