from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from pxtextmining.factories import factory_predict_unlabelled_text
from pxtextmining.factories.factory_data_load_and_split import bert_data_to_dataset


def test_get_probabilities_bert():
    label_series = pd.Series([["label_one"], ["label_two", "label_three"]], name="test")
    labels = ["label_one", "label_two", "label_three"]
    predicted_probabilities = np.array([[0.8, 0.1, 0.1], [0.1, 0.9, 0.7]])
    test_probability_s = factory_predict_unlabelled_text.get_probabilities(
        label_series, labels, predicted_probabilities
    )
    assert len(test_probability_s.iloc[0]) == 1
    assert test_probability_s.iloc[1]["label_two"] == 0.9
    assert type(test_probability_s) == pd.Series
    assert len(test_probability_s) == len(label_series)


def test_get_probabilities_sklearn():
    label_series = pd.Series([["label_one"], ["label_two", "label_three"]], name="test")
    labels = ["label_one", "label_two", "label_three"]
    predicted_probabilities = np.array(
        [[[0.2, 0.8], [0.9, 0.1]], [[0.9, 0.1], [0.1, 0.9]], [[0.9, 0.1], [0.3, 0.7]]]
    )
    test_probability_s = factory_predict_unlabelled_text.get_probabilities(
        label_series,
        labels,
        predicted_probabilities,
    )
    assert len(test_probability_s.iloc[0]) == 1
    assert test_probability_s.iloc[1]["label_two"] == 0.9
    assert type(test_probability_s) == pd.Series
    assert len(test_probability_s) == len(label_series)


@pytest.mark.parametrize("rules_dict", [None, {"first": ["liked"]}])
def test_predict_multilabel_sklearn(rules_dict):
    data = pd.DataFrame(
        [
            {
                "Comment ID": "99999",
                "FFT answer": "I liked all of it",
                "FFT_q_standardised": "nonspecific",
            },
            {
                "Comment ID": "A55",
                "FFT answer": "",
                "FFT_q_standardised": "nonspecific",
            },
            {
                "Comment ID": "A56",
                "FFT answer": "Truly awful time finding parking",
                "FFT_q_standardised": "could_improve",
            },
            {
                "Comment ID": "4",
                "FFT answer": "I really enjoyed the session",
                "FFT_q_standardised": "what_good",
            },
            {
                "Comment ID": "5",
                "FFT answer": "7482367",
                "FFT_q_standardised": "nonspecific",
            },
        ]
    ).set_index("Comment ID")
    predictions = np.array([[0, 1, 0], [1, 0, 1], [0, 0, 1]])
    predicted_probs = np.array(
        [
            [
                [0.80465788, 0.19534212],
                [0.94292979, 0.05707021],
                [0.33439024, 0.66560976],
            ],
            [
                [0.33439024, 0.66560976],
                [0.9949298, 0.0050702],
                [0.99459238, 0.00540762],
            ],
            [
                [0.97472981, 0.02527019],
                [0.25069129, 0.74930871],
                [0.33439024, 0.66560976],
            ],
        ]
    )
    labels = ["first", "second", "third"]
    model = Mock(
        predict=Mock(return_value=predictions),
        predict_proba=Mock(return_value=predicted_probs),
    )
    preds_df = factory_predict_unlabelled_text.predict_multilabel_sklearn(
        data,
        model,
        labels=labels,
        additional_features=True,
        rules_dict=rules_dict,
        label_fix=False,
    )
    cols = len(labels) * 2 + 1
    assert preds_df.shape == (3, cols)


def test_predict_multilabel_sklearn_additional_params(grab_test_X_additional_feats):
    data = grab_test_X_additional_feats["FFT answer"].iloc[:3]
    predictions = np.array([[0, 1, 1], [1, 0, 0], [1, 0, 1]])
    predicted_probs = np.array(
        [
            [
                [0.80465788, 0.19534212],
                [0.05707021, 0.94292979],
                [0.33439024, 0.66560976],
            ],
            [
                [0.33439024, 0.66560976],
                [0.9949298, 0.0050702],
                [0.99459238, 0.00540762],
            ],
            [
                [0.25069129, 0.74930871],
                [0.97472981, 0.02527019],
                [0.33439024, 0.66560976],
            ],
        ]
    )
    labels = ["Labelling not possible", "second", "third"]
    model = Mock(
        predict=Mock(return_value=predictions),
        predict_proba=Mock(return_value=predicted_probs),
    )
    preds_df = factory_predict_unlabelled_text.predict_multilabel_sklearn(
        data,
        model,
        labels=labels,
        additional_features=False,
        label_fix=True,
    )
    cols = len(labels) * 2 + 1
    assert preds_df.shape == (3, cols)


@pytest.mark.parametrize("rules_dict", [None, {"first": ["liked"]}])
@pytest.mark.parametrize(
    "custom_threshold_dict",
    [None, {"one": 0.6, "two": 0.5, "three": 0.75, "four": 0.6, "five": 0.5}],
)
@pytest.mark.parametrize("additional_features", [True, False])
@pytest.mark.parametrize("label_fix", [True, False])
def test_predict_multilabel_bert(
    additional_features, custom_threshold_dict, label_fix, rules_dict
):
    data = pd.DataFrame(
        [
            {
                "Comment ID": "99999",
                "FFT answer": "I liked all of it",
                "FFT_q_standardised": "nonspecific",
            },
            {
                "Comment ID": "A55",
                "FFT answer": "",
                "FFT_q_standardised": "nonspecific",
            },
            {
                "Comment ID": "A56",
                "FFT answer": "Truly awful time finding parking",
                "FFT_q_standardised": "could_improve",
            },
            {
                "Comment ID": "4",
                "FFT answer": "I really enjoyed the session",
                "FFT_q_standardised": "what_good",
            },
            {
                "Comment ID": "5",
                "FFT answer": "7482367",
                "FFT_q_standardised": "nonspecific",
            },
        ]
    ).set_index("Comment ID")
    predicted_probs = np.array(
        [
            [6.2770307e-01, 2.3520987e-02, 1.3149388e-01, 2.7835215e-02, 1.8944685e-01],
            [9.8868138e-01, 1.9990385e-03, 5.4453085e-03, 9.0726715e-04, 2.9669846e-03],
            [4.2310607e-01, 5.6546849e-01, 9.3136989e-03, 1.3205722e-03, 7.9117226e-04],
            [2.0081511e-01, 7.0609129e-04, 1.1107661e-03, 7.9677838e-01, 5.8961433e-04],
        ]
    )
    if additional_features is False:
        data = data["FFT answer"]
    labels = ["first", "second", "third", "fourth", "fifth"]
    model = Mock(predict=Mock(return_value=predicted_probs))

    preds_df = factory_predict_unlabelled_text.predict_multilabel_bert(
        data,
        model,
        labels=labels,
        label_fix=label_fix,
        additional_features=additional_features,
        custom_threshold_dict=custom_threshold_dict,
        rules_dict=rules_dict,
    )
    cols = len(labels) * 2 + 1
    assert preds_df.shape == (4, cols)


def test_predict_multilabel_bert_already_encoded():
    data = pd.DataFrame(
        [
            {
                "Comment ID": "99999",
                "FFT answer": "I liked all of it",
                "FFT_q_standardised": "nonspecific",
            },
            {
                "Comment ID": "A55",
                "FFT answer": "",
                "FFT_q_standardised": "nonspecific",
            },
            {
                "Comment ID": "A56",
                "FFT answer": "Truly awful time finding parking",
                "FFT_q_standardised": "could_improve",
            },
            {
                "Comment ID": "4",
                "FFT answer": "I really enjoyed the session",
                "FFT_q_standardised": "what_good",
            },
            {
                "Comment ID": "5",
                "FFT answer": "7482367",
                "FFT_q_standardised": "nonspecific",
            },
        ]
    ).set_index("Comment ID")
    dataset = bert_data_to_dataset(data)

    predicted_probs = np.array(
        [
            [6.2770307e-01, 2.3520987e-02, 1.3149388e-01, 2.7835215e-02, 1.8944685e-01],
            [9.8868138e-01, 1.9990385e-03, 5.4453085e-03, 9.0726715e-04, 2.9669846e-03],
            [4.2310607e-01, 5.6546849e-01, 9.3136989e-03, 1.3205722e-03, 7.9117226e-04],
            [2.0081511e-01, 7.0609129e-04, 1.1107661e-03, 7.9677838e-01, 5.8961433e-04],
        ]
    )

    labels = ["first", "second", "third", "fourth", "fifth"]
    model = Mock(predict=Mock(return_value=predicted_probs))

    preds_df = factory_predict_unlabelled_text.predict_multilabel_bert(
        dataset,
        model,
        labels=labels,
        label_fix=False,
        additional_features=False,
        custom_threshold_dict=None,
        rules_dict=None,
    )
    cols = len(labels) * 2 + 1
    assert preds_df.shape == (4, cols)


@pytest.mark.parametrize("preprocess_text", [True, False])
@pytest.mark.parametrize("additional_features", [True, False])
def test_predict_sentiment_bert(additional_features, preprocess_text):
    data = pd.DataFrame(
        [
            {
                "Comment ID": "99999",
                "FFT answer": "I liked all of it",
                "FFT_q_standardised": "nonspecific",
            },
            {
                "Comment ID": "A55",
                "FFT answer": "",
                "FFT_q_standardised": "nonspecific",
            },
            {
                "Comment ID": "A56",
                "FFT answer": "Truly awful time finding parking",
                "FFT_q_standardised": "could_improve",
            },
            {
                "Comment ID": "4",
                "FFT answer": "I really enjoyed the session",
                "FFT_q_standardised": "what_good",
            },
            {
                "Comment ID": "5",
                "FFT answer": "7482367",
                "FFT_q_standardised": "nonspecific",
            },
        ]
    ).set_index("Comment ID")
    if additional_features is False:
        data = data["FFT answer"]
    if preprocess_text is True:
        predicted_probs = np.array(
            [
                [0.9, 0.01, 0.07, 0.01, 0.01],
                [0.01, 0.07, 0.01, 0.01, 0.9],
                [0.07, 0.9, 0.01, 0.01, 0.01],
            ]
        )
        df_len = 3
    elif preprocess_text is False:
        predicted_probs = np.array(
            [
                [0.9, 0.01, 0.07, 0.01, 0.01],
                [0.01, 0.07, 0.01, 0.01, 0.9],
                [0.07, 0.9, 0.01, 0.01, 0.01],
                [0.07, 0.9, 0.01, 0.01, 0.01],
            ]
        )
        df_len = 4
    model = Mock(predict=Mock(return_value=predicted_probs))
    preds_df = factory_predict_unlabelled_text.predict_sentiment_bert(
        data,
        model,
        preprocess_text=preprocess_text,
        additional_features=additional_features,
    )
    assert preds_df.shape[0] == df_len
    assert "sentiment" in list(preds_df.columns)


def test_predict_with_bert(grab_test_X_additional_feats):
    # arrange
    data = grab_test_X_additional_feats
    model = Mock(
        predict=Mock(
            return_value=np.array(
                [
                    [
                        6.2770307e-01,
                        2.3520987e-02,
                        1.3149388e-01,
                        2.7835215e-02,
                        1.8944685e-01,
                    ],
                    [
                        9.8868138e-01,
                        1.9990385e-03,
                        5.4453085e-03,
                        9.0726715e-04,
                        2.9669846e-03,
                    ],
                    [
                        4.2310607e-01,
                        5.6546849e-01,
                        9.3136989e-03,
                        1.3205722e-03,
                        7.9117226e-04,
                    ],
                    [
                        2.0081511e-01,
                        7.0609129e-04,
                        1.1107661e-03,
                        7.9677838e-01,
                        5.8961433e-04,
                    ],
                    [
                        1.4777037e-03,
                        5.1493715e-03,
                        2.8268427e-03,
                        7.4673461e-04,
                        9.8979920e-01,
                    ],
                ]
            )
        )
    )

    # act
    predictions = factory_predict_unlabelled_text.predict_with_bert(
        data, model, additional_features=True
    )
    # assert
    model.predict.assert_called_once()
    assert type(predictions) == np.ndarray


def test_predict_multiclass_bert(grab_test_X_additional_feats):
    data = grab_test_X_additional_feats
    model = Mock(
        predict=Mock(
            return_value=np.array(
                [
                    [0.9, 0.01, 0.07, 0.01, 0.01],
                    [0.01, 0.07, 0.01, 0.01, 0.9],
                    [0.07, 0.9, 0.01, 0.01, 0.01],
                    [0.9, 0.01, 0.07, 0.01, 0.01],
                    [0.9, 0.01, 0.01, 0.01, 0.07],
                ]
            )
        )
    )
    predictions = factory_predict_unlabelled_text.predict_multiclass_bert(
        data, model, additional_features=False
    )
    assert predictions.sum() == len(data)


def test_predict_with_probs(grab_test_X_additional_feats):
    # arrange
    data = grab_test_X_additional_feats[:3]
    predicted_probs = [
        [[0.80465788, 0.19534212], [0.94292979, 0.05707021], [0.33439024, 0.66560976]],
        [[0.88, 0.12], [0.9949298, 0.0050702], [0.99459238, 0.00540762]],
        [[0.97472981, 0.02527019], [0.25069129, 0.74930871], [0.33439024, 0.66560976]],
    ]
    labels = ["first", "second", "third"]
    model = Mock(predict_proba=Mock(return_value=predicted_probs))
    # act
    predictions = factory_predict_unlabelled_text.predict_with_probs(
        data, model, labels=labels
    )
    # assert
    assert type(predictions) == np.ndarray
    assert len(predictions) == len(predicted_probs)


def test_get_thresholds_3d():
    three_dim_probs = np.array(
        [
            [
                [0.80465788, 0.19534212],
                [0.94292979, 0.05707021],
                [0.33439024, 0.66560976],
            ],
            [
                [0.33439024, 0.66560976],
                [0.9949298, 0.0050702],
                [0.99459238, 0.00540762],
            ],
            [
                [0.97472981, 0.02527019],
                [0.25069129, 0.74930871],
                [0.33439024, 0.66560976],
            ],
        ]
    )
    y_true = np.array([[1, 0, 1], [1, 0, 0], [0, 0, 1]])
    labels = ["one", "two", "three"]
    thresholds = factory_predict_unlabelled_text.get_thresholds(
        y_true, three_dim_probs, labels
    )
    assert isinstance(thresholds, dict) is True


def test_get_thresholds_2d():
    two_dim_probs = np.array(
        [
            [
                6.2770307e-01,
                2.3520987e-02,
                1.3149388e-01,
                2.7835215e-02,
                1.8944685e-01,
            ],
            [
                9.8868138e-01,
                1.9990385e-03,
                5.4453085e-03,
                9.0726715e-04,
                2.9669846e-03,
            ],
            [
                4.2310607e-01,
                5.6546849e-01,
                9.3136989e-03,
                1.3205722e-03,
                7.9117226e-04,
            ],
            [
                2.0081511e-01,
                7.0609129e-04,
                1.1107661e-03,
                7.9677838e-01,
                5.8961433e-04,
            ],
            [
                1.4777037e-03,
                5.1493715e-03,
                2.8268427e-03,
                7.4673461e-04,
                9.8979920e-01,
            ],
        ]
    )
    y_true = np.where(two_dim_probs > 0.2, 1, 0)
    labels = ["one", "two", "three", "four", "five"]
    thresholds = factory_predict_unlabelled_text.get_thresholds(
        y_true, two_dim_probs, labels
    )
    assert isinstance(thresholds, dict) is True


def test_get_thresholds_list():
    list_probs = [
        [
            6.2770307e-01,
            2.3520987e-02,
            1.3149388e-01,
            2.7835215e-02,
            1.8944685e-01,
        ],
        [
            9.8868138e-01,
            1.9990385e-03,
            5.4453085e-03,
            9.0726715e-04,
            2.9669846e-03,
        ],
        [
            4.2310607e-01,
            5.6546849e-01,
            9.3136989e-03,
            1.3205722e-03,
            7.9117226e-04,
        ],
        [
            2.0081511e-01,
            7.0609129e-04,
            1.1107661e-03,
            7.9677838e-01,
            5.8961433e-04,
        ],
        [
            1.4777037e-03,
            5.1493715e-03,
            2.8268427e-03,
            7.4673461e-04,
            9.8979920e-01,
        ],
    ]
    y_true = np.where(np.array(list_probs) > 0.2, 1, 0)
    labels = ["one", "two", "three", "four", "five"]
    thresholds = factory_predict_unlabelled_text.get_thresholds(
        y_true, list_probs, labels
    )
    assert isinstance(thresholds, dict) is True


def test_turn_probs_into_binary_nodict():
    test_probs = np.array(
        [
            [
                6.2770307e-01,
                2.3520987e-02,
                1.3149388e-01,
                2.7835215e-02,
                1.8944685e-01,
            ],
            [
                9.8868138e-01,
                1.9990385e-03,
                5.4453085e-03,
                9.0726715e-04,
                2.9669846e-03,
            ],
            [
                4.2310607e-01,
                5.6546849e-01,
                9.3136989e-03,
                1.3205722e-03,
                7.9117226e-04,
            ],
            [
                2.0081511e-01,
                7.0609129e-04,
                1.1107661e-03,
                7.9677838e-01,
                5.8961433e-04,
            ],
            [
                1.4777037e-03,
                5.1493715e-03,
                2.8268427e-03,
                7.4673461e-04,
                9.8979920e-01,
            ],
        ]
    )
    preds = factory_predict_unlabelled_text.turn_probs_into_binary(test_probs)
    assert test_probs.shape == preds.shape


def test_turn_probs_into_binary_dict():
    test_probs = np.array(
        [
            [
                6.2770307e-01,
                2.3520987e-02,
                1.3149388e-01,
                2.7835215e-02,
                1.8944685e-01,
            ],
            [
                9.8868138e-01,
                1.9990385e-03,
                5.4453085e-03,
                9.0726715e-04,
                2.9669846e-03,
            ],
            [
                4.2310607e-01,
                5.6546849e-01,
                9.3136989e-03,
                1.3205722e-03,
                7.9117226e-04,
            ],
            [
                2.0081511e-01,
                7.0609129e-04,
                1.1107661e-03,
                7.9677838e-01,
                5.8961433e-04,
            ],
            [
                1.4777037e-03,
                5.1493715e-03,
                2.8268427e-03,
                7.4673461e-04,
                9.8979920e-01,
            ],
        ]
    )
    custom_threshold_dict = {
        "one": 0.2,
        "two": 0.5,
        "three": 0.1,
        "four": 0.5,
        "five": 0.8,
    }
    preds = factory_predict_unlabelled_text.turn_probs_into_binary(
        test_probs, custom_threshold_dict
    )
    assert test_probs.shape == preds.shape


@pytest.mark.parametrize("method", ["probabilities", "categories"])
def test_combine_predictions(grab_preds_df, method):
    test_df_1 = grab_preds_df
    test_df_2 = grab_preds_df.copy()
    df = factory_predict_unlabelled_text.combine_predictions(
        [test_df_1, test_df_2],
        labels=["one", "two", "three", "four", "five"],
        method=method,
    )
    assert df.shape == test_df_1.shape


def test_rulebased_probs_2d():
    text = pd.DataFrame(
        [
            {
                "Comment ID": "99999",
                "FFT answer": "I liked all of it",
            },
            {
                "Comment ID": "A56",
                "FFT answer": "Truly awful time finding parking",
            },
            {
                "Comment ID": "4",
                "FFT answer": "I really enjoyed the session",
            },
        ]
    ).set_index("Comment ID")["FFT answer"]
    probs = np.array(
        [
            [6.2770307e-01, 2.3520987e-02, 1.3149388e-01, 2.7835215e-02, 1.8944685e-01],
            [9.8868138e-01, 1.9990385e-03, 5.4453085e-03, 9.0726715e-04, 2.9669846e-03],
            [4.2310607e-01, 5.6546849e-01, 9.3136989e-03, 1.3205722e-03, 7.9117226e-04],
        ]
    )
    labels = ["one", "two", "Negative experience", "three", "four", "five"]
    rules_dict = {"Negative experience": ["awful"]}
    improved_probs = factory_predict_unlabelled_text.rulebased_probs(
        text=text, pred_probs=probs, labels=labels, rules_dict=rules_dict
    )
    assert improved_probs.shape == probs.shape
    assert improved_probs[1][2] >= 0.3


def test_rulebased_probs_3d():
    text = pd.DataFrame(
        [
            {
                "Comment ID": "99999",
                "FFT answer": "I liked all of it",
            },
            {
                "Comment ID": "A56",
                "FFT answer": "Truly awful time finding parking",
            },
            {
                "Comment ID": "4",
                "FFT answer": "I really enjoyed the session",
            },
        ]
    ).set_index("Comment ID")["FFT answer"]
    probs = np.array(
        [
            [[0.34, 0.63], [0.98, 0.02], [0.87, 0.13], [0.97, 0.03], [0.81, 0.19]],
            [[0.01, 0.99], [0.99, 0.01], [0.99, 0.01], [0.99, 0.01], [0.99, 0.01]],
            [[0.58, 0.42], [0.43, 0.57], [0.99, 0.01], [0.99, 0.01], [0.99, 0.01]],
        ]
    )
    labels = ["one", "two", "Negative experience", "three", "four", "five"]
    rules_dict = {"Negative experience": ["awful"]}
    improved_probs = factory_predict_unlabelled_text.rulebased_probs(
        text=text, pred_probs=probs, labels=labels, rules_dict=rules_dict
    )
    assert improved_probs.shape == probs.shape
    assert improved_probs[1][2][1] >= 0.3


def test_fix_no_labels_2d():
    binary_preds = np.array([[0, 0, 0], [0, 1, 0]])
    probs_2d = np.array([[0.2, 0.3, 0.4], [0.1, 0.8, 0.4]])

    fixed_preds = factory_predict_unlabelled_text.fix_no_labels(binary_preds, probs_2d)
    assert fixed_preds[0].sum() == 1


def test_fix_no_labels_3d():
    binary_preds = np.array([[0, 0, 0], [0, 1, 0]])
    probs_3d = np.array(
        [[[0.8, 0.2], [0.7, 0.3], [0.6, 0.4]], [[0.9, 0.1], [0.2, 0.8], [0.6, 0.4]]]
    )

    fixed_preds = factory_predict_unlabelled_text.fix_no_labels(binary_preds, probs_3d)
    assert fixed_preds[0].sum() == 1
