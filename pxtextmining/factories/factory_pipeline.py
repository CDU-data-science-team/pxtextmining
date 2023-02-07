from imblearn import FunctionSampler
from imblearn.pipeline import Pipeline
from sklearn.pipeline import make_pipeline
# from sklearn.pipeline import Pipeline
from sklearn.metrics import make_scorer, accuracy_score, balanced_accuracy_score, matthews_corrcoef
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer, KBinsDiscretizer, OneHotEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectPercentile, chi2, f_classif
from sklearn.model_selection import RandomizedSearchCV
# from sklearn.svm import LinearSVC
from sklearn.linear_model import PassiveAggressiveClassifier, Perceptron, RidgeClassifier, SGDClassifier, LogisticRegression
from sklearn.naive_bayes import BernoulliNB, ComplementNB, MultinomialNB
from sklearn.multioutput import MultiOutputClassifier
from sklearn.neighbors import KNeighborsClassifier, NearestCentroid
from sklearn.ensemble import RandomForestClassifier
from pxtextmining.helpers.tokenization import LemmaTokenizer
from pxtextmining.helpers.word_vectorization import EmbeddingsTransformer
from pxtextmining.helpers.oversampling import random_over_sampler_data_generator
from pxtextmining.helpers.metrics import class_balance_accuracy_score
from pxtextmining.helpers.estimator_switcher import ClfSwitcher
from pxtextmining.helpers.ordinal_classification import OrdinalClassifier
from pxtextmining.helpers.scaler_switcher import ScalerSwitcher
from pxtextmining.helpers.feature_selection_switcher import FeatureSelectionSwitcher
from pxtextmining.helpers.text_transformer_switcher import TextTransformerSwitcher
from pxtextmining.helpers.theme_binarization import ThemeBinarizer
from scipy import stats
import time

def create_sklearn_pipeline(model_type):
    params = {'tfidfvectorizer__ngram_range': ((1,1), (1,2), (2,2)),
                'tfidfvectorizer__max_df': [0.8, 0.85, 0.9, 0.95, 1],
                'tfidfvectorizer__min_df': [0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.1]}
    if model_type == 'mnb':
        pipe = make_pipeline(TfidfVectorizer(),
                                       MultiOutputClassifier(MultinomialNB())
                                       )
        params['multioutputclassifier__estimator__alpha'] = stats.uniform(0.1,1)
    if model_type == 'sgd':
        pipe = make_pipeline(TfidfVectorizer(),
                            MultiOutputClassifier(SGDClassifier(loss='log', penalty='l2', alpha=1e-3, max_iter=1000, tol=None))
                            )
    if model_type == 'lr':
        pipe = make_pipeline(TfidfVectorizer(),
                            MultiOutputClassifier(LogisticRegression())
                            )
    return pipe, params

def search_sklearn_pipelines(X_train, Y_train, models_to_try):
    models = []
    training_times = []
    for model_type in models_to_try:
        if model_type not in ['mnb', 'sgd', 'lr']:
            raise ValueError('Please choose valid model_type. Options are mnb, sgd, or lr')
        else:
            pipe, params = create_sklearn_pipeline(model_type)
            start_time = time.time()
            print(f'****SEARCHING {pipe.steps[-1][-1]}')
            search = RandomizedSearchCV(pipe, params,
                                        scoring='f1_macro', n_iter=100,
                                        cv=4, n_jobs=-1, refit=True)
            search.fit(X_train, Y_train)
            models.append(search.best_estimator_)
            training_time = time.time() - start_time
            training_times.append(round(training_time,2))
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

def create_learners(learners, ordinal=False):
    """Creates list of learner models which is then fed into pipeline, based on user selection.

    :param list learners: Estimator types to be tried in pipeline
    :param bool ordinal: Whether model is ordinal or not. Defaults to False.

    :return: List containing the sklearn estimator model instances.
    :rtype: list

    """

    # If a single model is passed as a string, convert to list
    if isinstance(learners, str):
        learners = [learners]

    # Just in case user has supplied the same learner more than once
    learners = list(set(learners))
    learners.sort()
    # For Frank and Hall's (2001) ordinal method to work, we need models that can calculate probs/scores.
    if ordinal is True:
        learners = [lrn for lrn in learners if lrn not in ["RidgeClassifier", "Perceptron",
                                                           "PassiveAggressiveClassifier", "NearestCentroid"]]
    new_learners = []

    # Replace learner name with learner class in 'learners' function argument.
    learner_dict = {"SGDClassifier": SGDClassifier(),
                    "RidgeClassifier": RidgeClassifier(),
                    "Perceptron": Perceptron(),
                    "PassiveAggressiveClassifier": PassiveAggressiveClassifier(),
                    "BernoulliNB": BernoulliNB(),
                    "ComplementNB": ComplementNB(),
                    "MultinomialNB": MultinomialNB(),
                    "KNeighborsClassifier": KNeighborsClassifier(),
                    "NearestCentroid": NearestCentroid(),
                    "RandomForestClassifier": RandomForestClassifier()}

    for i in learners:
        try:
            new_learners.append(learner_dict[i])
        except:
            print(i)
            raise ValueError('Unrecognised learner provided. See documentation for permitted values')
    return new_learners

def factory_categorical_pipeline(x, y, tknz="spacy",
                     cv=5, n_iter=100, n_jobs=5,
                     learners=[
                         "SGDClassifier",
                         "RidgeClassifier",
                         "Perceptron",
                         "PassiveAggressiveClassifier",
                         "BernoulliNB",
                         "ComplementNB",
                         "MultinomialNB",
                         # "KNeighborsClassifier",
                         # "NearestCentroid",
                         "RandomForestClassifier"
                     ]):

    """
    Prepare and fit a text classification pipeline. The pipeline is then fitted using Randomized Search to identify the
    best performing model and hyperparameters.

    - Feature engineering:
        * Converts text into TF-IDFs or [GloVe](https://nlp.stanford.edu/projects/glove/) word vectors with
            [spaCy](https://spacy.io/);
        * Applies [sklearn.preprocessing.KBinsDiscretizer](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.KBinsDiscretizer.html)
            to the text length and sentiment indicator features, and
            [sklearn.preprocessing.StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)
            to the embeddings (word vectors);
    - Up-sampling of rare classes: uses [imblearn.over_sampling.RandomOverSampler](https://imbalanced-learn.org/stable/references/generated/imblearn.over_sampling.RandomOverSampler.html)
      to up-sample rare classes
    - Tokenization and lemmatization of the text feature: uses spaCy (default) or [NLTK](https://www.nltk.org/)
    - Feature selection: Uses [sklearn.feature_selection.SelectPercentile](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.SelectPercentile.html)
      with [sklearn.feature_selection.chi2](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.chi2.html#sklearn.feature_selection.chi2)
      for TF-IDFs or [sklearn.feature_selection.f_classif](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.f_classif.html#sklearn-feature-selection-f-classif)
      for embeddings.
    - Fitting and benchmarking of user-supplied [Scikit-learn classifiers](https://scikit-learn.org/stable/modules/classes.html)

    A param_grid containing a range of hyperparameters to test is created depending on the tokenizer and the learners chosen.
    The values in the grid are currently lists/tuples of values that are defined either empirically or
    are based on the published literature (e.g. for Random Forest, see [Probst et al. 2019](https://arxiv.org/abs/1802.09596).
    Values may be replaced by appropriate distributions in a future release.

    :param pd.DataFrame x: The text feature.
    :param pd.Series y: The response variable (target).
    :param str tknz: Tokenizer to use ("spacy" or "wordnet").
    :param int cv: Number of cross-validation folds.
    :param int n_iter: Number of parameter settings that are sampled in the RandomizedSearch.
    :param int n_jobs: Number of jobs to run in parallel in the RandomizedSearch.
    :param list learners: A list of ``Scikit-learn`` names of the learners to tune. Must be one or more of
        "SGDClassifier", "RidgeClassifier", "Perceptron", "PassiveAggressiveClassifier", "BernoulliNB", "ComplementNB",
        "MultinomialNB", "KNeighborsClassifier", "NearestCentroid", "RandomForestClassifier". When a single model is
        used, it can be passed as a string.

    :return: A tuned sklearn.pipeline.Pipeline
    :rtype: sklearn.pipeline.Pipeline
    """

    # Define transformers for pipeline #
    # Transformer for text_length column
    transformer_text_length = Pipeline(steps=[
        ('scaler', (ScalerSwitcher()))
    ])

    # Transformer for sentiment scores (vader and textblob)
    transformer_sentiment = Pipeline(steps=[
        ('scaler', (ScalerSwitcher()))
    ])

    # Transformer that converts text to Bag-of-Words or embeddings.
    transformer_text = Pipeline(steps=[
        ('text', (TextTransformerSwitcher()))
    ])

    # Gather transformers
    preprocessor = ColumnTransformer(transformers=[
            ('sentimenttr', transformer_sentiment, ['text_blob_polarity', 'text_blob_subjectivity', 'vader_compound']),
            ('lengthtr', transformer_text_length, ['text_length']),
            ('texttr', transformer_text, 'predictor')])

    # Up-sampling step #
    oversampler = FunctionSampler(func=random_over_sampler_data_generator,
                                  kw_args={'threshold': 200,
                                           'up_balancing_counts': 300,
                                        #    'random_state': 0
                                           },
                                  validate=False)

    # Make pipeline #
    pipe = Pipeline([
            ('sampling', oversampler),
            ('preprocessor', preprocessor),
            ('featsel', FeatureSelectionSwitcher()),
            ('clf', ClfSwitcher())])

    # Define (hyper)parameter grid #
    # A few initial value ranges for some (hyper)parameters.
    param_grid_preproc = {
        'sampling__kw_args': [{'threshold': 100}, {'threshold': 200}],
        'sampling__kw_args': [{'up_balancing_counts': 300}, {'up_balancing_counts': 800}],
        'clf__estimator': None,
        'preprocessor__sentimenttr__scaler__scaler': None,
        'preprocessor__lengthtr__scaler__scaler': None,
        'preprocessor__texttr__text__transformer': None,
        'featsel__selector': [SelectPercentile()],
        'featsel__selector__percentile': [80, 90, 100]
    }

    learners = create_learners(learners)

    # Further populate (hyper)parameter grid.
    # NOTE ABOUT PROCESS BELOW:
    # Use TfidfVectorizer() as CountVectorizer() also, to determine if raw
    # counts instead of frequencies improves performance. This requires
    # use_idf=False and norm=None. We want to ensure that norm=None
    # will not be combined with use_idf=True inside the grid search, so we
    # create a separate parameter set to prevent this from happening. We do
    # this below with temp list aux1.
    # Meanwhile, we want norm='l2' (the default) for the grid defined by temp
    # list aux. If we don't explicitly set norm='l2' in aux, the
    # norm column in the table of the CV results (following fitting) is
    # always empty. My speculation is that Scikit-learn does consider norm
    # to be 'l2' for aux, but it doesn't print it. That's because unless we
    # explicitly run aux['preprocessor__text__tfidf__norm'] = ['l2'], setting
    # norm as 'l2' in aux is implicit (i.e. it's the default), while setting
    # norm as None in aux1 is explicit (i.e. done by the user). But we want
    # the colum norm in the CV results to clearly state which runs used the
    # 'l2' norm, hence we explicitly run command
    # aux['preprocessor__text__tfidf__norm'] = ['l2'].

    param_grid = []
    for i in learners:
        for j in [TfidfVectorizer(), EmbeddingsTransformer()]:
            aux = param_grid_preproc.copy()
            aux['clf__estimator'] = [i]
            aux['preprocessor__texttr__text__transformer'] = [j]

            # if i.__class__.__name__ == LinearSVC().__class__.__name__:
            #     aux['clf__estimator__max_iter'] = [10000]
            #     aux['clf__estimator__class_weight'] = [None, 'balanced']
            #     # aux['clf__estimator__dual'] = [True, False] # https://stackoverflow.com/questions/52670012/convergencewarning-liblinear-failed-to-converge-increase-the-number-of-iterati
            if i.__class__.__name__ == BernoulliNB().__class__.__name__:
                aux['clf__estimator__alpha'] = (0.1, 0.5, 1)
            if i.__class__.__name__ == ComplementNB().__class__.__name__:
                aux['clf__estimator__alpha'] = (0.1, 0.5, 1)
            if i.__class__.__name__ == MultinomialNB().__class__.__name__:
                aux['clf__estimator__alpha'] = (0.1, 0.5, 1)
            if i.__class__.__name__ == SGDClassifier().__class__.__name__:
                aux['clf__estimator__max_iter'] = [10000]
                aux['clf__estimator__class_weight'] = [None, 'balanced']
                aux['clf__estimator__penalty'] = ('l2', 'elasticnet')
                aux['clf__estimator__loss'] = ['hinge', 'log']
            if i.__class__.__name__ == RidgeClassifier().__class__.__name__:
                aux['clf__estimator__class_weight'] = [None, 'balanced']
                aux['clf__estimator__alpha'] = (0.1, 1.0, 10.0)
            if i.__class__.__name__ == Perceptron().__class__.__name__:
                aux['clf__estimator__class_weight'] = [None, 'balanced']
                aux['clf__estimator__penalty'] = ('l2', 'elasticnet')
            if i.__class__.__name__ == RandomForestClassifier().__class__.__name__:
                aux['clf__estimator__max_features'] = ('sqrt', 0.666)

            if j.__class__.__name__ == TfidfVectorizer().__class__.__name__:
                aux['featsel__selector__score_func'] = [chi2]
                aux['preprocessor__texttr__text__transformer__tokenizer'] = [LemmaTokenizer(tknz)]
                aux['preprocessor__texttr__text__transformer__norm'] = ['l2']
                aux['preprocessor__texttr__text__transformer__ngram_range'] = ((1, 3), (1, 2), (2, 3), (3, 3))
                aux['preprocessor__texttr__text__transformer__max_df'] = [0.85, 0.9, 0.95]
                aux['preprocessor__texttr__text__transformer__min_df'] = [1,2,3]
                aux['preprocessor__texttr__text__transformer__use_idf'] = [True, False]

                # The transformation is a k-means discretizer with 3 bins:
                #   1. The three bins represent short, medium and long text length. Reluctant to make n_bins a tunable
                #      parameter for efficiency reasons;
                #   2. Discretizing and one-hot encoding satisfies the data format requirements for Chi^2-based feature
                #      selection;
                #   3. An added benefit is that this data format is acceptable by different models, some of which may
                #      not be scale-invariant, while others do not accept negative or continuous values other than
                #      TF-IDFs;
                aux['preprocessor__lengthtr__scaler__scaler'] = \
                    [KBinsDiscretizer(n_bins=3, encode='onehot', strategy='kmeans')]

                # The transformation is a k-means discretizer with 4 or 8 bins supplied as a tunable argument later on:
                #   1. The 4 bins represent weak, weak-medium, medium-strong and strong for values in [0, 1];
                #   2. The 8 bins represent weak, weak-medium, medium-strong and strong for values in [-1, 0] and [0, 1]
                #      (i.e. 8 bins for values in [-1, 1]);
                #   3. We also allow for the possibility of 8 bins for [0, 1] and 4 bins for [-1, 1]- no harm in trying;
                #   4. Discretizing and one-hot encoding satisfies the data format requirements for Chi^2-based feature
                #      selection;
                #   5. An added benefit is that this data format is acceptable by different models, some of which may
                #      not be scale-invariant, while others do not accept negative or continuous values other than
                #      TF-IDFs;
                aux['preprocessor__sentimenttr__scaler__scaler'] = [KBinsDiscretizer(encode='onehot', strategy='kmeans')]
                aux['preprocessor__sentimenttr__scaler__scaler__n_bins'] = [4, 8] # Based on the idea of having 4 (8) bins for indicators in [0, 1] ([-1, 1]), but open to trying 8 (4) for [0, 1] ([-1, 1]) too.

                param_grid.append(aux)

                aux1 = aux.copy()
                aux1['preprocessor__texttr__text__transformer__use_idf'] = [False]
                aux1['preprocessor__texttr__text__transformer__norm'] = [None]

                param_grid.append(aux1)

            if j.__class__.__name__ == EmbeddingsTransformer().__class__.__name__:
                aux['featsel__selector__score_func'] = [f_classif]
                aux['preprocessor__lengthtr__scaler__scaler'] = [StandardScaler()]
                aux['preprocessor__sentimenttr__scaler__scaler'] = [StandardScaler()]

                # We don't want learners than can't handle negative data in the embeddings.
                if (i.__class__.__name__ == BernoulliNB().__class__.__name__) or \
                        (i.__class__.__name__ == ComplementNB().__class__.__name__) or \
                        (i.__class__.__name__ == MultinomialNB().__class__.__name__):
                    aux = None

                param_grid.append(aux)

    param_grid = [x for x in param_grid if x is not None]

    # Performance metrics
    scoring = {'Accuracy': make_scorer(accuracy_score),
               'Balanced Accuracy': make_scorer(balanced_accuracy_score),
               'Matthews Correlation Coefficient': make_scorer(matthews_corrcoef),
               'Class Balance Accuracy': make_scorer(class_balance_accuracy_score)}

    # Define pipeline #
    pipe_cv = RandomizedSearchCV(pipe, param_grid, n_jobs=n_jobs, return_train_score=False,
                                 cv=cv, verbose=1,
                                 scoring=scoring, refit='Class Balance Accuracy', n_iter=n_iter)

    # Fit pipeline #
    pipe_cv.fit(x, y)

    return pipe_cv

def factory_ordinal_pipeline(x, y, tknz="spacy",
                     cv=5, n_iter=100, n_jobs=5,
                     learners=[
                         "SGDClassifier",
                         "RidgeClassifier",
                         "Perceptron",
                         "PassiveAggressiveClassifier",
                         "BernoulliNB",
                         "ComplementNB",
                         "MultinomialNB",
                         # "KNeighborsClassifier",
                         # "NearestCentroid",
                         "RandomForestClassifier"
                     ], theme=False):

    """
    Prepare and fit a text classification pipeline. The pipeline is then fitted using Randomized Search to identify the
    best performing model and hyperparameters.

    - Feature engineering:
        * Converts text into TF-IDFs or [GloVe](https://nlp.stanford.edu/projects/glove/) word vectors with
            [spaCy](https://spacy.io/);
        * Applies [sklearn.preprocessing.KBinsDiscretizer](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.KBinsDiscretizer.html)
            to the text length and sentiment indicator features, and
            [sklearn.preprocessing.StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)
            to the embeddings (word vectors);
    - Up-sampling of rare classes: uses [imblearn.over_sampling.RandomOverSampler](https://imbalanced-learn.org/stable/references/generated/imblearn.over_sampling.RandomOverSampler.html)
      to up-sample rare classes
    - Tokenization and lemmatization of the text feature: uses spaCy (default) or [NLTK](https://www.nltk.org/)
    - Feature selection: Uses [sklearn.feature_selection.SelectPercentile](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.SelectPercentile.html)
      with [sklearn.feature_selection.chi2](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.chi2.html#sklearn.feature_selection.chi2)
      for TF-IDFs or [sklearn.feature_selection.f_classif](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.f_classif.html#sklearn-feature-selection-f-classif)
      for embeddings.
    - Fitting and benchmarking of user-supplied [Scikit-learn classifiers](https://scikit-learn.org/stable/modules/classes.html)

    A param_grid containing a range of hyperparameters to test is created depending on the tokenizer and the learners chosen.
    The values in the grid are currently lists/tuples of values that are defined either empirically or
    are based on the published literature (e.g. for Random Forest, see [Probst et al. 2019](https://arxiv.org/abs/1802.09596).
    Values may be replaced by appropriate distributions in a future release.

     **NOTE:** As described later, argument `theme` is for internal use by Nottinghamshire Healthcare NHS Foundation
     Trust or other trusts who use the theme ("Access", "Environment/ facilities" etc.) labels. It can otherwise be
     safely ignored.

    :param pd.DataFrame x: The text feature.
    :param pd.Series y: The response variable (target).
    :param str tknz: Tokenizer to use ("spacy" or "wordnet").
    :param int cv: Number of cross-validation folds.
    :param int n_iter: Number of parameter settings that are sampled in the RandomizedSearch.
    :param int n_jobs: Number of jobs to run in parallel in the RandomizedSearch.
    :param list learners: A list of ``Scikit-learn`` names of the learners to tune. Must be one or more of
        "SGDClassifier", "RidgeClassifier", "Perceptron", "PassiveAggressiveClassifier", "BernoulliNB", "ComplementNB",
        "MultinomialNB", "KNeighborsClassifier", "NearestCentroid", "RandomForestClassifier". When a single model is
        used, it can be passed as a string.
    :param str theme: For internal use by Nottinghamshire Healthcare NHS Foundation Trust or other trusts
        that use theme labels ("Access", "Environment/ facilities" etc.). The column name of the theme variable.
        Defaults to `None`. If supplied, the theme variable will be used as a predictor (along with the text predictor)
        in the model that is fitted with criticality as the response variable. The rationale is two-fold. First, to
        help the model improve predictions on criticality when the theme labels are readily available. Second, to force
        the criticality for "Couldn't be improved" to always be "3" in the training and test data, as well as in the
        predictions. This is the only criticality value that "Couldn't be improved" can take, so by forcing it to always
        be "3", we are improving model performance, but are also correcting possible erroneous assignments of values
        other than "3" that are attributed to human error.
    :return: A tuned sklearn.pipeline.Pipeline
    :rtype: sklearn.pipeline.Pipeline
    """

    # Define transformers for pipeline #
    # Transformer for text_length column
    transformer_text_length = Pipeline(steps=[
        ('scaler', (ScalerSwitcher()))
    ])

    # Transformer for sentiment scores (vader and textblob)
    transformer_sentiment = Pipeline(steps=[
        ('scaler', (ScalerSwitcher()))
    ])

    # Transformer that converts text to Bag-of-Words or embeddings.
    transformer_text = Pipeline(steps=[
        ('text', (TextTransformerSwitcher()))
    ])

    # Gather transformers
    preprocessor = ColumnTransformer(transformers=[
            ('sentimenttr', transformer_sentiment, ['text_blob_polarity', 'text_blob_subjectivity', 'vader_compound']),
            ('lengthtr', transformer_text_length, ['text_length']),
            ('texttr', transformer_text, 'predictor')])

    # Up-sampling step #
    oversampler = FunctionSampler(func=random_over_sampler_data_generator,
                                  kw_args={'threshold': 200,
                                           'up_balancing_counts': 300,
                                        #    'random_state': 0
                                           },
                                  validate=False)

    # Make pipeline #
    if theme is not None:
        # This is for internal use by Nottinghamshire Healthcare NHS Foundation Trust or other trusts that use theme
        # labels ("Access", "Environment/ facilities" etc.). We want the criticality for "Couldn't be improved" to
        # always be "3". The theme label is passed as a one-hot encoded set of columns (or as a "binarized" column where
        # 1 is for "Couldn't be improved" and 0 is for everything else) of which the first is for # "Couldn't be
        # improved". The one-hot encoded columns (or the binarized column) are (is) actually the first column(s) of the
        # whole sparse matrix that has the TF-IDFs, sentiment features etc. that is produced when fitting by the
        # pipeline. When running the ordinal classification model, we want to find the records with "Couldn't be
        # improved" (i.e. records with a value of 1) in the first column and replace the predicted criticality values
        # with "3".
        # When one-hot encoded, we pass all of the theme's columns into the model, so we handle them separately from
        # text predictor to avoid the feature selection step for them. We thus make a separate pipeline with the
        # preprocessor and feature selection steps for the text predictor (pipe_all_but_theme) and one-hot encode the
        # theme column in all_transforms. We want to place "Couldn't be improved" in position 0 (first column) of the
        # thus produced sparse matrix so as to easily access it in the code for the ordinal model (OrdinalClassifier()).
        pipe_all_but_theme = Pipeline([
            ('preprocessor', preprocessor),
            ('featsel', FeatureSelectionSwitcher())
        ])

        all_transforms = ColumnTransformer([
            ('theme', ScalerSwitcher(), ['theme']), # Try out OneHotEncoder() or ThemeBinarizer().
            ('process', pipe_all_but_theme, ['predictor', 'text_length', 'text_blob_polarity',
                                             'text_blob_subjectivity', 'vader_compound'])
        ])

        pipe = Pipeline([
            ('sampling', oversampler),
            ('alltrans', all_transforms),
            ('clf', OrdinalClassifier(theme='theme', target_class_value='3', theme_class_value=1))
        ])
    elif theme is None:
        pipe = Pipeline([
            ('sampling', oversampler),
            ('preprocessor', preprocessor),
            ('featsel', FeatureSelectionSwitcher()),
            ('clf', OrdinalClassifier())])

    # Define (hyper)parameter grid #
    # A few initial value ranges for some (hyper)parameters.
    param_grid_preproc = {
        'sampling__kw_args': [{'threshold': 100}, {'threshold': 200}],
        'sampling__kw_args': [{'up_balancing_counts': 300}, {'up_balancing_counts': 800}],
        'clf__estimator': None,
        'preprocessor__sentimenttr__scaler__scaler': None,
        'preprocessor__lengthtr__scaler__scaler': None,
        'preprocessor__texttr__text__transformer': None,
        'featsel__selector': [SelectPercentile()],
        'featsel__selector__percentile': [80, 90, 100]
    }

    if theme is not None:
        param_grid_preproc['alltrans__theme__scaler'] = None

    learners = create_learners(learners, ordinal = True)

    # Further populate (hyper)parameter grid.
    # NOTE ABOUT PROCESS BELOW:
    # Use TfidfVectorizer() as CountVectorizer() also, to determine if raw
    # counts instead of frequencies improves performance. This requires
    # use_idf=False and norm=None. We want to ensure that norm=None
    # will not be combined with use_idf=True inside the grid search, so we
    # create a separate parameter set to prevent this from happening. We do
    # this below with temp list aux1.
    # Meanwhile, we want norm='l2' (the default) for the grid defined by temp
    # list aux. If we don't explicitly set norm='l2' in aux, the
    # norm column in the table of the CV results (following fitting) is
    # always empty. My speculation is that Scikit-learn does consider norm
    # to be 'l2' for aux, but it doesn't print it. That's because unless we
    # explicitly run aux['preprocessor__text__tfidf__norm'] = ['l2'], setting
    # norm as 'l2' in aux is implicit (i.e. it's the default), while setting
    # norm as None in aux1 is explicit (i.e. done by the user). But we want
    # the colum norm in the CV results to clearly state which runs used the
    # 'l2' norm, hence we explicitly run command
    # aux['preprocessor__text__tfidf__norm'] = ['l2'].

    param_grid = []
    for i in learners:
        for j in [TfidfVectorizer(), EmbeddingsTransformer()]:
            aux = param_grid_preproc.copy()
            aux['clf__estimator'] = [i]
            aux['preprocessor__texttr__text__transformer'] = [j]
            if theme is not None:
                onehot_categories = [["Couldn't be improved", 'Access', 'Care received', 'Communication', 'Dignity',
                                      'Environment/ facilities', 'Miscellaneous', 'Staff', 'Transition/coordination']]
                aux['alltrans__theme__scaler'] = \
                    [OneHotEncoder(categories=onehot_categories), ThemeBinarizer(class_col='theme',
                                                                                 target_class="Couldn't be improved")]

            # if i.__class__.__name__ == LinearSVC().__class__.__name__:
            #     aux['clf__estimator__max_iter'] = [10000]
            #     aux['clf__estimator__class_weight'] = [None, 'balanced']
            #     # aux['clf__estimator__dual'] = [True, False] # https://stackoverflow.com/questions/52670012/convergencewarning-liblinear-failed-to-converge-increase-the-number-of-iterati
            if i.__class__.__name__ == BernoulliNB().__class__.__name__:
                aux['clf__estimator__alpha'] = (0.1, 0.5, 1)
            if i.__class__.__name__ == ComplementNB().__class__.__name__:
                aux['clf__estimator__alpha'] = (0.1, 0.5, 1)
            if i.__class__.__name__ == MultinomialNB().__class__.__name__:
                aux['clf__estimator__alpha'] = (0.1, 0.5, 1)
            if i.__class__.__name__ == SGDClassifier().__class__.__name__:
                aux['clf__estimator__max_iter'] = [10000]
                aux['clf__estimator__class_weight'] = [None, 'balanced']
                aux['clf__estimator__penalty'] = ('l2', 'elasticnet')
                aux['clf__estimator__loss'] = ['log']
            if i.__class__.__name__ == RidgeClassifier().__class__.__name__:
                aux['clf__estimator__class_weight'] = [None, 'balanced']
                aux['clf__estimator__alpha'] = (0.1, 1.0, 10.0)
            if i.__class__.__name__ == Perceptron().__class__.__name__:
                aux['clf__estimator__class_weight'] = [None, 'balanced']
                aux['clf__estimator__penalty'] = ('l2', 'elasticnet')
            if i.__class__.__name__ == RandomForestClassifier().__class__.__name__:
                aux['clf__estimator__max_features'] = ('sqrt', 0.666)

            if j.__class__.__name__ == TfidfVectorizer().__class__.__name__:
                aux['featsel__selector__score_func'] = [chi2]
                aux['preprocessor__texttr__text__transformer__tokenizer'] = [LemmaTokenizer(tknz)]
                aux['preprocessor__texttr__text__transformer__norm'] = ['l2']
                aux['preprocessor__texttr__text__transformer__ngram_range'] = ((1, 3), (1, 2), (2, 3), (3, 3))
                aux['preprocessor__texttr__text__transformer__max_df'] = [0.85, 0.9, 0.95]
                aux['preprocessor__texttr__text__transformer__min_df'] = [1,2,3]
                aux['preprocessor__texttr__text__transformer__use_idf'] = [True, False]

                # The transformation is a k-means discretizer with 3 bins:
                #   1. The three bins represent short, medium and long text length. Reluctant to make n_bins a tunable
                #      parameter for efficiency reasons;
                #   2. Discretizing and one-hot encoding satisfies the data format requirements for Chi^2-based feature
                #      selection;
                #   3. An added benefit is that this data format is acceptable by different models, some of which may
                #      not be scale-invariant, while others do not accept negative or continuous values other than
                #      TF-IDFs;
                aux['preprocessor__lengthtr__scaler__scaler'] = \
                    [KBinsDiscretizer(n_bins=3, encode='onehot', strategy='kmeans')]

                # The transformation is a k-means discretizer with 4 or 8 bins supplied as a tunable argument later on:
                #   1. The 4 bins represent weak, weak-medium, medium-strong and strong for values in [0, 1];
                #   2. The 8 bins represent weak, weak-medium, medium-strong and strong for values in [-1, 0] and [0, 1]
                #      (i.e. 8 bins for values in [-1, 1]);
                #   3. We also allow for the possibility of 8 bins for [0, 1] and 4 bins for [-1, 1]- no harm in trying;
                #   4. Discretizing and one-hot encoding satisfies the data format requirements for Chi^2-based feature
                #      selection;
                #   5. An added benefit is that this data format is acceptable by different models, some of which may
                #      not be scale-invariant, while others do not accept negative or continuous values other than
                #      TF-IDFs;
                aux['preprocessor__sentimenttr__scaler__scaler'] = [KBinsDiscretizer(encode='onehot', strategy='kmeans')]
                aux['preprocessor__sentimenttr__scaler__scaler__n_bins'] = [4, 8] # Based on the idea of having 4 (8) bins for indicators in [0, 1] ([-1, 1]), but open to trying 8 (4) for [0, 1] ([-1, 1]) too.

                param_grid.append(aux)

                aux1 = aux.copy()
                aux1['preprocessor__texttr__text__transformer__use_idf'] = [False]
                aux1['preprocessor__texttr__text__transformer__norm'] = [None]

                param_grid.append(aux1)

            if j.__class__.__name__ == EmbeddingsTransformer().__class__.__name__:
                aux['featsel__selector__score_func'] = [f_classif]
                aux['preprocessor__lengthtr__scaler__scaler'] = [StandardScaler()]
                aux['preprocessor__sentimenttr__scaler__scaler'] = [StandardScaler()]

                # We don't want learners that can't handle negative data in the embeddings.
                if (i.__class__.__name__ == BernoulliNB().__class__.__name__) or \
                        (i.__class__.__name__ == ComplementNB().__class__.__name__) or \
                        (i.__class__.__name__ == MultinomialNB().__class__.__name__):
                    aux = None

                param_grid.append(aux)

    param_grid = [x for x in param_grid if x is not None]

    # When a theme is supplied for the ordinal model, the pipeline steps are a little different. Step "alltrans"
    # includes the steps for both the preprocessing of the text feature, and the one-hot encoding of the theme feature.
    # So, a parameter such as "featsel__selector" in the pipeline without a theme feature would be
    # "alltrans__process__featsel__selector" in this one. We need to pass these correct names to the tuning grid.
    if theme is not None:
        ordinal_with_theme_params = [
            'featsel__selector',
            'featsel__selector__percentile',
            'featsel__selector__score_func',
            'preprocessor__sentimenttr__scaler__scaler',
            'preprocessor__sentimenttr__scaler__scaler__n_bins',
            'preprocessor__lengthtr__scaler__scaler',
            'preprocessor__texttr__text__transformer',
            'preprocessor__texttr__text__transformer__tokenizer',
            'preprocessor__texttr__text__transformer__preprocessor',
            'preprocessor__texttr__text__transformer__norm',
            'preprocessor__texttr__text__transformer__ngram_range',
            'preprocessor__texttr__text__transformer__max_df',
            'preprocessor__texttr__text__transformer__min_df',
            'preprocessor__texttr__text__transformer__use_idf']

        for i in range(len(param_grid)):
            for j in ordinal_with_theme_params:
                if j in param_grid[i].keys():
                    old_key = j
                    new_key = 'alltrans__process__' + old_key
                    param_grid[i][new_key] = param_grid[i].pop(old_key)

    # Performance metrics
    scoring = {'Accuracy': make_scorer(accuracy_score),
               'Balanced Accuracy': make_scorer(balanced_accuracy_score),
               'Matthews Correlation Coefficient': make_scorer(matthews_corrcoef),
               'Class Balance Accuracy': make_scorer(class_balance_accuracy_score)}

    # Define pipeline #
    pipe_cv = RandomizedSearchCV(pipe, param_grid, n_jobs=n_jobs, return_train_score=False,
                                 cv=cv, verbose=1,
                                 scoring=scoring, refit='Class Balance Accuracy', n_iter=n_iter)

    # Fit pipeline #
    pipe_cv.fit(x, y)

    return pipe_cv
