from imblearn import FunctionSampler
from imblearn.pipeline import Pipeline
from sklearn.pipeline import make_pipeline
# from sklearn.pipeline import Pipeline
from sklearn.metrics import make_scorer, accuracy_score, balanced_accuracy_score, matthews_corrcoef
from sklearn.compose import ColumnTransformer, make_column_transformer
from sklearn.preprocessing import FunctionTransformer, KBinsDiscretizer, OneHotEncoder, StandardScaler, RobustScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectPercentile, chi2, f_classif
from sklearn.model_selection import RandomizedSearchCV
from sklearn.svm import SVC
from sklearn.linear_model import PassiveAggressiveClassifier, Perceptron, RidgeClassifier, SGDClassifier, LogisticRegression
from sklearn.naive_bayes import BernoulliNB, ComplementNB, MultinomialNB
from sklearn.multioutput import MultiOutputClassifier
from sklearn.neighbors import KNeighborsClassifier, NearestCentroid
from sklearn.ensemble import RandomForestClassifier
from pxtextmining.helpers.tokenization import LemmaTokenizer
from pxtextmining.helpers.word_vectorization import EmbeddingsTransformer
from pxtextmining.helpers.oversampling import random_over_sampler_data_generator
from pxtextmining.helpers.metrics import class_balance_accuracy_score, multi_label_accuracy
from pxtextmining.helpers.estimator_switcher import ClfSwitcher
from pxtextmining.helpers.ordinal_classification import OrdinalClassifier
from pxtextmining.helpers.scaler_switcher import ScalerSwitcher
from pxtextmining.helpers.feature_selection_switcher import FeatureSelectionSwitcher
from pxtextmining.helpers.text_transformer_switcher import TextTransformerSwitcher
from pxtextmining.helpers.theme_binarization import ThemeBinarizer
from scipy import stats
import datetime
import time
from pxtextmining.helpers.tokenization import spacy_tokenizer
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras import layers, Sequential
from tensorflow.keras.callbacks import EarlyStopping
from transformers import TFDistilBertForSequenceClassification
from tensorflow.keras.initializers import TruncatedNormal
from tensorflow.keras.layers import Input, Dropout, Dense, concatenate
from tensorflow.keras.losses import BinaryCrossentropy
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
import numpy as np
from transformers import DistilBertConfig

def create_bert_model(Y_train, model_name='distilbert-base-uncased', max_length=150):
    config = DistilBertConfig.from_pretrained(model_name)
    transformer_model = TFDistilBertForSequenceClassification.from_pretrained(model_name, output_hidden_states = False)
    bert = transformer_model.layers[0]
    input_ids = Input(shape=(max_length,), name='input_ids', dtype='int32')
    inputs = {'input_ids': input_ids}
    bert_model = bert(inputs)[0][:, 0, :]
    dropout = Dropout(config.dropout, name='pooled_output')
    pooled_output = dropout(bert_model, training=False)
    output = Dense(units=Y_train.shape[1],
                    kernel_initializer=TruncatedNormal(stddev=config.initializer_range),
                    activation="sigmoid",
                    name='output')(pooled_output)
    model = Model(inputs=inputs, outputs=output, name='BERT_MultiLabel')
    # compile model
    loss = BinaryCrossentropy()
    optimizer = Adam(5e-5)
    metrics = [
        'CategoricalAccuracy'
    ]
    model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
    return model


def create_bert_model_additional_features(Y_train, model_name='distilbert-base-uncased', max_length=150):
    config = DistilBertConfig.from_pretrained(model_name)
    transformer_model = TFDistilBertForSequenceClassification.from_pretrained(model_name, output_hidden_states = False)
    bert = transformer_model.layers[0]
    input_ids = Input(shape=(150,), name='input_ids', dtype='int32')
    input_text = {'input_ids': input_ids}
    bert_model = bert(input_text)[0][:, 0, :]
    dropout = Dropout(config.dropout, name='pooled_output')
    bert_output = dropout(bert_model, training=False)
    # Get onehotencoded categories in (3 categories)
    input_cat = Input(shape=(3,), name='input_cat')
    cat_dense = Dense(units = 10, activation = 'relu')
    cat_dense = cat_dense(input_cat)
    # concatenate both together
    concat_layer = concatenate([bert_output,cat_dense])
    output = Dense(units=Y_train.shape[1],
                    kernel_initializer=TruncatedNormal(stddev=config.initializer_range),
                    activation="sigmoid",
                    name='output')(concat_layer)
    model = Model(inputs=[input_ids, input_cat],
                outputs=output, name='BERT_MultiLabel')
    loss = BinaryCrossentropy()
    optimizer = Adam(5e-5)
    metrics = [
        'CategoricalAccuracy'
    ]
    model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
    return model

def train_bert_model(train_dataset, val_dataset, model, class_weights_dict = None, epochs = 30):
    es = EarlyStopping(patience=2, restore_best_weights=True)
    start_time = time.time()
    model.fit(train_dataset.shuffle(1000).batch(16), epochs=epochs, batch_size=16,
                                class_weight= class_weights_dict,
                                validation_data=val_dataset.batch(16),
                                callbacks=[es])
    total_time = round(time.time() - start_time, 0)
    training_time = str(datetime.timedelta(seconds=total_time))
    return model, training_time

def calculating_class_weights(y_true):
    y_np = np.array(y_true)
    number_dim = np.shape(y_np)[1]
    weights = np.empty([number_dim, 2])
    for i in range(number_dim):
        weights[i] = compute_class_weight('balanced', classes = [0.,1.], y = y_np[:, i])
    class_weights_dict = {}
    for i in range(len(weights)):
        class_weights_dict[i] = weights[i][-1]
    return class_weights_dict


def create_tf_model(vocab_size = None, embedding_size = 100):
    model = Sequential()
    model.add(layers.Embedding(
        input_dim=vocab_size+1,
        output_dim=embedding_size,
        mask_zero=True
    ))
    model.add(layers.LSTM(50))
    model.add(layers.Dense(20, activation='relu'))
    model.add(layers.Dense(13, activation='sigmoid'))
    model.compile(loss='binary_crossentropy',
                optimizer='rmsprop',
                metrics=['CategoricalAccuracy', 'Precision', 'Recall'])
    return model


def train_tf_model(X_train, Y_train, model, class_weights_dict = None):
    es = EarlyStopping(patience=3, restore_best_weights=True)
    start_time = time.time()
    model.fit(X_train, Y_train,
          epochs=200, batch_size=32, verbose=1,
          validation_split=0.2,
          callbacks=[es], class_weight= class_weights_dict)
    seconds_taken = round(time.time() - start_time, 0)
    training_time = str(datetime.timedelta(seconds=seconds_taken))
    return model, training_time


def create_sklearn_vectorizer(tokenizer = None):
    if tokenizer == 'spacy':
        vectorizer = TfidfVectorizer(tokenizer = spacy_tokenizer)
    else:
        vectorizer = TfidfVectorizer()
    return vectorizer

def create_sklearn_pipeline(model_type, tokenizer = None, additional_features = True):
    if additional_features == True:
        cat_transformer = OneHotEncoder(handle_unknown='ignore')
        vectorizer = create_sklearn_vectorizer(tokenizer = None)
        num_transformer = RobustScaler()
        preproc = make_column_transformer(
                (cat_transformer, ['FFT_q_standardised']),
                (vectorizer, 'FFT answer'),
                (num_transformer, ['text_length']))
        params = {'columntransformer__tfidfvectorizer__ngram_range': ((1,1), (1,2), (2,2)),
                    'columntransformer__tfidfvectorizer__max_df': [0.85,0.86,0.87,0.88,0.89,0.9,0.91,0.92,0.93,0.94,0.95,0.96,0.97],
                    'columntransformer__tfidfvectorizer__min_df': stats.uniform(0,0.15)
                    }
    else:
        preproc = create_sklearn_vectorizer(tokenizer = tokenizer)
        params = {'tfidfvectorizer__ngram_range': ((1,1), (1,2), (2,2)),
                'tfidfvectorizer__max_df': stats.uniform(0.8,1),
                'tfidfvectorizer__min_df': stats.uniform(0.01,0.1)}
    if model_type == 'mnb':
        pipe = make_pipeline(preproc,
                            MultiOutputClassifier(MultinomialNB())
                            )
        params['multioutputclassifier__estimator__alpha'] = stats.uniform(0.1,1)
    if model_type == 'knn':
        pipe = make_pipeline(preproc,
                            KNeighborsClassifier())
        params['kneighborsclassifier__n_neighbors'] = stats.randint(1,50)
        params['kneighborsclassifier__n_jobs'] = [-1]
    if model_type == 'svm':
        pipe = make_pipeline(preproc,
                            MultiOutputClassifier(SVC(probability = True, class_weight = 'balanced',
                                                      max_iter = 1000, cache_size = 500), n_jobs = -1)
                            )
        params['multioutputclassifier__estimator__C'] = stats.uniform(0.1, 20)
        params['multioutputclassifier__estimator__kernel'] = ['linear',
                                                              'rbf', 'sigmoid']
    if model_type == 'rfc':
        pipe = make_pipeline(preproc,
                            RandomForestClassifier(n_jobs = -1)
                            )
        params['randomforestclassifier__max_depth'] = stats.randint(5,50)
        params['randomforestclassifier__min_samples_split'] = stats.randint(2,5)
        params['randomforestclassifier__class_weight'] = ['balanced', 'balanced_subsample', None]
        params['randomforestclassifier__min_samples_leaf'] = stats.randint(1,10)
        params['randomforestclassifier__max_features'] = ['sqrt', 'log2', None, 0.3]
    return pipe, params

def search_sklearn_pipelines(X_train, Y_train, models_to_try, additional_features =True):
    models = []
    training_times = []
    for model_type in models_to_try:
        if model_type not in ['mnb', 'knn', 'svm', 'rfc']:
            raise ValueError('Please choose valid model_type. Options are mnb, knn, svm, or rfc')
        else:
            if additional_features == False:
                pipe, params = create_sklearn_pipeline(model_type, additional_features =False)
            elif additional_features == True:
                pipe, params = create_sklearn_pipeline(model_type, additional_features = True)
            start_time = time.time()
            print(f'****SEARCHING {pipe.steps[-1][-1]}')
            search = RandomizedSearchCV(pipe, params,
                                        scoring='f1_macro', n_iter=50,
                                        cv=4, n_jobs=-2, refit=True)
            search.fit(X_train, Y_train)
            models.append(search.best_estimator_)
            training_time = round(time.time() - start_time, 0)
            training_times.append(str(datetime.timedelta(seconds=training_time)))
    return models, training_times


def train_sklearn_multilabel_models(X_train, Y_train):
    # My idea is to create separate pipelines for each model. Gridsearch each one separately
    # Currently just vanilla model, not pipeline. Work in progress!
    # Need to have a think about which models and why... find some literature to support decisionmaking
    nb_clf = MultinomialNB()
    sgd = SGDClassifier(loss='log', penalty='l2', alpha=1e-3, max_iter=1000, tol=None)
    lr = LogisticRegression()
    models = []
    for classifier in [nb_clf, sgd, lr]:
        clf = MultiOutputClassifier(classifier)
        print(f'Training {clf}')
        clf.fit(X_train, Y_train)
        models.append(clf)
    return models
