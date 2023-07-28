import inspect
from collections import namedtuple
from enum import Enum

NO_SUGGESTIONS = "NO_SUGGESTIONS"
DEFAULT = object()


class OverlapError(ValueError):
    pass


class OnOverlap(str, Enum):
    ERROR = "error"
    OVERRIDE = "override"
    SAVE_OLD = "save_old"
    MERGE_STRICT = "merge_strict"  # Merge annotations that coincide exatly
    MERGE_EXPAND = "merge_expand"  # Merge annotations and expand their spans


class MutableTokens:
    """Represents list of tokens that can be modified."""

    def __init__(self, tokens):
        if isinstance(tokens, str):
            tokens = tokens.strip().split(" ")
        self._tokens = tokens
        self._edits = []

    def __str__(self):
        """Pretend to be a normal string."""
        return self.get_edited_text()

    def __repr__(self):
        return "<MutableTokens({})>".format(repr(str(self)))

    def replace(self, start, end, value):
        """Replace sublist with a value.

        Example:
            >>> t = MutableTokens('the red fox')
            >>> t.replace(1, 2, 'brown')
            >>> t.get_edited_text()
            'the brown fox'
        """
        self._edits.append((start, end, value))  # TODO: keep _edits sorted?

    def apply_edits(self):
        """Applies all edits made so far."""
        self._tokens = self.get_edited_tokens()
        self._edits = []

    def get_source_tokens(self):
        """Return list of tokens without pending edits applied.

        Example:
            >>> t = MutableTokens('the red fox')
            >>> t.replace(1, 2, 'brown')
            >>> t.get_source_tokens()
            ['the', 'red', 'fox']
        """
        return self._tokens

    def get_source_text(self):
        """Return string without no pending edits applied.

        Example:
            >>> t = MutableTokens('the red fox')
            >>> t.replace(1, 2, 'brown')
            >>> t.get_source_text()
            'the red fox'
        """
        return " ".join(self.get_source_tokens())

    def get_edited_tokens(self, *, highlight=False):
        """Return tokens with all corrections applied.

        Args:
            highlight (bool): If True, keep NO_SUGGESTIONS markup in correction.
                This signals the error is highlighted but no suggestion was
                provided.
        """
        result = []
        i = 0
        t = self._tokens
        for begin, end, val in sorted(self._edits, key=lambda x: (x[0], x[1])):
            result.extend(t[i:begin])
            if not highlight and "NO_SUGGESTIONS" in val:
                result.extend(t[begin:end])
            elif val:
                result.extend(val.split(" "))
            i = end
        result.extend(t[i:])
        return result

    def get_edited_text(self, *, highlight=False):
        """Return text with all corrections applied."""
        return " ".join(self.get_edited_tokens(highlight=highlight))


class AnnotatedTokens:
    """Tokens representation that allows easy replacements and annotations.

    All text representations is made by joining tokens by space. This format of
    converting is assumed by default in this class.
    """

    def __init__(self, tokens):
        """Creates object.

        Args:
            tokens (AnnotatedText or str or list): Allowed formats:
                - AnnotatedText instance
                - a string of tokens joined by space
                - a list of tokens.
        """

        self._annotations = []
        if isinstance(tokens, str):
            self._tokens = tokens.split(" ")
        else:
            self._tokens = tokens

    def __str__(self):
        return self.get_annotated_text()

    def __repr__(self):
        return "<AnnotatedTokens('{}')>".format(self.get_annotated_text())

    def __eq__(self, other):
        if type(self) != type(other):
            return False

        if self._tokens != other._tokens:
            return False

        if len(self._annotations) != len(other._annotations):
            return False

        for ann in other._annotations:
            if ann != self.get_annotation_at(ann.start, ann.end):
                return False

        return True

    def annotate(
        self, start, end, correct_value, meta=None, on_overlap=OnOverlap.ERROR
    ):
        """Annotate sublist as being corrected.

        Args:
            start (int): starting position of the sublist to annotate.
            end (int): ending position of the sublist to annotate.
            correct_value (str, iterable, None): one or more correction
                suggestions, each being a token list joined by space.
            meta (dict, optional): any additional info associated with the
                annotation. Defaults to an empty dict.

        Example:
            >>> t = AnnotatedTokens('the red fox')
            >>> t.annotate(1, 2, ['brown', 'white'])
            >>> t.get_annotated_text()
            'the {red=>brown|white} fox'
        """

        if start > end:
            raise ValueError(
                f"Start positition {start} should not greater "
                f"than end position {end}"
            )

        if meta is None:
            meta = dict()

        bad = " ".join(self._tokens[start:end])

        if isinstance(correct_value, str):
            suggestions = [correct_value]
        elif correct_value is None:
            suggestions = []
        else:
            suggestions = list(correct_value)

        new_ann = TokenAnnotation(start, end, bad, suggestions, meta)
        overlapping = self._get_overlaps(start, end)
        if overlapping:
            if callable(on_overlap):
                on_overlap(self, overlapping, new_ann)
            elif on_overlap == OnOverlap.SAVE_OLD:
                pass
            elif on_overlap == OnOverlap.OVERRIDE:
                for ann in overlapping:
                    self.remove(ann)
                self._annotations.append(new_ann)
            elif on_overlap == OnOverlap.ERROR:
                raise OverlapError(
                    f"Overlap detected: positions ({start}, {end}) with "
                    f"{len(overlapping)} existing annotations."
                )
            elif on_overlap == OnOverlap.MERGE_STRICT:
                merge_strict(self, overlapping, new_ann)
            elif on_overlap == OnOverlap.MERGE_EXPAND:
                merge_expand(self, overlapping, new_ann)
            else:
                raise ValueError(f"Unknown on_overlap action: {on_overlap}")
        else:
            self._annotations.append(new_ann)

    def _get_overlaps(self, start, end):
        """Find all annotations that overlap with given range."""

        res = []
        for ann in self._annotations:
            if span_intersect([(ann.start, ann.end)], start, end) != -1:
                res.append(ann)
            elif start == end and ann.start == ann.end and start == ann.start:
                res.append(ann)

        return res

    def get_annotations(self):
        """Return list of all annotations in the text."""
        return self._annotations

    def iter_annotations(self):
        """Iterate the annotations in the text.

        This differs from `get_annotations` in that you can safely modify
        current annotation during the iteration. Specifically, `remove` and
        `apply_correction` are allowed. Adding and modifying annotations other
        than the one being iterated is not yet well-defined!

        Example:
            >>> tokens = AnnotatedTokens('1 2 3')
            >>> tokens.annotate(0, 1, 'One')
            >>> tokens.annotate(1, 2, 'Two')
            >>> tokens.annotate(2, 3, 'Three')
            >>> for i, ann in enumerate(tokens.iter_annotations()):
            ...     if i == 0:
            ...         tokens.apply_correction(ann)
            ...     else:
            ...         tokens.remove(ann)
            >>> tokens.get_annotated_text()
            'One 2 3'

        Yields:
            TokenAnnotation instances.
        """

        n_anns = len(self._annotations)
        i = 0
        while i < n_anns:
            yield self._annotations[i]
            delta = len(self._annotations) - n_anns
            i += delta + 1
            n_anns = len(self._annotations)

    def get_annotation_at(self, start, end):
        """Return annotation for the region (start, end) or None."""

        for ann in self._annotations:
            if ann.start == start and ann.end == end:
                return ann

    def remove(self, annotation):
        """Remove annotation, replacing it with the original text."""

        try:
            self._annotations.remove(annotation)
        except ValueError:
            raise ValueError("{} is not in the list".format(annotation))

    def filter_annotations(self, f=None):
        """Filter annotations using function passed as an argument.

        Args:
            f: function receiving the annotation as argument and optionally
             the AnnotatedTokens object itself. If the function returns False,
             remove annotation.
        """

        f_param = inspect.signature(f).parameters.values() if f else []
        if len(f_param) not in [1, 2]:
            raise ValueError(
                "Filter function only accepts 1 or 2 arguments."
                "Arguments received: {}".format(f_param)
            )
        for ann in self.iter_annotations():
            if len(f_param) == 2:
                result = f(ann, self)
            else:
                result = f(ann)
            if not result:
                self.remove(ann)

    def apply_correction(self, annotation, level=0):
        """Remove annotation, replacing it with the corrected text.

        Example:
            >>> tokens = AnnotatedTokens('one too')
            >>> tokens.annotate(0, 1, 'ONE')
            >>> tokens.annotate(1, 2, 'two')
            >>> a = tokens.get_annotations()[0]
            >>> tokens.apply_correction(a)
            >>> tokens.get_annotated_text()
            'ONE {too=>two}'
        """

        try:
            self._annotations.remove(annotation)
        except ValueError:
            raise ValueError("{} is not in the list".format(annotation))

        tokens = MutableTokens(self._tokens)
        if annotation.suggestions:
            repl = annotation.suggestions[level]
        else:
            repl = annotation.source_text  # for NO_SUGGESTIONS annotations
        tokens.replace(annotation.start, annotation.end, repl)
        self._tokens = tokens.get_edited_tokens()

        # Adjust other annotations
        source_text = annotation.source_text
        old_len = len(source_text.split(" ")) if source_text else 0
        new_len = len(repl.split(" ")) if repl else 0
        delta = new_len - old_len
        for i, a in enumerate(self._annotations):
            if a.start >= annotation.start:
                a = a._replace(start=a.start + delta, end=a.end + delta)
                self._annotations[i] = a

    def get_original_tokens(self):
        """Return the original (unannotated) tokens.

        Example:
            >>> tokens = AnnotatedTokens('helo world !')
            >>> tokens.annotate(0, 1, 'Hello')
            >>> tokens.get_original_tokens()
            ['helo', 'world', '!']
        """

        return self._tokens

    def get_original_text(self):
        """Return the original (unannotated) text.

        Example:
            >>> tokens = AnnotatedTokens('helo world !')
            >>> tokens.annotate(0, 1, 'Hello')
            >>> tokens.get_original_text()
            'helo world !'
        """

        return " ".join(self.get_original_tokens())

    def get_corrected_tokens(self, level=0):
        """Return the unannotated tokens with all corrections applied.

        Example:
            >>> tokens = AnnotatedTokens('helo world !')
            >>> tokens.annotate(0, 1, 'Hello')
            >>> tokens.get_corrected_tokens()
            ['Hello', 'world', '!']
        """

        tokens = MutableTokens(self._tokens)
        for ann in self._annotations:
            try:
                tokens.replace(ann.start, ann.end, ann.suggestions[level])
            except IndexError:
                pass

        return tokens.get_edited_tokens()

    def get_corrected_text(self, level=0):
        """Return the corrected (unannotated) text.

        Example:
            >>> tokens = AnnotatedTokens('helo world !')
            >>> tokens.annotate(0, 1, 'Hello')
            >>> tokens.get_corrected_text()
            'Hello world !'
        """

        return " ".join(self.get_corrected_tokens(level))

    def get_annotated_text(self, *, with_meta=True):
        """Return the annotated tokens in text format.

        Example:
            >>> tokens = AnnotatedTokens('helo . world!')
            >>> tokens.annotate(0, 2, 'Hello ,', meta={'key': 'value'})
            >>> tokens.get_annotated_text(with_meta=False)
            '{helo .=>Hello ,} world!'
            >>> tokens.get_annotated_text()
            '{helo .=>Hello ,:::key=value} world!'
        """

        tokens = MutableTokens(self._tokens)
        for ann in self._annotations:
            tokens.replace(ann.start, ann.end, ann.to_str(with_meta=with_meta))

        return " ".join(tokens.get_edited_tokens(highlight=True))

    def combine(self, other, discard_overlap=True):
        """Combine annotations with other text's annotations.

        Args:
            other (AnnotatedTokens): Other text with annotations.
            discard_overlap (bool): If `False`, will raise an error when two
                annotations overlap, otherwise silently discards them, giving
                priority to current object's annotations.
        """

        if not isinstance(other, AnnotatedTokens):
            raise ValueError(
                "Expected `other` to be {}, received {}".format(
                    AnnotatedTokens, type(other)
                )
            )

        if self.get_original_text() != other.get_original_text():
            raise ValueError("Cannot combine with text from different " "original text")

        on_overlap = "save_old" if discard_overlap else "error"
        for ann in other.get_annotations():
            self.annotate(
                ann.start,
                ann.end,
                ann.suggestions,
                meta=ann.meta,
                on_overlap=on_overlap,
            )


class TokenAnnotation(
    namedtuple(
        "TokenAnnotation",
        ["start", "end", "source_text", "suggestions", "meta"],
    )
):
    """A single annotation in the list of tokens.

    Args:
        start: starting position in the original list of tokens.
        end: ending position in the original list of tokens.
        source_text: piece of the original tokens that is being corrected.
        suggestions: list of suggestions.
        meta (dict, optinal): additional data associated with the annotation.
    """

    def __new__(cls, start, end, source_text, suggestions, meta=DEFAULT):
        if meta is DEFAULT:
            meta = {}
        return super().__new__(cls, start, end, source_text, suggestions, meta)

    def __hash__(self):
        return hash(
            (
                self.start,
                self.end,
                self.source_text,
                tuple(self.suggestions),
                tuple(self.meta.items()),
            )
        )

    def __eq__(self, other):
        return (
            self.start == other.start
            and self.end == other.end
            and self.source_text == other.source_text
            and tuple(self.suggestions) == tuple(other.suggestions)
            and tuple(sorted(self.meta.items())) == tuple(sorted(other.meta.items()))
        )

    @property
    def top_suggestion(self):
        """Return the first suggestion or None if there are none."""

        return self.suggestions[0] if self.suggestions else None

    def to_str(self, *, with_meta=True):
        """Return a string representation of the annotation.

        Example:
            >>> ann = TokenAnnotation(0, 1, 'helo', ['hello', 'hola'])
            >>> ann.to_str()
            '{helo=>hello|hola}'

        """
        if self.suggestions:
            repl = "|".join(self.suggestions)
        else:
            repl = NO_SUGGESTIONS

        meta_text = self._format_meta() if with_meta else ""
        return "{%s=>%s%s}" % (self.source_text, repl, meta_text)

    def _format_meta(self):
        return "".join(":::{}={}".format(k, v) for k, v in self.meta.items())


def _unique_list(array):
    """Leave only unique elements in the list saving their order."""

    res = []
    for x in array:
        if x not in res:
            res.append(x)

    return res


def merge_strict(text, overlapping, new_ann):
    """On-overlap handler that merges two annotations that coincide in spans."""

    if len(overlapping) > 1:
        raise OverlapError(
            "Merge supports only 1-1 merges. "
            f"Call is done for {len(overlapping)}-1 merge."
        )

    existing = overlapping[0]
    if existing.start != new_ann.start or existing.end != new_ann.end:
        raise OverlapError(
            "Strict merge can be performed for annotations that "
            "share the span exactly."
        )

    suggestions = _unique_list(existing.suggestions + new_ann.suggestions)

    meta = {**existing.meta, **new_ann.meta}

    text.remove(existing)
    text.annotate(
        new_ann.start,
        new_ann.end,
        suggestions,
        meta=meta,
        on_overlap=OnOverlap.ERROR,
    )


def merge_expand(text, overlapping, new_ann):
    """On-overlap handler that merges two annotations possibly expanding spans."""

    if len(overlapping) > 1:
        raise OverlapError(
            "Merge supports only 1-1 merges. "
            f"Call is done for {len(overlapping)}-1 merge."
        )

    existing = overlapping[0]

    start = min(existing.start, new_ann.start)
    end = max(existing.end, new_ann.end)

    suggestions = []
    for annotation in (existing, new_ann):
        prefix = text._text[start : annotation.start]
        suffix = text._text[annotation.end : end]
        for sugg in annotation.suggestions:
            suggestions.append(prefix + sugg + suffix)

    suggestions = _unique_list(suggestions)

    meta = {**existing.meta, **new_ann.meta}

    text.remove(existing)
    text.annotate(start, end, suggestions, meta=meta, on_overlap=OnOverlap.ERROR)


def span_intersect(spans, begin, end):
    """Check if interval [begin, end) intersects with any of given spans.

    Args:
        spans: list of (begin, end) pairs.
        begin (int): starting position of the query interval.
        end (int): ending position of the query interval.

    Return:
        Index of a span that intersects with [begin, end),
            or -1 if no such span exists.
    """

    def strictly_inside(a, b, x, y):
        """Test that first segment is strictly inside second one."""
        return x < a <= b < y

    for index, (b, e) in enumerate(spans):
        overlap = max(0, min(end, e) - max(begin, b))
        if overlap:
            return index
        if strictly_inside(b, e, begin, end):
            return index
        if strictly_inside(begin, end, b, e):
            return index

    return -1
