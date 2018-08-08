# ******************************************************************************
# Copyright 2017-2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ******************************************************************************
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import numpy as np
import re


# pylint: disable=invalid-unary-operand-type
def pad_sentences(sequences, max_length=None, padding_value=0.):
    """
    Pad input sequences up to max_length
    values are aligned to the right

    Args:
        sequences (iter): a 2D matrix (np.array) to pad
        max_length (int, optional): max length of resulting sequences
        padding_value (int, optional): padding value

    Returns:
        input sequences padded to size 'max_length'
    """
    if max_length is None:
        max_length = np.max([len(s) for s in sequences])
    elif max_length < 1:
        raise ValueError('max sequence length must be > 0')

    padded_sequences = (np.ones((len(sequences), max_length)) * padding_value)
    for i, sent in enumerate(sequences):
        trunc = sent[-max_length:]
        padded_sequences[i, -len(trunc):] = trunc
    return padded_sequences.astype(dtype=np.int32)


def one_hot(mat, num_classes):
    """
    Convert a 1D matrix of ints into one-hot encoded vectors.

    Arguments:
        mat (numpy.ndarray): A 1D matrix of labels (int)
        num_classes (int): Number of all possible classes

    Returns:
        numpy.ndarray: A 2D matrix
    """
    assert len(mat.shape) < 2 or isinstance(mat.shape, int)
    vec = np.zeros((mat.shape[0], num_classes))
    for i, v in enumerate(mat):
        vec[i][v] = 1.0
    return vec


def one_hot_sentence(mat, num_classes):
    """
    Convert a 2D matrix of ints into one-hot encoded 3D matrix

    Arguments:
        mat (numpy.ndarray): A 2D matrix of labels (int)
        num_classes (int): Number of all possible classes

    Returns:
        numpy.ndarray: A 3D matrix
    """
    new_mat = []
    for i in range(mat.shape[0]):
        new_mat.append(one_hot(mat[i], num_classes))
    return np.asarray(new_mat)


def add_offset(mat, offset=1):
    """
    Add +1 to all values in matrix mat

    Arguments:
        mat (numpy.ndarray): A 2D matrix with int values
        offset (int): offset to add

    Returns:
        numpy.ndarray: input matrix
    """
    for i, vec in enumerate(mat):
        offset_arr = np.array(vec.shape)
        offset_arr.fill(offset)
        mat[i] = vec + offset_arr
    return mat


# pylint: disable=no-member
def get_paddedXY_sequence(X, y, vocab_size=20000, sentence_length=100, oov=2,
                          start=1, index_from=3, seed=113, shuffle=True):
    if shuffle:
        np.random.seed(seed)
        np.random.shuffle(X)
        np.random.seed(seed)
        np.random.shuffle(y)

    if start is not None:
        X = [[start] + [w + index_from for w in x] for x in X]
    else:
        X = [[w + index_from for w in x] for x in X]

    if not vocab_size:
        vocab_size = max([max(x) for x in X])

    # word ids - pad (0), start (1), oov (2)
    if oov is not None:
        X = [[oov if w >= vocab_size else w for w in x] for x in X]
    else:
        X = [[w for w in x if w < vocab_size] for x in X]

    X = pad_sentences(X, max_length=sentence_length)

    y = [[w + 1.0 for w in i] for i in y]
    y = pad_sentences(y, max_length=sentence_length)

    return X, y


def license_prompt(model_name, model_website, dataset_dir=None):
    if dataset_dir:
        print('{} was not found in the directory: {}'.format(model_name, dataset_dir))
    else:
        print('{} was not found on local installation'.format(model_name))
    print('{} can be downloaded from {}'.format(model_name, model_website))
    print('\nThe terms and conditions of the data set license apply. Intel does not '
          'grant any rights to the data files or database\n')
    response = input('\nTo download \'{}\' from {}, please enter YES: '.
                     format(model_name, model_website))
    res = response.lower().strip()
    if res == "yes" or (len(res) == 1 and res == 'y'):
        print('Downloading {}...'.format(model_name))
        responded_yes = True
    else:
        print('Download declined. Response received {} != YES|Y. '.format(res))
        if dataset_dir:
            print('Please download the model manually from {} and place in the directory: {}'
                  .format(model_website, dataset_dir))
        else:
            print('Please download the model manually from {}'.format(model_website))
        responded_yes = False
    return responded_yes


# character vocab
zhang_lecun_vocab = list("abcdefghijklmnopqrstuvwxyz0123456789-,;.!?:’/\|_@#$%ˆ&*˜‘+=<>()[]{}")
vocab_hash = {b: a for a, b in enumerate(zhang_lecun_vocab)}


def normalize(txt, vocab=None, replace_char=' ',
              max_length=300, pad_out=True,
              to_lower=True, reverse=False,
              truncate_left=False, encoding=None):

    # remove html
    # This will keep characters and other symbols
    txt = txt.split()
    # Remove HTML
    txt = [re.sub(r'http:.*', '', r) for r in txt]
    txt = [re.sub(r'https:.*', '', r) for r in txt]

    txt = (" ".join(txt))

    # Remove punctuation
    txt = re.sub("[.,!]", " ", txt)
    txt = " ".join(txt.split())

    # store length for multiple comparisons
    txt_len = len(txt)

    if truncate_left:
        txt = txt[-max_length:]
    else:
        txt = txt[:max_length]
    # change case
    if to_lower:
        txt = txt.lower()
    # Reverse order
    if reverse:
        txt = txt[::-1]
    # replace chars
    if vocab is not None:
        txt = ''.join([c if c in vocab else replace_char for c in txt])
    # re-encode text
    if encoding is not None:
        txt = txt.encode(encoding, errors="ignore")
    # pad out if needed
    if pad_out and max_length > txt_len:
        txt = txt + replace_char * (max_length - txt_len)
    return txt


def to_one_hot(txt, vocab=vocab_hash):
    vocab_size = len(vocab.keys())
    one_hot_vec = np.zeros((vocab_size + 1, len(txt)), dtype=np.float32)
    # run through txt and "switch on" relevant positions in one-hot vector
    for idx, char in enumerate(txt):
        if char in vocab_hash:
            vocab_idx = vocab_hash[char]
            one_hot_vec[vocab_idx, idx] = 1
        # raised if character is out of vocabulary
        else:
            pass
    return one_hot_vec


def balance(df):
    print("Balancing the classes")
    type_counts = df['Sentiment'].value_counts()
    min_count = min(type_counts.values)

    balanced_df = None
    for key in type_counts.keys():
        df_sub = df[df['Sentiment'] == key].sample(n=min_count, replace=False)
        if balanced_df is not None:
            balanced_df = balanced_df.append(df_sub)
        else:
            balanced_df = df_sub
    return balanced_df
