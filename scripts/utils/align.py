import difflib

from .annotated_tokens import AnnotatedTokens


def align(source, target):
    """Create AnnotatedTokens object based on two sentences.

    Args:
        source (str or list<str>): Original sentence or tokens.
        target (str or list<str>): Corrected sentence or tokens.

    Return:
        AnnotatedTokens object.

    Example:
        >>> align("Hello world", "Hey world")
        <AnnotatedTokens('{Hello=>Hey} world')>
    """

    if isinstance(source, str):
        source = source.split()

    ann_tokens = AnnotatedTokens(source)
    for diff in _gen_diffs(source, target):
        l, r, repl = diff
        ann_tokens.annotate(l, r, repl)
    return ann_tokens


def _gen_diffs(original, translation, merge=True):
    tokens = _get_tokens(original)
    translation_tokens = _get_tokens(translation)

    matcher = difflib.SequenceMatcher(None, tokens, translation_tokens)
    diffs = list(matcher.get_opcodes())

    for diff in diffs:
        if _tag(diff) == "equal":
            continue

        _, i1, i2, j1, j2 = diff
        yield i1, i2, " ".join(translation_tokens[j1:j2])


def _get_tokens(str_or_list):
    if isinstance(str_or_list, str):
        return str_or_list.split()

    if isinstance(str_or_list, list):
        return str_or_list[:]

    raise ValueError("Cannot cast {} to list of tokens.".format(type(str_or_list)))


def _tag(diff):
    return diff[0]
