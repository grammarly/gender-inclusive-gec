from st_augmentor import singular_they_augmentor
from gec_st_augmentor import st_augmentor_for_gec
from utils.align import align



texts = [
    'She is a linguist .', # Coreference with singular common noun.
    "She 's a linguist .", # Same but with a contraction.
    'When Gregor Samsa woke one morning from troubled dreams , he found himself transformed right there in his bed into some sort of monstrous insect .', # Coreference with NNP
    'The clock was striking as she stepped out into the street .', # No singularizing coreference
    'The universe ( which others call the Library ) is composed of an indefinite , perhaps infinite number of hexagonal galleries .' # No swappable pronoun
]

ungrammatical_texts = [
    "It \'s a linguist .", # Source doesn't support a safe swap
    "She \'s an linguist .", # Same but with a contraction, and a safe swap
    'When Gregor Samsa waked one morning from troubled dreams , he finds himself transformed right there in his bed into some sore of monstrous insect .', # Errors permit swaps
    'The clock striking as she stepped out into the street .', # No singularizing coreference, no swap
    'The universe ( which others call the Library ) is composed of indefinitely , perhaps infinite number of hexagonal galleries .' # No swappable pronoun, no swap
]

print('Singular `they` augmentation:')
for i, text in enumerate(texts):
    print(f'{i+1}:\tOriginal: {text}\n\tAugmented: {singular_they_augmentor(text)}')

print('Singular `they` augmentation for GEC:')
for i, (src, tgt) in enumerate(zip(ungrammatical_texts, texts)):
    augment = st_augmentor_for_gec(src, tgt)
    if augment:
        src_swapped, tgt_swapped = augment
        print(f'{i+1}\tSource: {src}\n\tTarget: {tgt}\n\tAligned: {align(src, tgt)}\n\tAugmented Swapped: {src_swapped}\n\tAugmented Target: {tgt_swapped}')
    else:
        print(f'{i+1}\tNo augment produced!\n\tSource: {src}\n\tTarget: {tgt}\n\tAligned: {align(src, tgt)}')
