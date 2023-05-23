import pickle
import os
import numpy as np
import pandas as pd

from pxtextmining.factories.factory_predict_unlabelled_text import get_labels, predict_multilabel_sklearn, predict_with_probs, get_probabilities
from tensorflow.keras import Model, Sequential
from pxtextmining.factories.factory_model_performance import parse_metrics_file


def write_multilabel_models_and_metrics(models, model_metrics, path):
    """Saves models and their associated performance metrics into a specified folder

    Args:
        models (list): List containing the trained tf.keras or sklearn models to be saved.
        model_metrics (list): List containing the model metrics in `str` format
        path (str): Path where model is to be saved.
    """
    for i in range(len(models)):
        model_name = f"model_{i}"
        if not os.path.exists(path):
            os.makedirs(path)
        fullpath = os.path.join(path, model_name)
        if isinstance(models[i], (Sequential, Model)):
            models[i].save(fullpath)
        else:
            modelpath = os.path.join(path, model_name + '.sav')
            pickle.dump(models[i], open(modelpath, "wb"))
        # Write performance metrics file
        txtpath = os.path.join(path, model_name + '.txt')
        with open(txtpath, "w") as file:
            file.write(model_metrics[i])
    print(f"{len(models)} models have been written to {path}")

def write_model_preds(x, y, model, labels, additional_features = True, path = 'labels.xlsx'):
    """Writes an Excel file to enable easier analysis of model outputs using the test set. Columns of the Excel file are: comment_id, actual_labels, predicted_labels, actual_label_probs, and predicted_label_probs.

    Currently only works with sklearn models.

    Args:
        x (pd.DataFrame): Features to be used to make the prediction.
        y (np.array): Numpy array containing the targets, in one-hot encoded format
        model (sklearn.base): Trained sklearn multilabel classifier.
        labels (list): List of labels for the categories to be predicted.
        additional_features (bool, optional): Whether or not FFT_q_standardised is included in data. Defaults to True.
        path (str, optional): Filename for the outputted file. Defaults to 'labels.xlsx'.
    """
    actual_labels = pd.DataFrame(y, columns = labels).apply(get_labels, args=(labels,), axis=1)
    actual_labels.name = 'actual_labels'
    predicted_labels = predict_multilabel_sklearn(x,
                                                  model,
                                                  labels=labels,
                                                  additional_features = additional_features,
                                                  label_fix = True,
                                                  enhance_with_probs=True
                                                ).reset_index()['labels']
    predicted_labels.name = 'predicted_labels'
    df = x.reset_index()

    probabilities = np.array(model.predict_proba(x))
    probs_actual = get_probabilities(actual_labels, labels, probabilities, model_type = 'sklearn')
    probs_predicted = get_probabilities(predicted_labels, labels, probabilities, model_type = 'sklearn')
    df = df.merge(actual_labels, left_index = True, right_index = True)
    df = df.merge(predicted_labels, left_index = True, right_index = True)
    df = df.merge(probs_actual, left_index = True, right_index = True)
    df = df.merge(probs_predicted, left_index = True, right_index = True)
    df.to_excel(path, index = False)
    print(f'Successfully completed, written to {path}')

def write_model_analysis(model_name, labels, dataset, path):
    metrics_df = parse_metrics_file(f"{path}/{model_name}.txt", labels=labels)
    label_counts = pd.DataFrame(dataset[labels].sum())
    label_counts = label_counts.reset_index()
    label_counts = label_counts.rename(columns={"index": "label", 0: "label_count"})
    metrics_df = metrics_df.merge(label_counts, on="label")
    metrics_df.to_excel(f"{path}/{model_name}_perf.xlsx", index=False)
