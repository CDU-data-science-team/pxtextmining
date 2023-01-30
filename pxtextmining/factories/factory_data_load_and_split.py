import pandas as pd
from os import path
import mysql.connector
from sklearn.model_selection import train_test_split
import re
import string
import numpy as np
from pxtextmining.helpers import decode_emojis, text_length, sentiment_scores
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer



def get_multilabel_class_counts(df):
    class_counts = {}
    for i in df.columns:
        class_counts[i] = df[i].sum()
    return class_counts


def load_multilabel_data(filename, target = 'major_categories'):
    """_summary_

    Args:
        filename (_type_): _description_
        target (str, optional): Options are 'minor_categories', 'major_categories', or 'sentiment. Defaults to 'minor_categories'.

    Raises:
        for: _description_
        for: _description_

    Returns:
        _type_: _description_
    """
    print('Loading multilabel dataset...')
    text_data = pd.read_csv(filename)
    text_data.columns = text_data.columns.str.strip()
    text_data = text_data.set_index('Comment ID').copy()
    features = ['FFT categorical answer', 'FFT question', 'FFT answer']
    #For now the labels are hardcoded, these are subject to change as framework is in progress
    if target in ['minor_categories', 'major_categories']:
        cols = ['Gratitude/ good experience', 'Negative experience', 'Not assigned',
        'Organisation & efficiency', 'Funding & use of financial resources',
        'Non-specific praise for staff',
        'Non-specific dissatisfaction with staff',
        'Staff manner & personal attributes', 'Number & deployment of staff',
        'Staff responsiveness', 'Staff continuity', 'Competence & training',
        'Unspecified communication',
        'Staff listening, understanding & involving patients',
        'Information directly from staff during care',
        'Information provision & guidance',
        'Being kept informed, clarity & consistency of information',
        'Service involvement with family/ carers',
        'Patient contact with family/ carers', 'Contacting services',
        'Appointment arrangements', 'Appointment method', 'Timeliness of care',
        'Supplying medication', 'Understanding medication', 'Pain management',
        'Diagnosis', 'Referals & continuity of care',
        'Length of stay/ duration of care', 'Discharge', 'Care plans',
        'Patient records', 'Impact of treatment/ care - physical health',
        'Impact of treatment/ care - mental health',
        'Impact of treatment/ care - general',
        'Links with non-NHS organisations',
        'Cleanliness, tidiness & infection control',
        'Noise & restful environment', 'Temperature', 'Lighting', 'Decoration',
        'Smell', 'Comfort of environment', 'Atmosphere of ward/ environment',
        'Access to outside/ fresh air', 'Privacy', 'Safety & security',
        'Provision of medical  equipment', 'Food & drink provision',
        'Food preparation facilities for patients & visitors',
        'Service location', 'Transport to/ from services', 'Parking',
        'Provision & range of activities', 'Electronic entertainment',
        'Feeling safe', 'Patient appearance & grooming', 'Mental Health Act',
        'Psychological therapy arrangements', 'Existence of services',
        'Choice of services', 'Respect for diversity', 'Admission',
        'Out of hours support (community services)', 'Learning organisation',
        'Collecting patients feedback']
    elif target == 'sentiment':
        cols = ['Comment sentiment']
    filtered_dataframe = text_data.loc[:,features + cols].copy()
    print(f'Shape of raw data is {filtered_dataframe.shape}')
    clean_dataframe = filtered_dataframe.dropna(subset=features).copy()
    # Standardize FFT qs
    q_map = {'Please tells us why you gave this answer?': 'nonspecific',
        'FFT Why?': 'nonspecific',
        'What was good?': 'what_good',
        'How could we improve?': 'could_improve',
        'What could we do better?': 'could_improve',
        'Please describe any things about the 111 service that \nyou were particularly satisfied and/or dissatisfied with': 'nonspecific'}
    clean_dataframe.loc[:,'FFT_q_standardised']  = clean_dataframe.loc[:,'FFT question'].map(q_map).copy()
    # Could probably do more text cleaning in here before doing text_length
    clean_dataframe.loc[:,'text_length'] = clean_dataframe.loc[:,'FFT answer'].apply(lambda x:
                                    len([word for word in str(x).split(' ') if word != '']))
    if target == 'major_categories':
        major_categories = {
        'Gratitude/ good experience': 'General',
        'Negative experience': 'General',
        'Not assigned': 'General',
        'Organisation & efficiency': 'General',
        'Funding & use of financial resources': 'General',
        'Non-specific praise for staff': 'Staff',
        'Non-specific dissatisfaction with staff': 'Staff',
        'Staff manner & personal attributes': 'Staff',
        'Number & deployment of staff': 'Staff',
        'Staff responsiveness': 'Staff',
        'Staff continuity': 'Staff',
        'Competence & training': 'Staff',
        'Unspecified communication': 'Communication & involvement',
        'Staff listening, understanding & involving patients': 'Communication & involvement',
        'Information directly from staff during care': 'Communication & involvement',
        'Information provision & guidance': 'Communication & involvement',
        'Being kept informed, clarity & consistency of information': 'Communication & involvement',
        'Service involvement with family/ carers': 'Communication & involvement',
        'Patient contact with family/ carers': 'Communication & involvement',
        'Contacting services': 'Access to medical care & support',
        'Appointment arrangements': 'Access to medical care & support',
        'Appointment method': 'Access to medical care & support',
        'Timeliness of care': 'Access to medical care & support',
        'Supplying medication': 'Medication',
        'Understanding medication': 'Medication',
        'Pain management': 'Medication',
        'Diagnosis': 'Patient journey & service coordination',
        'Referals & continuity of care': 'Patient journey & service coordination',
        'Length of stay/ duration of care': 'Patient journey & service coordination',
        'Discharge': 'Patient journey & service coordination',
        'Care plans': 'Patient journey & service coordination',
        'Patient records': 'Patient journey & service coordination',
        'Impact of treatment/ care - physical health': 'Patient journey & service coordination',
        'Impact of treatment/ care - mental health': 'Patient journey & service coordination',
        'Impact of treatment/ care - general': 'Patient journey & service coordination',
        'Links with non-NHS organisations': 'Patient journey & service coordination',
        'Cleanliness, tidiness & infection control': 'Environment & equipment',
        'Noise & restful environment': 'Environment & equipment',
        'Temperature': 'Environment & equipment',
        'Lighting': 'Environment & equipment',
        'Decoration': 'Environment & equipment',
        'Smell': 'Environment & equipment',
        'Comfort of environment': 'Environment & equipment',
        'Atmosphere of ward/ environment': 'Environment & equipment',
        'Access to outside/ fresh air': 'Environment & equipment',
        'Privacy': 'Environment & equipment',
        'Safety & security': 'Environment & equipment',
        'Provision of medical  equipment': 'Environment & equipment',
        'Food & drink provision': 'Food & diet',
        'Food preparation facilities for patients & visitors': 'Food & diet',
        'Service location': 'Service location, travel & transport',
        'Transport to/ from services': 'Service location, travel & transport',
        'Parking': 'Service location, travel & transport',
        'Provision & range of activities': 'Activities',
        'Electronic entertainment': 'Activities',
        'Feeling safe': 'Category TBC',
        'Patient appearance & grooming': 'Category TBC',
        'Mental Health Act': 'Mental Health specifics',
        'Psychological therapy arrangements': 'Mental Health specifics',
        'Existence of services': 'Additional',
        'Choice of services': 'Additional',
        'Respect for diversity': 'Additional',
        'Admission': 'Additional',
        'Out of hours support (community services)': 'Additional',
        'Learning organisation': 'Additional',
        'Collecting patients feedback': 'Additional'}
        new_df = clean_dataframe.copy().drop(columns = cols)
        for i in clean_dataframe[cols].index:
            for label in cols:
                if clean_dataframe.loc[i,label] == 1:
                    new_cat = major_categories[label]
                    new_df.loc[i,new_cat] = 1
        clean_dataframe = new_df.copy()
        cols = list(set(major_categories.values()))
    clean_dataframe.loc[:,'num_labels'] = clean_dataframe.loc[:,cols].sum(axis = 1)
    clean_dataframe = clean_dataframe[clean_dataframe['num_labels'] != 0]
    print(f'Shape of cleaned data is {clean_dataframe.shape}')
    return clean_dataframe

def vectorise_multilabel_data(text_data):
    # can try different types of vectorizer here
    count_vect = CountVectorizer()
    X_counts = count_vect.fit_transform(text_data)
    tfidf_transformer = TfidfTransformer()
    X_tfidf = tfidf_transformer.fit_transform(X_counts)
    return X_tfidf

def process_and_split_multilabel_data(df, target, vectorise = True):
    # Currently just the text itself. Not adding other features yet or doing any cleaning
    Y = df[target].fillna(value=0)
    if vectorise == True:
        X = vectorise_multilabel_data(df['FFT answer'])
    else:
        X = df['FFT answer']
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.3)
    return X_train, X_test, Y_train, Y_test

def load_data(filename, target, predictor, theme = None):
    """
    This function loads the data from a csv, dataframe, or SQL database. It returns a pd.DataFrame with the data
    required for training a machine learning model.

    :param filename: A ``pandas.DataFrame`` with the data (class and text columns), otherwise the
            dataset name (CSV), including full path to the data folder (if not in the project's working directory), and the
            data type suffix (".csv"). If ``filename`` is ``None``, the data is read from the SQL database.
            **NOTE:** The feature that reads data from the database is for internal use only. Experienced users who would
            like to pull their data from their own databases can, of course, achieve that by slightly modifying the
            relevant lines in the script and setting up the connection to the SQL server.
    :type filename: pd.DataFrame
    :param target: Name of the column containing the target to be predicted.
    :type target: str
    :param str predictor: Name of the column containing the text to be used to train the model or make predictions.
    :param theme: Name of the column containing the 'theme' data which can be used to train a model predicting
            'criticality'
    :type theme: str, optional

    :return: a pandas.DataFrame with the columns named in a way that works for the rest of the pipeline
    :rtype: pandas.DataFrame

    """
    print('Loading dataset...')
    # Read CSV if filename provided
    if filename is not None:
        if isinstance(filename, str):
            text_data = pd.read_csv(filename, encoding='utf-8')
        else:
            text_data = filename
    # Else load from mysql database
    # For this to work set my.conf settings to access mysql database
    else:
        db = mysql.connector.connect(option_files="my.conf", use_pure=True)
        if theme is None:
            with db.cursor() as cursor:
                query = f"SELECT id , {target} , {predictor} FROM text_data"
                cursor.execute(query)
                text_data = cursor.fetchall()
                text_data = pd.DataFrame(text_data)
                text_data.columns = cursor.column_names
                text_data = text_data.set_index('id')
        else:
            with db.cursor() as cursor:
                query = f"SELECT id , {target} , {predictor} , {theme} FROM text_data"
                cursor.execute(query)
                text_data = cursor.fetchall()
                text_data = pd.DataFrame(text_data)
                text_data.columns = cursor.column_names
                text_data = text_data.set_index('id')
    text_data = text_data.rename(columns={target: 'target', predictor: 'predictor'})
    if theme is not None:
        text_data = text_data.rename(columns={theme: 'theme'})
        text_data = text_data[['target', 'predictor', 'theme']]
    else:
        text_data = text_data[['target', 'predictor']]
    print(f'Shape of dataset before cleaning is {text_data.shape}')
    return text_data

def remove_punc_and_nums(text):
    """
    This function removes excess punctuation and numbers from the text. Exclamation marks and apostrophes have been
    left in, as have words in allcaps, as these may denote strong sentiment. Returns a string.

    :param str text: Text to be cleaned

    :return: the cleaned text as a str
    :rtype: str
    """
    text = re.sub('\\n', ' ', text)
    text = re.sub('\\r', ' ', text)
    text = ''.join(char for char in text if not char.isdigit())
    punc_list = string.punctuation.replace('!', '')
    punc_list = punc_list.replace("'", '')
    for punctuation in punc_list:
        text = text.replace(punctuation, ' ')
    text = decode_emojis.decode_emojis(text)
    text_split = [word for word in text.split(' ') if word != '']
    text_lower = []
    for word in text_split:
        if word.isupper():
            text_lower.append(word)
        else:
            text_lower.append(word.lower())
    cleaned_sentence = ' '.join(word for word in text_lower)
    cleaned_sentence = cleaned_sentence.strip()
    return cleaned_sentence

def clean_data(text_data, target = False):
    """
    Function to clean and preprocess data, for training a model or for making predictions using a trained model.
    target = True if processing labelled data for training a model. The DataFrame should contain a column named
    'predictor' containing the text to be processed. If processing dataset with no target, i.e. to make predictions
    using unlabelled data, then target = False. This function also drops NaNs.

    :param pd.DataFrame text_data: A ``pandas.DataFrame`` with the data to be cleaned. Essential to have one
    column labelled 'predictor', containing text for training or predictions.
    :param target: A string. If present, then it denotes that the dataset is for training a model and the y 'target'
    column is present in the dataframe. If set to False, then the function is able to clean text data in the 'predictor'
    column for making new predictions using a trained model.
    :type target: str, optional

    :return: a pandas.DataFrame with the 'predictor' column cleaned
    :rtype: pandas.DataFrame
    """
    if target == True:
        text_data_clean = text_data.dropna(subset=['target', 'predictor']).copy()
    else:
        text_data_clean = text_data.dropna(subset=['predictor']).copy()
    for i in ['NULL', 'N/A', 'NA', 'NONE']:
        text_data_clean = text_data_clean[text_data_clean['predictor'].str.upper() != i].copy()
    text_data_clean['original_text'] = text_data_clean['predictor'].copy()
    text_data_clean['predictor'] = text_data_clean['predictor'].apply(remove_punc_and_nums)
    text_data_clean['predictor'] = text_data_clean['predictor'].replace('', np.NaN)
    if target == True:
        text_data_clean = text_data_clean.dropna(subset=['target', 'predictor']).copy()
    else:
        text_data_clean = text_data_clean.dropna(subset=['predictor']).copy()
    # have decided against dropping duplicates for now as this is a natural part of dataset
    # text_data = text_data.drop_duplicates().copy()
    return text_data_clean

def reduce_crit(text_data, theme):
    """
    'Criticality' is an indication of how strongly negative or positive a comment is. A comment with a criticality
    value of '-5' is very strongly critical of the organisation. A comment with a criticality value of '3' is mildly
    positive about the organisation. 'Criticality' labels are specific to data collected by Nottinghamshire
    Healthcare NHS Foundation Trust.
    This function manipulates the criticality levels to account for an imbalanced dataset. There are not enough samples
    belonging to classes '-5' and '5' so these are set to '-4' and '4'. This function also sets the 'criticality'
    value for all comments tagged as 'Couldn't be improved' to '3'.

    :param pd.DataFrame text_data: A ``pandas.DataFrame`` with the data to be cleaned. Essential to have one
        column labelled 'predictor', containing text for training or predictions.
    :param theme: Name of the column containing the 'theme' data which can be used to train a model predicting
        'criticality'
    :type theme: str, optional

    :return: a pandas.DataFrame with the ordinal values in the 'target' column changed from 5 to 4, or -5 to -4.
    :rtype: pandas.DataFrame

    """
    text_data_crit = text_data.query("target in ('-5', '-4', '-3', '-2', '-1', '0', '1', '2', '3', '4', '5')").copy()
    text_data_crit['target'] = text_data_crit['target'].copy().replace('-5', '-4')
    text_data_crit['target'] = text_data_crit['target'].copy().replace('5', '4')
    if theme is not None:
        text_data_crit.loc[text_data_crit['theme'] == "Couldn't be improved", 'target'] = '3'
    return text_data_crit

def process_data(text_data, target = False):
    """
    Function to clean data and add feature engineering including sentiment scores and text length.
    target = True if processing labelled data for training a model. If processing dataset with no target,
    i.e. to make predictions using unlabelled data, then target = False.

    :param pd.DataFrame, text_data: A ``pandas.DataFrame`` with the data to be cleaned. Essential to have one
    column labelled 'predictor', containing text for training or predictions.
    :param target: Name of the column containing the target to be predicted.
    :type target: str, optional

    :return: a pandas.DataFrame with the ordinal values in the 'target' column changed from 5 to 4, or -5 to -4.
    :rtype: pandas.DataFrame


    """
    # Add feature text_length
    text_data['text_length'] = text_data['predictor'].apply(lambda x:
                                len([word for word in str(x).split(' ') if word != '']))
    # Clean data - basic preprocessing, removing punctuation, decode emojis, dropnas
    text_data_cleaned = clean_data(text_data, target)
    # Get sentiment scores
    if 'original_text' in list(text_data_cleaned.columns):
        sentiment = sentiment_scores.sentiment_scores(text_data_cleaned[['original_text']])
        sentiment = sentiment.copy().drop(columns=['vader_neg', 'vader_neu', 'vader_pos'])
        text_data = text_data_cleaned.join(sentiment).drop(columns=['original_text']).copy()
    else:
        sentiment = sentiment_scores.sentiment_scores(text_data_cleaned[['predictor']])

    print(f'Shape of dataset after cleaning and processing is {text_data.shape}')
    return text_data

def factory_data_load_and_split(filename, target, predictor, test_size=0.33, reduce_criticality=False, theme=None):
    """
    This function pulls together all the functions above. It loads the dataset, renames the response and predictor as
    "target" and "predictor" respectively, conducts preprocessing, and splits the dataset into training and test sets.

    **NOTE:** As described later, arguments `reduce_criticality` and `theme` are for internal use by Nottinghamshire
    Healthcare NHS Foundation Trust or other trusts who use the theme ("Access", "Environment/ facilities" etc.) and
    criticality labels. They can otherwise be safely ignored.

    :param filename: A ``pandas.DataFrame`` with the data (class and text columns), otherwise the
            dataset name (CSV), including full path to the data folder (if not in the project's working directory), and the
            data type suffix (".csv"). If ``filename`` is ``None``, the data is read from the SQL database.
            **NOTE:** The feature that reads data from the database is for internal use only. Experienced users who would
            like to pull their data from their own databases can, of course, achieve that by slightly modifying the
            relevant lines in the script and setting up the connection to the SQL server.
    :type filename: pd.DataFrame
    :param target: Name of the column containing the target to be predicted.
    :type target: str
    :param str predictor: Name of the column containing the text to be used to train the model or make predictions.
    :param test_size: Proportion of data that will form the test dataset.
    :type test_size: float, optional
    :param reduce_criticality: For internal use by Nottinghamshire Healthcare NHS Foundation Trust or other trusts
        that hold data on criticality. If `True`, then all records with a criticality of "-5" (respectively, "5") are
        assigned a criticality of "-4" (respectively, "4"). This is to avoid situations where the pipeline breaks due to
        a lack of sufficient data for "-5" and/or "5". This param is only relevant when target = "criticality"
    :type reduce_criticality: bool, optional
    :param theme: Name of the column containing the 'theme' data which can be used to train a model predicting
            'criticality'. If supplied, the theme variable will be used as a predictor (along with the text predictor)
        in the model that is fitted with criticality as the response variable. The rationale is two-fold. First, to
        help the model improve predictions on criticality when the theme labels are readily available. Second, to force
        the criticality for "Couldn't be improved" to always be "3" in the training and test data, as well as in the
        predictions. This is the only criticality value that "Couldn't be improved" can take, so by forcing it to always
        be "3", we are improving model performance, but are also correcting possible erroneous assignments of values
        other than "3" that are attributed to human error.
    :type theme: str, optional

    :return: A tuple containing the following objects in order:
        x_train, a pd.DataFrame containing the training data;
        x_test, a pd.DataFrame containing the test data;
        y_train, a pd.Series containing the targets for the training data;
        y_test, a pd.Series containing the targets for the test data;
        index_training_data, a pd.Series of the indices of the data used in the train set;
        index_test_data, a pd.Series of the indices of the data used in the test set
    :rtype: tuple

    """

    # Get data from CSV if filename provided. Else, load fom SQL server
    text_data = load_data(filename=filename, theme=theme, target=target, predictor=predictor)

    text_data = process_data(text_data, target = True)

    # This is specific to NHS patient feedback data labelled with "criticality" classes
    if reduce_criticality == True:
        text_data = reduce_crit(text_data, theme)

    print('Preparing training and test sets...')
    x = text_data.drop(columns = 'target').copy() # Needs to be an array of a data frame- can't be a pandas Series
    # if theme is not None:
    #     x['theme'] = text_data['theme'].copy()
    y = text_data['target'].to_numpy()
    x_train, x_test, y_train, y_test, index_training_data, index_test_data = \
            train_test_split(x, y, pd.DataFrame(x).index,
                            test_size=test_size,
                            stratify=y,
                            shuffle=True
                            )
    print("Done")

    return x_train, x_test, y_train, y_test, index_training_data, index_test_data


if __name__ == '__main__':
    df = load_multilabel_data(filename = 'datasets/phase_2_test.csv', target = 'major_categories')
    print(df.head())
