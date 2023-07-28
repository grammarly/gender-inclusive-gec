import spacy
from spacy.tokens import Token, Span, Doc
import pyinflect
import neuralcoref

from typing import Callable, List, Optional

nlp = spacy.load("en_core_web_lg")

neuralcoref.add_to_pipe(nlp)

Token.set_extension("swapped_text", default="")
Token.set_extension("has_swap", default=False)
Doc.set_extension("has_swap", default=False)
Doc.set_extension("swapped_text", default="")
Doc.set_extension("swap_clusters", default=[])

sing_copulae = ["is", "was", "'s", "s"]
pronouns = ["he", "she", "him", "her", "his", "himself", "herself", "hers"]

verbal_pos = ["VERB", "AUX"]
subj_dep = ["nsubj", "nsubjpass"]
aux_dep = ["aux", "auxpass"]


def token_is_nn(tok: Token) -> bool:
    """
    Token has NN part of speech tag.
    :param tok: Token
    :return: bool
    """
    return tok.tag_ == "NN"


def token_is_name(tok: Token) -> bool:
    """
    Token has PROPN part of speech tag.
    :param tok: Token
    :return: bool
    """
    return tok.pos_ == "PROPN"


def token_has_sing_possesum(tok: Token) -> bool:
    """
    Token has a singular possessum.
    :param tok: Token
    :return: bool
    """
    if tok.tag_[-1] == "$":
        return (tok.dep_ == "poss") and (tok.head.tag_ == "NN")
    else:
        return False


def token_has_nn_attr(tok: Token) -> bool:
    """
    Token has an NN attribute (for copular-like constructions).
    :param tok: Token
    :return: bool
    """
    has_attr_head = any(
        child.dep_ == "attr" and child.tag_ == "NN" for child in tok.head.children
    )
    return tok.dep_ == "nsubj" and has_attr_head


def token_is_singular(tok: Token) -> bool:
    """
    Token has a feature identifying it as singular.
    :param tok: Token
    :return: bool
    """
    return any(
        [
            token_is_nn(tok),
            token_is_name(tok),
            token_has_sing_possesum(tok),
            token_has_nn_attr(tok),
        ]
    )


def token_is_conjoined_agr_verb(tok: Token) -> bool:
    """
    Verb agrees with the subject of a conjoined verb.
    :param tok: Token
    :return:
    """
    tok_is_verbal = tok.pos_ in verbal_pos
    tok_has_no_nsubj = not any(child.dep_ in subj_dep for child in tok.children)
    return tok_is_verbal and tok_has_no_nsubj


def get_agreeing_verb(tok: Token) -> Token:
    """
    Given a verbal token, return a child auxiliary verb that would morphologically agree
    with the subject noun. If no such verb, return input verb.
    :param tok: Token
    :return: Token
    """
    if any(child.pos_ == "AUX" and child.dep_ in aux_dep for child in tok.children):
        # Pick the leftmost auxiliary child
        agreeing_head = list(
            filter(lambda x: x.pos_ == "AUX" and x.dep_ in aux_dep, tok.children)
        )[0]
    else:
        agreeing_head = tok
    return agreeing_head


def get_conjoined_agr_verb(tok: Token) -> Optional[Token]:
    """
    Checks if the conjoined token is verbal and has no dependent subject.
    This means it shares a subject with the leftward conjunct. Returns
    the verbal head that would agree with this subject.
    :param tok: Token
    :return: Optional[Token]
    """
    tok_is_verbal = tok.pos_ in verbal_pos
    tok_has_no_nsubj = not any(child.dep_ in subj_dep for child in tok.children)
    if tok_is_verbal and tok_has_no_nsubj:
        return get_agreeing_verb(tok)
    else:
        return None


def get_agr_verb_ids(tok: Token) -> Optional[List[int]]:
    """
    Get agreeing verb indices for a given (nominal) input token. Returns more than
    one in the case of conjoined verbs.
    :param tok: Token
    :return: Optional[List[int]]
    """
    if tok.head.pos_ in verbal_pos and tok.dep_ in subj_dep:
        agreeing_head = get_agreeing_verb(tok.head)
        agreeing_children = list(
            filter(
                lambda x: x is not None, map(get_conjoined_agr_verb, tok.head.conjuncts)
            )
        )
        return list(map(lambda x: x.i, [agreeing_head, *agreeing_children]))
    else:
        return None


def get_plural_verb(tok: Token) -> str:
    """
    Returns the 3PL form of a given (verbal) token.
    :param tok: Token
    :return: string
    """
    if tok.text.casefold() in sing_copulae:
        if tok.text.casefold() == "'s":
            return match_tok_case(tok, "'re")
        elif tok.tag_ == "VBZ":
            return tok._.inflect("VBP", inflect_oov=True, form_num=1)
        elif tok.tag_ == "VBD":
            return tok._.inflect("VBD", inflect_oov=True, form_num=1)
    if tok.tag_ == "VBZ":
        return tok._.inflect("VBP", inflect_oov=True)
    else:
        return tok.text


def get_cluster_roots(tok: Token) -> List[Token]:
    """
    Get the roots of the tokens in the coref cluster for an input token.
    :param tok: Token
    :return: List[Token]
    """
    roots = [span.root for cluster in tok._.coref_clusters for span in cluster]
    return roots


def token_is_singleton(tok: Token) -> bool:
    """
    Checks if a token is not part of some larger span.
    :param tok: Token
    :return: bool
    """
    roots = get_cluster_roots(tok)
    return tok not in roots


def match_tok_case(tok: Token, text: str) -> str:
    """
    Match the case of text to the token's case.
    :param tok: Token
    :param text: str
    :return: str
    """
    if tok.is_title:
        return text.title()
    elif tok.is_upper:
        return text.upper()
    else:
        return text.lower()


def get_plural_pronoun(tok: Token) -> str:
    """
    Get the corresponding 3PL pronoun for the input (pronominal) token.
    :param tok: Token
    :return: str
    """
    if tok.text.casefold() in ["he", "she"]:
        return match_tok_case(tok, "they")
    elif tok.text.casefold() in ["himself", "herself"]:
        return match_tok_case(tok, "themself")
    elif tok.tag_ == "PRP$":
        if tok.dep_ not in ["poss", "nsubj"] and tok.text.casefold() in ["his", "hers"]:
            return match_tok_case(tok, "theirs")
        else:
            return match_tok_case(tok, "their")
    elif tok.text.casefold() == "hers":
        return match_tok_case(tok, "theirs")
    else:
        return match_tok_case(tok, "them")


def cluster_has_pronoun(cluster: List[Span]) -> bool:
    """
    Return True if the coreference cluster has a pronoun.
    :param cluster: List[Span]
    :return: bool
    """
    return any(span.root.text.casefold() in pronouns for span in cluster)


def cluster_is_singular(cluster: List[Span]) -> bool:
    """
    Return True if any of the spans in the cluster are singular.
    Singular spans indicate that swapping would result in unambiguous
    singular "they".
    :param cluster: List[Span]
    :return: bool
    """
    return any(token_is_singular(span.root) for span in cluster)


def set_swapped_token_text(
    tok: Token, annotation: Optional[Callable[[str], str]] = None
) -> None:
    """
    Set the swapped replacement text for the token. I.e., "they" or
    a verb with 3PL morphological agreement. Swapped tokens can be noted
    by specifying an annotation function in the `annotation` argument.
    :param tok: Token
    :param annotation: Optional[Callable[[str], str]]
    :return: None
    """
    if not annotation:
        annotation = lambda x: x
    if tok.text.casefold() in pronouns:
        tok._.has_swap = True
        tok.doc._.has_swap = True
        tok._.swapped_text = annotation(get_plural_pronoun(tok))
        agr_verb_ids = get_agr_verb_ids(tok)
        if agr_verb_ids:
            for id in agr_verb_ids:
                tok.doc[id]._.swapped_text = annotation(get_plural_verb(tok.doc[id]))


def set_swapped_doc_text(
    doc: Doc,
    check_singular: bool = True,
    annotation: Optional[Callable[[str], str]] = None,
) -> None:
    """
    Determine if the doc has a swappable cluster and set the swapped text. Swapped tokens can be noted
    by specifying an annotation function in the `annotation` argument.
    :param doc: Doc
    :param check_singular: bool
    :param annotation: Optional[Callable[[str], str]]
    :return: None
    """
    if check_singular:
        if doc._.has_coref:
            for cluster in doc._.coref_clusters:
                if cluster_is_singular(cluster) and cluster_has_pronoun(cluster):
                    doc._.swap_clusters.append(cluster)
                    for span in cluster:
                        set_swapped_token_text(span.root, annotation)
        for tok in doc:
            if (
                tok.text.casefold() in pronouns
                and token_is_singleton(tok)
                and token_has_nn_attr(tok)
            ):
                set_swapped_token_text(tok, annotation)
    else:
        for tok in doc:
            if tok.text.casefold() in pronouns:
                set_swapped_token_text(tok, annotation)


def get_swapped_string(doc: Doc) -> str:
    """
    Get the entire swapped string from the doc.
    :param doc: Doc
    :return: str
    """
    swapped_str = ""
    for tok in doc:
        if tok._.swapped_text:
            swapped_str += str(tok._.swapped_text) + str(tok.whitespace_)
        else:
            swapped_str += tok.text_with_ws
    return swapped_str


def singular_they_augmentor(
    text: str,
    check_singular: bool = True,
    annotation: Optional[Callable[[str], str]] = None,
) -> Optional[str]:
    """
    Perform singular-they augmentation. Returns None if no augmentation is
    possible for the given text. If `check_singular` is True, swaps
    are only performed if result would have singular coreference. Swapped tokens can be noted
    by specifying an annotation function in the `annotation` argument.
    :param text: str
    :param check_singular: bool
    :param annotation: Optional[Callable[[str], str]]
    :return: Optional[str]
    """
    doc = nlp(text)
    set_swapped_doc_text(doc, check_singular, annotation)
    if doc._.has_swap:
        swapped_text = get_swapped_string(doc)
    else:
        swapped_text = None
    return swapped_text
