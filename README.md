# Gender-Inclusive Grammatical Error Correction through Augmentation

Evaluation datasets presented in [Gender-Inclusive Grammatical Error Correction through Augmentation](https://arxiv.org/abs/2306.07415) by Gunnar Lund, Kostiantyn Omelianchuk, and Igor Samokhin, presented at the 18th Workshop on Innovative Use of NLP for Building Educational Applications; co-located with ACL 2023.

## Data

* `bea_dev_195_st_aug(.m2|.src.txt|.tgt.txt)` - Singular *they* evaluation data, created from the BEA 2019 shared-task dev dataset ([Bryant et al., 2019](https://aclanthology.org/W19-4406/)) using an automated augmentation procedure and manually checked by a linguist for quality/consistency.
* `bea_dev_195_orig(.m2|.src.txt|.tgt.txt)` - Original parallel subset of the BEA 2019 shared-task dev dataset with minor edits to ensure consistency and parallelism with singular *they* dataset.
* `bea_dev_556_mf_aug(.m2|.src.txt|.tgt.txt)` - Masculine/feminine pronoun evaluation data, created from the BEA 2019 shared-task dev dataset using an automated augmentation procedure and manually checked by a linguist for quality/consistency.
* `bea_dev_556_orig(.m2|.src.txt|.tgt.txt)` - Original parallel subset of the BEA 2019 shared-task dev dataset with minor edits to ensure consistency and parallelism with masculine/feminine pronoun dataset.

## Scripts
The code for generating augmented data will be added soon.

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
