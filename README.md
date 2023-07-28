# Gender-Inclusive Grammatical Error Correction through Augmentation

Evaluation datasets presented in [Gender-Inclusive Grammatical Error Correction through Augmentation](https://arxiv.org/abs/2306.07415) by Gunnar Lund, Kostiantyn Omelianchuk, and Igor Samokhin, presented at the 18th Workshop on Innovative Use of NLP for Building Educational Applications; co-located with ACL 2023.

## Data

* `bea_dev_195_st_aug(.m2|.src.txt|.tgt.txt)` - Singular *they* evaluation data, created from the BEA 2019 shared-task dev dataset ([Bryant et al., 2019](https://aclanthology.org/W19-4406/)) using an automated augmentation procedure and manually checked by a linguist for quality/consistency.
* `bea_dev_195_orig(.m2|.src.txt|.tgt.txt)` - Original parallel subset of the BEA 2019 shared-task dev dataset with minor edits to ensure consistency and parallelism with singular *they* dataset.
* `bea_dev_556_mf_aug(.m2|.src.txt|.tgt.txt)` - Masculine/feminine pronoun evaluation data, created from the BEA 2019 shared-task dev dataset using an automated augmentation procedure and manually checked by a linguist for quality/consistency.
* `bea_dev_556_orig(.m2|.src.txt|.tgt.txt)` - Original parallel subset of the BEA 2019 shared-task dev dataset with minor edits to ensure consistency and parallelism with masculine/feminine pronoun dataset.

## Scripts

All code that is required for generating `singular they` augmentation is located in `scripts` directory.

### Installation

The default way of installation is:

0. Make sure you have python 3.7+
1. Clone the repository.
2. `cd gender-inclusive-gec`
3. `pip install -r requirements.txt`
4. Install `neuralcoref==4.0.0` from the source as described here: https://github.com/huggingface/neuralcoref#install-neuralcoref-from-source
5. Download spacy model: `python -m spacy download en_core_web_lg`

### Demo

After the installation is done, to test how the code works, please try running `python scripts/demo.py`.  
Examples from demo.

```
Singular `they` augmentation:
1:      Original: She is a linguist .
        Augmented: They are a linguist .
2:      Original: She 's a linguist .
        Augmented: They 're a linguist .
3:      Original: When Gregor Samsa woke one morning from troubled dreams , he found himself transformed right there in his bed into some sort of monstrous insect .
        Augmented: When Gregor Samsa woke one morning from troubled dreams , they found themself transformed right there in their bed into some sort of monstrous insect .
4:      Original: The clock was striking as she stepped out into the street .
        Augmented: None
5:      Original: The universe ( which others call the Library ) is composed of an indefinite , perhaps infinite number of hexagonal galleries .
        Augmented: None
Singular `they` augmentation for GEC:
1       No augment produced!
        Source: It 's a linguist .
        Target: She is a linguist .
        Aligned: {It 's=>She is} a linguist .
2       Source: She 's an linguist .
        Target: She 's a linguist .
        Aligned: She 's {an=>a} linguist .
        Augmented Swapped: They 're an linguist .
        Augmented Target: They 're a linguist .
3       Source: When Gregor Samsa waked one morning from troubled dreams , he finds himself transformed right there in his bed into some sore of monstrous insect .
        Target: When Gregor Samsa woke one morning from troubled dreams , he found himself transformed right there in his bed into some sort of monstrous insect .
        Aligned: When Gregor Samsa {waked=>woke} one morning from troubled dreams , he {finds=>found} himself transformed right there in his bed into some {sore=>sort} of monstrous insect .
        Augmented Swapped: When Gregor Samsa waked one morning from troubled dreams , they found themself transformed right there in their bed into some sore of monstrous insect .
        Augmented Target: When Gregor Samsa woke one morning from troubled dreams , they found themself transformed right there in their bed into some sort of monstrous insect .
4       No augment produced!
        Source: The clock striking as she stepped out into the street .
        Target: The clock was striking as she stepped out into the street .
        Aligned: The clock {=>was} striking as she stepped out into the street .
5       No augment produced!
        Source: The universe ( which others call the Library ) is composed of indefinitely , perhaps infinite number of hexagonal galleries .
        Target: The universe ( which others call the Library ) is composed of an indefinite , perhaps infinite number of hexagonal galleries .
        Aligned: The universe ( which others call the Library ) is composed of {indefinitely=>an indefinite} , perhaps infinite number of hexagonal galleries .
```

## Citation

```
@inproceedings{lund-etal-2023-gender,
    title = "Gender-Inclusive Grammatical Error Correction through Augmentation",
    author = "Lund, Gunnar  and
      Omelianchuk, Kostiantyn  and
      Samokhin, Igor",
    booktitle = "Proceedings of the 18th Workshop on Innovative Use of NLP for Building Educational Applications (BEA 2023)",
    month = jul,
    year = "2023",
    address = "Toronto, Canada",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2023.bea-1.13",
    pages = "148--162",
    abstract = "In this paper we show that GEC systems display gender bias related to the use of masculine and feminine terms and the gender-neutral singular {``}they{''}. We develop parallel datasets of texts with masculine and feminine terms, and singular {``}they{''}, and use them to quantify gender bias in three competitive GEC systems. We contribute a novel data augmentation technique for singular {``}they{''} leveraging linguistic insights about its distribution relative to plural {``}they{''}. We demonstrate that both this data augmentation technique and a refinement of a similar augmentation technique for masculine and feminine terms can generate training data that reduces bias in GEC systems, especially with respect to singular {``}they{''} while maintaining the same level of quality.",
}
```
