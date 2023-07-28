import re
from copy import deepcopy
from typing import List, Optional, Tuple
import nltk
nltk.download('wordnet')
from nltk.stem import WordNetLemmatizer
from st_augmentor import singular_they_augmentor
from utils import align, TokenAnnotation, AnnotatedTokens

lemmatizer = WordNetLemmatizer()


def lemmatize_verb(text: str) -> str:
    return lemmatizer.lemmatize(text, pos="v")


pronoun_map_st = {
    "they": ["he", "she"],
    "them": [
        "her",
        "him",
    ],
    "their": ["his", "her"],
    "themself": ["herself", "himself"],
    "themselves": ["herself", "himself"],
}


def are_counterparts(source_str: str, target_str: str) -> bool:
    """
    Checks if two token strings are counterparts. Tokens are counterparts
    if they are pronominal and the 3PL target_str corresponds in case with
    the 3SG source_str, or if they are the same verbal lemma.
    :param source_str: str
    :param target_str: str
    :return: bool
    """
    gendered_counterparts = source_str.casefold() in pronoun_map_st.get(
        target_str.casefold(), []
    )
    copular_counterparts = (source_str.casefold() in ['is', '\'s']) and (target_str.casefold() in ['are', '\'re'])
    verbal_counterparts = lemmatize_verb(source_str.casefold()) == lemmatize_verb(target_str.casefold())
    return gendered_counterparts | copular_counterparts | verbal_counterparts


def align_annotation_text(
    annotation: TokenAnnotation, annotation_pattern: re.Pattern
) -> Optional[str]:
    """
    Swaps a target token for a source token if the source token was swapped and they are counterparts. Otherwise, returns None.
    :param annotation: TokenAnnotation
    :param annotation_pattern: re.Pattern
    :return: Optional[str]
    """
    def align_token_strings(source_str: str, target_str: str) -> Optional[str]:
        "Checks if token strings can be aligned."
        if annotation_pattern.search(target_str) is not None:
            target_str_clean = annotation_pattern.search(target_str).group(1)
            if are_counterparts(source_str, target_str_clean):
                return target_str_clean
            else:
                return None
        else:
            return source_str

    if annotation_pattern.search(annotation.suggestions[0]) is None:  # nothing to swap
        return annotation.source_text
    source_tokens = annotation.source_text.split()
    suggestion_tokens = annotation.suggestions[0].split()
    if len(source_tokens) != len(suggestion_tokens):
        return None
    else:
        aligned_tokens = [
            align_token_strings(src_str, tgt_str)
            for src_str, tgt_str in zip(source_tokens, suggestion_tokens)
        ]
        if all(isinstance(token, str) for token in aligned_tokens):
            return " ".join(aligned_tokens)
        else:
            return None


def merge_aligned(
    aligned_text: AnnotatedTokens, annotation_pattern: re.Pattern
) -> Optional[str]:
    """
    Merges in swapped tokens from the target text to the source text in an aligned text
    if the swap is safe. If a swap isn't safe, returns None.
    :param aligned_text: AnnotatedTokens
    :param annotation_pattern: re.Pattern
    :return: Optional[str]
    """
    aligned_copy = deepcopy(aligned_text)
    for annotation in aligned_copy.iter_annotations():
        aligned_text = align_annotation_text(annotation, annotation_pattern)
        if aligned_text == None:
            return None
        else:
            annotation.suggestions[0] = aligned_text
            aligned_copy.apply_correction(annotation)
    return aligned_copy.get_corrected_text()


def gec_safe_swap_target(
    source_str: str, target_str: str, annotation_pattern: re.Pattern
) -> Optional[str]:
    """
    Safely merges in swapped tokens from the target text to the source text. If the swap isn't safe, returns None.
    :param source_str: str
    :param target_str: str
    :param annotation_pattern: re.Pattern
    :return: Optional[str]
    """
    aligned_text = align(source_str, target_str)
    merged_source = merge_aligned(aligned_text, annotation_pattern)
    return merged_source


def st_augmentor_for_gec(source_str: str, target_str: str) -> Optional[Tuple[str, str]]:
    """
    Given a source string and a target string, create singular they versions of these strings
    if possible. If it's not possible, return None
    :param source_str: str
    :param target_str: str
    :return: Optional[Tuple[str, str]]
    """
    annotation = lambda x: "<<<{text}>>>".format(text=x)
    annotation_pattern = re.compile(r"<<<(\S*)>>>")
    st_target_str = singular_they_augmentor(
        target_str, check_singular=True, annotation=annotation
    )
    if st_target_str is None:
        return None
    else:
        st_source_str = gec_safe_swap_target(
            source_str, st_target_str, annotation_pattern
        )
        if st_source_str is None:
            return None
        else:
            return st_source_str, annotation_pattern.sub(
                lambda m: m.group(1), st_target_str
            )
