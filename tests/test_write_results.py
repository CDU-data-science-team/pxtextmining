from pxtextmining.factories import factory_write_results
import pandas as pd
import numpy as np
import pytest
from unittest.mock import Mock, mock_open, patch
from tensorflow.keras import Model
import os


@patch("pickle.dump", Mock())
@patch("builtins.open", new_callable=mock_open, read_data="somestr")
def test_write_multilabel_models_and_metrics(mock_file):
    # arrange
    mock_model = Mock(spec=Model)
    models = [mock_model]
    model_metrics = ["somestr"]
    path = "somepath"
    # act
    factory_write_results.write_multilabel_models_and_metrics(
        models, model_metrics, path
    )
    # assert
    mock_model.save.assert_called_once()
    mock_file.assert_called_with(os.path.join("somepath", "model_0.txt"), "w")
    assert open(os.path.join("somepath", "model_0.txt")).read() == "somestr"


@patch("pxtextmining.factories.factory_write_results.pd.DataFrame.to_excel")
def test_write_model_preds(mock_toexcel, grab_test_X_additional_feats):
    # arrange
    x = grab_test_X_additional_feats[:3]
    y = np.array([[0, 1, 0], [1, 0, 0], [1, 0, 0]])
    predictions = np.array([[0, 1, 0], [1, 0, 1], [0, 0, 1]])
    predicted_probs = [
        [[0.80465788, 0.19534212], [0.94292979, 0.05707021], [0.33439024, 0.66560976]],
        [[0.33439024, 0.66560976], [0.9949298, 0.0050702], [0.99459238, 0.00540762]],
        [[0.97472981, 0.02527019], [0.25069129, 0.74930871], [0.33439024, 0.66560976]],
    ]
    mock_model = Mock(
        predict=Mock(return_value=predictions),
        predict_proba=Mock(return_value=predicted_probs),
    )
    labels = ["A", "B", "C"]
    path = "somepath.xlsx"
    # act
    factory_write_results.write_model_preds(x, y, mock_model, labels, path=path)
    # assert
    mock_model.predict_proba.assert_called_with(x)
    mock_toexcel.assert_called_with(path, index=False)
