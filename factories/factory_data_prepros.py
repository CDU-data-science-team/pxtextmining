import re
import pandas as pd
from os import path
import emojis
from sklearn.model_selection import train_test_split


def factory_data_prepros(filename, target, predictor, test_size=0.33, keep_emojis=True):
    """
    Function loads the dataset, renames the response and predictor as "target" and "predictor" respectively,
    cleans the text in the predictor, splits the dataset into training and test sets.

    :param str filename: Dataset name (CSV), including the data type suffix.
    :param str target: Name of the response variable.
    :param str predictor: Name of the predictor variable.
    :param float test_size: Proportion of data that will form the test dataset.
    :param bool keep_emojis: Whether to keep and decode emojis or completely remove them from text.
    :return: A tuple of length 4 predictor-train, predictor-test, target-train and target-test datasets.
    """

    print('Loading dataset...')

    data_path = path.join('datasets', filename)
    text_data = pd.read_csv(data_path)
    text_data = text_data.rename(columns={target: 'target', predictor: 'predictor'})

    # predictor_raw = text_data.predictor.copy()  # Keep a copy of the original text
    # Strip punctuation, excess spaces, \r and \n from the text
    print('Stripping punctuation from text...')
    #text_data['predictor'] = text_data['predictor'].str.replace('[^\w\s]', '')
    print("Stripping excess spaces, whitespaces and line breaks from text...")
    for text, index in zip(text_data["predictor"], text_data.index):
        aux = str(text)
        aux = emojis.decode(aux)
        pattern = "\:(.*?)\:"  # Decoded emojis are enclosed inside ":", e.g. ":blush:"
        pattern_search = re.search(pattern, aux)
        # We want to tell the model that words inside ":" are decoded emojis.
        # However, "[^\w]" removes ":". It doesn't remove "_" or "__" though, so we may enclose decoded emojis
        # inside "__" instead.
        if pattern_search is not None:
            emoji_decoded = pattern_search.group(1)
            if keep_emojis:
                aux = re.sub(pattern, "__" + emoji_decoded + "__", aux)
                # Sometimes emojis are consecutive e.g. ❤❤ is encoded into __heart____heart__. Split them.
                aux = re.sub("____", "__ __", aux)
            else:
                aux = re.sub(pattern, "", aux)
        # Remove non-alphanumeric characters
        aux = re.sub("[^\w]", " ", aux)
        # Remove excess whitespaces
        aux = re.sub(" +", " ", aux)
        #aux = " ".join(text.splitlines())
        text_data.loc[index, "predictor"] = aux

    print('Preparing training and test sets...')
    x = pd.DataFrame(text_data["predictor"])
    y = text_data["target"].to_numpy()
    x_train, x_test, y_train, y_test = train_test_split(x, y,
                                                        test_size=test_size,
                                                        stratify=y,
                                                        shuffle=True,
                                                        random_state=42
                                                        )

    return x_train, x_test, y_train, y_test
