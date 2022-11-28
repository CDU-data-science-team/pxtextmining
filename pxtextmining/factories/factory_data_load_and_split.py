import pandas as pd
from os import path
import mysql.connector
from sklearn.model_selection import train_test_split
import re
import string
import numpy as np
from pxtextmining.helpers import decode_emojis, text_length, sentiment_scores

def load_data(filename, target, predictor, theme = None):
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
    # removes punctuation and numbers
    # converts emojis into text
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

def clean_data(text_data, target = None):
    # text_data['predictor'] = text_data.predictor.fillna('__notext__')
    if target != None:
        text_data_clean = text_data.dropna(subset=['target', 'predictor']).copy()
    else:
        text_data_clean = text_data.dropna(subset=['predictor']).copy()
    for i in ['NULL', 'N/A', 'NA', 'NONE']:
        text_data_clean = text_data_clean[text_data_clean['predictor'].str.upper() != i].copy()
    text_data['predictor'] = text_data_clean['predictor'].apply(remove_punc_and_nums)
    text_data['predictor'] = text_data['predictor'].replace('', np.NaN)
    if target != None:
        text_data = text_data.dropna(subset=['target', 'predictor']).copy()
    else:
        text_data = text_data.dropna(subset=['predictor']).copy()
    # have decided against dropping duplicates for now as this is a natural part of dataset
    # text_data = text_data.drop_duplicates().copy()
    return text_data

def reduce_crit(text_data, theme):
    text_data = text_data.query("target in ('-5', '-4', '-3', '-2', '-1', '0', '1', '2', '3', '4', '5')")
    text_data.loc[text_data.target == '-5', 'target'] = '-4'
    text_data.loc[text_data.target == '5', 'target'] = '4'
    print('error?')
    if theme is not None:
        text_data.loc[text_data['theme'] == "Couldn't be improved", 'target'] = '3'
    return text_data

def process_data(text_data, target = None):
    # Add feature text_length
    text_data['text_length'] = text_data['predictor'].apply(lambda x:
                                len([word for word in str(x).split(' ') if word != '']))
    # Clean data - basic preprocessing, removing punctuation, decode emojis, dropnas
    text_data_cleaned = clean_data(text_data, target)
    # Get sentiment scores
    sentiment = sentiment_scores.sentiment_scores(text_data[['predictor']])
    text_data = text_data_cleaned.join(sentiment).copy()
    print(f'Shape of dataset after cleaning and processing is {text_data.shape}')
    return text_data

def factory_data_load_and_split(filename, target, predictor, test_size=0.33, reduce_criticality=False, theme=None):
    """
    Function loads the dataset, renames the response and predictor as "target" and "predictor" respectively,
    and splits the dataset into training and test sets.

    **NOTE:** As described later, arguments `reduce_criticality` and `theme` are for internal use by Nottinghamshire
    Healthcare NHS Foundation Trust or other trusts who use the theme ("Access", "Environment/ facilities" etc.) and
    criticality labels. They can otherwise be safely ignored.

    :param str, pandas.DataFrame filename: A ``pandas.DataFrame`` with the data (class and text columns), otherwise the
        dataset name (CSV), including full path to the data folder (if not in the project's working directory), and the
        data type suffix (".csv"). If ``filename`` is ``None``, the data are read from the database.
        **NOTE:** The feature that reads data from the database is for internal use only. Experienced users who would
        like to pull their data from their own databases can, of course, achieve that by slightly modifying the
        relevant lines in the script. A "my.conf" file will need to be placed in the root, with five lines, as follows
        (without the ";", "<" and ">"):

        - [connector_python];
        - host = <host_name>;
        - database = <database_name>;
        - user = <username>;
        - password = <password>;
    :param str target: Name of the response variable.
    :param str predictor: Name of the predictor variable.
    :param float test_size: Proportion of data that will form the test dataset.
    :param bool reduce_criticality: For internal use by Nottinghamshire Healthcare NHS Foundation Trust or other trusts
        that hold data on criticality. If `True`, then all records with a criticality of "-5" (respectively, "5") are
        assigned a criticality of "-4" (respectively, "4"). This is to avoid situations where the pipeline breaks due to
        a lack of sufficient data for "-5" and/or "5". Defaults to `False`.
    :param str theme: For internal use by Nottinghamshire Healthcare NHS Foundation Trust or other trusts
        that use theme labels ("Access", "Environment/ facilities" etc.). The column name of the theme variable.
        Defaults to `None`. If supplied, the theme variable will be used as a predictor (along with the text predictor)
        in the model that is fitted with criticality as the response variable. The rationale is two-fold. First, to
        help the model improve predictions on criticality when the theme labels are readily available. Second, to force
        the criticality for "Couldn't be improved" to always be "3" in the training and test data, as well as in the
        predictions. This is the only criticality value that "Couldn't be improved" can take, so by forcing it to always
        be "3", we are improving model performance, but are also correcting possible erroneous assignments of values
        other than "3" that are attributed to human error.
    :return: A tuple of length 4: predictor-train, predictor-test, target-train and target-test datasets.
    """

    # Get data from CSV if filename provided. Else, load fom SQL server
    text_data = load_data(filename, theme, target, predictor)

    text_data = process_data(text_data, target = target)

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
    x_train, x_test, y_train, y_test, index_training_data, index_test_data = \
        factory_data_load_and_split(filename='datasets/text_data.csv', target="criticality", predictor="feedback",
                                 test_size=0.33, reduce_criticality=True,
                                 theme="label")
    print(x_train.head())
